"""
FastAPI router for AI classification endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import logging
import json

from app.database import get_db
from app.auth.oauth2_scheme import get_current_user
from app.models.models import (
    User, EmissionTransaction, AuditLog, Organization
)
from app.schemas.schemas import (
    ClassificationRequest,
    ClassificationResponse,
    ReviewQueueItem,
    ReviewApproval
)
from app.config import settings
from app.services.dspy_agents import MultiAgentClassifier

router = APIRouter(
    prefix="/api/v1/classify",
    tags=["classification"],
    responses={401: {"description": "Unauthorized"}}
)
logger = logging.getLogger(__name__)

# Global classifier instance (initialized once)
_classifier = None

def get_classifier() -> MultiAgentClassifier:
    """Get or initialize classifier"""
    global _classifier
    if _classifier is None:
        _classifier = MultiAgentClassifier(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL
        )
        logger.info("Classifier initialized")
    return _classifier

# ==================== Classification Endpoints ====================

@router.post("/", response_model=ClassificationResponse)
async def classify_transaction(
    request: ClassificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Classify a transaction using multi-agent AI system
    
    Returns scope prediction, confidence score, and CO2e calculation
    """
    
    try:
        # Verify transaction exists
        result = await db.execute(
            select(EmissionTransaction).where(
                EmissionTransaction.id == request.transaction_id
            )
        )
        tx = result.scalar_one_or_none()
        
        if not tx:
            logger.warning(f"Transaction not found: {request.transaction_id}")
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Verify authorization
        if tx.organization_id != current_user.organization_id:
            logger.warning(
                f"Unauthorized access attempt - User {current_user.id} "
                f"tried to classify transaction in org {tx.organization_id}"
            )
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Get classifier and classify
        clf = get_classifier()
        logger.info(f"Classifying transaction {request.transaction_id}")
        
        classification = clf.classify(
            transaction_id=request.transaction_id,
            description=request.description,
            category=request.category,
            activity_value=request.activity_value
        )
        
        # Handle errors from classifier
        if 'error' in classification:
            logger.error(f"Classification error: {classification['error']}")
            raise HTTPException(
                status_code=500,
                detail=f"Classification failed: {classification['error']}"
            )
        
        # Update transaction
        tx.ai_scope_prediction = classification['scope']
        tx.ai_confidence_score = classification['confidence']
        tx.ai_needs_review = classification['needs_review']
        tx.emission_factor_value = classification['factor_value']
        tx.co2e_kg = classification['co2e_kg']
        tx.co2e_tonnes = round(classification['co2e_kg'] / 1000, 6)
        
        await db.commit()
        await db.refresh(tx)
        
        # Log in background
        background_tasks.add_task(
            log_classification_event,
            db,
            current_user.organization_id,
            current_user.id,
            request.transaction_id,
            classification
        )
        
        logger.info(
            f"Transaction {request.transaction_id} classified - "
            f"Scope: {classification['scope']}, "
            f"Confidence: {classification['confidence']}"
        )
        
        return ClassificationResponse(
            transaction_id=request.transaction_id,
            scope=classification['scope'],
            confidence=classification['confidence'],
            needs_review=classification['needs_review'],
            reasoning=classification['reasoning'],
            co2e_kg=classification['co2e_kg'],
            co2e_tonnes=tx.co2e_tonnes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Classification endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{transaction_id}", response_model=ClassificationResponse)
async def get_classification(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get previously saved classification for a transaction"""
    
    try:
        result = await db.execute(
            select(EmissionTransaction).where(
                EmissionTransaction.id == transaction_id
            )
        )
        tx = result.scalar_one_or_none()
        
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if tx.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        if not tx.ai_scope_prediction:
            raise HTTPException(
                status_code=404,
                detail="Transaction has not been classified yet"
            )
        
        return ClassificationResponse(
            transaction_id=transaction_id,
            scope=tx.ai_scope_prediction,
            confidence=tx.ai_confidence_score or 0.0,
            needs_review=tx.ai_needs_review or False,
            reasoning={"note": "Retrieved from database"},
            co2e_kg=tx.co2e_kg,
            co2e_tonnes=tx.co2e_tonnes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get classification error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# ==================== Review Queue Endpoints ====================

@router.get("/review-queue/items", response_model=List[ReviewQueueItem])
async def get_review_queue(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """Get all low-confidence transactions requiring review"""
    
    try:
        result = await db.execute(
            select(EmissionTransaction).where(
                and_(
                    EmissionTransaction.organization_id == current_user.organization_id,
                    EmissionTransaction.ai_needs_review == True
                )
            ).order_by(
                EmissionTransaction.ai_confidence_score.asc(),  # Lowest confidence first
                EmissionTransaction.created_at.asc()
            ).limit(limit).offset(offset)
        )
        transactions = result.scalars().all()
        
        return [
            ReviewQueueItem(
                transaction_id=tx.id,
                description=tx.description,
                category=tx.category,
                transaction_date=tx.transaction_date,
                ai_prediction=tx.ai_scope_prediction,
                ai_confidence=tx.ai_confidence_score,
                created_at=tx.created_at
            )
            for tx in transactions
        ]
        
    except Exception as e:
        logger.error(f"Review queue error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/review-queue/count")
async def get_review_queue_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get count of items in review queue"""
    
    try:
        result = await db.execute(
            select(EmissionTransaction).where(
                and_(
                    EmissionTransaction.organization_id == current_user.organization_id,
                    EmissionTransaction.ai_needs_review == True
                )
            )
        )
        items = result.scalars().all()
        
        return {
            "pending_review_count": len(items),
            "message": f"{len(items)} transactions require review"
        }
        
    except Exception as e:
        logger.error(f"Review queue count error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/review-queue/{transaction_id}/approve")
async def approve_classification(
    transaction_id: str,
    approval: ReviewApproval,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manager approves or overrides AI classification"""
    
    try:
        # Only admins can approve
        if not current_user.is_admin:
            logger.warning(
                f"Non-admin {current_user.id} attempted to approve classification"
            )
            raise HTTPException(
                status_code=403,
                detail="Only administrators can approve classifications"
            )
        
        result = await db.execute(
            select(EmissionTransaction).where(
                EmissionTransaction.id == transaction_id
            )
        )
        tx = result.scalar_one_or_none()
        
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if tx.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Save old values for audit
        old_scope = tx.scope
        old_co2e = tx.co2e_kg
        
        # Update with approved scope
        tx.scope = approval.approved_scope
        tx.verified_by_user_id = current_user.id
        tx.verified_at = datetime.now(timezone.utc)
        tx.ai_needs_review = False
        
        # Recalculate CO2e if scope changed
        if old_scope != approval.approved_scope:
            co2e_kg = tx.activity_value * tx.emission_factor_value
            tx.co2e_kg = round(co2e_kg, 3)
            tx.co2e_tonnes = round(co2e_kg / 1000, 6)
        
        await db.commit()
        await db.refresh(tx)
        
        # Log in background
        background_tasks.add_task(
            log_approval_event,
            db,
            current_user.organization_id,
            current_user.id,
            transaction_id,
            old_scope,
            approval.approved_scope,
            approval.notes
        )
        
        logger.info(
            f"Classification {transaction_id} approved - "
            f"Changed from Scope {old_scope} to {approval.approved_scope}"
        )
        
        return {
            "status": "approved",
            "transaction_id": transaction_id,
            "approved_scope": approval.approved_scope,
            "verified_by": current_user.username,
            "verified_at": tx.verified_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approval error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# ==================== Metrics Endpoints ====================

@router.get("/metrics/accuracy")
async def get_accuracy_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = 30
):
    """Get AI classification accuracy metrics"""
    
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get verified transactions (manager has reviewed)
        result = await db.execute(
            select(EmissionTransaction).where(
                and_(
                    EmissionTransaction.organization_id == current_user.organization_id,
                    EmissionTransaction.verified_at >= cutoff_date,
                    EmissionTransaction.ai_scope_prediction.isnot(None)
                )
            )
        )
        verified_txs = result.scalars().all()
        
        if not verified_txs:
            return {
                "period_days": days,
                "total_verified": 0,
                "accuracy": 0.0,
                "message": "No verified transactions in period"
            }
        
        # Calculate accuracy
        matches = sum(
            1 for tx in verified_txs
            if tx.ai_scope_prediction == tx.scope
        )
        
        accuracy = matches / len(verified_txs)
        
        return {
            "period_days": days,
            "total_verified": len(verified_txs),
            "correct_predictions": matches,
            "incorrect_predictions": len(verified_txs) - matches,
            "accuracy": round(accuracy, 3),
            "accuracy_percent": f"{accuracy * 100:.1f}%",
            "trend": "improving" if accuracy > 0.85 else "needs improvement"
        }
        
    except Exception as e:
        logger.error(f"Accuracy metrics error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/metrics/confidence-distribution")
async def get_confidence_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get distribution of confidence scores"""
    
    try:
        result = await db.execute(
            select(EmissionTransaction).where(
                and_(
                    EmissionTransaction.organization_id == current_user.organization_id,
                    EmissionTransaction.ai_confidence_score.isnot(None)
                )
            )
        )
        transactions = result.scalars().all()
        
        if not transactions:
            return {"message": "No classified transactions"}
        
        # Bucket confidence scores
        buckets = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0
        }
        
        for tx in transactions:
            conf = tx.ai_confidence_score
            if conf < 0.2:
                buckets["0.0-0.2"] += 1
            elif conf < 0.4:
                buckets["0.2-0.4"] += 1
            elif conf < 0.6:
                buckets["0.4-0.6"] += 1
            elif conf < 0.8:
                buckets["0.6-0.8"] += 1
            else:
                buckets["0.8-1.0"] += 1
        
        avg_confidence = sum(tx.ai_confidence_score for tx in transactions) / len(transactions)
        
        return {
            "total_transactions": len(transactions),
            "average_confidence": round(avg_confidence, 3),
            "distribution": buckets,
            "high_confidence_percent": f"{(buckets['0.8-1.0'] / len(transactions) * 100):.1f}%"
        }
        
    except Exception as e:
        logger.error(f"Confidence distribution error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# ==================== Background Tasks ====================

async def log_classification_event(
    db: AsyncSession,
    org_id: str,
    user_id: str,
    transaction_id: str,
    classification: dict
):
    """Log AI classification event to audit log"""
    
    try:
        audit_log = AuditLog(
            organization_id=org_id,
            user_id=user_id,
            action="AI_CLASSIFICATION",
            resource_type="EmissionTransaction",
            resource_id=transaction_id,
            new_values={
                "scope": classification['scope'],
                "confidence": classification['confidence'],
                "needs_review": classification['needs_review'],
                "co2e_kg": classification['co2e_kg']
            },
            description=f"AI classified: {classification['reasoning']['scope_reasoning']}"
        )
        db.add(audit_log)
        await db.commit()
        logger.debug(f"Audit log created for {transaction_id}")
    except Exception as e:
        logger.error(f"Failed to log classification: {str(e)}")

async def log_approval_event(
    db: AsyncSession,
    org_id: str,
    user_id: str,
    transaction_id: str,
    old_scope: int,
    new_scope: int,
    notes: str
):
    """Log manager approval event"""
    
    try:
        audit_log = AuditLog(
            organization_id=org_id,
            user_id=user_id,
            action="CLASSIFICATION_OVERRIDE",
            resource_type="EmissionTransaction",
            resource_id=transaction_id,
            old_values={"scope": old_scope},
            new_values={"scope": new_scope},
            description=f"Manager override: {notes}"
        )
        db.add(audit_log)
        await db.commit()
        logger.debug(f"Approval audit log created for {transaction_id}")
    except Exception as e:
        logger.error(f"Failed to log approval: {str(e)}")