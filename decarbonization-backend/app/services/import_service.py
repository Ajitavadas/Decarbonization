from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Tuple
from app.models.models import EmissionTransaction, AuditLog

class ImportService:
    """Service for handling bulk import operations"""
    
    @staticmethod
    async def bulk_insert_transactions(
        db: AsyncSession,
        transactions: List[EmissionTransaction],
        batch_size: int = 1000
    ) -> Tuple[int, List[str]]:
        """
        Bulk insert transactions in batches
        
        Args:
            db: Database session
            transactions: List of EmissionTransaction objects
            batch_size: Number of records per batch (default: 1000)
            
        Returns:
            (successful_count, error_list)
        """
        successful = 0
        errors = []
        
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            try:
                db.add_all(batch)
                await db.commit()
                successful += len(batch)
            except Exception as e:
                await db.rollback()
                errors.append(f"Batch {i//batch_size + 1}: {str(e)}")
        
        return successful, errors
    
    @staticmethod
    async def check_duplicates(
        db: AsyncSession,
        org_id: str,
        transactions: List[dict]
    ) -> Tuple[List[dict], List[dict]]:
        """
        Check for duplicate transactions
        
        Args:
            db: Database session
            org_id: Organization ID
            transactions: List of transaction dictionaries
            
        Returns:
            (unique_transactions, duplicate_errors)
        """
        unique_transactions = []
        duplicate_errors = []
        seen = set()
        
        # Check for internal duplicates
        for tx in transactions:
            key = (
                tx['description'],
                str(tx['transaction_date']),
                tx['scope'],
                tx['category']
            )
            
            if key in seen:
                duplicate_errors.append({
                    "row": tx.get('_row_num'),
                    "error": "Duplicate transaction (matches previous row)"
                })
            else:
                seen.add(key)
                unique_transactions.append(tx)
        
        return unique_transactions, duplicate_errors
    
    @staticmethod
    async def create_audit_log(
        db: AsyncSession,
        org_id: str,
        user_id: str,
        import_id: str,
        success_count: int,
        error_count: int,
        filename: str,
        processing_time: float
    ):
        """
        Create audit log for import operation
        
        Args:
            db: Database session
            org_id: Organization ID
            user_id: User ID
            import_id: Import job ID
            success_count: Number of successful imports
            error_count: Number of failed rows
            filename: Name of imported file
            processing_time: Time taken for processing in seconds
        """
        
        audit_log = AuditLog(
            organization_id=org_id,
            user_id=user_id,
            action="CSV_BULK_IMPORT",
            resource_type="EmissionTransaction",
            description=f"Bulk imported {success_count} transactions from {filename}",
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