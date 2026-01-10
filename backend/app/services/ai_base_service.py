"""
AI Base Service
Base class for AI provider integrations (Mistral AI)
"""

import logging
import json
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIBaseService:
    """Base service for AI provider integrations"""
    
    def __init__(self):
        """Initialize AI clients"""
        self.mistral_api_key = settings.MISTRAL_API_KEY
        self.mistral_base_url = "https://api.mistral.ai/v1"
        self.timeout = httpx.Timeout(15.0, connect=5.0)  # Reduced timeout for faster fallback
    
    async def call_ai(
        self,
        prompt: str,
        json_mode: bool = False,
        preferred_provider: Optional[str] = None
    ) -> str:
        """
        Call AI provider (Mistral AI)
        
        Args:
            prompt: The prompt to send
            json_mode: Whether to request JSON format
            preferred_provider: Provider to use (currently only "mistral")
            
        Returns:
            Response text from AI
        """
        try:
            if preferred_provider == "mistral" or not preferred_provider:
                return await self._call_mistral(prompt, json_mode=json_mode)
            else:
                raise ValueError(f"Unknown provider: {preferred_provider}")
        except Exception as e:
            logger.error(f"AI call failed: {str(e)}")
            raise
    
    async def _call_mistral(
        self,
        prompt: str,
        json_mode: bool = False
    ) -> str:
        """
        Call Mistral AI API
        
        Args:
            prompt: The prompt to send
            json_mode: Whether to request JSON format
            
        Returns:
            Response text from Mistral
        """
        headers = {
            "Authorization": f"Bearer {self.mistral_api_key}",
            "Content-Type": "application/json"
        }
        
        # Use Mistral Large 2 for better JSON output
        payload = {
            "model": "mistral-large-latest",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Lower temperature for more deterministic output
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.mistral_base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                choices = result.get("choices", [])
                if not choices:
                    raise ValueError("No choices in Mistral response")
                
                content = choices[0].get("message", {}).get("content", "")
                if not content:
                    raise ValueError("Empty content in Mistral response")
                
                return content
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Mistral API error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Mistral API error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Mistral API call failed: {str(e)}")
                raise

