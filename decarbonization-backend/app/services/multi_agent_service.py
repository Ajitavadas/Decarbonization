"""
Multi-Agent System - US-3.3
Improves AI accuracy from 80% to 88%+ using specialized agents
"""

import logging
from typing import Dict, Tuple
import json

import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)


class MultiAgentService:
    """
    Multi-Agent System for Improved Accuracy (US-3.3)
    
    AC:
    - Accuracy improves from 80% to 88% or better
    - Each classification shows reasoning from all three agents
    - Confidence scores reflect combined agent confidence
    - System completes analysis within seconds
    """
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def classify_with_multi_agent(
        self,
        description: str,
        category: str,
        supplier_name: Optional[str] = None,
        amount: Optional[float] = None
    ) -> Dict:
        """
        Use three specialized agents to classify transaction
        
        Returns:
            {
                "final_scope": int,
                "final_confidence": float,
                "agent_results": {
                    "scope_classifier": {...},
                    "factor_matcher": {...},
                    "validator": {...}
                }
            }
        """
        # Run all three agents in parallel
        results = await asyncio.gather(
            self._agent_scope_classifier(description, category, supplier_name),
            self._agent_factor_matcher(description, category, amount),
            self._agent_validator(description, category)
        )
        
        scope_result, factor_result, validation_result = results
        
        # Combine agent decisions
        final_scope = self._consensus_scope(
            scope_result["scope"],
            factor_result["suggested_scope"],
            validation_result["expected_scope"]
        )
        
        # Calculate combined confidence
        confidences = [
            scope_result["confidence"],
            factor_result["confidence"],
            validation_result["confidence"]
        ]
        final_confidence = sum(confidences) / len(confidences)
        
        # Boost confidence if all agents agree
        if (scope_result["scope"] == factor_result["suggested_scope"] == 
            validation_result["expected_scope"]):
            final_confidence = min(1.0, final_confidence * 1.1)
        
        return {
            "final_scope": final_scope,
            "final_confidence": round(final_confidence, 3),
            "needs_review": final_confidence < settings.AI_MIN_CONFIDENCE_THRESHOLD,
            "agent_results": {
                "scope_classifier": scope_result,
                "factor_matcher": factor_result,
                "validator": validation_result
            }
        }
    
    async def _agent_scope_classifier(
        self,
        description: str,
        category: str,
        supplier_name: Optional[str]
    ) -> Dict:
        """Agent 1: Scope Classification Specialist"""
        
        prompt = f"""
        You are Agent 1: Scope Classification Specialist.
        
        Your expertise: Determining Scope 1, 2, or 3 per GHG Protocol.
        
        **Transaction:**
        - Description: {description}
        - Category: {category}
        {f'- Supplier: {supplier_name}' if supplier_name else ''}
        
        **Scope Definitions:**
        - Scope 1: Direct emissions (fuel combustion, company vehicles, fugitive emissions)
        - Scope 2: Indirect emissions from purchased energy (electricity, steam, heating, cooling)
        - Scope 3: All other indirect (supply chain, business travel, commuting, waste)
        
        Analyze carefully and return ONLY this JSON:
        {{
            "scope": <1, 2, or 3>,
            "confidence": <0.0 to 1.0>,
            "reasoning": "<your analysis>"
        }}
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            return self._parse_agent_response(response.text, agent_name="Scope Classifier")
        except Exception as e:
            logger.error(f"Scope classifier failed: {str(e)}")
            return {"scope": 3, "confidence": 0.5, "reasoning": "Fallback"}
    
    async def _agent_factor_matcher(
        self,
        description: str,
        category: str,
        amount: Optional[float]
    ) -> Dict:
        """Agent 2: Emission Factor Matcher"""
        
        prompt = f"""
        You are Agent 2: Emission Factor Matcher.
        
        Your expertise: Selecting the most appropriate emission factor.
        
        **Transaction:**
        - Description: {description}
        - Category: {category}
        {f'- Amount: ${amount}' if amount else ''}
        
        **Task:**
        1. Identify the emission source type (fuel, electricity, travel, etc.)
        2. Suggest the appropriate Scope (1, 2, or 3)
        3. Recommend best emission factor category
        
        Return ONLY this JSON:
        {{
            "suggested_scope": <1, 2, or 3>,
            "factor_category": "<emission factor category>",
            "confidence": <0.0 to 1.0>,
            "reasoning": "<your analysis>"
        }}
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            return self._parse_agent_response(response.text, agent_name="Factor Matcher")
        except Exception as e:
            logger.error(f"Factor matcher failed: {str(e)}")
            return {"suggested_scope": 3, "factor_category": "Unknown", "confidence": 0.5, "reasoning": "Fallback"}
    
    async def _agent_validator(
        self,
        description: str,
        category: str
    ) -> Dict:
        """Agent 3: Reasonableness Validator"""
        
        prompt = f"""
        You are Agent 3: Reasonableness Validator.
        
        Your expertise: Checking if classifications make logical sense.
        
        **Transaction:**
        - Description: {description}
        - Category: {category}
        
        **Task:**
        1. Based on description, what Scope would you expect?
        2. Are there any red flags or unusual patterns?
        3. Does the category match the description?
        
        Return ONLY this JSON:
        {{
            "expected_scope": <1, 2, or 3>,
            "confidence": <0.0 to 1.0>,
            "red_flags": ["<any concerns>"],
            "reasoning": "<your analysis>"
        }}
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            result = self._parse_agent_response(response.text, agent_name="Validator")
            if "red_flags" not in result:
                result["red_flags"] = []
            return result
        except Exception as e:
            logger.error(f"Validator failed: {str(e)}")
            return {"expected_scope": 3, "confidence": 0.5, "red_flags": [], "reasoning": "Fallback"}
    
    def _parse_agent_response(self, response_text: str, agent_name: str) -> Dict:
        """Parse agent JSON response"""
        try:
            # Clean response
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
            
            data = json.loads(response_text)
            return data
            
        except Exception as e:
            logger.error(f"{agent_name} parse error: {str(e)}")
            raise
    
    def _consensus_scope(self, scope1: int, scope2: int, scope3: int) -> int:
        """Determine consensus scope from three agents"""
        # If 2+ agents agree, use that
        scopes = [scope1, scope2, scope3]
        for s in [1, 2, 3]:
            if scopes.count(s) >= 2:
                return s
        
        # No consensus - use Agent 1 (scope specialist)
        return scope1