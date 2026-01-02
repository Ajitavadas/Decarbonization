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
                return autopilot_result
            else:
                print("DEBUG - Autopilot returned 0 CO2e, trying specific endpoint")
                
        except Exception as e:
            print(f"DEBUG - Autopilot failed: {e}, trying specific endpoint")
        
        # Strategy 2: Try specific endpoint based on unit type and description
        try:
            if unit_type == "energy" and unit.lower() in ['kwh', 'mwh', 'gwh', 'wh']:
                # Use Energy endpoint for electricity - CORRECT PAYLOAD FORMAT
                energy_payload = {
                    "year": year or datetime.now().year,
                    "region": region or "US",
                    "amount": {
                        "energy": float(amount),
                        "energy_unit": unit
                    }
                }
                
                print(f"DEBUG - Trying Energy endpoint: {energy_payload}")
                result = await self.client.electricity(energy_payload)

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
                    },
                    "endpoint_type": "energy"
                }
                
            elif unit_type == "energy" and unit.lower() in ['therms', 'mmbtu', 'btu']:
                # Use Fuel endpoint for natural gas - CORRECT PAYLOAD FORMAT
                # Convert therms to liters (1 therm ≈ 29.3 kWh ≈ 105.5 MJ ≈ 2.83 L gasoline equivalent)
                if unit.lower() in ['therms', 'therm']:
                    volume_amount = float(amount) * 2.83  # Convert therms to liters
                    volume_unit = "l"
                elif unit.lower() in ['mmbtu']:
                    volume_amount = float(amount) * 28.3  # Convert MMBtu to liters  
                    volume_unit = "l"
                else:
                    volume_amount = float(amount)
                    volume_unit = unit
                
                fuel_payload = {
                    "fuel_type": "natural_gas",
                    "amount": {
                        "volume": volume_amount,
                        "volume_unit": volume_unit
                    },
                    "region": region or "US",
                    "year": year or datetime.now().year
                }
                
                print(f"DEBUG - Trying Fuel endpoint: {fuel_payload}")
                result = await self.client.fuel(fuel_payload)

                return {
                    "estimate": {
                        "co2e": result.get("combustion", {}).get("co2e", 0),
                        "co2e_unit": "kg",
                        "emission_factor": result.get("combustion", {}).get("emission_factor", {}),
                        "activity_data": {
                            "activity_value": float(amount),
                            "activity_unit": unit
                        }
                    },
                    "endpoint_type": "fuel"
                }
                
            elif unit_type == "money" and ("procurement" in text.lower() or "supplies" in text.lower() or "spending" in text.lower()):
                # Use Procurement endpoint for spend-based calculations - CORRECT PAYLOAD FORMAT
                procurement_payload = {
                    "activity": {
                        "classification_code": "25",  # Default to manufacturing
                        "classification_type": "isic4"
                    },
                    "spend_year": year or datetime.now().year,
                    "spend_region": region or "US",
                    "money": float(amount),
                    "money_unit": unit
                }

                print(f"DEBUG - Trying Procurement endpoint: {procurement_payload}")
                result = await self.client.procurement(procurement_payload)

                # Procurement returns estimate object directly
                return {
                    "estimate": result.get("estimate", {
                        "co2e": 0,
                        "co2e_unit": "kg"
                    }),
                    "endpoint_type": "procurement"
                }
                
            elif unit_type == "distance" and ("travel" in text.lower() or "flight" in text.lower() or "car" in text.lower()):
                # Use Travel endpoint for distance-based travel
                travel_payload = {
                    "origin": {"query": region or "US"},
                    "destination": {"query": region or "US"},  # Simple fallback
                    "travel_mode": "car" if "car" in text.lower() else "air"
                }
                
                # Add car details if it's a car trip
                if "car" in text.lower():
                    travel_payload["car_details"] = {
                        "car_type": "average"
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
                    result = await self.client.travel_spend(travel_payload)
                else:
                    print(f"DEBUG - Trying Travel distance endpoint: {travel_payload}")
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