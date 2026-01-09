"""
Groq AI Service for Carbon Auditor Agent
Integration with Groq API for fast AI-powered contextual anomaly analysis
"""

import logging
import json
from typing import Optional, Dict, Any, List
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class GroqService:
    """
    Groq AI integration for the Carbon Accounting Auditor Agent
    Uses Groq's fast LLM inference for emission data analysis
    """
    
    def __init__(self):
        """Initialize Groq client"""
        self.api_key = settings.GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = "llama-3.3-70b-versatile"  # Fast, capable model
        self.timeout = httpx.Timeout(60.0, connect=10.0)
        self.max_retries = 3
    
    async def analyze_anomalies(
        self,
        activity_data: List[Dict[str, Any]],
        archetype: str,
        organization_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use Groq to analyze activity data for contextual anomalies
        
        Args:
            activity_data: List of emission activities to analyze
            archetype: Organization's emission archetype
            organization_context: Additional org context (industry, country, etc.)
            
        Returns:
            Dict with findings and recommendations
        """
        if not self.api_key:
            logger.warning("Groq API key not configured, skipping AI analysis")
            return {"findings": [], "skipped": True, "reason": "API key not configured"}
        
        prompt = self._build_anomaly_prompt(activity_data, archetype, organization_context)
        
        try:
            response = await self._call_groq(prompt, json_mode=True)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Groq analysis failed: {e}")
            return {"findings": [], "error": str(e)}
    
    async def generate_recommendation(
        self,
        finding_type: str,
        finding_details: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        Generate actionable recommendations for a specific finding
        
        Args:
            finding_type: Type of finding (gap, anomaly, archetype_mismatch)
            finding_details: Details of the finding
            context: Additional context
            
        Returns:
            Recommendation string
        """
        if not self.api_key:
            return "Review this finding and take appropriate action."
        
        prompt = self._build_recommendation_prompt(finding_type, finding_details, context)
        
        try:
            response = await self._call_groq(prompt, json_mode=False)
            return response.strip()
        except Exception as e:
            logger.error(f"Groq recommendation generation failed: {e}")
            return "Review this finding and take appropriate action."
    
    async def generate_strategies(
        self,
        prompt: str,
        use_quality_model: bool = True
    ) -> Dict[str, Any]:
        """
        Generate reduction strategies using Groq
        
        Args:
            prompt: The strategy generation prompt
            use_quality_model: If True, use 70b model; else use 8b instant
            
        Returns:
            Dict with strategies list
        """
        if not self.api_key:
            logger.warning("Groq API key not configured, skipping strategy generation")
            return {"strategies": [], "skipped": True, "reason": "API key not configured"}
        
        # Select model based on quality requirement
        model = "llama-3.3-70b-versatile" if use_quality_model else "llama-3.1-8b-instant"
        
        try:
            response = await self._call_groq(prompt, json_mode=True, model=model)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"Groq strategy generation failed: {e}")
            return {"strategies": [], "error": str(e)}
    
    def _build_anomaly_prompt(
        self,
        activity_data: List[Dict[str, Any]],
        archetype: str,
        organization_context: Dict[str, Any]
    ) -> str:
        """Build prompt for anomaly analysis"""
        
        # Limit activities to avoid token limits
        sample_activities = activity_data[:20]  # Analyze first 20
        
        activities_text = "\n".join([
            f"- {a.get('activity_type', 'unknown')}: {a.get('co2e_kg', 0):.2f} kg CO2e "
            f"({a.get('description', 'No description')[:50]})"
            for a in sample_activities
        ])
        
        return f"""You are a Carbon Accounting Auditor AI. Analyze the following emission activity data for anomalies, data issues, and recommendations.

Organization Context:
- Industry: {organization_context.get('industry', 'Unknown')}
- Country: {organization_context.get('country', 'Unknown')}
- Archetype: {archetype or 'Not specified'}

Sample Activities (showing {len(sample_activities)} of {len(activity_data)} total):
{activities_text}

Analyze this data and identify:
1. Any unusual patterns or anomalies
2. Data quality issues
3. Potential misclassifications
4. Recommendations for improvement

Return your analysis as a JSON object with this structure:
{{
    "findings": [
        {{
            "type": "anomaly|gap|recommendation",
            "severity": "critical|warning|info",
            "title": "Brief title",
            "description": "Detailed description",
            "recommendation": "What to do about it"
        }}
    ],
    "overall_assessment": "Brief overall assessment of data quality"
}}

Return ONLY valid JSON, no markdown code blocks or additional text."""
    
    def _build_recommendation_prompt(
        self,
        finding_type: str,
        finding_details: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for recommendation generation"""
        return f"""As a Carbon Accounting expert, provide a specific, actionable recommendation for this finding:

Finding Type: {finding_type}
Details: {json.dumps(finding_details, indent=2)}
Context: {json.dumps(context, indent=2)}

Provide a concise (1-2 sentences), actionable recommendation. Be specific to the context."""
    
    async def _call_groq(self, prompt: str, json_mode: bool = False, model: Optional[str] = None) -> str:
        """
        Make API call to Groq
        
        Args:
            prompt: The prompt to send
            json_mode: Whether to request JSON output
            model: Optional model override (defaults to self.model)
            
        Returns:
            Response text from Groq
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [{"role": "user", "content": prompt}]
        
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": 0.3,  # Lower for more consistent analysis
            "max_tokens": 2000
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    
                    if response.status_code == 429:
                        # Rate limited
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Groq rate limit hit, waiting {wait_time}s")
                        import asyncio
                        await asyncio.sleep(wait_time)
                        continue
                    
                    response.raise_for_status()
                    
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                    
                except httpx.HTTPStatusError as e:
                    logger.error(f"Groq API error: {e.response.status_code} - {e.response.text}")
                    if attempt == self.max_retries - 1:
                        raise Exception(f"Groq API error: {e.response.status_code}")
                except Exception as e:
                    logger.error(f"Groq call failed: {e}")
                    if attempt == self.max_retries - 1:
                        raise
        
        raise Exception("Groq API call failed after all retries")
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse Groq response into structured finding
        
        Args:
            response: Raw response from Groq
            
        Returns:
            Parsed findings dictionary
        """
        try:
            # Try to parse as JSON directly
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError:
            # Try to extract JSON from response
            try:
                # Look for JSON block
                import re
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    parsed = json.loads(json_match.group())
                    return parsed
            except:
                pass
            
            # Return as single finding if not parseable
            return {
                "findings": [{
                    "type": "recommendation",
                    "severity": "info",
                    "title": "AI Analysis",
                    "description": response[:500],
                    "recommendation": "Review the AI analysis above."
                }],
                "overall_assessment": "Analysis provided in text format."
            }


# Factory function for compatibility with existing code
def create_groq_service() -> GroqService:
    """Create a Groq service instance"""
    return GroqService()
