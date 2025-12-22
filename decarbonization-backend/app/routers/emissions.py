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
from app.models.models import EmissionEvent, CalculationLedger, User, AuditTrail
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
    Create a new emission event and calculation result
    """
    # Calculate CO2e
    co2e_kg, co2e_tonnes, audit_info = CalculationService.calculate_co2e(
        activity_value=transaction_data.activity_value,
        emission_factor=transaction_data.emission_factor_value,
        activity_unit=transaction_data.activity_unit
    )
    
    # 1. Create EmissionEvent (Phase 1)
    new_event = EmissionEvent(
        organization_id=current_user.organization_id,
        activity_date=transaction_data.transaction_date,
        activity_value=transaction_data.activity_value,
        activity_unit_raw=transaction_data.activity_unit,
        activity_unit_normalized=transaction_data.activity_unit,
        activity_value_normalized=transaction_data.activity_value,
        source_type="user_entry",
        scope=f"Scope {transaction_data.scope}",
        description=transaction_data.description,
        confidence_score=1.0 # Manual entry
    )
    db.add(new_event)
    await db.flush() # Get event ID
    
    # 2. Create CalculationLedger (Phase 2)
    new_ledger = CalculationLedger(
        organization_id=current_user.organization_id,
        emission_event_id=new_event.id,
        activity_value=transaction_data.activity_value,
        activity_unit_normalized=transaction_data.activity_unit,
        emission_factor_value=transaction_data.emission_factor_value,
        result_kg_co2e=co2e_kg,
        result_kg_total=co2e_kg,
        calculated_by_user_id=current_user.id
    )
    db.add(new_ledger)
    
    # 3. Create Audit Trail
    audit_trail = AuditTrail(
        organization_id=current_user.organization_id,
        actor_user_id=current_user.id,
        action_type="CREATE",
        resource_type="EmissionEvent",
        resource_id=new_event.id,
        new_values=audit_info
    )
    db.add(audit_trail)
    
    await db.commit()
    await db.refresh(new_ledger)
    await db.refresh(new_event)
    
    return EmissionTransactionResponse(
        id=str(new_ledger.id),
        event_id=str(new_event.id),
        description=new_event.description,
        date=new_event.activity_date,
        scope=new_event.scope,
        category=transaction_data.category, # Handled as Scope 3 Cat usually
        amount=float(new_ledger.activity_value),
        unit=new_ledger.activity_unit_normalized,
        co2e_tonnes=float(new_ledger.result_kg_co2e / 1000)
    )


@router.get("/review-queue", response_model=List[EmissionTransactionResponse])
async def get_review_queue(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get transactions flagged for manual review (US-2.4)
    """
    query = (
        select(
            CalculationLedger.id,
            EmissionEvent.id.label("event_id"),
            EmissionEvent.description,
            EmissionEvent.activity_date.label("date"),
            EmissionEvent.scope,
            EmissionEvent.scope_3_category.label("category"),
            CalculationLedger.activity_value.label("amount"),
            CalculationLedger.activity_unit_normalized.label("unit"),
            (CalculationLedger.result_kg_co2e / 1000.0).label("co2e_tonnes")
        )
        .join(EmissionEvent, CalculationLedger.emission_event_id == EmissionEvent.id)
        .where(
            and_(
                CalculationLedger.organization_id == current_user.organization_id,
                EmissionEvent.needs_review == True,
                EmissionEvent.verified_by_user_id == None
            )
        )
        .order_by(EmissionEvent.created_at.desc())
        .limit(limit)
    )
    
    result = await db.execute(query)
    transactions = result.all()
    
    return [
        EmissionTransactionResponse(
            id=str(row.id),
            event_id=str(row.event_id),
            description=row.description,
            date=row.date,
            scope=row.scope,
            category=row.category,
            amount=float(row.amount),
            unit=row.unit,
            co2e_tonnes=float(row.co2e_tonnes)
        )
        for row in transactions
    ]


@router.post("/review/{ledger_id}", response_model=EmissionReviewResponse)
async def review_transaction(
    ledger_id: str,
    review_data: EmissionReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve or override AI classification (US-2.4)
    """
    # Get ledger and event
    query = (
        select(CalculationLedger, EmissionEvent)
        .join(EmissionEvent, CalculationLedger.emission_event_id == EmissionEvent.id)
        .where(CalculationLedger.id == ledger_id)
    )
    result = await db.execute(query)
    ledger_event = result.first()
    
    if not ledger_event:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    ledger, event = ledger_event
    
    # Verify user belongs to same organization
    if ledger.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Store old values for audit
    old_values = {
        "scope": event.scope,
        "category": event.scope_3_category
    }
    
    # Apply review decision
    if review_data.approved:
        # Accept AI recommendation (if we had a prediction field, for now assume current is AI prediction or use provided)
        # Assuming event.scope was set by AI during import
        decision = "AI_APPROVED"
    else:
        # Override with manager's choice
        event.scope = f"Scope {review_data.final_scope}"
        decision = "MANUAL_OVERRIDE"
    
    # Mark as verified
    event.verified_by_user_id = current_user.id
    event.needs_review = False
    
    # Update description/notes if needed
    if review_data.review_notes:
        event.description = (event.description or "") + f" (Reviewed: {review_data.review_notes})"
    
    # Create audit trail
    audit_trail = AuditTrail(
        organization_id=ledger.organization_id,
        actor_user_id=current_user.id,
        action_type=decision,
        resource_type="EmissionEvent",
        resource_id=event.id,
        old_values=old_values,
        new_values={
            "scope": event.scope,
            "review_notes": review_data.review_notes,
            "decision": decision
        }
    )
    db.add(audit_trail)
    
    await db.commit()
    await db.refresh(event)
    
    return {
        "transaction_id": str(ledger.id),
        "final_scope": int(event.scope.split(" ")[1]) if " " in event.scope else 3,
        "decision": decision,
        "reviewed_by": str(current_user.id),
        "reviewed_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("", response_model=List[EmissionTransactionResponse])
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scope: Optional[str] = Query(None),
    category: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    List emission events with calculations
    """
    query = (
        select(
            CalculationLedger.id,
            EmissionEvent.id.label("event_id"),
            EmissionEvent.description,
            EmissionEvent.activity_date.label("date"),
            EmissionEvent.scope,
            EmissionEvent.scope_3_category.label("category"),
            CalculationLedger.activity_value.label("amount"),
            CalculationLedger.activity_unit_normalized.label("unit"),
            (CalculationLedger.result_kg_co2e / 1000.0).label("co2e_tonnes")
        )
        .join(EmissionEvent, CalculationLedger.emission_event_id == EmissionEvent.id)
        .where(CalculationLedger.organization_id == current_user.organization_id)
    )
    
    if scope:
        query = query.where(EmissionEvent.scope == scope)
    if category:
        query = query.where(EmissionEvent.scope_3_category.ilike(f"%{category}%"))
    if start_date:
        query = query.where(EmissionEvent.activity_date >= start_date)
    if end_date:
        query = query.where(EmissionEvent.activity_date <= end_date)
    
    query = query.order_by(EmissionEvent.activity_date.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    transactions = result.all()
    
    return [
        EmissionTransactionResponse(
            id=str(row.id),
            event_id=str(row.event_id),
            description=row.description,
            date=row.date,
            scope=row.scope,
            category=row.category,
            amount=float(row.amount),
            unit=row.unit,
            co2e_tonnes=float(row.co2e_tonnes)
        )
        for row in transactions
    ]


@router.get("/stats", response_model=dict)
async def get_emission_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get emission statistics summary"""
    # Total emissions
    total_query = select(func.sum(CalculationLedger.result_kg_co2e)).where(
        CalculationLedger.organization_id == current_user.organization_id
    )
    total_result = await db.execute(total_query)
    total_tonnes = (total_result.scalar() or 0.0) / 1000.0
    
    # Transaction count
    count_query = select(func.count(CalculationLedger.id)).where(
        CalculationLedger.organization_id == current_user.organization_id
    )
    count_result = await db.execute(count_query)
    transaction_count = count_result.scalar() or 0
    
    # Pending review count
    review_query = select(func.count(EmissionEvent.id)).where(
        and_(
            EmissionEvent.organization_id == current_user.organization_id,
            EmissionEvent.needs_review == True,
            EmissionEvent.verified_by_user_id == None
        )
    )
    review_result = await db.execute(review_query)
    pending_review = review_result.scalar() or 0
    
    return {
        "total_emissions_tonnes": round(float(total_tonnes), 3),
        "transaction_count": transaction_count,
        "pending_review_count": pending_review
    }