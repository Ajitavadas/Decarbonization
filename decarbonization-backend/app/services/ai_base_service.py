import logging
import asyncio
import google.generativeai as genai
from groq import AsyncGroq
from typing import Optional, Any, List
from app.config import settings

logger = logging.getLogger(__name__)

class AIBaseService:
    """Base class for AI services with retry and fallback logic"""
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        
        # Initialize Gemini
        self.gemini_model = None
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "Gemini API Key":
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
                logger.info("Gemini AI initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
        else:
            logger.warning("Gemini API key missing or invalid.")
                
        # Initialize Groq (Async)
        self.groq_client = None
        if settings.GROQ_API_KEY:
            try:
                self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
                logger.info("Groq AI initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize Groq: {e}")
        else:
            logger.warning("Groq API key is missing.")

    async def _call_gemini(self, prompt: str, json_mode: bool = False) -> str:
        if not self.gemini_model:
            raise ValueError("Gemini key not configured")
        
        generation_config = {}
        if json_mode:
            generation_config["response_mime_type"] = "application/json"
            
        response = await self.gemini_model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        return response.text

    async def _call_groq(self, prompt: str, json_mode: bool = False) -> str:
        if not self.groq_client:
            raise ValueError("Groq key not configured")
            
        response_format = None
        if json_mode:
            response_format = {"type": "json_object"}
            
        completion = await self.groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a professional GHG emission expert. " + ("Return JSON only." if json_mode else "")},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0,
            response_format=response_format
        )
        return completion.choices[0].message.content

    async def call_ai(self, prompt: str, json_mode: bool = False, preferred_provider: str = "gemini") -> str:
        """
        Call AI with fallback and retries.
        Order: Preferred -> Alternative -> Raise
        """
        providers = [preferred_provider]
        if preferred_provider == "gemini":
            providers.append("groq")
        else:
            providers.append("gemini")
            
        last_error = None
        
        # Filter available providers
        available_providers = []
        for p in providers:
            if p == "gemini" and self.gemini_model:
                available_providers.append(p)
            elif p == "groq" and self.groq_client:
                available_providers.append(p)
        
        if not available_providers:
            logger.error("No AI providers configured!")
            raise Exception("No AI providers (Gemini/Groq) are configured.")

        for p_idx, provider in enumerate(available_providers):
            for attempt in range(self.max_retries):
                try:
                    logger.info(f"AI Call: Provider={provider}, Attempt={attempt + 1}/{self.max_retries}")
                    if provider == "gemini":
                        return await self._call_gemini(prompt, json_mode)
                    else:
                        return await self._call_groq(prompt, json_mode)
                except Exception as e:
                    last_error = e
                    err_str = str(e).lower()
                    logger.warning(f"AI Call failed ({provider}, attempt {attempt + 1}): {e}")
                    
                    # If this is a quota error and we have another provider to try, 
                    # switch immediately to save time and avoid "infinite loop" perception.
                    if ("429" in err_str or "quota" in err_str or "limit" in err_str) and (p_idx < len(available_providers) - 1):
                        logger.warning(f"Quota exceeded for {provider}. Switching to fallback provider immediately.")
                        break # Break out of attempt loop to move to next provider
                    
                    # Otherwise wait for retry
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
            
            logger.error(f"Provider {provider} exhausted or skipped. Checking next available.")
            
        raise Exception(f"All AI providers failed. Last error: {last_error}")
