"""
Climatiq Service Layer
Business logic facade for Climatiq API interactions
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal

from app.integration.climatiq.client import ClimatiqClient
from app.integration.climatiq.schemas import (
    EstimateRequest,
    EstimateResponse,
    BatchEstimateRequest,
    DistanceTravelRequest,
    SpendTravelRequest,
    ElectricityRequest,
    FuelRequest,
    IntermodalFreightRequest,
    ProcurementRequest,
    AutopilotSuggestRequest
)
from app.core.config import settings


class ClimatiqService:
    """
    High-level service for Climatiq API operations
    
    Provides:
    - Type-safe API interactions using Pydantic schemas
    - Business logic abstraction
    - Response normalization
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = ClimatiqClient(api_key)
    
    # ========== Estimate Operations ==========
    
    async def calculate_single_estimate(
        self,
        activity_id: str,
        parameters: Dict[str, Any],
        region: Optional[str] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate single emission estimate
        
        Args:
            activity_id: Climatiq activity ID
            parameters: Activity parameters (energy, weight, money)
            region: Region code (ISO 3166-1)
            year: Data year
            
        Returns:
            Estimate result with co2e
        """
        payload = {
            "emission_factor": {
                "activity_id": activity_id,
                "data_version": settings.CLIMATIQ_DATA_VERSION,
                "region": region,
                "year": year
            },
            "parameters": parameters
        }
        
        return await self.client.estimate(payload)
    
    async def calculate_batch_estimates(
        self,
        estimates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate batch emissions (auto-chunked to 100-item limit)
        
        Args:
            estimates: List of estimate requests
            
        Returns:
            Batch results with individual results array
        """
        return await self.client.estimate_batch(estimates)
    
    # ========== Travel Operations ==========
    
    async def calculate_flight_emissions(
        self,
        origin: str,
        destination: str,
        cabin_class: str = "economy",
        year: int = 2024
    ) -> Dict[str, Any]:
        """
        Calculate air travel emissions
        
        Args:
            origin: Airport IATA code or location query
            destination: Airport IATA code or location query
            cabin_class: economy, business, first, premium_economy
            year: Travel year
            
        Returns:
            Distance and co2e result
        """
        payload = {
            "origin": {"query": origin},
            "destination": {"query": destination},
            "travel_mode": "air",
            "year": year,
            "air_details": {"class": cabin_class}
        }
        
        return await self.client.travel_distance(payload)
    
    async def calculate_hotel_emissions(
        self,
        spend_amount: Decimal,
        currency: str,
        spend_year: int,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate hotel accommodation emissions from spend
        
        Args:
            spend_amount: Money spent
            currency: Currency code (usd, eur, gbp)
            spend_year: Year of spend (critical for inflation)
            location: Hotel location region
            
        Returns:
            Spend-based co2e result
        """
        payload = {
            "spend_type": "hotel",
            "money": float(spend_amount),
            "money_unit": currency,
            "spend_year": spend_year
        }
        
        if location:
            payload["spend_location"] = {"query": location}
        
        return await self.client.travel_spend(payload)
    
    # ========== Energy Operations ==========
    
    async def calculate_electricity_emissions(
        self,
        energy_kwh: Decimal,
        region: str,
        year: int = 2024,
        renewable_credits: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Calculate electricity emissions (Scope 2)
        
        Args:
            energy_kwh: Energy consumption in kWh
            region: Grid region code (required - 10x variance!)
            year: Consumption year
            renewable_credits: RECs for market-based reporting
            
        Returns:
            Scope 2 emissions result
        """
        payload = {
            "energy": float(energy_kwh),
            "energy_unit": "kWh",
            "region": region,
            "year": year
        }
        
        if renewable_credits:
            payload["renewable_energy_credits"] = float(renewable_credits)
        
        return await self.client.electricity(payload)
    
    async def calculate_fuel_emissions(
        self,
        fuel_type: str,
        volume: Decimal,
        volume_unit: str,
        year: int = 2024
    ) -> Dict[str, Any]:
        """
        Calculate fuel combustion emissions (Scope 1)
        
        Args:
            fuel_type: natural_gas, diesel, gasoline, propane
            volume: Fuel volume
            volume_unit: liters, gallons, m3
            year: Consumption year
            
        Returns:
            Scope 1 emissions result
        """
        payload = {
            "fuel_type": fuel_type,
            "volume": float(volume),
            "volume_unit": volume_unit,
            "year": year
        }
        
        return await self.client.fuel(payload)
    
    # ========== Freight Operations ==========
    
    async def calculate_freight_emissions(
        self,
        route: List[Dict[str, Any]],
        cargo_weight_kg: Decimal
    ) -> Dict[str, Any]:
        """
        Calculate intermodal freight emissions
        
        Args:
            route: List of transport legs with origin, destination, mode
            cargo_weight_kg: Cargo weight in kg
            
        Returns:
            Total co2e with per-leg breakdown
        """
        payload = {
            "route": route,
            "cargo": {
                "weight": float(cargo_weight_kg),
                "weight_unit": "kg"
            }
        }
        
        return await self.client.freight_intermodal(payload)
    
    # ========== Procurement Operations ==========
    
    async def calculate_procurement_emissions(
        self,
        spend_amount: Decimal,
        currency: str,
        spend_year: int,
        classification_code: str,
        classification_type: str = "naics2017"
    ) -> Dict[str, Any]:
        """
        Calculate spend-based procurement emissions (EEIO)
        
        Args:
            spend_amount: Money spent
            currency: Currency code
            spend_year: Year (critical for inflation!)
            classification_code: Industry code
            classification_type: naics2017, isic4, nace2, mcc
            
        Returns:
            Scope 3 emissions result
        """
        payload = {
            "money": float(spend_amount),
            "money_unit": currency,
            "spend_year": spend_year,
            "classification": {
                "code": classification_code,
                "classification_type": classification_type
            }
        }
        
        return await self.client.procurement(payload)
    
    # ========== Autopilot Operations ==========
    
    async def suggest_emission_factors(
        self,
        description: str,
        domain: str = "general"
    ) -> Dict[str, Any]:
        """
        Get AI-powered emission factor suggestions
        
        Args:
            description: Natural language activity description
            domain: "general" or "manufacturing"
            
        Returns:
            List of suggested factors with confidence scores
        """
        return await self.client.autopilot_suggest(description, domain)
    
    async def calculate_with_autopilot(
        self,
        description: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combined suggestion + calculation
        
        Args:
            description: Natural language activity description
            parameters: Quantity parameters
            
        Returns:
            Estimate with explanation of factor selection
        """
        payload = {
            "query": description,
            "parameters": parameters
        }
        
        return await self.client.autopilot_estimate(payload)
    
    # ========== Search Operations ==========
    
    async def search_factors(
        self,
        query: str,
        region: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search emission factors database
        
        Args:
            query: Search query text
            region: Filter by region
            category: Filter by category
            page: Page number
            limit: Results per page
            
        Returns:
            Search results with emission factors
        """
        return await self.client.search_emission_factors(
            query=query,
            region=region,
            category=category,
            page=page,
            limit=limit
        )
