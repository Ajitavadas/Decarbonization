from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import uuid
from typing import Dict, Optional
import json

import redis.asyncio as redis

from app.database import get_db, async_session
from app.auth.oauth2_scheme import get_current_user
from app.models.models import User
from app.services.csv_service import CSVParsingService
from app.services.import_service import ImportService

router = APIRouter(prefix="/api/v1/import", tags=["csv_import"])

# Result storage: use Redis when available, with in-memory fallback for dev/tests
REDIS_URL = "redis://redis:6379/0"
redis_client: Optional[redis.Redis] = redis.from_url(REDIS_URL, decode_responses=True)

# In-memory fallback store for import results (used if Redis unavailable)
import_results: Dict[str, dict] = {}


async def _store_import_result(import_id: str, data: dict) -> None:
    """Persist import status/result to Redis if available, else in-memory."""
    payload = json.dumps(data)
    try:
        if redis_client:
            await redis_client.set(f"import:{import_id}", payload)
            return
    except Exception:
        # Fall back to in-memory store on any Redis error
        pass
    import_results[import_id] = data


async def _get_import_result(import_id: str) -> Optional[dict]:
    """Retrieve import status/result from Redis or in-memory fallback."""
    try:
        if redis_client:
            raw = await redis_client.get(f"import:{import_id}")
            if raw:
                return json.loads(raw)
    except Exception:
        pass
    return import_results.get(import_id)

@router.post("/csv", status_code=202, response_model=dict)
async def upload_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload CSV file for bulk emission import
    
    Args:
        file: CSV or XLSX file to upload
        db: Database session
        current_user: Authenticated user
        background_tasks: Background task runner
        
    Returns:
        {
            "import_id": "uuid-string",
            "status": "pending",
            "message": "File accepted. Processing started."
        }
    """
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    
    if not file.filename.endswith(('.csv', '.xlsx')):
        raise HTTPException(
            status_code=400,
            detail="File must be CSV or XLSX format"
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size (max 50MB)
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum size: 50MB"
        )
    
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="File is empty"
        )
    
    # Create import job record
    import_id = str(uuid.uuid4())
    
    # Initialize result entry
    initial_result = {
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
    }
    await _store_import_result(import_id, initial_result)
    
    # Queue for background processing
    background_tasks.add_task(
        process_csv_import,
        import_id=import_id,
        file_content=content,
        filename=file.filename,
        user_id=current_user.id,
        org_id=current_user.organization_id,
    )
    
    return {
        "import_id": import_id,
        "status": "pending",
        "message": "File accepted. Processing started."
    }

async def process_csv_import(
    import_id: str,
    file_content: bytes,
    filename: str,
    user_id: str,
    org_id: str,
):
    """
    Background task to process CSV import
    """
    from app.models.models import EmissionTransaction, AuditLog
    
    start_time = datetime.now(timezone.utc)
    
    # Dedicated DB session for background task
    async with async_session() as db:
    try:
            # Parse file (CSV or XLSX)
            if filename.lower().endswith(".csv"):
        valid_rows, error_rows = CSVParsingService.parse_csv(file_content)
            elif filename.lower().endswith(".xlsx"):
                valid_rows, error_rows = CSVParsingService.parse_xlsx(file_content)
            else:
                valid_rows, error_rows = [], [{"row": 0, "error": "Unsupported file type"}]
            
            # Check for internal duplicates
            unique_rows, duplicate_errors = await ImportService.check_duplicates(db, org_id, valid_rows)
            error_rows.extend(duplicate_errors)
        
        total_rows = len(valid_rows) + len(error_rows)
        
            # Process valid unique rows
        transaction_objects = []
            for row in unique_rows:
            try:
                co2e_kg, co2e_tonnes = CSVParsingService.calculate_co2e(
                    float(row['activity_value']),
                    float(row['emission_factor_value'])
                )
                
                transaction = EmissionTransaction(
                    organization_id=org_id,
                    description=row['description'].strip(),
                    transaction_date=datetime.fromisoformat(
                        row['transaction_date'].replace('Z', '+00:00')
                    ),
                    scope=int(row['scope']),
                    category=row['category'].strip(),
                    activity_value=float(row['activity_value']),
                    activity_unit=row['activity_unit'].strip(),
                    emission_factor_value=float(row['emission_factor_value']),
                    co2e_kg=co2e_kg,
                    co2e_tonnes=co2e_tonnes,
                    supplier_name=row.get('supplier_name', '').strip() or None,
                    project_id=row.get('project_id', '').strip() or None,
                    notes=row.get('notes', '').strip() or None,
                    created_by_user_id=user_id
                )
                transaction_objects.append(transaction)
            except Exception as e:
                error_rows.append({
                    "row": row.get("_row_num", "?"),
                    "error": f"Processing error: {str(e)}"
                })
        
            # Bulk insert
        if transaction_objects:
                successful, batch_errors = await ImportService.bulk_insert_transactions(db, transaction_objects)
                for idx, err in enumerate(batch_errors, start=1):
                    error_rows.append({"row": f"batch-{idx}", "error": err})
            else:
                successful = 0
            
            # Processing time
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Audit log
            await ImportService.create_audit_log(
                db=db,
                org_id=org_id,
            user_id=user_id,
                import_id=import_id,
                success_count=successful,
                error_count=len(error_rows),
                filename=filename,
                processing_time=processing_time,
            )
        
            # Persist result
            result = {
            "import_id": import_id,
            "status": "completed",
            "user_id": user_id,
            "org_id": org_id,
            "filename": filename,
            "total_rows": total_rows,
                "successful_rows": successful,
            "failed_rows": len(error_rows),
            "errors": error_rows,
            "processing_time_seconds": round(processing_time, 2),
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
            await _store_import_result(import_id, result)
        
    except Exception as e:
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # Log error
        error_log = AuditLog(
            organization_id=org_id,
            user_id=user_id,
            action="CSV_BULK_IMPORT_FAILED",
            resource_type="EmissionTransaction",
            description=f"CSV import failed: {str(e)}"
        )
        db.add(error_log)
        await db.commit()
        
            # Persist failure result
            result = {
            "import_id": import_id,
            "status": "failed",
            "user_id": user_id,
            "org_id": org_id,
            "filename": filename,
            "error": str(e),
            "processing_time_seconds": round(processing_time, 2),
            "failed_at": datetime.now(timezone.utc).isoformat()
        }
            await _store_import_result(import_id, result)

@router.get("/csv/{import_id}", response_model=dict)
async def get_import_status(
    import_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get status and results of CSV import
    
    Args:
        import_id: UUID of the import job
        current_user: Authenticated user
        
    Returns:
        {
            "import_id": "uuid",
            "status": "pending|processing|completed|failed",
            "total_rows": 1000,
            "successful_rows": 995,
            "failed_rows": 5,
            "errors": [
                {"row": 15, "error": "Invalid scope value"}
            ],
            "processing_time_seconds": 12.5
        }
    """
    
    result = await _get_import_result(import_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Import job not found"
        )
    
    # Verify user owns this import
    if result.get('user_id') != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized"
        )
    
    return result

@router.get("/csv/{import_id}/errors")
async def get_import_errors(
    import_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed error report for import
    
    Returns:
        {
            "total_errors": 5,
            "errors": [
                {"row": 15, "error": "Invalid scope value"},
                ...
            ]
        }
    """
    
    result = await _get_import_result(import_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Import job not found"
        )
    
    # Verify user owns this import
    if result.get('user_id') != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized"
        )
    
    return {
        "import_id": import_id,
        "total_errors": len(result.get('errors', [])),
        "errors": result.get('errors', [])
    }