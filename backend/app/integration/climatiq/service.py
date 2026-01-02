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
        
        # Strategy 1: Try Autopilot first (most flexible)
        try:
            autopilot_payload = {
                "text": text
            }

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
            
            if co2e > 0:
                print("DEBUG - Autopilot worked!")
                autopilot_result["endpoint_type"] = "autopilot"
                return autopilot_result
            else:
                print("DEBUG - Autopilot returned 0 CO2e, trying specific endpoint")
                
        except Exception as e:
            print(f"DEBUG - Autopilot failed: {e}, trying specific endpoint")
        
        # Strategy 2: Try specific endpoint based on unit type and description
        text_lower = text.lower()
        try:
            # ELECTRICITY: kWh, MWh for electricity usage
            if unit_type == "energy" and unit.lower() in ['kwh', 'mwh', 'gwh', 'wh']:
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
            
            # TRAVEL DISTANCE: miles, km for car travel, commute
            elif unit_type == "distance" or unit.lower() in ['miles', 'mile', 'km', 'kilometers']:
                travel_mode = "car"  # Default
                if any(air in text_lower for air in ['flight', 'fly', 'air']):
                    travel_mode = "air"
                elif any(rail in text_lower for rail in ['train', 'rail']):
                    travel_mode = "rail"
                
                travel_payload = {
                    "origin": {"query": region or "US"},
                    "destination": {"query": region or "US"},
                    "travel_mode": travel_mode
                }
                
                if travel_mode == "car":
                    travel_payload["car_details"] = {"car_type": "average"}
                
                print(f"DEBUG - Trying Travel Distance endpoint: {travel_payload}")
                result = await self.client.travel_distance(travel_payload)

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
                    "endpoint_type": "travel"
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
                "data_version": "20.20",
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
                        "data_version": "20.20"
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