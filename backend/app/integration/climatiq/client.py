"""
Climatiq API HTTP Client
Async HTTP client with retry logic and error handling
"""

import httpx
from typing import Dict, Any, Optional, List
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type
)

from app.core.config import settings
from app.core.errors import ClimatiqAPIError


class ClimatiqClient:
    """
    Async HTTP client for Climatiq API
    
    Handles:
    - Bearer token authentication
    - Exponential backoff for rate limits (429)
    - Request/response logging
    - Error handling and standardization
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.CLIMATIQ_API_KEY
        self.base_url = settings.CLIMATIQ_BASE_URL
        self.preview_url = settings.CLIMATIQ_PREVIEW_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.timeout = httpx.Timeout(60.0, connect=10.0)
    
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(httpx.HTTPStatusError)
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        use_preview: bool = False
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Climatiq API with retry logic
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint path
            data: Request payload
            params: Query parameters
            use_preview: Use preview API URL
            
        Returns:
            JSON response as dictionary
            
        Raises:
            ClimatiqAPIError: On API errors
        """
        base = self.preview_url if use_preview else self.base_url
        url = f"{base}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(
                        url,
                        headers=self.headers,
                        params=params
                    )
                elif method.upper() == "POST":
                    response = await client.post(
                        url,
                        headers=self.headers,
                        json=data,
                        params=params
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                error_detail = e.response.text
                raise ClimatiqAPIError(
                    f"Climatiq API error: {e.response.status_code} - {error_detail}",
                    status_code=e.response.status_code
                )
            except httpx.RequestError as e:
                raise ClimatiqAPIError(
                    f"Network error communicating with Climatiq API: {str(e)}"
                )
    
    # ========== Estimate Endpoints ==========
    
    async def estimate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Single estimate calculation
        POST /data/v1/estimate
        
        Args:
            payload: Estimate request with emission_factor and parameters
            
        Returns:
            Estimate response with co2e result
        """
        return await self._make_request("POST", "/data/v1/estimate", data=payload)
    
    async def estimate_batch(self, payloads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Batch estimation (max 100 items per request)
        POST /data/v1/estimate/batch
        
        Automatically chunks requests into batches of 100
        
        Args:
            payloads: List of estimate requests
            
        Returns:
            Combined batch results
        """
        # Chunk into max 100 items
        chunk_size = settings.BATCH_CHUNK_SIZE
        chunks = [payloads[i:i+chunk_size] for i in range(0, len(payloads), chunk_size)]
        
        all_results = []
        for chunk in chunks:
            response = await self._make_request(
                "POST",
                "/data/v1/estimate/batch",
                data={"estimates": chunk}
            )
            all_results.extend(response.get("results", []))
        
        return {"results": all_results}
    
    # ========== Travel Endpoints ==========
    
    async def travel_distance(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Distance-based travel calculation
        POST /travel/distance
        
        Args:
            payload: Travel request with origin, destination, mode
            
        Returns:
            Travel response with distance and co2e
        """
        return await self._make_request("POST", "/travel/distance", data=payload)
    
    async def travel_spend(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Spend-based travel calculation
        POST /travel/spend
        
        Args:
            payload: Spend request with spend_type, money, spend_year
            
        Returns:
            Travel response with co2e
        """
        return await self._make_request("POST", "/travel/spend", data=payload)
    
    # ========== Energy Endpoints ==========
    
    async def electricity(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Electricity emissions calculation
        POST /energy/electricity
        
        Args:
            payload: Electricity request with energy, region
            
        Returns:
            Energy response with co2e (Scope 2)
        """
        return await self._make_request("POST", "/energy/electricity", data=payload)
    
    async def fuel(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fuel combustion calculation
        POST /energy/fuel
        
        Args:
            payload: Fuel request with fuel_type, volume/energy
            
        Returns:
            Energy response with co2e (Scope 1)
        """
        return await self._make_request("POST", "/energy/fuel", data=payload)
    
    async def heat_steam(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Heat and steam calculation
        POST /energy/heat-steam
        
        Args:
            payload: Heat/steam request with energy, fuel_type
            
        Returns:
            Energy response with co2e (Scope 2)
        """
        return await self._make_request("POST", "/energy/heat-steam", data=payload)
    
    # ========== Freight Endpoints ==========
    
    async def freight_intermodal(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intermodal freight calculation
        POST /freight/intermodal
        
        Args:
            payload: Freight request with route legs and cargo
            
        Returns:
            Freight response with total co2e and per-leg breakdown
        """
        return await self._make_request("POST", "/freight/intermodal", data=payload)
    
    # ========== Procurement Endpoints ==========
    
    async def procurement(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Spend-based procurement calculation
        POST /procurement/spend
        
        Args:
            payload: Procurement request with money, classification
            
        Returns:
            Procurement response with co2e
        """
        return await self._make_request("POST", "/procurement/spend", data=payload)
    
    # ========== Autopilot Endpoints ==========
    
    async def autopilot_suggest(self, query: str, domain: str = "general") -> Dict[str, Any]:
        """
        Get emission factor suggestions from natural language
        POST /autopilot/suggest
        
        Args:
            query: Natural language description
            domain: "general" or "manufacturing"
            
        Returns:
            List of suggested emission factors with confidence scores
        """
        return await self._make_request(
            "POST",
            "/autopilot/suggest",
            data={"query": query, "domain": domain}
        )
    
    async def autopilot_estimate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combined suggestion + estimation
        POST /autopilot/estimate
        
        Args:
            payload: Query and optional parameters
            
        Returns:
            Estimate with transparency about factor selection
        """
        return await self._make_request("POST", "/autopilot/estimate", data=payload)
    
    # ========== Search Endpoints ==========
    
    async def search_emission_factors(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        region: Optional[str] = None,
        year: Optional[int] = None,
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search emission factors database
        GET /data/v1/search
        
        Args:
            query: Search query text
            category: Activity category filter
            region: Region filter
            year: Year filter
            page: Page number
            limit: Results per page
            
        Returns:
            Search results with emission factors
        """
        params = {
            "page": page,
            "results_per_page": limit
        }
        
        if query:
            params["query"] = query
        if category:
            params["category"] = category
        if region:
            params["region"] = region
        if year:
            params["year"] = year
        
        return await self._make_request("GET", "/data/v1/search", params=params)
