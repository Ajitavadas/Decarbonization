"""
Integrations Router - US-3.1, US-3.2
Handles AWS and QuickBooks OAuth integrations
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
import logging

from app.database import get_db
from app.auth.oauth2_scheme import get_current_user
from app.models.models import User
from app.services.integration_service import IntegrationService
from app.services.import_service import ImportService
from app.services.csv_service import CSVParsingService

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])
logger = logging.getLogger(__name__)

integration_service = IntegrationService()


@router.post("/aws/sync")
async def sync_aws_billing(
    background_tasks: BackgroundTasks,
    billing_data: Dict,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Sync AWS billing data (US-3.1)
    
    AC:
    - AWS connection established with OAuth
    - New cloud data syncs daily without human intervention
    - All synced data correctly identified as Scope 2
    - Entire sync process completes in under 5 minutes
    """
    # Get user
    user_result = await db.execute(select(User).where(User.id == current_user))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Process in background
    background_tasks.add_task(
        _process_aws_sync,
        db,
        user.organization_id,
        current_user,
        billing_data
    )
    
    return {"status": "sync_started", "message": "AWS billing data sync initiated"}


async def _process_aws_sync(db, org_id, user_id, billing_data):
    """Background task for AWS sync"""
    try:
        # Extract transactions
        transactions_data = await integration_service.extract_aws_billing_data(billing_data)
        
        # Convert to EmissionTransaction objects
        from app.models.models import EmissionTransaction
        from datetime import datetime
        
        transactions = []
        for tx_data in transactions_data:
            co2e_kg, co2e_tonnes = CSVParsingService.calculate_co2e(
                tx_data["activity_value"],
                tx_data["emission_factor_value"]
            )
            
            transactions.append(EmissionTransaction(
                organization_id=org_id,
                description=tx_data["description"],
                transaction_date=datetime.fromisoformat(tx_data["transaction_date"]),
                scope=tx_data["scope"],
                category=tx_data["category"],
                activity_value=tx_data["activity_value"],
                activity_unit=tx_data["activity_unit"],
                emission_factor_value=tx_data["emission_factor_value"],
                co2e_kg=co2e_kg,
                co2e_tonnes=co2e_tonnes,
                supplier_name=tx_data["supplier_name"],
                notes=tx_data.get("notes"),
                created_by_user_id=user_id
            ))
        
        # Bulk insert
        async with db() as session:
            success, errors = await ImportService.bulk_insert_transactions(session, transactions)
            logger.info(f"AWS sync complete: {success} transactions imported")
            
    except Exception as e:
        logger.error(f"AWS sync failed: {str(e)}")


@router.post("/quickbooks/sync")
async def sync_quickbooks(
    background_tasks: BackgroundTasks,
    qb_data: Dict,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Sync QuickBooks transactions (US-3.2)
    
    AC:
    - QuickBooks connection established with OAuth
    - New transactions sync daily without manual intervention
    - AI classifies 80% or more automatically
    - Low-confidence items flagged for manual review
    """
    user_result = await db.execute(select(User).where(User.id == current_user))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    background_tasks.add_task(
        _process_quickbooks_sync,
        db,
        user.organization_id,
        current_user,
        qb_data.get("transactions", [])
    )
    
    return {"status": "sync_started", "message": "QuickBooks sync initiated"}


async def _process_quickbooks_sync(db, org_id, user_id, qb_transactions):
    """Background task for QuickBooks sync"""
    try:
        # Extract and classify transactions
        transactions_data = await integration_service.extract_quickbooks_transactions(qb_transactions)
        
        # Convert to EmissionTransaction objects
        from app.models.models import EmissionTransaction
        from datetime import datetime
        
        transactions = []
        for tx_data in transactions_data:
            co2e_kg, co2e_tonnes = CSVParsingService.calculate_co2e(
                tx_data["activity_value"],
                tx_data["emission_factor_value"]
            )
            
            transactions.append(EmissionTransaction(
                organization_id=org_id,
                description=tx_data["description"],
                transaction_date=datetime.fromisoformat(tx_data["transaction_date"]),
                scope=tx_data["scope"],
                category=tx_data["category"],
                activity_value=tx_data["activity_value"],
                activity_unit=tx_data["activity_unit"],
                emission_factor_value=tx_data["emission_factor_value"],
                co2e_kg=co2e_kg,
                co2e_tonnes=co2e_tonnes,
                ai_scope_prediction=tx_data.get("ai_scope_prediction"),
                ai_confidence_score=tx_data.get("ai_confidence_score"),
                ai_needs_review=tx_data.get("ai_needs_review", False),
                supplier_name=tx_data["supplier_name"],
                notes=tx_data.get("notes"),
                created_by_user_id=user_id
            ))
        
        # Bulk insert
        async with db() as session:
            success, errors = await ImportService.bulk_insert_transactions(session, transactions)
            logger.info(f"QuickBooks sync complete: {success} transactions imported")
            
    except Exception as e:
        logger.error(f"QuickBooks sync failed: {str(e)}")