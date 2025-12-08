"""
Integration tests for classification API endpoints
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_classify_transaction_endpoint(async_client, test_user_token, db_session, test_transaction):
    """Test POST /classify endpoint"""
    
    response = await async_client.post(
        "/api/v1/classify/",
        json={
            "transaction_id": test_transaction.id,
            "description": "Monthly electricity bill",
            "category": "Electricity",
            "activity_value": 100.0
        },
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    
    assert result['transaction_id'] == test_transaction.id
    assert result['scope'] in [1, 2, 3]
    assert 0.0 <= result['confidence'] <= 1.0
    assert 'needs_review' in result
    assert result['co2e_kg'] > 0

@pytest.mark.asyncio
async def test_get_review_queue(async_client, test_user_token):
    """Test GET /review-queue endpoint"""
    
    response = await async_client.get(
        "/api/v1/classify/review-queue/items",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    items = response.json()
    
    assert isinstance(items, list)
    # Items should all have needs_review = True
    for item in items:
        assert 'transaction_id' in item
        assert 'ai_prediction' in item
        assert 'ai_confidence' in item

@pytest.mark.asyncio
async def test_approve_classification(async_client, admin_token, test_transaction):
    """Test POST /review-queue/{id}/approve endpoint"""
    
    response = await async_client.post(
        f"/api/v1/classify/review-queue/{test_transaction.id}/approve",
        json={
            "approved_scope": 2,
            "notes": "Confirmed as Scope 2 - purchased electricity"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    
    assert result['status'] == 'approved'
    assert result['approved_scope'] == 2

@pytest.mark.asyncio
async def test_accuracy_metrics(async_client, test_user_token):
    """Test GET /metrics/accuracy endpoint"""
    
    response = await async_client.get(
        "/api/v1/classify/metrics/accuracy?days=30",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    metrics = response.json()
    
    assert 'total_verified' in metrics
    assert 'accuracy' in metrics
    assert 'accuracy_percent' in metrics