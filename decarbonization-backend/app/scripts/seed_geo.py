# app/scripts/seed_geo.py
import asyncio
import os
import sys

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.models import Base
from app.models.geo import GridRegion
from app.services.location_service import LocationService
from geoalchemy2.elements import WKTElement

# Use the database URL from environment or default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://decarb_user:decarb_password@localhost:5432/decarb_db")

async def seed_regions():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Tables are created by alembic or docker-entrypoint usually. 
    # If we need to create them here:
    async with engine.begin() as conn:
         await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        try:
            # Check if regions already exist
            result = await db.execute(select(GridRegion))
            if result.scalars().first():
                print("Regions already seeded.")
                # We can still run verification
            else:
                print("Seeding regions...")
                
                # Approximate simplified polygons
                # WECC (Western Interconnection)
                wecc_poly = "POLYGON((-125 49, -100 49, -100 30, -125 30, -125 49))"
                wecc = GridRegion(
                    name="Western Interconnection",
                    code="US-WECC",
                    boundary=WKTElement(wecc_poly, srid=4326)
                )
                
                # ERCOT (Texas)
                ercot_poly = "POLYGON((-106 36, -93 36, -93 25, -106 25, -106 36))"
                ercot = GridRegion(
                    name="ERCOT",
                    code="US-ERCOT",
                    boundary=WKTElement(ercot_poly, srid=4326)
                )
                
                db.add(wecc)
                db.add(ercot)
                await db.commit()
                print("Seeding complete!")
            
            # Verification
            print("Verifying spatial query...")
            # Point in WECC (e.g., San Francisco: -122.4, 37.7)
            region = await LocationService.get_region_by_coordinates(db, 37.7, -122.4)
            if region and region.code == "US-WECC":
                print(f"SUCCESS: Point (-122.4, 37.7) found in {region.name}")
            else:
                print(f"FAILURE: Point (-122.4, 37.7) not found in WECC. Found: {region}")

        except Exception as e:
            print(f"Error seeding data: {e}")
            await db.rollback()
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(seed_regions())
