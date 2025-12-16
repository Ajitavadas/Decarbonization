"""
AI Scope Classification Service using Google Gemini
- Classifies transactions into Scope 1, 2, or 3
- Returns confidence scores and review flags
"""

import logging
from typing import Tuple, Optional
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)

class AIScopeClassifierService:
    """Service for AI-powered scope classification using Gemini"""
    
    def __init__(self):
        """Initialize Gemini API"""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.min_confidence = settings.AI_MIN_CONFIDENCE_THRESHOLD
    
    async def classify_transaction(
        self, 
        description: str, 
        category: str,
        supplier_name: Optional[str] = None
    ) -> Tuple[int, float, bool]:
        """
        Classify emission transaction into Scope 1, 2, or 3
        
        Args:
            description: Transaction description
            category: Category (e.g., "Fuel", "Electricity", "Business Travel")
            supplier_name: Optional supplier name
            
        Returns:
            Tuple of (scope: int, confidence: float, needs_review: bool)
            
        Raises:
            Exception: If Gemini API call fails
        """
        try:
            # Build prompt for Gemini
            prompt = self._build_classification_prompt(
                description, category, supplier_name
            )
            
            # Call Gemini API
            response = await self.model.generate_content_async(prompt)
            
            # Parse response
            scope, confidence = self._parse_gemini_response(response.text)
            
            # Determine if manual review is needed
            needs_review = confidence < self.min_confidence
            
            logger.info(
                f"AI Classification: {description[:50]}... -> "
                f"Scope {scope} ({confidence:.1%} confidence, "
                f"review_needed={needs_review})"
            )
            
            return scope, confidence, needs_review
            
        except Exception as e:
            logger.error(f"AI classification failed: {str(e)}")
            # Fallback to manual review
            return 3, 0.0, True
    
    def _build_classification_prompt(
        self, 
        description: str, 
        category: str,
        supplier_name: Optional[str]
    ) -> str:
        """Build optimized prompt for Gemini"""
        
        context = f"""
        You are a carbon accounting expert classifying emissions into Scope 1, 2, or 3 per GHG Protocol.

        **Scope Definitions:**
        - Scope 1: Direct emissions from owned/controlled sources (fuel combustion, company vehicles, fugitive emissions)
        - Scope 2: Indirect emissions from purchased electricity, steam, heating, or cooling
        - Scope 3: All other indirect emissions (business travel, purchased goods, employee commuting, waste)

        **Transaction Details:**
        - Description: {description}
        - Category: {category}
        {f'- Supplier: {supplier_name}' if supplier_name else ''}

        **Instructions:**
        1. Analyze the transaction and classify as Scope 1, 2, or 3
        2. Provide confidence score (0.0-1.0)
        3. Return ONLY this JSON format: {{"scope": 1, "confidence": 0.95}}

        **Examples:**
        - "Diesel for company trucks" -> Scope 1, high confidence
        - "Electricity bill for office" -> Scope 2, high confidence
        - "Flight to client meeting" -> Scope 3, high confidence
        - "Paper purchase for office" -> Scope 3, medium confidence
        """
        
        return context.strip()
    
    def _parse_gemini_response(self, response_text: str) -> Tuple[int, float]:
        """Parse Gemini's JSON response"""
        try:
            # Clean response text
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
            
            # Parse JSON
            import json
            data = json.loads(response_text)
            
            scope = int(data["scope"])
            confidence = float(data["confidence"])
            
            # Validate scope
            if scope not in [1, 2, 3]:
                raise ValueError(f"Invalid scope: {scope}")
            
            # Clamp confidence to valid range
            confidence = max(0.0, min(1.0, confidence))
            
            return scope, confidence
            
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {response_text[:100]}...")
            raise

# Singleton instance
ai_classifier = AIScopeClassifierService()