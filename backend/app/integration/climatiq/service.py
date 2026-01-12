"""
Climatiq API integration service
Handles all communication with Climatiq API for emission calculations
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
from datetime import datetime

from app.core.config import settings
from app.integration.climatiq.client import ClimatiqClient
from app.integration.climatiq.exceptions import ClimatiqAPIError


class ClimatiqService:
    """
    Service for interacting with Climatiq API
    Handles emission calculations using various Climatiq endpoints
    """
    
    def __init__(self):
        self.client = ClimatiqClient()
    
    async def calculate_with_autopilot(
        self,
        text: str,
        amount: Optional[float] = None,
        unit: Optional[str] = None,
        unit_type: str = "money",
        region: Optional[str] = None,
        year: Optional[int] = None,
        scope: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        One-shot AI suggestion + calculation (Autopilot One-shot Estimate)
        """
        payload = {
            "domain": "general",
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
                    "money_unit": unit
                }
            elif unit_type == "weight":
                payload["parameters"] = {
                    "weight": float(amount),
                    "weight_unit": unit
                }
            elif unit_type == "volume":
                payload["parameters"] = {
                    "volume": float(amount),
                    "volume_unit": unit
                }
            elif unit_type == "energy":
                payload["parameters"] = {
                    "energy": float(amount),
                    "energy_unit": unit
                }
        
        return await self.client.autopilot_estimate(payload)
    
    async def calculate_with_ai_suggestion(
        self,
        text: str,
        amount: Optional[float] = None,
        unit: Optional[str] = None,
        unit_type: str = "money",
        region: Optional[str] = None,
        year: Optional[int] = None,
        scope: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Smart calculation strategy using available Climatiq endpoints:
        1. Try Autopilot (AI-powered)
        2. Try specific endpoint based on unit type and description
        3. Try direct Estimate endpoint with search
        """
        print(f"DEBUG - Smart calculation for: {text} ({amount} {unit})")
        
        text_lower = text.lower()
        
        # Skip Autopilot for activities that benefit from direct endpoint calculation:
        # - Flights/travel (Autopilot often misclassifies to wrong vehicle types)
        # - Natural gas/heating (Autopilot may use wrong emission factors)
        skip_autopilot = (
            any(air in text_lower for air in ['flight', 'fly', 'air', 'plane']) or
            any(gas in text_lower for gas in ['natural gas', 'heating', 'furnace', 'boiler']) or
            unit.lower() in ['therms', 'therm', 'mmbtu', 'btu']
        )
        
        # Strategy 1: Try Autopilot first (most flexible) - unless we should skip it
        if not skip_autopilot:
            try:
                autopilot_payload = {
                    "text": text
                }
                
                # CRITICAL: Include region and year in Autopilot request
                # Without this, Climatiq may use wrong country's emission factors
                if region:
                    autopilot_payload["region"] = region
                if year:
                    autopilot_payload["year"] = year

                if amount is not None and unit:
                    if unit_type == "money":
                        autopilot_payload["parameters"] = {
                            "money": float(amount),
                            "money_unit": unit
                        }
                    elif unit_type == "energy":
                        autopilot_payload["parameters"] = {
                            "energy": float(amount),
                            "energy_unit": unit
                        }
                    elif unit_type == "weight":
                        autopilot_payload["parameters"] = {
                            "weight": float(amount),
                            "weight_unit": unit
                        }
                    elif unit_type == "distance":
                        autopilot_payload["parameters"] = {
                            "distance": float(amount),
                            "distance_unit": unit
                        }
                    elif unit_type == "volume":
                        autopilot_payload["parameters"] = {
                            "volume": float(amount),
                            "volume_unit": unit
                        }
                
                print(f"DEBUG - Trying Autopilot with: {autopilot_payload}")
                autopilot_result = await self.client.autopilot_estimate(autopilot_payload)
                
                # Check if we got a valid result with CO2e > 0
                estimate = autopilot_result.get("estimate", {})
                co2e = estimate.get("co2e", 0)
                
                # VALIDATION: Check if Autopilot used the correct region
                if co2e > 0 and region:
                    emission_factor = estimate.get("emission_factor", {})
                    used_region = emission_factor.get("region", "")
                    
                    # Check if region matches (allow partial match, e.g., "US" in "US-CA")
                    region_ok = (
                        used_region.upper() == region.upper() or
                        used_region.upper().startswith(region.upper() + "-") or
                        region.upper().startswith(used_region.upper() + "-")
                    )
                    
                    if not region_ok:
                        print(f"DEBUG - Autopilot used wrong region: requested={region}, got={used_region}. Falling back.")
                    else:
                        print(f"DEBUG - Autopilot worked with correct region: {used_region}")
                        autopilot_result["endpoint_type"] = "autopilot"
                        return autopilot_result
                elif co2e > 0:
                    print("DEBUG - Autopilot worked!")
                    autopilot_result["endpoint_type"] = "autopilot"
                    return autopilot_result
                else:
                    print("DEBUG - Autopilot returned 0 CO2e, trying specific endpoint")
                    
            except Exception as e:
                print(f"DEBUG - Autopilot failed: {e}, trying specific endpoint")
        else:
            print(f"DEBUG - Skipping Autopilot for: {text[:50]}... (using direct endpoint)")
        
        # Strategy 2: Try specific endpoint based on unit type and description
        text_lower = text.lower()
        
        # Check if this is natural gas/heating (even if unit is kWh after conversion)
        is_gas_heating = any(gas in text_lower for gas in [
            'natural gas', 'gas heating', 'heating', 'furnace', 'boiler', 'therms'
        ])
        
        try:
            # NATURAL GAS / HEATING: Use Estimate endpoint with natural gas activity_id
            if is_gas_heating or unit.lower() in ['therms', 'therm', 'mmbtu', 'btu']:
                # Convert to kWh if needed
                if unit.lower() in ['therms', 'therm']:
                    energy_amount = float(amount) * 29.3  # 1 therm = 29.3 kWh
                    energy_unit = "kWh"
                elif unit.lower() == 'mmbtu':
                    energy_amount = float(amount) * 293.07  # 1 MMBtu = 293.07 kWh
                    energy_unit = "kWh"
                else:
                    energy_amount = float(amount)
                    energy_unit = unit if unit.lower() in ['kwh', 'mwh'] else 'kWh'
                
                # Use Estimate endpoint with direct activity_id for natural gas
                estimate_payload = {
                    "emission_factor": {
                        "activity_id": "fuel-type_natural_gas-fuel_use_stationary",
                        "region": region or "US",
                        "data_version": settings.CLIMATIQ_DATA_VERSION
                    },
                    "parameters": {
                        "energy": energy_amount,
                        "energy_unit": energy_unit
                    }
                }
                
                print(f"DEBUG - Trying Estimate endpoint (natural gas): {estimate_payload}")
                result = await self.client.estimate(estimate_payload)

                co2e = result.get("co2e", 0)
                
                return {
                    "estimate": {
                        "co2e": co2e,
                        "co2e_unit": "kg",
                        "emission_factor": result.get("emission_factor", {}),
                        "activity_data": result.get("activity_data", {
                            "activity_value": float(amount),
                            "activity_unit": unit
                        })
                    },
                    "endpoint_type": "estimate_natural_gas"
                }
            
            # ELECTRICITY: kWh, MWh for electricity usage (NOT heating)
            elif unit_type == "energy" and unit.lower() in ['kwh', 'mwh', 'gwh', 'wh']:
                energy_payload = {
                    "year": year or datetime.now().year,
                    "region": region or "US",
                    "amount": {
                        "energy": float(amount),
                        "energy_unit": unit
                    }
                }
                
                print(f"DEBUG - Trying Electricity endpoint: {energy_payload}")
                result = await self.client.electricity(energy_payload)

                # Electricity returns: location.consumption.co2e OR direct co2e
                co2e = 0
                if "location" in result and "consumption" in result["location"]:
                    co2e = result["location"]["consumption"].get("co2e", 0)
                elif "co2e" in result:
                    co2e = result.get("co2e", 0)
                
                return {
                    "estimate": {
                        "co2e": co2e,
                        "co2e_unit": "kg",
                        "emission_factor": result.get("emission_factor", {}),
                        "activity_data": {
                            "activity_value": float(amount),
                            "activity_unit": unit
                        }
                    },
                    "endpoint_type": "energy"
                }
            
            # FUEL: Diesel, gasoline, petrol, natural gas
            elif (unit_type == "volume" or unit.lower() in ['gallons', 'gallon', 'gal', 'liters', 'l', 'm3']) and \
                 any(fuel in text_lower for fuel in ['diesel', 'gasoline', 'petrol', 'fuel', 'generator', 'fleet', 'vehicle']):
                
                # Determine fuel type from description - use CORRECT Climatiq fuel_type values
                if 'diesel' in text_lower:
                    fuel_type = "diesel"  # Not diesel_100!
                elif 'gasoline' in text_lower or 'petrol' in text_lower:
                    fuel_type = "motor_gasoline"  # Not petrol_average!
                else:
                    fuel_type = "diesel"  # Default for fleet/generator
                
                # Convert gallons to liters (1 gallon = 3.78541 liters)
                if unit.lower() in ['gallons', 'gallon', 'gal']:
                    volume_amount = float(amount) * 3.78541
                    volume_unit = "l"
                else:
                    volume_amount = float(amount)
                    volume_unit = unit.lower() if unit.lower() in ['l', 'm3'] else 'l'
                
                fuel_payload = {
                    "fuel_type": fuel_type,
                    "amount": {
                        "volume": volume_amount,
                        "volume_unit": volume_unit
                    },
                    "region": region or "US",
                    "year": year or datetime.now().year
                }
                
                print(f"DEBUG - Trying Fuel endpoint: {fuel_payload}")
                result = await self.client.fuel(fuel_payload)

                # Fuel returns: combustion.co2e
                co2e = result.get("combustion", {}).get("co2e", 0)
                
                return {
                    "estimate": {
                        "co2e": co2e,
                        "co2e_unit": "kg",
                        "emission_factor": result.get("combustion", {}).get("emission_factor", {}),
                        "activity_data": {
                            "activity_value": float(amount),
                            "activity_unit": unit
                        }
                    },
                    "endpoint_type": "fuel"
                }
            
            # NATURAL GAS: therms, MMBtu for heating
            elif (unit.lower() in ['therms', 'therm', 'mmbtu', 'btu'] or 
                  any(gas in text_lower for gas in ['natural gas', 'gas heating', 'heating'])):
                
                # Natural gas uses energy units, convert therms to kWh
                if unit.lower() in ['therms', 'therm']:
                    energy_amount = float(amount) * 29.3  # 1 therm = 29.3 kWh
                    energy_unit = "kWh"
                elif unit.lower() == 'mmbtu':
                    energy_amount = float(amount) * 293.07  # 1 MMBtu = 293.07 kWh
                    energy_unit = "kWh"
                else:
                    energy_amount = float(amount)
                    energy_unit = unit
                
                fuel_payload = {
                    "fuel_type": "natural_gas",
                    "amount": {
                        "energy": energy_amount,
                        "energy_unit": energy_unit
                    },
                    "region": region or "US",
                    "year": year or datetime.now().year
                }
                
                print(f"DEBUG - Trying Fuel endpoint (natural gas): {fuel_payload}")
                result = await self.client.fuel(fuel_payload)

                co2e = result.get("combustion", {}).get("co2e", 0)
                
                return {
                    "estimate": {
                        "co2e": co2e,
                        "co2e_unit": "kg",
                        "emission_factor": result.get("combustion", {}).get("emission_factor", {}),
                        "activity_data": {
                            "activity_value": float(amount),
                            "activity_unit": unit
                        }
                    },
                    "endpoint_type": "fuel"
                }
            
            # TRAVEL SPEND: flights, travel with money units
            elif unit_type == "money" and any(travel in text_lower for travel in ['flight', 'travel', 'air']):
                travel_spend_payload = {
                    "spend_type": "air",
                    "money": float(amount),
                    "money_unit": unit.lower(),
                    "spend_location": {"query": region or "US"},
                    "spend_year": year or datetime.now().year
                }
                
                print(f"DEBUG - Trying Travel Spend endpoint: {travel_spend_payload}")
                result = await self.client.travel_spend(travel_spend_payload)

                return {
                    "estimate": {
                        "co2e": result.get("co2e", 0),
                        "co2e_unit": "kg",
                        "emission_factor": result.get("emission_factor", {}),
                        "activity_data": {
                            "activity_value": float(amount),
                            "activity_unit": unit
                        }
                    },
                    "endpoint_type": "travel_spend"
                }
            
            # TRAVEL DISTANCE: miles, km for car travel, commute, flights
            # Use Estimate endpoint with distance-based emission factors
            elif unit_type == "distance" or unit.lower() in ['miles', 'mile', 'mi', 'km', 'kilometers', 'kilometre']:
                # Determine emission factor based on activity type
                is_flight = any(air in text_lower for air in ['flight', 'fly', 'air', 'plane'])
                
                if is_flight:
                    # Flights use PassengerOverDistance unit type (passenger-km)
                    # BEIS provides best flight factors (GB region)
                    activity_id = "passenger_flight-route_type_domestic-aircraft_type_na-distance_na-class_na-rf_included-distance_uplift_included"
                    
                    # Convert miles to km if needed
                    if unit.lower() in ['miles', 'mile', 'mi']:
                        distance_km = float(amount) * 1.60934
                    else:
                        distance_km = float(amount)
                    
                    estimate_payload = {
                        "emission_factor": {
                            "activity_id": activity_id,
                            "region": "GB",  # BEIS factors for flights
                            "data_version": settings.CLIMATIQ_DATA_VERSION
                        },
                        "parameters": {
                            "passengers": 1,  # Assuming 1 passenger per business trip
                            "distance": distance_km,
                            "distance_unit": "km"
                        }
                    }
                    
                    print(f"DEBUG - Trying Estimate endpoint for FLIGHT: {estimate_payload}")
                    result = await self.client.estimate(estimate_payload)
                    
                    co2e = result.get("co2e", 0)
                    
                    return {
                        "estimate": {
                            "co2e": co2e,
                            "co2e_unit": "kg",
                            "emission_factor": result.get("emission_factor", {}),
                            "activity_data": result.get("activity_data", {
                                "activity_value": float(amount),
                                "activity_unit": unit
                            })
                        },
                        "endpoint_type": "estimate_flight"
                    }
                
                elif any(rail in text_lower for rail in ['train', 'rail']):
                    activity_id = "passenger_train-route_type_intercity-fuel_source_na"
                else:
                    # Default to car for commute, rental car, business travel
                    activity_id = "passenger_vehicle-vehicle_type_car-fuel_source_na-engine_size_na-vehicle_age_na-vehicle_weight_na"
                
                # For non-flight travel: car/train
                # Normalize distance unit to Climatiq format
                distance_unit_map = {
                    'miles': 'mi',
                    'mile': 'mi', 
                    'mi': 'mi',
                    'km': 'km',
                    'kilometers': 'km',
                    'kilometre': 'km',
                    'kilometer': 'km'
                }
                normalized_unit = distance_unit_map.get(unit.lower(), 'mi')
                
                estimate_payload = {
                    "emission_factor": {
                        "activity_id": activity_id,
                        "region": region or "US",
                        "data_version": settings.CLIMATIQ_DATA_VERSION
                    },
                    "parameters": {
                        "distance": float(amount),
                        "distance_unit": normalized_unit
                    }
                }
                
                print(f"DEBUG - Trying Estimate endpoint for travel: {estimate_payload}")
                result = await self.client.estimate(estimate_payload)
                
                # Estimate endpoint returns co2e directly
                co2e = result.get("co2e", 0)
                
                return {
                    "estimate": {
                        "co2e": co2e,
                        "co2e_unit": "kg",
                        "emission_factor": result.get("emission_factor", {}),
                        "activity_data": result.get("activity_data", {
                            "activity_value": float(amount),
                            "activity_unit": unit
                        })
                    },
                    "endpoint_type": "estimate"
                }
            
            # PROCUREMENT: spending on supplies, equipment, services
            elif unit_type == "money":
                procurement_payload = {
                    "activity": {
                        "classification_code": "25",  # Default to manufacturing
                        "classification_type": "isic4"
                    },
                    "spend_year": year or datetime.now().year,
                    "spend_region": region or "US",
                    "money": float(amount),
                    "money_unit": unit.lower()
                }

                print(f"DEBUG - Trying Procurement endpoint: {procurement_payload}")
                result = await self.client.procurement(procurement_payload)

                # Procurement returns: estimate.co2e
                co2e = result.get("estimate", {}).get("co2e", 0)
                
                return {
                    "estimate": {
                        "co2e": co2e,
                        "co2e_unit": "kg",
                        "emission_factor": result.get("estimate", {}).get("emission_factor", {}),
                        "activity_data": {
                            "activity_value": float(amount),
                            "activity_unit": unit
                        }
                    },
                    "endpoint_type": "procurement"
                }
                
        except Exception as e:
            print(f"DEBUG - Specific endpoint failed: {e}, trying Estimate endpoint")
        
        # Strategy 3: Try direct Estimate endpoint with search
        try:
            # Search for emission factors first
            search_params = {
                "query": text,
                "data_version": settings.CLIMATIQ_DATA_VERSION,
                "limit": 5
            }
            if region:
                search_params["region"] = region
            if year:
                search_params["year"] = year
            
            print(f"DEBUG - Searching emission factors: {search_params}")
            search_result = await self.client.search_emission_factors(search_params)
            
            if search_result.get("results") and len(search_result["results"]) > 0:
                # Use first (most relevant) emission factor
                factor = search_result["results"][0]
                activity_id = factor.get("id")
                
                # Build estimate payload
                estimate_payload = {
                    "emission_factor": {
                        "id": activity_id,
                        "data_version": settings.CLIMATIQ_DATA_VERSION
                    },
                    "parameters": {}
                }
                
                # Add parameters based on unit type
                if unit_type == "money":
                    estimate_payload["parameters"] = {
                        "money": float(amount),
                        "money_unit": unit
                    }
                elif unit_type == "energy":
                    estimate_payload["parameters"] = {
                        "energy": float(amount),
                        "energy_unit": unit
                    }
                elif unit_type == "weight":
                    estimate_payload["parameters"] = {
                        "weight": float(amount),
                        "weight_unit": unit
                    }
                elif unit_type == "distance":
                    estimate_payload["parameters"] = {
                        "distance": float(amount),
                        "distance_unit": unit
                    }
                elif unit_type == "volume":
                    estimate_payload["parameters"] = {
                        "volume": float(amount),
                        "volume_unit": unit
                    }
                
                print(f"DEBUG - Trying Estimate endpoint: {estimate_payload}")
                result = await self.client.estimate(estimate_payload)
                return result
                
        except Exception as e:
            print(f"DEBUG - Estimate endpoint failed: {e}")
        
        # Fallback: Return empty result
        print("DEBUG - All strategies failed, returning empty result")
        return {
            "estimate": {
                "co2e": 0,
                "co2e_unit": "kg",
                "emission_factor": None,
                "error": "No suitable emission factor found"
            }
        }
    
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
        Suggests emission factors based on natural language text.
        
        Exact format from Climatiq docs (v1-preview4):
        {
            "text": "Steel production",
            "filter": {
                "unit_type": ["Weight", "Money"],
                "region": "DE",
                "year": 2022,
                "source": ["EPA", "BEIS"]
            },
            "max_suggestions": 5
        }
        """
        suggest = {
            "text": text
        }
        
        filter_params = {}
        if unit_type:
            filter_params["unit_type"] = unit_type
        if region:
            filter_params["region"] = region
        if year:
            filter_params["year"] = year
        if source:
            filter_params["source"] = source
        if scope:
            filter_params["scope"] = scope
            
        if filter_params:
            suggest["filter"] = filter_params
            
        suggest["max_suggestions"] = max_suggestions
        
        return await self.client.autopilot_suggest(suggest)
    
    def _parse_location(self, location_str: str) -> Dict[str, Any]:
        """
        Parse location string into Climatiq-compatible format
        """
        if not location_str:
            return {"query": "Global"}
        
        # Check if it's a country code
        if len(location_str) == 2 and location_str.isupper():
            return {"query": location_str}
        
        # Check if it's coordinates
        if "," in location_str:
            try:
                lat, lon = map(float, location_str.split(","))
                return {
                    "latitude": lat,
                    "longitude": lon
                }
            except:
                pass
        
        # Default to free text query
        return {"query": location_str}
    
    async def calculate_with_classification(
        self,
        classification: Dict[str, Any],
        amount: float,
        unit: str,
        region: Optional[str] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate emissions using AI classification to route to correct endpoint.
        
        Args:
            classification: AI classification result containing:
                - endpoint: The endpoint to use
                - parameter_type: Type of parameter
                - fuel_type: (optional) For fuel endpoint
                - activity_search: Keywords to search for activity_id
                - normalized_description: For autopilot
            amount: Activity amount
            unit: Unit of measurement
            region: Geographic region
            year: Year of activity
            
        Returns:
            Emission calculation result with co2e
        """
        endpoint = classification.get("endpoint", "autopilot")
        param_type = classification.get("parameter_type", "weight")
        fuel_type = classification.get("fuel_type")
        activity_search = classification.get("activity_search", "")
        normalized_desc = classification.get("normalized_description", "")
        
        year = year or datetime.now().year
        region = region or "US"
        
        print(f"DEBUG - Using endpoint: {endpoint}, param_type: {param_type}, search: {activity_search}")
        
        try:
            # Route to appropriate endpoint
            if endpoint == "fuel":
                return await self._calculate_fuel(fuel_type, amount, unit, param_type, region, year)
            
            elif endpoint == "electricity":
                return await self._calculate_electricity(amount, unit, region, year)
            
            elif endpoint == "heat_steam":
                return await self._calculate_heat_steam(amount, unit, region, year)
            
            elif endpoint == "estimate":
                return await self._calculate_estimate(activity_search, amount, unit, param_type, region, year)
            
            elif endpoint == "freight":
                return await self._calculate_freight(activity_search, amount, unit, region, year)
            
            else:  # autopilot
                return await self._calculate_autopilot(normalized_desc, amount, unit, param_type, region, year)
                
        except Exception as e:
            print(f"DEBUG - Endpoint {endpoint} failed: {e}, falling back to autopilot")
            # Fallback to autopilot
            try:
                return await self._calculate_autopilot(normalized_desc, amount, unit, param_type, region, year)
            except Exception as e2:
                print(f"DEBUG - Autopilot fallback also failed: {e2}")
                return {
                    "estimate": {"co2e": 0, "co2e_unit": "kg", "error": str(e)},
                    "endpoint_type": "error"
                }
    
    async def _calculate_fuel(
        self,
        fuel_type: str,
        amount: float,
        unit: str,
        param_type: str,
        region: str,
        year: int
    ) -> Dict[str, Any]:
        """Calculate emissions using the fuel endpoint"""
        
        # Map common fuel types to Climatiq values
        fuel_type_map = {
            "diesel": "diesel",
            "lpg": "lpg",
            "natural_gas": "natural_gas",
            "motor_gasoline": "motor_gasoline",
            "petrol": "motor_gasoline",
            "gasoline": "motor_gasoline",
            "propane": "lpg"
        }
        
        mapped_fuel = fuel_type_map.get(fuel_type, "diesel")
        
        # Build amount based on parameter type
        if param_type == "volume":
            # Normalize volume unit
            unit_lower = unit.lower()
            if unit_lower in ['gal', 'gallon', 'gallons']:
                volume = float(amount) * 3.78541  # Convert to liters
                volume_unit = "l"
            elif unit_lower in ['m3', 'm³']:
                volume = float(amount) * 1000  # Convert to liters
                volume_unit = "l"
            else:
                volume = float(amount)
                volume_unit = "l"
            
            fuel_payload = {
                "fuel_type": mapped_fuel,
                "amount": {
                    "volume": volume,
                    "volume_unit": volume_unit
                },
                "region": region,
                "year": year
            }
        
        elif param_type == "energy":
            # Fuel by energy (e.g., natural gas in kWh)
            unit_lower = unit.lower()
            if unit_lower in ['therm', 'therms']:
                energy = float(amount) * 29.3  # Convert to kWh
                energy_unit = "kWh"
            elif unit_lower == 'mmbtu':
                energy = float(amount) * 293.07  # Convert to kWh
                energy_unit = "kWh"
            elif unit_lower == 'gj':
                energy = float(amount) * 277.78  # Convert to kWh
                energy_unit = "kWh"
            else:
                energy = float(amount)
                energy_unit = unit if unit.lower() in ['kwh', 'mwh'] else 'kWh'
            
            fuel_payload = {
                "fuel_type": mapped_fuel,
                "amount": {
                    "energy": energy,
                    "energy_unit": energy_unit
                },
                "region": region,
                "year": year
            }
        
        elif param_type == "weight":
            # Fuel by weight (e.g., LPG in kg)
            weight = float(amount)
            unit_lower = unit.lower()
            if unit_lower in ['tonne', 'tonnes', 't', 'ton', 'tons']:
                weight = weight * 1000  # Convert to kg
            weight_unit = "kg"
            
            fuel_payload = {
                "fuel_type": mapped_fuel,
                "amount": {
                    "weight": weight,
                    "weight_unit": weight_unit
                },
                "region": region,
                "year": year
            }
        
        else:
            # Default to volume
            fuel_payload = {
                "fuel_type": mapped_fuel,
                "amount": {
                    "volume": float(amount),
                    "volume_unit": "l"
                },
                "region": region,
                "year": year
            }
        
        print(f"DEBUG - Fuel payload: {fuel_payload}")
        result = await self.client.fuel(fuel_payload)
        
        # Extract CO2e from fuel response
        co2e = result.get("combustion", {}).get("co2e", 0)
        
        return {
            "estimate": {
                "co2e": co2e,
                "co2e_unit": "kg",
                "emission_factor": result.get("combustion", {}).get("emission_factor", {}),
                "activity_data": {
                    "activity_value": float(amount),
                    "activity_unit": unit
                }
            },
            "endpoint_type": "fuel"
        }
    
    async def _calculate_electricity(
        self,
        amount: float,
        unit: str,
        region: str,
        year: int
    ) -> Dict[str, Any]:
        """Calculate emissions using the electricity endpoint"""
        
        # Normalize energy unit
        unit_lower = unit.lower()
        if unit_lower == 'mwh':
            energy = float(amount) * 1000  # Convert to kWh
            energy_unit = "kWh"
        elif unit_lower == 'gwh':
            energy = float(amount) * 1000000  # Convert to kWh
            energy_unit = "kWh"
        else:
            energy = float(amount)
            energy_unit = "kWh"
        
        electricity_payload = {
            "year": year,
            "region": region,
            "amount": {
                "energy": energy,
                "energy_unit": energy_unit
            }
        }
        
        print(f"DEBUG - Electricity payload: {electricity_payload}")
        result = await self.client.electricity(electricity_payload)
        
        # Extract CO2e from electricity response
        co2e = 0
        if "location" in result and "consumption" in result["location"]:
            co2e = result["location"]["consumption"].get("co2e", 0)
        elif "co2e" in result:
            co2e = result.get("co2e", 0)
        
        return {
            "estimate": {
                "co2e": co2e,
                "co2e_unit": "kg",
                "emission_factor": result.get("emission_factor", {}),
                "activity_data": {
                    "activity_value": float(amount),
                    "activity_unit": unit
                }
            },
            "endpoint_type": "electricity"
        }
    
    async def _calculate_heat_steam(
        self,
        amount: float,
        unit: str,
        region: str,
        year: int
    ) -> Dict[str, Any]:
        """Calculate emissions using direct estimation for heat/steam"""
        
        # Normalize energy unit for the estimate call
        unit_lower = unit.lower()
        if unit_lower == 'gj':
            energy = float(amount) * 277.78  # Convert to kWh
            energy_unit = "kWh"
        elif unit_lower == 'mmbtu':
            energy = float(amount) * 293.07  # Convert to kWh
            energy_unit = "kWh"
        elif unit_lower == 'mwh':
            energy = float(amount) * 1000  # Convert to kWh
            energy_unit = "kWh"
        else:
            energy = float(amount)
            energy_unit = "kWh"
        
        print(f"DEBUG - Heat/Steam using direct estimate with {energy} {energy_unit}")
        
        # Use direct estimation with steam activity_id
        return await self._calculate_estimate(
            activity_search="steam heat purchased",
            amount=energy,
            unit=energy_unit,
            param_type="energy",
            region=region,
            year=year
        )
    
    async def _calculate_estimate(
        self,
        activity_search: str,
        amount: float,
        unit: str,
        param_type: str,
        region: str,
        year: int
    ) -> Dict[str, Any]:
        """Calculate emissions using the estimate endpoint with dynamic activity_id search"""
        
        # Ensure activity_search is a string (may come as list from AI)
        if isinstance(activity_search, list):
            activity_search = " ".join(activity_search)
        
        # Search for the best activity_id
        print(f"DEBUG - Searching for activity_id with: {activity_search}")
        search_result = await self.client.search_emission_factors(
            query=activity_search,
            region=region,
            year=year,
            data_version=settings.CLIMATIQ_DATA_VERSION,
            limit=5
        )
        
        results = search_result.get("results", [])
        
        # If no results for specific region, try without region filter
        if not results:
            print(f"DEBUG - No results for '{activity_search}' in {region}, trying global search")
            search_result = await self.client.search_emission_factors(
                query=activity_search,
                data_version=settings.CLIMATIQ_DATA_VERSION,
                limit=10
            )
            results = search_result.get("results", [])
        
        # If still no results, try broader search
        if not results:
            print(f"DEBUG - No results, trying broader search with first word")
            first_word = activity_search.split()[0] if activity_search else ""
            search_result = await self.client.search_emission_factors(
                query=first_word,
                data_version=settings.CLIMATIQ_DATA_VERSION,
                limit=10
            )
            results = search_result.get("results", [])
        
        if not results:
            print(f"DEBUG - Still no results, falling back to autopilot")
            return await self._calculate_autopilot(activity_search, amount, unit, param_type, region, year)
        
        # Find the best matching result based on unit type
        activity_id = None
        selected_result = None
        for r in results:
            unit_type = r.get("unit_type", [])
            
            # Match unit type to parameter type
            if param_type == "weight" and "Weight" in unit_type:
                activity_id = r.get("activity_id")
                selected_result = r
                break
            elif param_type == "distance" and "Distance" in unit_type:
                activity_id = r.get("activity_id")
                selected_result = r
                break
            elif param_type == "energy" and "Energy" in unit_type:
                activity_id = r.get("activity_id")
                selected_result = r
                break
            elif param_type == "money" and "Money" in unit_type:
                activity_id = r.get("activity_id")
                selected_result = r
                break
            elif param_type == "passengers_distance" and "PassengersDistance" in unit_type:
                activity_id = r.get("activity_id")
                selected_result = r
                break
        
        # If no exact match, use the first result
        if not activity_id and results:
            activity_id = results[0].get("activity_id")
            selected_result = results[0]
        
        if not activity_id:
            return await self._calculate_autopilot(activity_search, amount, unit, param_type, region, year)
        
        print(f"DEBUG - Found activity_id: {activity_id}")
        
        # Build parameters based on type
        params = self._build_estimate_params(amount, unit, param_type)
        
        # Use the region from the found result if original region had no results
        result_region = selected_result.get("region", region) if selected_result else region
        
        estimate_payload = {
            "emission_factor": {
                "activity_id": activity_id,
                "data_version": settings.CLIMATIQ_DATA_VERSION
            },
            "parameters": params
        }
        
        # Only add region if we have one
        if result_region:
            estimate_payload["emission_factor"]["region"] = result_region
        
        print(f"DEBUG - Estimate payload: {estimate_payload}")
        result = await self.client.estimate(estimate_payload)
        
        co2e = result.get("co2e", 0)
        
        return {
            "estimate": {
                "co2e": co2e,
                "co2e_unit": "kg",
                "emission_factor": result.get("emission_factor", {}),
                "activity_data": result.get("activity_data", {
                    "activity_value": float(amount),
                    "activity_unit": unit
                })
            },
            "endpoint_type": "estimate"
        }
    
    def _build_estimate_params(self, amount: float, unit: str, param_type: str) -> Dict[str, Any]:
        """Build parameters for the estimate endpoint"""
        
        unit_lower = unit.lower()
        
        if param_type == "weight":
            weight = float(amount)
            if unit_lower in ['tonne', 'tonnes', 't', 'ton', 'tons']:
                weight = weight * 1000  # Convert to kg
            return {"weight": weight, "weight_unit": "kg"}
        
        elif param_type == "distance":
            distance = float(amount)
            if unit_lower in ['mi', 'mile', 'miles']:
                return {"distance": distance, "distance_unit": "mi"}
            return {"distance": distance, "distance_unit": "km"}
        
        elif param_type == "passengers_distance":
            distance = float(amount)
            if unit_lower in ['mi', 'mile', 'miles']:
                return {"passengers": 1, "distance": distance, "distance_unit": "mi"}
            return {"passengers": 1, "distance": distance, "distance_unit": "km"}
        
        elif param_type == "weight_distance":
            # For freight in tkm (tonne-kilometers)
            # Amount is already in tkm, need to provide weight and distance
            # Climatiq expects weight (kg) and distance (km) separately
            tkm = float(amount)
            # Assume 1 tonne weight, so tkm = distance in km
            # This means: weight = 1000 kg, distance = tkm km
            return {"weight": 1000, "weight_unit": "kg", "distance": tkm, "distance_unit": "km"}
        
        elif param_type == "energy":
            energy = float(amount)
            if unit_lower == 'gj':
                energy = energy * 277.78
            elif unit_lower == 'mwh':
                energy = energy * 1000
            return {"energy": energy, "energy_unit": "kWh"}
        
        elif param_type == "money":
            return {"money": float(amount), "money_unit": unit.lower()}
        
        else:
            # Default to weight
            return {"weight": float(amount), "weight_unit": "kg"}
    
    async def _calculate_freight(
        self,
        activity_search: str,
        amount: float,
        unit: str,
        region: str,
        year: int
    ) -> Dict[str, Any]:
        """Calculate emissions using freight estimation"""
        
        # For now, use estimate endpoint with freight-related activity
        return await self._calculate_estimate(
            activity_search=activity_search,
            amount=amount,
            unit=unit,
            param_type="distance",
            region=region,
            year=year
        )
    
    async def _calculate_autopilot(
        self,
        description: str,
        amount: float,
        unit: str,
        param_type: str,
        region: str,
        year: int
    ) -> Dict[str, Any]:
        """Calculate emissions using the autopilot endpoint"""
        
        autopilot_payload = {
            "text": description,
            "region": region,
            "year": year
        }
        
        # Build parameters
        params = self._build_estimate_params(amount, unit, param_type)
        autopilot_payload["parameters"] = params
        
        print(f"DEBUG - Autopilot payload: {autopilot_payload}")
        
        try:
            result = await self.client.autopilot_estimate(autopilot_payload)
            
            # Extract CO2e
            estimate = result.get("estimate", {})
            co2e = estimate.get("co2e", 0)
            
            return {
                "estimate": {
                    "co2e": co2e,
                    "co2e_unit": "kg",
                    "emission_factor": estimate.get("emission_factor", {}),
                    "activity_data": {
                        "activity_value": float(amount),
                        "activity_unit": unit
                    }
                },
                "endpoint_type": "autopilot"
            }
        except Exception as e:
            # If region-specific call fails, try without region
            if "region" in str(e).lower() or "no_emission_factors" in str(e).lower():
                print(f"DEBUG - Autopilot failed for region {region}, retrying without region")
                autopilot_payload_global = {
                    "text": description,
                    "year": year,
                    "parameters": params
                }
                
                try:
                    result = await self.client.autopilot_estimate(autopilot_payload_global)
                    estimate = result.get("estimate", {})
                    co2e = estimate.get("co2e", 0)
                    
                    return {
                        "estimate": {
                            "co2e": co2e,
                            "co2e_unit": "kg",
                            "emission_factor": estimate.get("emission_factor", {}),
                            "activity_data": {
                                "activity_value": float(amount),
                                "activity_unit": unit
                            }
                        },
                        "endpoint_type": "autopilot"
                    }
                except Exception as e2:
                    print(f"DEBUG - Autopilot fallback also failed: {e2}")
            else:
                print(f"DEBUG - Autopilot fallback also failed: {e}")
            
            # Return error result
            return {
                "estimate": {
                    "co2e": 0,
                    "co2e_unit": "kg",
                    "emission_factor": {},
                    "activity_data": {
                        "activity_value": float(amount),
                        "activity_unit": unit
                    },
                    "error": str(e)
                },
                "endpoint_type": "error"
            }