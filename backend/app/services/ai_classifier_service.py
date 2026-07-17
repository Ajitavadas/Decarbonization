"""
AI Scope Classification Service using Groq (Llama-3.3-70b)
- Classifies transactions into Scope 1, 2, or 3
- Categorizes Scope 3 into 15 distinct categories
- Provides confidence scores and reasoning
"""

import logging
import json
from typing import Tuple, Optional, List, Dict, Any

from app.core.config import settings
from app.services.ai_base_service import AIBaseService

logger = logging.getLogger(__name__)

# Fallback factors as provided in TS
ESTIMATED_FACTORS: Dict[str, float] = {
    "Electricity": 0.5,
    "Travel": 0.2,
    "Cloud Services": 0.05,
    "Fuel": 8.89,
    "Heating": 5.3,
    "Waste": 0.5,
    "Water": 1.0,
    "Office Supplies": 2.0,
}

class AIScopeClassifierService(AIBaseService):
    """Service for AI-powered scope classification with Groq <-> Gemini fallback"""
    
    def __init__(self):
        """Initialize AI clients"""
        super().__init__()
        self.min_confidence = settings.AI_MIN_CONFIDENCE_THRESHOLD
    
    async def classify_batch(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classify multiple transactions in one batch.
        Tries providers via AIBaseService call_ai.
        """
        if not rows:
            return []

        simplified_data = self._prepare_rows(rows)
        prompt = self._build_scope_prompt(simplified_data)
        
        try:
            # Auto provider order: Vertex AI Gemini first (credits/no rate limit),
            # then Mistral as fallback.
            response_text = await self.call_ai(prompt, json_mode=True)
            parsed_results = self._parse_json_response(response_text)
            return self._map_results(rows, parsed_results, "ai")
        except Exception as e:
            logger.warning(f"All AI classification providers failed: {str(e)}")
            return self._fallback_classify(rows, str(e))

    def _prepare_rows(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "index": i,
                "desc": r.get("description") or r.get("desc"),
                "cat": r.get("category") or r.get("cat"),
                "supplier": r.get("supplier_name") or r.get("supplier")
            }
            for i, r in enumerate(rows)
        ]

    def _map_results(self, original_rows: List[Dict[str, Any]], parsed_results: List[Dict[str, Any]], provider: str) -> List[Dict[str, Any]]:
        final_results = []
        for idx, row in enumerate(original_rows):
            cls = next((p for p in parsed_results if p.get("index") == idx), None)
            inferred = self._infer_scope_and_category(row)

            scope = cls.get("scope") if cls else inferred["scope"]
            scope3_cat = cls.get("scope3Category") if cls else inferred["scope3Category"]
            reasoning = cls.get("reasoning") if cls else inferred["reasoning"]
            confidence = cls.get("confidence", 0.8) if cls else 0.4

            final_results.append({
                "id": f"ai_{provider}_{idx}_{hash(str(row))}",
                "scope": scope,
                "scope3Category": scope3_cat,
                "reasoning": reasoning,
                "confidence": confidence,
                "needs_review": confidence < self.min_confidence or cls is None
            })
        return final_results

    def _parse_json_response(self, content: str) -> List[Dict[str, Any]]:
        """Generic JSON parser for both providers"""
        try:
            # Strip markdown blocks if present
            clean_content = content.strip()
            if clean_content.startswith("```json"):
                clean_content = clean_content[7:-3].strip()
            elif clean_content.startswith("```"):
                clean_content = clean_content[3:-3].strip()
                
            data = json.loads(clean_content)
            if isinstance(data, list):
                return data
            if "classifications" in data:
                return data["classifications"]
            if "data" in data:
                return data["data"]
            # Fallback to finding first list
            for val in data.values():
                if isinstance(val, list):
                    return val
            return []
        except Exception as e:
            logger.error(f"JSON Parse Error: {str(e)} | Content: {content[:100]}...")
            return []

    async def classify_transaction(
        self, 
        description: str, 
        category: str,
        supplier_name: Optional[str] = None
    ) -> Tuple[int, float, bool]:
        """Backward compatible single-row classifier"""
        results = await self.classify_batch([{
            "description": description,
            "category": category,
            "supplier_name": supplier_name
        }])
        
        if results:
            res = results[0]
            scope_str = str(res.get("scope", "Scope 3"))
            scope = int(scope_str.split(" ")[1]) if " " in scope_str else 3
            return scope, res.get("confidence", 0.0), res.get("needs_review", True)
        
        return 3, 0.0, True

    def _build_scope_prompt(self, rows: List[Dict[str, Any]]) -> str:
        """Build the comprehensive prompt with Scope 3 Reference and Decision Tree"""
        
        prompt = f"""
You are an expert greenhouse gas (GHG) accountant following the Greenhouse Gas Protocol.

Task: Classify emissions into Scope 1, Scope 2, or Scope 3 (with specific category).

Definitions:
- Scope 1: Direct emissions (owned assets, fuel combustion).
- Scope 2: Indirect emissions (purchased electricity/heat).
- Scope 3: All other value chain emissions.

**Scope 3 Categories Reference Table:**

| Category | Name | Description |
|----------|------|-------------|
| 1 | Purchased Goods & Services | Extraction, production, transport of purchased materials |
| 2 | Capital Goods | Extraction, production of machinery/equipment |
| 3 | Fuel & Energy Related | Extraction, production of purchased fuels not in Scope 1/2 |
| 4 | Upstream Transportation | Transport of purchased products before company |
| 5 | Waste Generated in Operations | Disposal of operational waste |
| 6 | Business Travel | Employee travel (air, train, car) |
| 7 | Employee Commuting | Commute to office |
| 8 | Upstream Leased Assets | Emissions from leased equipment/vehicles |
| 9 | Downstream Transportation | Transport of sold products to customers |
| 10 | Processing of Sold Products | Further processing by downstream companies |
| 11 | Use of Sold Products | End-use emissions from sold products |
| 12 | End-of-Life Treatment | Disposal/recycling of sold products |
| 13 | Downstream Leased Assets | Emissions from assets leased out |
| 14 | Franchises | Emissions from franchised operations |
| 15 | Investments | Emissions from invested companies |

**Decision Trees for Scope 3 Categorization:**
- IF transaction is a Purchase of Raw Materials/Components -> Category 1
- IF transaction is a Purchase of Machinery/Equipment -> Category 2
- IF transaction is a Purchase of Fuel/Energy (not Scope 1/2) -> Category 3
- IF transaction is Third-party logistics -> Category 4
- IF transaction is Waste/Recycling -> Category 5
- IF transaction is Travel (Business) -> Category 6
- IF transaction is Travel (Commute) -> Category 7
- IF transaction is Leasing (Inbound) -> Category 8
- IF transaction is Leasing (Outbound) -> Category 13
- IF transaction is Sales/Distribution (Downstream) -> Category 9, 10, 11, or 12

Input Data:
{json.dumps(rows, indent=2)}

Output Requirement:
Return a STRICT JSON object with a key "classifications" containing an array.
Each object in the array must have:
- index: integer (matching the input index)
- scope: "Scope 1" | "Scope 2" | "Scope 3"
- scope3Category: string or null
- reasoning: string
- confidence: number (0.0 to 1.0)

Example:
{{
  "classifications": [
    {{
      "index": 0,
      "scope": "Scope 3",
      "scope3Category": "Business Travel",
      "reasoning": "Flight for business conference",
      "confidence": 0.98
    }}
  ]
}}
"""
        return prompt.strip()

    def _infer_scope_and_category(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Heuristic fallback logic from TS code"""
        desc = f"{row.get('description', '')} {row.get('category', '')}".lower()

        if "electricity" in desc or "power" in desc:
            return {"scope": "Scope 2", "scope3Category": None, "reasoning": "Purchased electricity (Heuristic)"}

        if any(x in desc for x in ["fuel", "gas", "diesel", "petrol"]):
            return {"scope": "Scope 1", "scope3Category": None, "reasoning": "Stationary/Mobile Combustion (Heuristic)"}

        # Business Travel - flights, trains, rental cars, taxis
        if any(x in desc for x in ["flight", "travel", "train", "rail", "air", "airline", "taxi", "uber", "rental car", "business trip"]):
            return {"scope": "Scope 3", "scope3Category": "6 - Business Travel", "reasoning": "Business Travel (Heuristic)"}
        
        # Employee Commuting
        if any(x in desc for x in ["commut", "metro", "subway", "bus pass", "employee transport"]):
            return {"scope": "Scope 3", "scope3Category": "7 - Employee Commuting", "reasoning": "Employee Commuting (Heuristic)"}

        # Default
        return {"scope": "Scope 3", "scope3Category": "1 - Purchased Goods & Services", "reasoning": "Purchased Goods (Heuristic)"}

    def _fallback_classify(self, data: List[Dict[str, Any]], error_reason: str) -> List[Dict[str, Any]]:
        """Ported from TS for Python"""
        results = []
        for idx, row in enumerate(data):
            inferred = self._infer_scope_and_category(row)
            results.append({
                "id": f"fallback_{idx}",
                "scope": inferred["scope"],
                "scope3Category": inferred["scope3Category"],
                "reasoning": f"{inferred['reasoning']}. Error: {error_reason}",
                "confidence": 0.0,
                "needs_review": True
            })
        return results

    def _parse_groq_response(self, content: str) -> List[Dict[str, Any]]:
        """Gracefully parse Groq's JSON response"""
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return data
            if "classifications" in data:
                return data["classifications"]
            if "data" in data:
                return data["data"]
            # Fallback to finding first list
            for val in data.values():
                if isinstance(val, list):
                    return val
            return []
        except Exception:
            logger.error(f"Failed to parse Groq JSON: {content}")
            return []
    
    async def classify_for_climatiq(
        self,
        description: str,
        unit: str,
        category: str = "",
        region: str = None  # REQUIRED - will be validated
    ) -> Dict[str, Any]:
        """
        Classify an activity for Climatiq API routing.
        
        Args:
            description: Activity description
            unit: Unit of measurement
            category: Optional category
            region: ISO 3166-1 Alpha-2 or extended code (REQUIRED)
            
        Raises:
            ValueError: If region is not provided
        
        Returns comprehensive classification including:
        - scope: 1, 2, or 3
        - endpoint: \"fuel\", \"electricity\", \"heat_steam\", \"estimate\", \"freight\", \"autopilot\"
        - parameter_type: \"energy\", \"volume\", \"weight\", \"distance\", \"money\", \"passengers_distance\"
        - fuel_type: (for fuel endpoint) \"diesel\", \"lpg\", \"natural_gas\", etc.
        - activity_search: Keywords to search for activity_id
        - normalized_description: Cleaned description for Autopilot
        """
        # Region is mandatory - no fallbacks
        if not region or not region.strip():
            raise ValueError(
                "Region is required for emission calculations. "
                "Provide an ISO 3166-1 Alpha-2 code (e.g., US, IN, GB) or extended code (US-CA)."
            )
        region = region.strip().upper()
        
        prompt = f"""You are an expert in carbon emissions calculation and the Climatiq API.

Analyze this activity and determine the best Climatiq API endpoint and parameters:

Description: {description}
Unit: {unit}
Category: {category}
Region: {region}

Based on the activity, determine:

1. **scope**: 1 (direct emissions), 2 (purchased energy), or 3 (value chain)

2. **endpoint**: Which Climatiq API endpoint to use:
   - "fuel": For fuel combustion (diesel, gasoline, LPG, natural gas burned on-site)
   - "electricity": For purchased electricity (kWh, MWh)
   - "heat_steam": For purchased steam/heat (GJ, MMBtu)
   - "estimate": For other activities using emission factors (materials, travel, waste, refrigerants)
   - "freight": For freight/logistics - use this if category contains "freight", "upstream transport", "downstream transport", "logistics", or description mentions goods/materials transport
   - "autopilot": When unsure, let AI decide

3. **parameter_type**: The unit category:
   - "energy": kWh, MWh, GJ, therms
   - "volume": L, gallons, m3
   - "weight": kg, tonne, lb
   - "distance": km, miles (for passenger travel only)
   - "weight_distance": tkm, tonne-km (for freight - this is weight × distance)
   - "money": USD, EUR, etc.
   - "passengers_distance": For passenger travel (flights, trains)

   IMPORTANT: For freight transport, the correct parameter_type is "weight_distance" (tkm).
   If the unit is km but the activity is freight (goods transport), set parameter_type to "weight_distance".

4. **fuel_type** (only if endpoint="fuel"):
   - "diesel" for diesel fuel
   - "lpg" for LPG/propane
   - "natural_gas" for natural gas
   - "motor_gasoline" for petrol/gasoline

5. **activity_search**: 2-4 keywords to search for the right emission factor in Climatiq.
   Examples:
   - "diesel generator" -> "fuel diesel stationary"
   - "LPG heating" -> "lpg heating stationary"
   - "business flights" -> "passenger flight domestic"
   - "steel purchased" -> "steel production manufacturing"
   - "employee commuting cars" -> "passenger car commute"
   - "waste landfill" -> "waste landfill municipal"
   - "refrigerant R410A" -> "refrigerant fugitive r410a"
   - "transport raw materials" -> "freight truck road transport"
   - "transport finished goods" -> "freight vehicle road downstream"
   - "upstream freight" -> "freight truck supply chain"
   - "downstream freight" -> "freight vehicle delivery"

6. **normalized_description**: Clean, simple description for Climatiq Autopilot API.
   Remove unnecessary words, keep the essential activity type.

7. **freight_weight_tonnes** (OPTIONAL, only if endpoint="freight" AND unit is distance like km):
   If this is a freight activity but the unit is distance (km, miles), provide an estimated 
   average cargo weight in tonnes per trip. Use 10 tonnes as default for heavy goods,
   5 tonnes for medium goods, 1 tonne for light goods. This helps convert distance to tkm.

Return ONLY a JSON object (no markdown):
{{
    "scope": 3,
    "endpoint": "freight",
    "parameter_type": "weight_distance",
    "fuel_type": null,
    "activity_search": "freight truck road transport",
    "normalized_description": "Road freight transport",
    "freight_weight_tonnes": 10
}}
"""
        
        try:
            # Auto provider order: Vertex AI Gemini first, Mistral fallback.
            response_text = await self.call_ai(prompt, json_mode=True)

            # Parse JSON response
            clean_content = response_text.strip()
            if clean_content.startswith("```json"):
                clean_content = clean_content[7:-3].strip()
            elif clean_content.startswith("```"):
                clean_content = clean_content[3:-3].strip()
            
            result = json.loads(clean_content)
            
            # Validate required fields
            if "scope" not in result:
                result["scope"] = 3
            if "endpoint" not in result:
                result["endpoint"] = "autopilot"
            if "parameter_type" not in result:
                result["parameter_type"] = self._infer_parameter_type(unit)
            if "activity_search" not in result:
                result["activity_search"] = description
            if "normalized_description" not in result:
                result["normalized_description"] = description
            
            logger.info(f"AI Classification for '{description[:50]}...': {result}")
            return result
            
        except Exception as e:
            logger.warning(f"AI classification failed: {e}, using fallback")
            return self._fallback_climatiq_classification(description, unit, category)
    
    def _infer_parameter_type(self, unit: str) -> str:
        """Infer parameter type from unit"""
        unit_lower = unit.lower()
        
        if unit_lower in ['kwh', 'mwh', 'gwh', 'wh', 'gj', 'mj', 'therm', 'therms', 'mmbtu', 'btu']:
            return "energy"
        elif unit_lower in ['l', 'liter', 'liters', 'litre', 'litres', 'gal', 'gallon', 'gallons', 'm3', 'm³']:
            return "volume"
        elif unit_lower in ['kg', 'kilogram', 'kilograms', 't', 'tonne', 'tonnes', 'ton', 'tons', 'lb', 'lbs', 'g', 'gram']:
            return "weight"
        elif unit_lower in ['km', 'kilometer', 'kilometers', 'mi', 'mile', 'miles', 'm', 'meter', 'meters']:
            return "distance"
        elif unit_lower in ['usd', 'eur', 'gbp', 'inr', 'cad', 'aud', 'jpy', 'chf', 'cny', 'aed']:
            return "money"
        else:
            return "weight"  # Default fallback
    
    def _fallback_climatiq_classification(self, description: str, unit: str, category: str) -> Dict[str, Any]:
        """Fallback classification when AI fails"""
        desc_lower = description.lower()
        cat_lower = category.lower()
        unit_lower = unit.lower()
        
        # Determine parameter type
        param_type = self._infer_parameter_type(unit)
        
        # Fuel-related activities (Scope 1)
        if any(x in desc_lower for x in ['diesel', 'gasoline', 'petrol', 'lpg', 'propane']):
            fuel_type = "diesel"
            if 'lpg' in desc_lower or 'propane' in desc_lower:
                fuel_type = "lpg"
            elif 'gasoline' in desc_lower or 'petrol' in desc_lower:
                fuel_type = "motor_gasoline"
            
            return {
                "scope": 1,
                "endpoint": "fuel",
                "parameter_type": param_type,
                "fuel_type": fuel_type,
                "activity_search": f"fuel {fuel_type} combustion stationary",
                "normalized_description": f"{fuel_type} fuel combustion"
            }
        
        # Natural gas/heating (Scope 1)
        if any(x in desc_lower for x in ['natural gas', 'heating', 'furnace', 'boiler']) and 'electricity' not in desc_lower:
            return {
                "scope": 1,
                "endpoint": "fuel",
                "parameter_type": "energy" if param_type == "energy" else "volume",
                "fuel_type": "natural_gas",
                "activity_search": "natural gas heating combustion",
                "normalized_description": "Natural gas combustion for heating"
            }
        
        # Electricity (Scope 2)
        if 'electricity' in desc_lower or ('grid' in desc_lower and 'power' in desc_lower):
            return {
                "scope": 2,
                "endpoint": "electricity",
                "parameter_type": "energy",
                "activity_search": "electricity grid supply",
                "normalized_description": "Electricity consumption from grid"
            }
        
        # Steam/Heat (Scope 2)
        if 'steam' in desc_lower or ('heat' in desc_lower and 'purchased' in desc_lower):
            return {
                "scope": 2,
                "endpoint": "heat_steam",
                "parameter_type": "energy",
                "activity_search": "steam heat purchased",
                "normalized_description": "Purchased steam or heat"
            }
        
        # Flights (Scope 3)
        if any(x in desc_lower for x in ['flight', 'fly', 'air travel', 'airline', 'plane']):
            return {
                "scope": 3,
                "endpoint": "estimate",
                "parameter_type": "passengers_distance",
                "activity_search": "passenger flight domestic",
                "normalized_description": "Business air travel"
            }
        
        # Employee commuting (Scope 3)
        if any(x in desc_lower for x in ['commut', 'employee travel', 'staff travel']):
            return {
                "scope": 3,
                "endpoint": "estimate",
                "parameter_type": "distance",
                "activity_search": "passenger car commute employee",
                "normalized_description": "Employee commuting by car"
            }
        
        # Business travel by car (Scope 3)
        if any(x in desc_lower for x in ['car rental', 'rental car', 'business mileage', 'business travel']) and 'flight' not in desc_lower:
            return {
                "scope": 3,
                "endpoint": "estimate",
                "parameter_type": "distance",
                "activity_search": "passenger car business travel",
                "normalized_description": "Business travel by car"
            }
        
        # Freight/Transport (Scope 3)
        if any(x in desc_lower for x in ['freight', 'transport', 'logistics', 'shipping', 'delivery']):
            return {
                "scope": 3,
                "endpoint": "estimate",
                "parameter_type": "distance",
                "activity_search": "freight road transport truck",
                "normalized_description": "Freight transport by road"
            }
        
        # Materials - steel, metals (Scope 3)
        if any(x in desc_lower for x in ['steel', 'iron', 'metal', 'aluminum', 'aluminium']):
            return {
                "scope": 3,
                "endpoint": "estimate",
                "parameter_type": "weight",
                "activity_search": "steel production manufacturing metal",
                "normalized_description": "Steel production"
            }
        
        # Materials - plastics (Scope 3)
        if any(x in desc_lower for x in ['plastic', 'polymer', 'pvc', 'polyethylene']):
            return {
                "scope": 3,
                "endpoint": "estimate",
                "parameter_type": "weight",
                "activity_search": "plastic production manufacturing",
                "normalized_description": "Plastic production"
            }
        
        # Waste (Scope 3)
        if any(x in desc_lower for x in ['waste', 'landfill', 'disposal', 'recycling']):
            return {
                "scope": 3,
                "endpoint": "estimate",
                "parameter_type": "weight",
                "activity_search": "waste landfill disposal municipal",
                "normalized_description": "Waste disposal to landfill"
            }
        
        # Refrigerants (Scope 1)
        if any(x in desc_lower for x in ['refrigerant', 'r-410a', 'r410a', 'hfc', 'ac system', 'air condition']):
            return {
                "scope": 1,
                "endpoint": "estimate",
                "parameter_type": "weight",
                "activity_search": "refrigerant fugitive emissions hfc",
                "normalized_description": "Refrigerant leakage"
            }
        
        # Trucks/Fleet vehicles (Scope 1)
        if any(x in desc_lower for x in ['truck', 'fleet', 'company vehicle', 'owned vehicle']):
            return {
                "scope": 1,
                "endpoint": "fuel",
                "parameter_type": param_type,
                "fuel_type": "diesel",
                "activity_search": "fuel diesel mobile combustion truck",
                "normalized_description": "Diesel combustion in company vehicles"
            }
        
        # Default: Use autopilot
        return {
            "scope": 3,
            "endpoint": "autopilot",
            "parameter_type": param_type,
            "activity_search": description[:50],
            "normalized_description": description
        }

# Singleton instance
ai_classifier = AIScopeClassifierService()