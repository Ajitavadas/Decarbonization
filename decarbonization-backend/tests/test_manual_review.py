"""
Test Manual Review Workflow (US-2.4)

Acceptance Criteria:
- Review queue displays 50 items in under 5 minutes of review time
- Managers can see AI recommendation, confidence score, and transaction details
- Overrides are recorded with user name, timestamp, and rationale
- Audit history is retained for compliance
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.models.models import EmissionTransaction, AuditLog
from tests.conftest import create_test_transaction


@pytest.mark.asyncio
async def test_review_queue_display(client: AsyncClient, auth_headers, test_organization, test_user, db_session):
    """US-2.4 AC1: Review queue displays flagged items"""
    # Create transactions needing review
    for i in range(10):
        tx = create_test_transaction(
            test_organization.id,
            test_user.id,
            ai_needs_review=True,
            ai_scope_prediction=2,
            ai_confidence_score=0.75
        )
        db_session.add(tx)
    
    await db_session.commit()
    
    # Fetch review queue
    response = await client.get(
        "/api/v1/emissions/review-queue",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10
    
    # Verify AI data is present
    for item in data:
        assert "ai_scope_prediction" in item
        assert "ai_confidence_score" in item
        assert item["ai_needs_review"] == True


@pytest.mark.asyncio
async def test_review_approval(client: AsyncClient, auth_headers, test_organization, test_user, db_session):
    """US-2.4 AC3: Review workflow with approval"""
    # Create transaction needing review
    tx = create_test_transaction(
        test_organization.id,
        test_user.id,
        scope=1,
        ai_needs_review=True,
        ai_scope_prediction=2,
        ai_confidence_score=0.75
    )
    db_session.add(tx)
    await db_session.commit()
    
    # Submit review (approve AI)
    response = await client.post(
        f"/api/v1/emissions/review/{tx.id}",
        headers=auth_headers,
        json={
            "approved": True,
            "review_notes": "AI classification looks correct"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["final_scope"] == 2  # Should use AI prediction
    assert data["decision"] == "AI_APPROVED"


@pytest.mark.asyncio
async def test_review_override(client: AsyncClient, auth_headers, test_organization, test_user, db_session):
    """US-2.4 AC3: Review workflow with override and audit trail"""
    # Create transaction
    tx = create_test_transaction(
        test_organization.id,
        test_user.id,
        scope=1,
        ai_needs_review=True,
        ai_scope_prediction=2,
        ai_confidence_score=0.75
    )
    db_session.add(tx)
    await db_session.commit()
    
    # Submit review (override AI)
    response = await client.post(
        f"/api/v1/emissions/review/{tx.id}",
        headers=auth_headers,
        json={
            "approved": False,
            "final_scope": 3,
            "review_notes": "This should be Scope 3, not Scope 2"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["final_scope"] == 3
    assert data["decision"] == "MANUAL_OVERRIDE"
    
    # Verify audit log was created
    from sqlalchemy import select
    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.resource_id == tx.id
        )
    )
    audit = result.scalar_one_or_none()
    
    assert audit is not None
    assert audit.action == "MANUAL_OVERRIDE"
    assert "review_notes" in audit.new_values