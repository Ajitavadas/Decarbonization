"""
LLM Router Service
Routes LLM calls to appropriate models with budget enforcement and caching.

Model Strategy:
- llama-3.1-8b-instant: High volume, chat explanations (14,400 RPD free tier)
- llama-3.3-70b-versatile: Quality model, strategies/reports (1,000 RPD free tier)

Golden Rule: LLMs explain decisions. They NEVER discover facts.
"""

import logging
import hashlib
import json
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMTask(Enum):
    """Categorization of LLM tasks for routing and budgeting"""
    CHAT_EXPLAIN = "chat_explain"           # Copilot explanations
    ANOMALY_EXPLAIN = "anomaly_explain"     # Explain flagged events
    STRATEGY_GENERATE = "strategy_generate" # Generate reduction strategies
    REPORT_SUMMARY = "report_summary"       # Executive report summaries
    CLASSIFICATION = "classification"       # Scope/activity classification


@dataclass
class LLMPolicy:
    """Policy configuration for an LLM task"""
    model: str
    max_calls_per_org_day: int
    cache_ttl_hours: int
    requires_user_trigger: bool
    max_tokens: int = 2000


# Model routing policies
LLM_POLICIES: Dict[LLMTask, LLMPolicy] = {
    LLMTask.CHAT_EXPLAIN: LLMPolicy(
        model="llama-3.1-8b-instant",
        max_calls_per_org_day=10,
        cache_ttl_hours=24,
        requires_user_trigger=True,
        max_tokens=1000
    ),
    LLMTask.ANOMALY_EXPLAIN: LLMPolicy(
        model="llama-3.1-8b-instant",
        max_calls_per_org_day=5,
        cache_ttl_hours=168,  # 7 days
        requires_user_trigger=True,
        max_tokens=500
    ),
    LLMTask.STRATEGY_GENERATE: LLMPolicy(
        model="llama-3.3-70b-versatile",
        max_calls_per_org_day=2,
        cache_ttl_hours=168,  # 7 days
        requires_user_trigger=True,
        max_tokens=2000
    ),
    LLMTask.REPORT_SUMMARY: LLMPolicy(
        model="llama-3.3-70b-versatile",
        max_calls_per_org_day=1,
        cache_ttl_hours=24,
        requires_user_trigger=True,
        max_tokens=1500
    ),
    LLMTask.CLASSIFICATION: LLMPolicy(
        model="llama-3.1-8b-instant",
        max_calls_per_org_day=50,  # Higher limit for batch processing
        cache_ttl_hours=168,
        requires_user_trigger=False,  # Automated during upload
        max_tokens=1500
    ),
}


@dataclass
class LLMResponse:
    """Standardized LLM response"""
    text: Optional[str]
    source: str  # "llm", "cache", "budget_exceeded", "error"
    model: str
    cached: bool = False
    tokens_used: int = 0
    error: Optional[str] = None


class LLMRouter:
    """
    Routes LLM calls with:
    - Model selection based on task type
    - Budget enforcement per organization
    - Response caching
    - Graceful degradation when limits exceeded
    """
    
    def __init__(self, redis_client=None, org_id: Optional[UUID] = None):
        """
        Initialize router with optional Redis for caching/budget tracking.
        
        Args:
            redis_client: Redis connection for caching
            org_id: Organization ID for budget tracking
        """
        self.redis = redis_client
        self.org_id = org_id
        self._groq_client = None
    
    @property
    def groq_client(self):
        """Lazy load Groq client"""
        if self._groq_client is None:
            import httpx
            self._groq_client = httpx.AsyncClient(
                base_url="https://api.groq.com/openai/v1",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
        return self._groq_client
    
    def get_policy(self, task: LLMTask) -> LLMPolicy:
        """Get policy for a task type"""
        return LLM_POLICIES.get(task, LLM_POLICIES[LLMTask.CHAT_EXPLAIN])
    
    async def call(
        self,
        task: LLMTask,
        prompt: str,
        cache_key: Optional[str] = None,
        skip_cache: bool = False,
        json_mode: bool = False
    ) -> LLMResponse:
        """
        Route LLM call with caching and budget enforcement.
        
        Args:
            task: Type of LLM task (determines model and limits)
            prompt: The prompt to send
            cache_key: Optional cache key (generated if not provided)
            skip_cache: Force fresh LLM call
            json_mode: Request JSON response format
            
        Returns:
            LLMResponse with text or fallback info
        """
        policy = self.get_policy(task)
        
        # Generate cache key if not provided
        if cache_key is None:
            cache_key = self._generate_cache_key(task, prompt)
        
        # 1. Check cache first (unless skipped)
        if not skip_cache and self.redis:
            cached = await self._get_cache(cache_key)
            if cached:
                logger.debug(f"Cache hit for {task.value}: {cache_key[:20]}...")
                return LLMResponse(
                    text=cached,
                    source="cache",
                    model=policy.model,
                    cached=True
                )
        
        # 2. Check budget
        if self.org_id and not await self._has_budget(task):
            logger.warning(f"Budget exceeded for {task.value}, org {self.org_id}")
            return LLMResponse(
                text=None,
                source="budget_exceeded",
                model=policy.model,
                error=f"Daily limit of {policy.max_calls_per_org_day} calls reached"
            )
        
        # 3. Make LLM call
        try:
            response_text, tokens = await self._call_llm(
                model=policy.model,
                prompt=prompt,
                max_tokens=policy.max_tokens,
                json_mode=json_mode
            )
            
            # 4. Cache successful response
            if self.redis and response_text:
                await self._set_cache(cache_key, response_text, policy.cache_ttl_hours)
            
            # 5. Increment usage
            if self.org_id:
                await self._increment_usage(task)
            
            logger.info(f"LLM call successful: {task.value}, model={policy.model}, tokens={tokens}")
            
            return LLMResponse(
                text=response_text,
                source="llm",
                model=policy.model,
                tokens_used=tokens
            )
            
        except Exception as e:
            logger.error(f"LLM call failed: {task.value}, error={str(e)}")
            return LLMResponse(
                text=None,
                source="error",
                model=policy.model,
                error=str(e)
            )
    
    async def _call_llm(
        self,
        model: str,
        prompt: str,
        max_tokens: int,
        json_mode: bool = False
    ) -> tuple[str, int]:
        """Make actual LLM API call"""
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.3  # Lower for more deterministic output
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        response = await self.groq_client.post("/chat/completions", json=payload)
        response.raise_for_status()
        
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        
        return text, tokens
    
    def _generate_cache_key(self, task: LLMTask, prompt: str) -> str:
        """Generate a cache key from task and prompt"""
        content = f"{task.value}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    async def _get_cache(self, key: str) -> Optional[str]:
        """Get cached response"""
        if not self.redis:
            return None
        try:
            full_key = f"llm:cache:{key}"
            return await self.redis.get(full_key)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
            return None
    
    async def _set_cache(self, key: str, value: str, ttl_hours: int) -> None:
        """Set cached response with TTL"""
        if not self.redis:
            return
        try:
            full_key = f"llm:cache:{key}"
            await self.redis.setex(full_key, ttl_hours * 3600, value)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
    
    async def _has_budget(self, task: LLMTask) -> bool:
        """Check if organization has remaining budget for this task"""
        if not self.redis or not self.org_id:
            return True  # No tracking, allow all
        
        policy = self.get_policy(task)
        usage_key = f"llm:usage:{self.org_id}:{task.value}:{datetime.utcnow().date()}"
        
        try:
            current = await self.redis.get(usage_key)
            current_count = int(current) if current else 0
            return current_count < policy.max_calls_per_org_day
        except Exception as e:
            logger.warning(f"Budget check failed: {e}")
            return True  # Fail open
    
    async def _increment_usage(self, task: LLMTask) -> None:
        """Increment usage counter for organization"""
        if not self.redis or not self.org_id:
            return
        
        usage_key = f"llm:usage:{self.org_id}:{task.value}:{datetime.utcnow().date()}"
        
        try:
            await self.redis.incr(usage_key)
            await self.redis.expire(usage_key, 86400)  # 24 hour TTL
        except Exception as e:
            logger.warning(f"Usage increment failed: {e}")
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics for organization"""
        if not self.redis or not self.org_id:
            return {}
        
        stats = {}
        today = datetime.utcnow().date()
        
        for task in LLMTask:
            policy = self.get_policy(task)
            usage_key = f"llm:usage:{self.org_id}:{task.value}:{today}"
            
            try:
                current = await self.redis.get(usage_key)
                current_count = int(current) if current else 0
                stats[task.value] = {
                    "used": current_count,
                    "limit": policy.max_calls_per_org_day,
                    "remaining": policy.max_calls_per_org_day - current_count,
                    "model": policy.model
                }
            except Exception:
                stats[task.value] = {"error": "Unable to fetch"}
        
        return stats
    
    async def invalidate_cache(self, pattern: str) -> int:
        """Invalidate cached responses matching pattern"""
        if not self.redis:
            return 0
        
        try:
            keys = await self.redis.keys(f"llm:cache:{pattern}*")
            if keys:
                await self.redis.delete(*keys)
            return len(keys)
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")
            return 0


# Factory function for easy instantiation
def create_llm_router(redis_client=None, org_id: Optional[UUID] = None) -> LLMRouter:
    """Create an LLM router instance"""
    return LLMRouter(redis_client=redis_client, org_id=org_id)
