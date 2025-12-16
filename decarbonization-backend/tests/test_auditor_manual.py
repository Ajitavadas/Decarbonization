
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
import random
from sqlalchemy import select

from app.database import get_db, engine
from app.models.models import Organization, EmissionTransaction, EmissionFactor, FlaggedEvent, User, Base
from app.services.auditor_service import AuditorService

async def setup_data(db):
    # 1. Create Organization
    org_id = str(uuid.uuid4())
    org = Organization(
        id=org_id,
        name=f"Auditor Test Org {random.randint(1000,9999)}",
        slug=f"auditor-test-{random.randint(1000,9999)}",
    )
    db.add(org)
    
    # 2. Create Emission Factors (one for heating/cold region context)
    ef_gas = EmissionFactor(
        id=str(uuid.uuid4()),
        name="Natural Gas US-NE",
        source="EPA",
        scope=1,
        category="Natural Gas",
        region="US-NE", # Cold Region!
        factor_value=53.06,
        factor_unit="kg CO2e/mmbtu",
        effective_date=datetime(2023, 1, 1, tzinfo=timezone.utc)
    )
    db.add(ef_gas)
    
    ef_elec = EmissionFactor(
        id=str(uuid.uuid4()),
        name="Grid Electricity",
        source="EPA",
        scope=2,
        category="Electricity",
        region="US-Grid",
        factor_value=0.4,
        factor_unit="kg CO2e/kWh",
        effective_date=datetime(2023, 1, 1, tzinfo=timezone.utc)
    )
    db.add(ef_elec)
    
    # Create a user for foreign key constraints
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=f"auditor_test_{random.randint(1000,9999)}@example.com",
        username=f"auditor_test_{random.randint(1000,9999)}",
        hashed_password="hashed_password",
        organization_id=org_id
    )
    db.add(user)

    # 3. Seed Transactions
    # NOTE: Dates must be within last 365 days. 
    # Current simulated time is ~Dec 2025. So we use 2025 dates.
    
    # Scenario A: Heating Consistency Gap
    
    t1 = EmissionTransaction(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        description="January Electricity",
        transaction_date=datetime(2025, 1, 15, tzinfo=timezone.utc), # Winter 2025
        scope=2,
        category="Electricity",
        activity_value=1000,
        activity_unit="kWh",
        emission_factor_id=ef_gas.id, 
        emission_factor_value=0.0,
        co2e_kg=0.0,
        co2e_tonnes=0.0,
        created_by_user_id=user_id
    )
    # The rule says: If Region is Cold. How do we know Region is Cold?
    # Logic: "Find distinct regions from emission factors used by this org"
    
    t_region_setter = EmissionTransaction(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        description="Old Gas Transaction establishing region",
        transaction_date=datetime(2025, 6, 15, tzinfo=timezone.utc), # Summer
        scope=1,
        category="Natural Gas",
        activity_value=100,
        activity_unit="therms",
        emission_factor_id=ef_gas.id, # Links to US-NE
        emission_factor_value=5.3,
        co2e_kg=530.0,
        co2e_tonnes=0.53,
        created_by_user_id=user_id
    )
    db.add(t_region_setter)
    
    # Now we have activity in Winter (Jan) but NO heating transactions in Winter.
    t_jan_elec = EmissionTransaction(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        description="Jan Elec",
        transaction_date=datetime(2025, 1, 10, tzinfo=timezone.utc),
        scope=2,
        category="Electricity",
        activity_value=500,
        activity_unit="kWh",
        emission_factor_id=ef_elec.id,
        emission_factor_value=0.4,
        co2e_kg=200,
        co2e_tonnes=0.2,
        created_by_user_id=user_id
    )
    db.add(t_jan_elec)
    
    # Scenario B: Sequence Gap
    # Add Diesel for Jan and Mar, but missing Feb.
    
    t_jan_diesel = EmissionTransaction(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        description="Jan Diesel",
        transaction_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
        scope=1,
        category="Diesel Fleet", 
        activity_value=100,
        activity_unit="gal",
        emission_factor_value=10.0,
        co2e_kg=1000,
        co2e_tonnes=1.0,
        created_by_user_id=user_id
    )
    db.add(t_jan_diesel)
    
    t_mar_diesel = EmissionTransaction(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        description="Mar Diesel",
        transaction_date=datetime(2025, 3, 15, tzinfo=timezone.utc),
        scope=1,
        category="Diesel Fleet",
        activity_value=100,
        activity_unit="gal",
        emission_factor_value=10.0,
        co2e_kg=1000,
        co2e_tonnes=1.0,
        created_by_user_id=user_id
    )
    db.add(t_mar_diesel)
    
    await db.commit()
    return org_id

async def run_test():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async for session in get_db():
        print("Seeding data...")
        org_id = await setup_data(session)
        print(f"Data seeded for Org: {org_id}")
        
        print("Running Auditor...")
        results = await AuditorService.run_audit(session, org_id)
        print("Auditor Results:", results)
        
        # Verify specific flags
        result = await session.execute(
            select(FlaggedEvent).where(FlaggedEvent.organization_id == org_id)
        )
        events = result.scalars().all()
        
        print("\n--- Detected Events ---")
        for e in events:
            print(f"[{e.type.upper()}] {e.description} (Severity: {e.severity})")
            print(f"Details: {e.details}")
            print("-" * 30)
            
        # Assertions
        types = [e.type for e in events]
        descriptions = [e.description for e in events]
        
        # Expect Sequence Gap
        has_sequence_gap = any("sequence_gap" in t for t in types)
        # Expect Heating Consistency (missing winter heating)
        has_heating_gap = any("heating_consistency" in t for t in types)
        
        if has_sequence_gap and has_heating_gap:
            print("\n✅ SUCCESS: Both gap types detected!")
        else:
            print(f"\n❌ FAILED: Missed some gaps. Sequence: {has_sequence_gap}, Heating: {has_heating_gap}")

        break # run once

if __name__ == "__main__":
    asyncio.run(run_test())
