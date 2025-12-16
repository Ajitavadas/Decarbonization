from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from app.models.geo import GridRegion
from typing import Optional

class LocationService:
    @staticmethod
    async def get_region_by_coordinates(db: AsyncSession, lat: float, lon: float) -> Optional[GridRegion]:
        """
        Finds the GridRegion containing the given latitude and longitude.
        Uses PostGIS ST_Contains or ST_Intersects.
        """
        # Create a point geometry from lat/lon (WGS 84)
        # ST_SetSRID(ST_MakePoint(lon, lat), 4326)
        # Note: ST_MakePoint takes (x, y) which is (lon, lat)
        
        point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        
        # Query for the region that contains the point
        # Async syntax: await db.execute(select(...))
        stmt = select(GridRegion).where(
            func.ST_Contains(GridRegion.boundary, point)
        )
        
        result = await db.execute(stmt)
        return result.scalars().first()
