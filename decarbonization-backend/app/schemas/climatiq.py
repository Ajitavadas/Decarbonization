from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ClimatiqEmissionFactor(BaseModel):
    activity_id: Optional[str] = None
    id: Optional[str] = None
    data_version: Optional[str] = "20.20"
    region: Optional[str] = None
    year: Optional[int] = None
    source: Optional[str] = None
    source_lca_activity: Optional[str] = None

class ClimatiqParameters(BaseModel):
    # Flexible container for parameters like fuel, weight, distance, energy, etc.
    # The actual key depends on the activity (e.g., "energy", "weight", "distance")
    values: Dict[str, Any]

class ClimatiqEstimateRequest(BaseModel):
    emission_factor: ClimatiqEmissionFactor
    parameters: Dict[str, Any]

class ClimatiqEstimateResponse(BaseModel):
    co2e: float
    co2e_unit: str
    co2e_calculation_method: str
    co2e_calculation_origin: str
    emission_factor: Dict[str, Any]
    constituent_gases: Dict[str, Optional[float]]
    activity_data: Dict[str, Any]
    audit_trail: str

class ClimatiqSearchResult(BaseModel):
    id: str  # The UUID
    activity_id: str
    name: str
    category: str
    sector: str
    source: str
    region: str
    year: int
    unit_type: str
    data_version: str
    access_type: str
    source_lca_activity: Optional[str] = None

class ClimatiqSearchResponse(BaseModel):
    results: List[ClimatiqSearchResult]
    current_page: int
    last_page: int
    total_results: int
