"""
Climatiq Service Layer
Business logic facade for Climatiq API interactions

Updated to match exact Climatiq API format based on official documentation:
- Electricity: /energy/electricity with amount/components structure
- Fuel: /energy/fuel with fuel_type and amount structure  
- Travel: /travel/distance and /travel/spend with origin/destination objects
- Freight: /freight/intermodal with route array (location/transport_mode alternating)
- Procurement: /procurement/spend with classification object
- Autopilot: /autopilot/estimate and /autopilot/suggest with text/domain/parameters
"""

from typing import Dict, Any, List, Optional, Union
from decimal import Decimal

from app.integration.climatiq.client import ClimatiqClient
from app.core.config import settings


class ClimatiqService:
    """
    High-level service for Climatiq API operations
    
    Provides:
    - Type-safe API interactions matching Climatiq's exact JSON format
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
        Calculate single emission estimate using generic estimate endpoint
        
        Args:
            activity_id: Climatiq activity ID
            parameters: Activity parameters (energy, weight, money)
            region: Region code (ISO 3166-1)
            year: Data year
            
        Returns:
            Estimate result with co2e
        """
        emission_factor = {
            "activity_id": activity_id,
            "data_version": settings.CLIMATIQ_DATA_VERSION
        }
        
        # Only include region/year if provided (avoid null values)
        if region:
            emission_factor["region"] = region
        if year:
            emission_factor["year"] = year
            
        payload = {
            "emission_factor": emission_factor,
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
    
    def _build_location(self, location: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build location object for Climatiq travel/freight endpoints
        
        Supports:
        - IATA codes (3 letters): {"iata": "CDG"}
        - Coordinates (lat,lon string): {"latitude": 46.08, "longitude": 2.34}
        - Free text: {"query": "Berlin, Germany"}
        """
        if isinstance(location, dict):
            return location
            
        location_str = str(location).strip()
        
        # Check if it's an IATA code (3 uppercase letters)
        if len(location_str) == 3 and location_str.isupper() and location_str.isalpha():
            return {"iata": location_str}
        
        # Check if it's coordinates (lat, lon format)
        if "," in location_str:
            parts = location_str.split(",")
            if len(parts) == 2:
                try:
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        return {"latitude": lat, "longitude": lon}
                except ValueError:
                    pass
        
        # Default to free text query
        return {"query": location_str}
    
    async def calculate_travel_distance(
        self,
        travel_mode: str,
        origin: Union[str, Dict[str, Any]],
        destination: Union[str, Dict[str, Any]],
        year: Optional[int] = None,
        flight_class: Optional[str] = None,
        car_size: Optional[str] = None,
        car_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate activity-based travel emissions
        
        Exact format from Climatiq docs:
        {
            "origin": {"iata": "CDG"} or {"query": "Berlin"} or {"latitude": X, "longitude": Y},
            "destination": {...},
            "year": 2022,
            "travel_mode": "air" | "car" | "rail",
            "air_details": {"class": "economy"},
            "car_details": {"car_size": "large", "car_type": "petrol"}
        }
        
        Args:
            travel_mode: "air", "car", or "rail"
            origin: IATA code, coordinates, or location name
            destination: IATA code, coordinates, or location name
            year: Travel year
            flight_class: For air: economy, business, first, average
            car_size: For car: small, medium, large, average
            car_type: For car: petrol, diesel, hybrid, plugin_hybrid, battery, average
            
        Returns:
            Travel emissions result
        """
        payload = {
            "origin": self._build_location(origin),
            "destination": self._build_location(destination),
            "travel_mode": travel_mode
        }
        
        if year:
            payload["year"] = year
        
        # Add mode-specific details
        if travel_mode == "air" and flight_class:
            payload["air_details"] = {"class": flight_class}
        elif travel_mode == "car":
            car_details = {}
            if car_size:
                car_details["car_size"] = car_size
            if car_type:
                car_details["car_type"] = car_type
            if car_details:
                payload["car_details"] = car_details
        
        return await self.client.travel_distance(payload)
    
    async def calculate_flight_emissions(
        self,
        origin: str,
        destination: str,
        cabin_class: str = "economy",
        year: int = 2024
    ) -> Dict[str, Any]:
        """
        Calculate air travel emissions (convenience method)
        
        Args:
            origin: Airport IATA code or location query
            destination: Airport IATA code or location query
            cabin_class: economy, business, first, premium_economy
            year: Travel year
            
        Returns:
            Distance and co2e result
        """
        return await self.calculate_travel_distance(
            travel_mode="air",
            origin=origin,
            destination=destination,
            year=year,
            flight_class=cabin_class
        )
    
    async def calculate_travel_spend(
        self,
        spend_type: str,
        amount: Decimal,
        currency: str,
        spend_year: int,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate spend-based travel emissions
        
        Exact format from Climatiq docs:
        {
            "spend_type": "hotel" | "air" | "rail" | "road" | "sea",
            "money": 10000,
            "money_unit": "eur",
            "spend_year": 2023,
            "spend_location": {"query": "Bern, Switzerland"}
        }
        
        Args:
            spend_type: hotel, air, rail, road, sea
            amount: Money spent
            currency: Currency code (eur, usd, gbp, etc.)
            spend_year: Year of spend (critical for inflation)
            location: Spend location (optional)
            
        Returns:
            Spend-based co2e result
        """
        payload = {
            "spend_type": spend_type,
            "money": float(amount),
            "money_unit": currency.lower(),
            "spend_year": spend_year
        }
        
        if location:
            payload["spend_location"] = {"query": location}
        
        return await self.client.travel_spend(payload)
    
    async def calculate_hotel_emissions(
        self,
        spend_amount: Decimal,
        currency: str,
        spend_year: int,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate hotel accommodation emissions from spend (convenience method)
        """
        return await self.calculate_travel_spend(
            spend_type="hotel",
            amount=spend_amount,
            currency=currency,
            spend_year=spend_year,
            location=location
        )
    
    # ========== Energy Operations ==========
    
    async def calculate_electricity_emissions(
        self,
        energy_kwh: Decimal,
        region: str,
        year: int = 2024,
        connection_type: str = "grid",
        energy_source: Optional[str] = None,
        renewable_credits: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Calculate electricity emissions (Scope 2)
        
        Exact format from Climatiq docs:
        {
            "year": 2024,
            "region": "ZA",
            "amount": {"energy": 13000, "energy_unit": "kWh"},
            "components": [{
                "amount": {"energy": 13000, "energy_unit": "kWh"},
                "connection_type": "grid",
                "energy_source": "coal"
            }],
            "recs": {"energy": 100, "energy_unit": "kWh"}  // optional
        }
        
        Args:
            energy_kwh: Energy consumption in kWh
            region: Grid region code (2-letter ISO or UN-LOCODE) - REQUIRED
            year: Consumption year
            connection_type: "grid" or "direct"
            energy_source: Optional: coal, natural_gas, biomass, nuclear, renewable
            renewable_credits: RECs for market-based reporting (kWh)
            
        Returns:
            Scope 2 emissions result
        """
        energy_amount = {
            "energy": float(energy_kwh),
            "energy_unit": "kWh"
        }
        
        payload = {
            "year": year,
            "region": region,
            "amount": energy_amount,
            "components": [{
                "amount": energy_amount,
                "connection_type": connection_type
            }]
        }
        
        # Add energy source if specified
        if energy_source:
            payload["components"][0]["energy_source"] = energy_source
        
        # Add RECs if specified
        if renewable_credits:
            payload["recs"] = {
                "energy": float(renewable_credits),
                "energy_unit": "kWh"
            }
        
        return await self.client.electricity(payload)
    
    async def calculate_fuel_emissions(
        self,
        fuel_type: str,
        amount: Decimal,
        unit: str,
        unit_type: str = "volume",
        region: Optional[str] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate fuel combustion emissions (Scope 1)
        
        Exact format from Climatiq docs:
        {
            "fuel_type": "natural_gas",
            "amount": {"volume": 23000, "volume_unit": "l"},
            "region": "US",
            "year": 2021
        }
        OR for weight:
        {
            "fuel_type": "coal",
            "amount": {"weight": 10, "weight_unit": "t"},
            "region": "BR"
        }
        
        Supported fuel_types: natural_gas, coal, cng, diesel, biodiesel_bio_100,
            gasoline, ethanol, heavy_fuel_oil, fuel_oil, kerosene, biogas_bio_100,
            hydrogen, wood_chips_bio_100, recycled_gas, propane
        
        Args:
            fuel_type: Type of fuel burned
            amount: Amount of fuel
            unit: Unit (l, kg, t, gal, m3, kWh, MJ, etc.)
            unit_type: "volume", "weight", or "energy"
            region: Country code (optional, 2-letter ISO)
            year: Consumption year (optional)
            
        Returns:
            Scope 1 emissions result
        """
        # Build amount object based on unit type
        if unit_type == "volume":
            amount_obj = {"volume": float(amount), "volume_unit": unit}
        elif unit_type == "weight":
            amount_obj = {"weight": float(amount), "weight_unit": unit}
        else:  # energy
            amount_obj = {"energy": float(amount), "energy_unit": unit}
        
        payload = {
            "fuel_type": fuel_type,
            "amount": amount_obj
        }
        
        if region:
            payload["region"] = region
        if year:
            payload["year"] = year
        
        return await self.client.fuel(payload)
    
    # ========== Freight Operations ==========
    
    async def calculate_freight_emissions(
        self,
        origin: Union[str, Dict[str, Any]],
        destination: Union[str, Dict[str, Any]],
        transport_mode: str,
        cargo_weight: Decimal,
        weight_unit: str = "kg"
    ) -> Dict[str, Any]:
        """
        Calculate simple freight emissions (single leg)
        
        Exact format from Climatiq docs:
        {
            "route": [
                {"location": {"query": "Barcelona, Spain"}},
                {"transport_mode": "air"},
                {"location": {"query": "Hamburg, Germany"}}
            ],
            "cargo": {"weight": 250, "weight_unit": "kg"}
        }
        
        Args:
            origin: Start location (query, IATA, UN-LOCODE, or coordinates)
            destination: End location
            transport_mode: "air", "road", "rail", "sea"
            cargo_weight: Weight of cargo
            weight_unit: "kg", "t", "lb", "ton"
            
        Returns:
            Freight emissions result with total co2e
        """
        payload = {
            "route": [
                {"location": self._build_location(origin)},
                {"transport_mode": transport_mode},
                {"location": self._build_location(destination)}
            ],
            "cargo": {
                "weight": float(cargo_weight),
                "weight_unit": weight_unit
            }
        }
        
        return await self.client.freight_intermodal(payload)
    
    async def calculate_intermodal_freight_emissions(
        self,
        route_legs: List[Dict[str, Any]],
        cargo_weight: Decimal,
        weight_unit: str = "kg"
    ) -> Dict[str, Any]:
        """
        Calculate multi-leg intermodal freight emissions
        
        Args:
            route_legs: List of legs, each with:
                - location: origin/waypoint location
                - transport_mode: mode to next location (optional for last)
            cargo_weight: Weight of cargo
            weight_unit: "kg", "t", "lb", "ton"
            
        Example route_legs:
        [
            {"location": "Barcelona, Spain", "transport_mode": "road"},
            {"location": "JFK", "transport_mode": "air"},
            {"location": "Los Angeles, USA"}
        ]
            
        Returns:
            Freight emissions with per-leg breakdown
        """
        # Build route in Climatiq's alternating format
        route = []
        for i, leg in enumerate(route_legs):
            # Add location
            route.append({"location": self._build_location(leg["location"])})
            # Add transport mode if not last leg
            if "transport_mode" in leg:
                route.append({"transport_mode": leg["transport_mode"]})
        
        payload = {
            "route": route,
            "cargo": {
                "weight": float(cargo_weight),
                "weight_unit": weight_unit
            }
        }
        
        return await self.client.freight_intermodal(payload)
    
    # ========== Procurement Operations ==========
    # NOTE: Procurement is also an ADD-ON feature.
    
    async def calculate_procurement_emissions(
        self,
        spend_amount: Decimal,
        currency: str,
        classification_code: str,
        classification_type: str = "mcc",
        region: Optional[str] = None,
        spend_year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate spend-based procurement emissions (EEIO)
        
        Exact format from Climatiq official docs (v1):
        POST https://api.climatiq.io/procurement/v1/spend
        {
            "activity": {
                "classification_code": "25",
                "classification_type": "isic4"
            },
            "spend_year": 2022,
            "spend_region": "DE",
            "money": 100,
            "money_unit": "eur"
        }
        
        Supported classification_types:
        - mcc: Merchant Category Codes  
        - unspsc: United Nations Standard Products and Services Code
        - isic4: International Standard Industrial Classification
        - nace2: Statistical Classification of Economic Activities (EU)
        - naics2017: North American Industry Classification System
        
        Args:
            spend_amount: Money spent
            currency: Currency code (eur, usd, gbp, etc.)
            classification_code: Industry/category code
            classification_type: mcc, unspsc, isic4, nace2, naics2017
            region: Supplier country (2-letter ISO code) - REQUIRED
            spend_year: Year of purchase - REQUIRED for inflation adjustment
            
        Returns:
            Scope 3 emissions result
        """
        # Build activity object
        activity = {
            "classification_code": str(classification_code),
            "classification_type": classification_type
        }
        
        payload = {
            "activity": activity,
            "money": float(spend_amount),
            "money_unit": currency.lower()
        }
        
        # spend_region is required
        if region:
            payload["spend_region"] = region
        else:
            raise ValueError("spend_region is required for procurement calculations")
        
        # spend_year is required
        if spend_year:
            payload["spend_year"] = spend_year
        else:
            raise ValueError("spend_year is required for procurement calculations")
        
        return await self.client.procurement(payload)
    
    # ========== Autopilot Operations ==========
    # NOTE: Autopilot is an ADD-ON feature that requires explicit opt-in from Climatiq.
    # Contact Climatiq at https://www.climatiq.io/contact-us to enable this feature.
    
    async def suggest_emission_factors(
        self,
        text: str,
        max_suggestions: int = 5,
        unit_type: Optional[List[str]] = None,
        region: Optional[str] = None,
        year: Optional[int] = None,
        source: Optional[List[str]] = None,
        scope: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get AI-powered emission factor suggestions (Autopilot Suggest)
        
        Exact format from Climatiq docs (v1-preview4):
        {
            "suggest": {
                "text": "Cement",
                "unit_type": ["Weight", "Money"],
                "region": "DE",
                "year": 2022,
                "source": ["EPA", "BEIS"]
            },
            "max_suggestions": 5
        }
        
        Args:
            text: Natural language activity description
            max_suggestions: Number of suggestions to return (1-20)
            unit_type: Filter by unit types: ["Money", "Weight", "Volume", "Energy", "Number"]
            region: Filter by region (2-letter ISO code)
            year: Filter by year
            source: Filter by data sources (e.g., ["EPA", "BEIS", "Ecoinvent"])
            scope: Filter by scope (e.g., ["1", "2", "3"] or ["3.1", "3.2"])
            
        Returns:
            List of suggested factors with suggestion_ids
        """
        suggest = {
            "text": text
        }
        
        if unit_type:
            suggest["unit_type"] = unit_type
        if region:
            suggest["region"] = region
        if year:
            suggest["year"] = year
        if source:
            suggest["source"] = source
        if scope:
            suggest["scope"] = scope
        
        payload = {
            "suggest": suggest,
            "max_suggestions": max_suggestions
        }
        
        return await self.client.autopilot_suggest(payload)
    
    async def calculate_with_autopilot(
        self,
        text: str,
        amount: Optional[Decimal] = None,
        unit: Optional[str] = None,
        unit_type: str = "money",
        region: Optional[str] = None,
        year: Optional[int] = None,
        scope: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        One-shot AI suggestion + calculation (Autopilot One-shot Estimate)
        
        Exact format from Climatiq docs (v1-preview4):
        {
            "text": "Steel",
            "parameters": {
                "money": 100,
                "money_unit": "usd"
            }
        }
        OR for weight:
        {
            "text": "Cement",
            "parameters": {
                "weight": 100,
                "weight_unit": "kg"
            },
            "region": "DE",
            "year": 2022
        }
        
        Args:
            text: Natural language activity description
            amount: Quantity value
            unit: Unit for the amount (eur, usd, kg, t, kWh, etc.)
            unit_type: "money", "weight", "volume", or "energy"
            region: Region code (optional)
            year: Year (optional)
            scope: Filter by scope (e.g., ["1", "2", "3"])
            
        Returns:
            Estimate with explanation of factor selection
        """
        payload = {
            "text": text
        }
        
        if region:
            payload["region"] = region
        if year:
            payload["year"] = year
        if scope:
            payload["scope"] = scope
        
        # Build parameters based on unit type
        if amount is not None and unit:
            if unit_type == "money":
                payload["parameters"] = {
                    "money": float(amount),
                    "money_unit": unit  # Keep original casing from normalizer
                }
            elif unit_type == "weight":
                payload["parameters"] = {
                    "weight": float(amount),
                    "weight_unit": unit  # Keep original casing from normalizer
                }
            elif unit_type == "volume":
                payload["parameters"] = {
                    "volume": float(amount),
                    "volume_unit": unit  # Keep original casing from normalizer
                }
            elif unit_type == "energy":
                payload["parameters"] = {
                    "energy": float(amount),
                    "energy_unit": unit  # Keep original casing from normalizer
                }
        
        print(f"DEBUG CLIMATIQ - Payload being sent: {payload}")
        return await self.client.autopilot_estimate(payload)
    
    async def calculate_with_ai_suggestion(
        self,
        text: str,
        amount: float,
        unit: str,
        unit_type: str = "energy",
        region: Optional[str] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Smart calculation using available Climatiq API access:
        1. Try Autopilot first (available to you)
        2. If Autopilot returns 0 CO2e, use Energy endpoint for electricity/gas
        3. Fall back to Emission Factors Data search + Estimate
        
        Args:
            text: Natural language activity description
            amount: Quantity value
            unit: Unit for the amount (kWh, kg, etc.)
            unit_type: "money", "weight", "volume", or "energy"
            region: Region code (optional)
            year: Year (optional)
            
        Returns:
            Estimate with CO2e calculation
        
        if co2e > 0:
            print("DEBUG - Autopilot worked!")
            return autopilot_result
        else:
            print("DEBUG - Autopilot returned 0 CO2e, trying specific endpoint")
            
    except Exception as e:
        print(f"DEBUG - Autopilot failed: {e}, trying specific endpoint")
    
    # Strategy 2: Try specific endpoint based on unit type and description
    try:
        if unit_type == "energy" and unit.lower() in ['kwh', 'mwh', 'gwh']:
            # Use Energy endpoint for electricity
            energy_payload = {
                "year": year or datetime.now().year,
                "amount": {
                    "energy": float(amount),
                    "energy_unit": unit
                },
                "data_version": "20.20"
            }
            if region:
                energy_payload["region"] = region
            
            print(f"DEBUG - Trying Energy endpoint: {energy_payload}")
            result = await client.electricity(energy_payload)
            
            # Convert to standard format
            return {
                "estimate": {
                    "co2e": result.get("co2e", 0),
                    "co2e_unit": "kg",
                    "emission_factor": result.get("emission_factor", {}),
                    "activity_data": {
                        "activity_value": float(amount),
                        "activity_unit": unit
                    }
                }
            }
            
        elif unit_type == "energy" and unit.lower() in ['therms', 'mmbtu', 'btu']:
            # Use Fuel endpoint for natural gas
            fuel_payload = {
                "fuel_type": "natural_gas",
                "amount": {
                    "energy": float(amount),
                    "energy_unit": unit
                },
                "year": year or datetime.now().year,
                "data_version": "20.20"
            }
            if region:
                fuel_payload["region"] = region
            
            print(f"DEBUG - Trying Fuel endpoint: {fuel_payload}")
            result = await client.fuel(fuel_payload)
            
            return {
                "estimate": {
                    "co2e": result.get("co2e", 0),
                    "co2e_unit": "kg",
                    "emission_factor": result.get("emission_factor", {}),
                    "activity_data": {
                        "activity_value": float(amount),
                        "activity_unit": unit
                    }
                }
            }
            
        elif unit_type == "distance" and ("travel" in text.lower() or "flight" in text.lower() or "car" in text.lower()):
            # Use Travel endpoint for distance-based travel
            travel_payload = {
                "origin": {"query": region or "US"},
                "destination": {"query": region or "US"},  # Simple fallback
                "travel_mode": "car" if "car" in text.lower() else "air",
                "car_details": {"car_type": "average"} if "car" in text.lower() else None
            }
            
            # For flights, use spend-based if amount is money
            if unit_type == "money" and "flight" in text.lower():
                travel_payload = {
                    "spend_type": "air",
                    "money": float(amount),
                    "money_unit": unit,
                    "spend_location": {"query": region or "US"},
                    "spend_year": year or datetime.now().year
                }
                print(f"DEBUG - Trying Travel spend endpoint: {travel_payload}")
                result = await client.travel_spend(travel_payload)
            else:
                print(f"DEBUG - Trying Travel distance endpoint: {travel_payload}")
                result = await client.travel_distance(travel_payload)
            
            return {
                "estimate": {
                    "co2e": result.get("co2e", 0),
                    "co2e_unit": "kg",
                    "emission_factor": result.get("emission_factor", {}),
                    "activity_data": {
                        "activity_value": float(amount),
                        "activity_unit": unit
                    }
                }
            }
            
    except Exception as e:
        print(f"DEBUG - Specific endpoint failed: {e}, trying Estimate endpoint")
    
    # Strategy 3: Try direct Estimate endpoint with search
    try:
        # Search for emission factors first
        search_params = {
            "query": text,
            "data_version": "20.20",
            "limit": 5
        }
        if region:
            search_params["region"] = region
        if year:
            search_params["year"] = year
        
        print(f"DEBUG - Searching emission factors: {search_params}")
        search_result = await client.search_emission_factors(search_params)
        
        if search_result.get("results") and len(search_result["results"]) > 0:
            # Use the first (most relevant) emission factor
            factor = search_result["results"][0]
            activity_id = factor.get("id")
    async def calculate_with_suggestion(
        self,
        suggestion_id: str,
        amount: Decimal,
        unit: str,
        unit_type: str = "weight"
    ) -> Dict[str, Any]:
        """
        Calculate using a suggestion_id from suggest_emission_factors
        
        Exact format from Climatiq docs (v1-preview4):
        {
            "suggestion_id": "mqydemtghbrtillegaztsljugm2dsllbga2wcljsgfrtcobrmm3dqnbxge...",
            "parameters": {
                "weight": 100,
                "weight_unit": "kg"
            }
        }
        
        Args:
            suggestion_id: ID from suggest_emission_factors result
            amount: Quantity value
            unit: Unit for the amount
            unit_type: "money", "weight", "volume", or "energy"
            
        Returns:
            Detailed estimation result
        """
        payload = {
            "suggestion_id": suggestion_id
        }
        
        if unit_type == "money":
            payload["parameters"] = {
                "money": float(amount),
                "money_unit": unit  # Keep original casing from normalizer
            }
        elif unit_type == "weight":
            payload["parameters"] = {
                "weight": float(amount),
                "weight_unit": unit  # Keep original casing from normalizer
            }
        elif unit_type == "volume":
            payload["parameters"] = {
                "volume": float(amount),
                "volume_unit": unit  # Keep original casing from normalizer
            }
        elif unit_type == "energy":
            payload["parameters"] = {
                "energy": float(amount),
                "energy_unit": unit  # Keep original casing from normalizer
            }
        
        return await self.client.autopilot_estimate_with_suggestion(payload)
    
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
