"""
Emission Transactions Router - US-2.4
Handles manual review workflow and transaction management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
from app.auth.oauth2_scheme import get_current_user
from app.models.models import EmissionTransaction, User, AuditLog
from app.schemas.schemas import (
    EmissionTransactionResponse,
    EmissionReviewRequest,
    EmissionReviewResponse,
    EmissionTransactionCreate
)
from app.services.calculation_service import CalculationService

router = APIRouter(prefix="/api/v1/emissions", tags=["emissions"])


@router.post("", response_model=EmissionTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_emission_transaction(
    transaction_data: EmissionTransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new emission transaction
    
    AC (US-2.2):
    - All calculations accurate to 3 decimal places
    - Audit trail shows source factor
    """
    user = current_user
    
    # Calculate CO2e
    co2e_kg, co2e_tonnes, audit_info = CalculationService.calculate_co2e(
        activity_value=transaction_data.activity_value,
        emission_factor=transaction_data.emission_factor_value,
        activity_unit=transaction_data.activity_unit
    )
    
    # Create transaction
    transaction = EmissionTransaction(
        organization_id=user.organization_id,
        description=transaction_data.description,
        transaction_date=transaction_data.transaction_date,
        scope=transaction_data.scope,
        category=transaction_data.category,
        activity_value=transaction_data.activity_value,
        activity_unit=transaction_data.activity_unit,
        emission_factor_id=transaction_data.emission_factor_id,
        emission_factor_value=transaction_data.emission_factor_value,
        co2e_kg=co2e_kg,
        co2e_tonnes=co2e_tonnes,
        supplier_name=transaction_data.supplier_name,
        project_id=transaction_data.project_id,
        notes=transaction_data.notes,
        created_by_user_id=current_user.id
    )
    
    db.add(transaction)
    
    # Create audit log
    audit_log = AuditLog(
        organization_id=user.organization_id,
        user_id=current_user.id,
        action="CREATE",
        resource_type="EmissionTransaction",
        resource_id=transaction.id,
        new_values=audit_info
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(transaction)
    
    return transaction


@router.get("/review-queue", response_model=List[EmissionTransactionResponse])
async def get_review_queue(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get transactions flagged for manual review (US-2.4)
    
    AC:
    - Review queue displays 50 items in under 5 minutes of review time
    - Managers can see AI recommendation, confidence score, and details
    """
    user = current_user
    
    # Query transactions needing review
    query = select(EmissionTransaction).where(
        and_(
            EmissionTransaction.organization_id == user.organization_id,
            EmissionTransaction.ai_needs_review == True,
            EmissionTransaction.verified_by_user_id == None
        )
    ).order_by(EmissionTransaction.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    return transactions


@router.post("/review/{transaction_id}", response_model=EmissionReviewResponse)
async def review_transaction(
    transaction_id: str,
    review_data: EmissionReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve or override AI classification (US-2.4)
    
    AC:
    - Overrides recorded with user name, timestamp, and rationale
    - Audit history retained for compliance
    """
    # Get transaction
    result = await db.execute(
        select(EmissionTransaction).where(EmissionTransaction.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    user = current_user
    
    # Verify user belongs to same organization
    if transaction.organization_id != user.organization_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Store old values for audit
    old_scope = transaction.scope
    
    # Apply review decision
    if review_data.approved:
        # Accept AI recommendation
        transaction.scope = transaction.ai_scope_prediction
        decision = "AI_APPROVED"
    else:
        # Override with manager's choice
        transaction.scope = review_data.final_scope
        decision = "MANUAL_OVERRIDE"
    
    # Mark as verified
    transaction.verified_by_user_id = current_user.id
    transaction.verified_at = datetime.now(timezone.utc)
    transaction.ai_needs_review = False
    
    # Update notes if provided
    if review_data.review_notes:
        transaction.notes = (transaction.notes or "") + f"\n[Review: {review_data.review_notes}]"
    
    # Create audit log
    audit_log = AuditLog(
        organization_id=transaction.organization_id,
        user_id=current_user.id,
        action=decision,
        resource_type="EmissionTransaction",
        resource_id=transaction.id,
        old_values={"scope": old_scope},
        new_values={
            "scope": transaction.scope,
            "review_notes": review_data.review_notes,
            "decision": decision
        },
        description=f"Transaction reviewed by {user.full_name or user.username}"
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(transaction)
    
    return {
        "transaction_id": transaction.id,
        "final_scope": transaction.scope,
        "decision": decision,
        "reviewed_by": current_user.id,
        "reviewed_at": transaction.verified_at
    }


@router.get("", response_model=List[EmissionTransactionResponse])
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: Optional[int] = Query(None, ge=1, le=3),
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    List emission transactions with filters
    
    AC (US-3.4):
    - Any combination of filters works correctly
    - Results update in under 500 milliseconds
    """
    user = current_user
    
    # Build query
    query = select(EmissionTransaction).where(
        EmissionTransaction.organization_id == user.organization_id
    )
    
    if scope:
        query = query.where(EmissionTransaction.scope == scope)
    if category:
        query = query.where(EmissionTransaction.category.ilike(f"%{category}%"))
    if start_date:
        query = query.where(EmissionTransaction.transaction_date >= start_date)
    if end_date:
        query = query.where(EmissionTransaction.transaction_date <= end_date)
    
    query = query.order_by(EmissionTransaction.transaction_date.desc())
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    return transactions


@router.get("/stats", response_model=dict)
async def get_emission_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get emission statistics summary"""
    user = current_user
    
    # Total emissions
    total_query = select(func.sum(EmissionTransaction.co2e_tonnes)).where(
        EmissionTransaction.organization_id == user.organization_id
    )
    total_result = await db.execute(total_query)
    total_emissions = total_result.scalar() or 0.0
    
    # Transaction count
    count_query = select(func.count(EmissionTransaction.id)).where(
        EmissionTransaction.organization_id == user.organization_id
    )
    count_result = await db.execute(count_query)
    transaction_count = count_result.scalar() or 0
    
    # Pending review count
    review_query = select(func.count(EmissionTransaction.id)).where(
        and_(
            EmissionTransaction.organization_id == user.organization_id,
            EmissionTransaction.ai_needs_review == True,
            EmissionTransaction.verified_by_user_id == None
        )
    )
    review_result = await db.execute(review_query)
    pending_review = review_result.scalar() or 0
    
    return {
        "total_emissions_tonnes": round(total_emissions, 3),
        "transaction_count": transaction_count,
        "pending_review_count": pending_review
    }