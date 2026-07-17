"""
AI Base Service
Base class for AI provider integrations (Vertex AI Gemini, Mistral AI)
"""

import logging
import json
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIBaseService:
    """Base service for AI provider integrations"""

    # Shared Vertex AI client across instances (auth handshake is expensive)
    _vertex_client = None
    _vertex_init_failed = False

    def __init__(self):
        """Initialize AI clients"""
        self.mistral_api_key = settings.MISTRAL_API_KEY
        self.mistral_base_url = "https://api.mistral.ai/v1"
        self.timeout = httpx.Timeout(15.0, connect=5.0)  # Reduced timeout for faster fallback

    @classmethod
    def _get_vertex_client(cls):
        """Lazily build a shared Vertex AI client authenticated via ADC."""
        if cls._vertex_client is not None or cls._vertex_init_failed:
            return cls._vertex_client
        if not settings.USE_VERTEX_AI or not settings.VERTEX_PROJECT_ID:
            cls._vertex_init_failed = True
            return None
        try:
            from google import genai
            cls._vertex_client = genai.Client(
                vertexai=True,
                project=settings.VERTEX_PROJECT_ID,
                location=settings.VERTEX_LOCATION,
            )
            logger.info(
                f"Vertex AI client initialized (project={settings.VERTEX_PROJECT_ID}, "
                f"model={settings.VERTEX_MODEL})"
            )
        except Exception as e:
            logger.error(f"Vertex AI client init failed, will fall back to Mistral: {e}")
            cls._vertex_init_failed = True
            cls._vertex_client = None
        return cls._vertex_client

    async def call_ai(
        self,
        prompt: str,
        json_mode: bool = False,
        preferred_provider: Optional[str] = None
    ) -> str:
        """
        Call an AI provider with automatic fallback.

        Default order is Vertex AI Gemini (billed to a GCP project via ADC)
        first, then Mistral. Pass preferred_provider="mistral" or "vertex"
        to force a single provider.

        Args:
            prompt: The prompt to send
            json_mode: Whether to request JSON format
            preferred_provider: "vertex", "mistral", or None for auto

        Returns:
            Response text from AI
        """
        # Explicit single-provider requests
        if preferred_provider == "vertex":
            return await self._call_vertex(prompt, json_mode=json_mode)
        if preferred_provider == "mistral":
            # Honour explicit Mistral requests but still fall back to Vertex
            try:
                return await self._call_mistral(prompt, json_mode=json_mode)
            except Exception as e:
                logger.warning(f"Mistral call failed ({e}); trying Vertex AI")
                return await self._call_vertex(prompt, json_mode=json_mode)

        # Auto: prefer Vertex AI (has credits / no rate limit), fall back to Mistral
        if self._get_vertex_client() is not None:
            try:
                return await self._call_vertex(prompt, json_mode=json_mode)
            except Exception as e:
                logger.warning(f"Vertex AI call failed ({e}); falling back to Mistral")
        return await self._call_mistral(prompt, json_mode=json_mode)

    async def _call_vertex(self, prompt: str, json_mode: bool = False) -> str:
        """Call Gemini via Vertex AI using the async google-genai client."""
        client = self._get_vertex_client()
        if client is None:
            raise RuntimeError("Vertex AI client is not available")

        config: Dict[str, Any] = {"temperature": 0.1}
        if json_mode:
            config["response_mime_type"] = "application/json"

        response = await client.aio.models.generate_content(
            model=settings.VERTEX_MODEL,
            contents=prompt,
            config=config,
        )
        text = response.text
        if not text:
            raise ValueError("Empty content in Vertex AI response")
        return text
    
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

