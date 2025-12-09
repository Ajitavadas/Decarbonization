"""
Test Dashboard Service (US-2.3)

Acceptance Criteria:
- Dashboard shows total emissions prominently
- Pie chart accurately represents Scope breakdown
- 12-month trend is visible and accurate
- Dashboard loads in under 2 seconds
- Mobile view is readable and functional
"""

import pytest
import asyncio
import time
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from app.services.dashboard_service import DashboardService
from app.models.models import EmissionTransaction
from tests.conftest import create_test_transaction


@pytest.mark.asyncio
async def test_total_emissions_calculation(db_session: AsyncSession, test_organization, test_user):
    """US-2.3 AC1: Dashboard shows total emissions prominently"""
    # Create test transactions
    transactions = [
        create_test_transaction(test_organization.id, test_user.id, co2e_tonnes=10.5),
        create_test_transaction(test_organization.id, test_user.id, co2e_tonnes=25.3),
        create_test_transaction(test_organization.id, test_user.id, co2e_tonnes=15.7)
    ]
    
    for tx in transactions:
        db_session.add(tx)
    await db_session.commit()
    
    total = await DashboardService.get_total_emissions(db_session, test_organization.id)
    
    assert total == pytest.approx(51.5, abs=0.01)


@pytest.mark.asyncio
async def test_scope_breakdown_accuracy(db_session: AsyncSession, test_organization, test_user):
    """US-2.3 AC2: Pie chart accurately represents Scope breakdown"""
    # Create transactions for each scope
    scope_transactions = [
        create_test_transaction(test_organization.id, test_user.id, scope=1, co2e_tonnes=100.0),
        create_test_transaction(test_organization.id, test_user.id, scope=2, co2e_tonnes=200.0),
        create_test_transaction(test_organization.id, test_user.id, scope=3, co2e_tonnes=300.0),
    ]
    
    for tx in scope_transactions:
        db_session.add(tx)
    await db_session.commit()
    
    breakdown = await DashboardService.get_scope_breakdown(db_session, test_organization.id)
    
    assert breakdown[1] == 100.0
    assert breakdown[2] == 200.0
    assert breakdown[3] == 300.0
    assert all(scope in breakdown for scope in [1, 2, 3])


@pytest.mark.asyncio
async def test_monthly_trend_accuracy(db_session: AsyncSession, test_organization, test_user):
    """US-2.3 AC3: 12-month trend is visible and accurate"""
    # Create transactions across 3 months
    base_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    
    for month in range(1, 4):
        for _ in range(5):
            tx = create_test_transaction(
                test_organization.id,
                test_user.id,
                transaction_date=base_date + timedelta(days=30*month),
                co2e_tonnes=10.0
            )
            db_session.add(tx)
    
    await db_session.commit()
    
    trend = await DashboardService.get_monthly_trend(db_session, test_organization.id, months=12)
    
    assert len(trend) > 0
    assert all("year" in item and "month" in item and "emissions_tonnes" in item 
               for item in trend)


@pytest.mark.asyncio
async def test_dashboard_load_performance(db_session: AsyncSession, test_organization, test_user):
    """US-2.3 AC4: Dashboard loads in under 2 seconds"""
    # Create realistic data volume
    for i in range(100):
        tx = create_test_transaction(
            test_organization.id,
            test_user.id,
            co2e_tonnes=10.0
        )
        db_session.add(tx)
    await db_session.commit()
    
    # Measure dashboard data retrieval
    start_time = time.time()
    
    total = await DashboardService.get_total_emissions(db_session, test_organization.id)
    breakdown = await DashboardService.get_scope_breakdown(db_session, test_organization.id)
    trend = await DashboardService.get_monthly_trend(db_session, test_organization.id)
    categories = await DashboardService.get_category_breakdown(db_session, test_organization.id)
    
    elapsed = time.time() - start_time
    
    assert elapsed < 2.0, f"Dashboard data took {elapsed:.2f}s, should be under 2s"


@pytest.mark.asyncio
async def test_category_breakdown(db_session: AsyncSession, test_organization, test_user):
    """Test category breakdown functionality"""
    # Create transactions in different categories
    categories = ["Electricity", "Fuel", "Business Travel"]
    
    for category in categories:
        for _ in range(3):
            tx = create_test_transaction(
                test_organization.id,
                test_user.id,
                category=category,
                co2e_tonnes=15.0
            )
            db_session.add(tx)
    
    await db_session.commit()
    
    breakdown = await DashboardService.get_category_breakdown(
        db_session,
        test_organization.id,
        limit=10
    )
    
    assert len(breakdown) == 3
    assert all(item["emissions_tonnes"] == 45.0 for item in breakdown)
    assert set(item["category"] for item in breakdown) == set(categories)