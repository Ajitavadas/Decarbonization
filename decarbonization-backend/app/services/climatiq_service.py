import httpx
import logging
from typing import List, Dict, Any, Optional
from app.config import settings
from app.schemas.climatiq import (
    ClimatiqEstimateRequest, 
    ClimatiqEstimateResponse,
    ClimatiqSearchResponse,
    ClimatiqEmissionFactor
)

logger = logging.getLogger(__name__)

class ClimatiqService:
    """Wrapper for Climatiq REST API"""
    
    BASE_URL = "https://api.climatiq.io/data/v1"
    
    def __init__(self):
        self.api_key = settings.CLIMATIQ_API_KEY
        if not self.api_key:
            logger.warning("CLIMATIQ_API_KEY is not set in configuration")
            
    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def estimate(self, request: ClimatiqEstimateRequest) -> ClimatiqEstimateResponse:
        """Calculate emissions for a particular activity"""
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/estimate"
            # Remove None values from emission_factor to keep request clean
            payload = request.model_dump(exclude_none=True)
            
            response = await client.post(url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Climatiq Estimate API error: {response.text}")
                response.raise_for_status()
                
            return ClimatiqEstimateResponse(**response.json())

    async def batch_estimate(self, requests: List[ClimatiqEstimateRequest]) -> List[Dict[str, Any]]:
        """Calculate multiple emission estimations in a single request"""
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/estimate/batch"
            payload = [req.model_dump(exclude_none=True) for req in requests]
            
            response = await client.post(url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Climatiq Batch Estimate API error: {response.text}")
                response.raise_for_status()
                
            return response.json()

    async def search(self, params: Dict[str, Any]) -> ClimatiqSearchResponse:
        """Query for emission factors and metadata"""
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/search"
            # Filter out None params
            query_params = {k: v for k, v in params.items() if v is not None}
            
            response = await client.get(url, headers=self.headers, params=query_params)
            
            if response.status_code != 200:
                logger.error(f"Climatiq Search API error: {response.text}")
                response.raise_for_status()
                
            return ClimatiqSearchResponse(**response.json())

    async def get_activity_id_metadata(self, activity_id: str) -> Optional[Dict[str, Any]]:
        """Utility to get metadata (including UUID id) for a specific activity_id string"""
        response = await self.search({"activity_id": activity_id, "results_per_page": 1})
        if response.results:
            return response.results[0].model_dump()
        return None

    async def get_data_versions(self) -> List[str]:
        """Get all available data versions"""
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/data-versions"
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_unit_types(self) -> List[str]:
        """Get all available unit types"""
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/unit-types"
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
