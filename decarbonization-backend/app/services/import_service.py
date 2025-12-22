from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Tuple, Any
from app.models.models import EmissionEvent, CalculationLedger, AuditTrail

class ImportService:
    """Service for handling bulk import operations with new schema"""
    
    @staticmethod
    async def bulk_insert_import(
        db: AsyncSession,
        events: List[EmissionEvent],
        ledgers: List[CalculationLedger],
        batch_size: int = 100
    ) -> Tuple[int, List[str]]:
        """
        Bulk insert events and their corresponding calculation results
        """
        successful = 0
        errors = []
        
        for i in range(0, len(events), batch_size):
            evt_batch = events[i:i + batch_size]
            ldgr_batch = ledgers[i:i + batch_size]
            try:
                db.add_all(evt_batch)
                await db.flush() # Ensure event IDs are generated for ledger FK
                
                # Update ledger FKs if needed (though they should be linked in the objects)
                db.add_all(ldgr_batch)
                await db.commit()
                successful += len(evt_batch)
            except Exception as e:
                await db.rollback()
                errors.append(f"Batch {i//batch_size + 1}: {str(e)}")
        
        return successful, errors
    
    @staticmethod
    async def create_audit_log(
        db: AsyncSession,
        org_id: Any,
        user_id: Any,
        import_id: str,
        success_count: int,
        error_count: int,
        filename: str,
        processing_time: float
    ):
        """Create audit log using AuditTrail"""
        
        audit_log = AuditTrail(
            organization_id=org_id,
            actor_user_id=user_id,
            action_type="CSV_BULK_IMPORT",
            resource_type="EmissionEvent",
            new_values={
                "import_id": import_id,
                "filename": filename,
                "successful": success_count,
                "failed": error_count,
                "processing_time_seconds": round(processing_time, 2)
            }
        )
        
        db.add(audit_log)
        await db.commit()