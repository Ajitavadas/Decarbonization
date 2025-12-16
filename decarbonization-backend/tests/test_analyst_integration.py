
import asyncio
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import select

from app.models.models import User, Organization, FlaggedEvent, EmissionTransaction
from app.services.analyst_service import AnalystService

# Mock or use real DB session via pytest-asyncio fixture if available
# Adapting to existing test patterns in the repo

@pytest.mark.asyncio
async def test_analyst_integration(db_session):
    """
    Test Phase 2.4 Analyst Agent logic:
    1. Create a Gap (FlaggedEvent).
    2. Simulate User providing missing data.
    3. Analyst validates and calculates.
    4. Verify Transaction created and Event resolved.
    """
    db = db_session
    
    # Setup: Org and User
    org_id = str(uuid4())
    user_id = str(uuid4())
    
    org = Organization(id=org_id, name="Test Org Analyst", slug=f"test-analyst-{str(uuid4())[:8]}")
    user = User(id=user_id, email=f"analyst-{str(uuid4())[:8]}@test.com", hashed_password="pw", organization_id=org_id, username=f"analyst_user_{str(uuid4())[:8]}")
    
    db.add(org)
    db.add(user)
    await db.commit()

    # 1. Create Flagged Event (The Gap)
    event_id = str(uuid4())
    gap_event = FlaggedEvent(
        id=event_id,
        organization_id=org_id,
        type="gap",
        severity="medium",
        description="Missing heating data for Jan",
        status="open"
    )
    db.add(gap_event)
    await db.commit()

    # 2. Simulate User Response Data
    user_data = {
        "organization_id": org_id,
        "activity_value": 500.0,
        "activity_unit": "therms",
        "activity_type": "natural_gas",
        "description": "January Heating Bill"
    }

    # 3. Analyst Execution
    analyst = AnalystService(db)

    # 3a. Validate
    is_valid = await analyst.validate_input(user_data)
    assert is_valid is True, "Input " + str(user_data) + " should be valid"

    # 3b. Calculate & Resolve
    transaction = await analyst.execute_calculation(event_id, user_data, user_id)
    
    assert transaction is not None
    assert transaction.co2e_kg > 0
    # 500 therms * ~5.3 kg/therm (approx) -> check rough range or mock factor used?
    # CalculationService uses a mocked factor of 0.5 kg/unit for MVP in some paths, 
    # but let's check broadly.
    # Wait, CalculationService.calculate_emissions uses a HARDCODED mock factor (0.5 kgCO2e/kWh equivalent?).
    # It converts input to "kwh" (Mock Factor denominator is kwh).
    # 500 therms * 29.3071 kwh/therm = 14653.55 kwh
    # 14653.55 * 0.5 = ~7326 kg CO2e
    print(f"Calculated CO2e: {transaction.co2e_kg} kg")
    assert transaction.co2e_kg > 1000

    # 4. Verify Database State
    # Check Flag Resolution
    result = await db.execute(select(FlaggedEvent).where(FlaggedEvent.id == event_id))
    updated_event = result.scalars().first()
    
    assert updated_event.status == "resolved"
    assert updated_event.resolved_by_user_id == user_id
    assert "Resolved by Analyst Agent" in updated_event.resolution_notes

    # Check Transaction
    result_tx = await db.execute(select(EmissionTransaction).where(EmissionTransaction.id == transaction.id))
    stored_tx = result_tx.scalars().first()
    assert stored_tx is not None
    assert stored_tx.category == "natural_gas"

    print("Test Passed: Analyst Agent Integration Verified")
