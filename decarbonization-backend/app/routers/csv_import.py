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
from app.models.models import User, EmissionTransaction, AuditLog
from app.services.csv_service import CSVParsingService
from app.services.import_service import ImportService

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
    
    return {"import_id": import_id, "status": "pending"}

async def process_import(
    import_id: str,
    file_content: bytes,
    filename: str,
    user_id: str,
    org_id: str,
):
    """Background processor"""
    from app import async_session
    
    start = datetime.now(timezone.utc)
    async with async_session() as db:
        try:
            # Parse
            if filename.lower().endswith('.csv'):
                rows, errors = CSVParsingService.parse_csv(file_content)
            else:
                rows, errors = CSVParsingService.parse_xlsx(file_content)
            
            # AI Classification
            if rows:
                enhanced_rows, ai_errors = await CSVParsingService.classify_and_enhance_rows(rows)
                errors.extend(ai_errors)
            else:
                enhanced_rows = rows
            
            # Deduplicate
            unique_rows, dup_errors = await ImportService.check_duplicates(db, org_id, enhanced_rows)
            errors.extend(dup_errors)
            
            # Create transactions
            transactions = []
            for row in unique_rows:
                try:
                    co2e_kg, co2e_tonnes = CSVParsingService.calculate_co2e(
                        float(row['activity_value']),
                        float(row['emission_factor_value'])
                    )
                    
                    final_scope = int(row['scope']) if row.get('ai_needs_review', True) else int(row['ai_scope_prediction'])
                    
                    transactions.append(EmissionTransaction(
                        organization_id=org_id,
                        description=row['description'].strip(),
                        transaction_date=datetime.fromisoformat(row['transaction_date'].replace('Z', '+00:00')),
                        scope=final_scope,
                        category=row['category'].strip(),
                        activity_value=float(row['activity_value']),
                        activity_unit=row['activity_unit'].strip(),
                        emission_factor_value=float(row['emission_factor_value']),
                        co2e_kg=co2e_kg,
                        co2e_tonnes=co2e_tonnes,
                        ai_scope_prediction=row.get('ai_scope_prediction'),
                        ai_confidence_score=row.get('ai_confidence_score'),
                        ai_needs_review=row.get('ai_needs_review', False),
                        supplier_name=row.get('supplier_name', '').strip() or None,
                        project_id=row.get('project_id', '').strip() or None,
                        notes=row.get('notes', '').strip() or None,
                        created_by_user_id=user_id
                    ))
                except Exception as e:
                    errors.append({"row": row.get('_row_num', '?'), "error": str(e)})
            
            # Insert
            successful = 0
            if transactions:
                successful, batch_errors = await ImportService.bulk_insert_transactions(db, transactions)
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