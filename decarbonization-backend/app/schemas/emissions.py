from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
from uuid import UUID

# This is the "Handshake" contract.
# The Semantic Adapter OUTPUTS this.
# The Analyst and Estimator INPUT/OUTPUT this.

class MarketInstrument(BaseModel):
    type: Literal["REC", "PPA"]
    volume_matched: float

class LocationData(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address_string: Optional[str] = None
    grid_region_id: Optional[str] = Field(default=None, description="Populated by PostGIS logic later")

class DataQuality(BaseModel):
    source_type: Literal["invoice_ocr", "meter_api", "user_entry", "estimation", "csv_import"]
    confidence_score: float = Field(ge=0.0, le=1.0)
    is_estimated: bool = False
    methodology: Optional[str] = None # e.g., "gap_filling_regression"

class StandardizedEmissionEvent(BaseModel):
    event_id: UUID | str
    org_id: UUID | str
    timestamp: datetime
    
    # Normalized Activity Data
    activity_type: Literal["electricity", "natural_gas", "diesel", "refrigerant", "purchased_goods"]
    activity_value: float
    activity_unit: Literal["kWh", "MWh", "therms", "liters", "gallons", "kg", "tonnes"]
    activity_id: Optional[str] = None # Added for Climatiq matching
    emission_factor: Optional[float] = None
    
    location: LocationData
    data_quality: DataQuality
    market_instruments: List[MarketInstrument] = []

    class Config:
        use_enum_values = True

class EmissionResult(BaseModel):
    location_based_co2e_kg: float
    market_based_co2e_kg: float
    factor_used: Dict[str, Any]  # Details of the factor used
    calculation_method: str = "standard_factor"