"""
AI Scope Classification Service using Groq (Llama-3.3-70b)
- Classifies transactions into Scope 1, 2, or 3
- Categorizes Scope 3 into 15 distinct categories
- Provides confidence scores and reasoning
"""

import logging
import json
from typing import Tuple, Optional, List, Dict, Any
import google.generativeai as genai
from groq import Groq
from app.config import settings

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
            # Groq is typically faster/better for structured classification in some cases, 
            # but user wants failsafe across all.
            response_text = await self.call_ai(prompt, json_mode=True, preferred_provider="gemini")
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

        if "flight" in desc or "travel" in desc:
            return {"scope": "Scope 3", "scope3Category": "6 - Business Travel", "reasoning": "Business Travel (Heuristic)"}

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

# Singleton instance
ai_classifier = AIScopeClassifierService()