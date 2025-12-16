# app/models/geo.py
from sqlalchemy import Column, String, Integer
from geoalchemy2 import Geometry
from app.models.models import Base
import uuid

class GridRegion(Base):
    """
    Model representing a power grid region with spatial definition.
    Used for locating which grid a coordinate belongs to.
    """
    __tablename__ = "grid_regions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)  # e.g., "WECC", "ERCOT"
    code = Column(String(50), nullable=False, unique=True, index=True) # e.g., "US-WECC"
    
    # Spatial column: Polygon or MultiPolygon (SRID 4326 = WGS 84)
    # management=True is often default/useful for ensuring geometry columns are set up correctly
    boundary = Column(Geometry('MULTIPOLYGON', srid=4326), nullable=False)

    def __repr__(self):
        return f"<GridRegion(name={self.name}, code={self.code})>"
