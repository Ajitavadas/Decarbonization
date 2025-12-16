
import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'decarbonization-backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, desc
from app.models.models import EmissionTransaction

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://decarb_user:decarb_password@localhost:5432/decarb_db")

async def verify_calculation():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        # Get latest transaction
        result = await db.execute(select(EmissionTransaction).order_by(desc(EmissionTransaction.created_at)).limit(1))
        tx = result.scalars().first()
        
        if not tx:
            print("No transactions found!")
            return
            
        print(f"Latest Transaction: {tx.description}")
        print(f"Activity: {tx.activity_value} {tx.activity_unit}")
        print(f"CO2e: {tx.co2e_kg} kg")
        
        # Expected: 500 Therms -> ~7326.775 kg
        # 500 * 29.3071 = 14653.55 kWh
        # * 0.5 = 7326.775
        expected = 7326.775
        tolerance = 1.0 
        
        if abs(tx.co2e_kg - expected) < tolerance:
            print(f"✅ VERIFIED: Calculation matches expected value ({expected}) within tolerance.")
        else:
            print(f"❌ FAILED: Calculation mismatch. Expected {expected}, got {tx.co2e_kg}")

if __name__ == "__main__":
    asyncio.run(verify_calculation())
