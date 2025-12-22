# app/routers/csv_import.py
"""
CSV Import Router with AI Classification - FIXED Syntax Error
Issue: background_tasks must come before parameters with defaults
"""

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import uuid
import json
import logging
from typing import Optional, Dict

import redis.asyncio as redis

from app.database import get_db, async_session as app_async_session
from app.auth.oauth2_scheme import get_current_user
from app.models.models import User, EmissionEvent, CalculationLedger, AuditTrail
from app.services.csv_service import CSVParsingService
from app.services.import_service import ImportService
from app.services.location_service import LocationService
from app.services.calculation_service import CalculationService
from app.schemas.emissions import StandardizedEmissionEvent

router = APIRouter(prefix="/api/v1/import", tags=["csv_import"])

logger = logging.getLogger(__name__)

# Redis client (lazy init)
_redis_client: Optional[redis.Redis] = None

async def _get_redis() -> Optional[redis.Redis]:
    """Get Redis client with fallback"""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url("redis://redis:6379", decode_responses=True)
            await _redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis fallback active: {e}")
            _redis_client = None
    return _redis_client

# In-memory fallback
_import_results: Dict[str, dict] = {}

async def _store_result(import_id: str, data: dict) -> None:
    """Store result in Redis or memory"""
    try:
        redis_client = await _get_redis()
        if redis_client:
            await redis_client.set(f"import:{import_id}", json.dumps(data), ex=7200)
            return
    except Exception:
        pass
    _import_results[import_id] = data

async def _get_result(import_id: str) -> Optional[dict]:
    """Retrieve result"""
    try:
        redis_client = await _get_redis()
        if redis_client:
            raw = await redis_client.get(f"import:{import_id}")
            if raw:
                return json.loads(raw)
    except Exception:
        pass
    return _import_results.get(import_id)

@router.post("/csv", status_code=status.HTTP_202_ACCEPTED)
async def upload_csv(
    background_tasks: BackgroundTasks,  # ✅ FIXED: Moved to first position
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload CSV/XLSX for bulk import"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    
    if not file.filename.endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="File must be CSV or XLSX")
    
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    
    import_id = str(uuid.uuid4())
    await _store_result(import_id, {
        "import_id": import_id,
        "status": "pending",
        "user_id": current_user.id,
        "org_id": current_user.organization_id,
        "filename": file.filename,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_rows": 0,
        "successful_rows": 0,
        "failed_rows": 0,
        "errors": [],
        "processing_time_seconds": 0
    })
    
    background_tasks.add_task(process_import, import_id, content, file.filename, current_user.id, current_user.organization_id)
    # DEBUG: Run synchronously to verify logic
    # await process_import(import_id, content, file.filename, current_user.id, current_user.organization_id)
    
    return {"import_id": import_id, "status": "pending"}

async def process_import(
    import_id: str,
    file_content: bytes,
    filename: str,
    user_id: str,
    org_id: str,
):
    """Background processor"""
    from app.database import async_session
    
    start = datetime.now(timezone.utc)
    logger.info(f"Processing import {import_id} started for {filename}")
    async with async_session() as db:
        try:
            logger.info(f"Parsing file content length: {len(file_content)}")
            # 1. Raw Parse (capture all data, no validation yet)
            if filename.lower().endswith('.csv'):
                rows, parse_errors = CSVParsingService.parse_csv(file_content, validate=False)
            else:
                rows, parse_errors = CSVParsingService.parse_xlsx(file_content, validate=False)
            
            errors = parse_errors
            
            # 2. Universal Semantic Adapter (AI Header Mapping)
            if rows:
                first_row = rows[0]
                # Check for standard headers
                standard_keys = set(CSVParsingService.REQUIRED_COLUMNS.keys())
                row_keys = set(first_row.keys())
                overlap = len(standard_keys.intersection(row_keys))
                
                # If low overlap, likely messy headers -> trigger AI
                if overlap < 3:
                    logger.info(f"Low schema overlap ({overlap}/7). Triggering Semantic Adapter...")
                    try:
                        from app.services.semantic_adapter_service import semantic_adapter
                        mapping = await semantic_adapter.map_headers(list(first_row.keys()))
                        rows = semantic_adapter.normalize_rows(rows, mapping)
                        logger.info("Semantic normalization complete.")
                    except Exception as e:
                        logger.error(f"Semantic adapter failed: {e}")
                        errors.append({"row": 0, "error": f"Semantic mapping failed: {str(e)}"})
            
            # 3. Row Refinement (Data Refiner)
            # Use Semaphore to limit concurrent AI calls
            import asyncio
            from app.services.semantic_adapter_service import semantic_adapter
            from app.schemas.emissions import StandardizedEmissionEvent
            
            logger.info(f"Starting Data Refiner for {len(rows)} rows...")
            sem = asyncio.Semaphore(10) # Process 10 rows concurrently

            async def refine_row_wrapper(row_data):
                async with sem:
                    return await semantic_adapter.normalize_row(row_data, org_id)

            tasks = [refine_row_wrapper(row) for row in rows]
            # Use return_exceptions=True to continue even if one fails
            refined_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 4. Construct Events and Calculations
            events_to_save = []
            ledgers_to_save = []
            valid_refined_count = 0
            
            for i, result in enumerate(refined_results):
                original_row = rows[i]
                row_num = original_row.get('_row_num', '?')
                
                if isinstance(result, Exception):
                    errors.append({"row": row_num, "error": f"Refinement failed: {str(result)}"})
                    continue
                
                if not result:
                    errors.append({"row": row_num, "error": "AI could not refine row"})
                    continue
                    
                valid_refined_count += 1
                event_schema: StandardizedEmissionEvent = result
                
                # 1. Geographer: Find Region
                grid_region_id = None
                if event_schema.location.latitude and event_schema.location.longitude:
                    try:
                        region = await LocationService.get_region_by_coordinates(
                            db, event_schema.location.latitude, event_schema.location.longitude
                        )
                        if region:
                            grid_region_id = region.code
                    except Exception as loc_err:
                        logger.warning(f"Row {row_num}: Location lookup failed: {loc_err}")

                # 2. Analyst: Calculate Emissions
                try:
                    calc_result = await CalculationService.calculate_emissions(db, event_schema)
                except Exception as calc_err:
                    logger.error(f"Row {row_num}: Calculation failed: {calc_err}")
                    errors.append({"row": row_num, "error": f"Calculation failed: {calc_err}"})
                    continue

                # 3. Create Models
                try:
                    # EmissionEvent (Phase 1)
                    new_event = EmissionEvent(
                        organization_id=org_id,
                        activity_date=event_schema.timestamp,
                        activity_value=event_schema.activity_value,
                        activity_unit_raw=original_row.get('unit', event_schema.activity_unit),
                        activity_unit_normalized=event_schema.activity_unit,
                        activity_value_normalized=event_schema.activity_value,
                        source_type="csv_import",
                        scope=event_schema.activity_type, # Placeholder for scope if not classified yet
                        activity_id_matched=event_schema.activity_id,
                        confidence_score=event_schema.data_quality.confidence_score
                    )
                    
                    # CalculationLedger (Phase 2)
                    new_ledger = CalculationLedger(
                        organization_id=org_id,
                        batch_id=import_id,
                        emission_event=new_event,
                        activity_value=event_schema.activity_value,
                        activity_unit_normalized=event_schema.activity_unit,
                        emission_factor_id=uuid.UUID(calc_result.factor_used.get('id')) if calc_result.factor_used.get('id') else None,
                        emission_factor_value=calc_result.factor_used.get('value', 0.0),
                        result_kg_co2e=calc_result.location_based_co2e_kg,
                        result_kg_total=calc_result.location_based_co2e_kg,
                        fell_back_to_climatiq=calc_result.calculation_method == 'climatiq',
                        calculated_by_user_id=user_id
                    )
                    
                    events_to_save.append(new_event)
                    ledgers_to_save.append(new_ledger)
                except Exception as e:
                    errors.append({"row": row_num, "error": f"Model mapping failed: {e}"})

            # 5. AI Classification (Scope) - Integrate the new classifier
            if events_to_save:
                try:
                    from app.services.ai_classifier_service import ai_classifier
                    # Prepare rows for classifier from event schemas
                    rows_to_classify = [
                        {
                            "description": rows[i].get('description', ''),
                            "category": events_to_save[i].scope, # initial activity_type
                            "unit": events_to_save[i].activity_unit_normalized,
                            "value": float(events_to_save[i].activity_value)
                        }
                        for i in range(len(events_to_save))
                    ]
                    classifications = await ai_classifier.classify_batch(rows_to_classify)
                    for i, cls in enumerate(classifications):
                        events_to_save[i].scope = cls.get('scope', 'Scope 3')
                        events_to_save[i].scope_3_category = cls.get('scope3Category')
                except Exception as ai_err:
                    logger.error(f"AI Classification failed: {ai_err}")

            # 6. Insert
            successful = 0
            if events_to_save:
                successful, batch_errors = await ImportService.bulk_insert_import(db, events_to_save, ledgers_to_save)
                errors.extend([{"row": f"batch-{i}", "error": err} for i, err in enumerate(batch_errors)])
            
            # Audit
            duration = (datetime.now(timezone.utc) - start).total_seconds()
            await ImportService.create_audit_log(db, org_id, user_id, import_id, successful, len(errors), filename, duration)
            
            await _store_result(import_id, {
                "import_id": import_id,
                "status": "completed",
                "user_id": user_id,
                "org_id": org_id,
                "filename": filename,
                "total_rows": len(rows) + len(errors),
                "successful_rows": successful,
                "failed_rows": len(errors),
                "errors": errors,
                "processing_time_seconds": round(duration, 2),
                "completed_at": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            logger.error(f"Import failed {import_id}: {str(e)}")
            await _store_result(import_id, {
                "import_id": import_id,
                "status": "failed",
                "user_id": user_id,
                "org_id": org_id,
                "filename": filename,
                "error": str(e),
                "failed_at": datetime.now(timezone.utc).isoformat()
            })

@router.get("/csv/{import_id}", status_code=200)
async def get_import_status(import_id: str, current_user: User = Depends(get_current_user)):
    """Get import status"""
    result = await _get_result(import_id)
    if not result:
        raise HTTPException(status_code=404, detail="Import not found")
    
    if result.get('user_id') != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return result

@router.get("/csv/{import_id}/errors", status_code=200)
async def get_import_errors(import_id: str, current_user: User = Depends(get_current_user)):
    """Get import errors"""
    result = await _get_result(import_id)
    if not result:
        raise HTTPException(status_code=404, detail="Import not found")
    
    if result.get('user_id') != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return {"import_id": import_id, "errors": result.get('errors', [])}