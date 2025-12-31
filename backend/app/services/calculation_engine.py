"""
Calculation engine service
Orchestrates emission calculations with caching and scope classification
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime

from app.integration.climatiq.service import ClimatiqService
from app.services.cache_manager import cache_manager
from app.services.scope_classifier import scope_classifier
from app.core.config import settings


class CalculationEngine:
    """
    High-level calculation orchestration service
    
    Responsibilities:
    - Coordinate between Climatiq API and cache
    - Apply scope classification
    - Normalize responses
    - Handle errors gracefully
    """
    
    def __init__(self):
        self.climatiq_service = ClimatiqService()
    
    async def calculate_emission(
        self,
        activity_type: str,
        activity_id: str,
        parameters: Dict[str, Any],
        region: Optional[str] = None,
        year: Optional[int] = None,
        sub_type: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate emission with automatic caching and scope classification
        
        Args:
            activity_type: Activity category (energy, travel, freight, procurement)
            activity_id: Climatiq emission factor ID
            parameters: Activity parameters
            region: Region code
            year: Data year
            sub_type: Activity subcategory for scope classification
            use_cache: Whether to use caching
            
        Returns:
            Normalized result with scope, co2e, and metadata
        """
        # Generate cache key
        cache_key = None
        if use_cache:
            cache_key = cache_manager._generate_cache_key(
                activity_id=activity_id,
                region=region,
                year=year,
                version=settings.CLIMATIQ_DATA_VERSION,
                parameters=parameters
            )
            
            # Check cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result:
                return cached_result
        
        # Cache miss or caching disabled - calculate
        result = await self.climatiq_service.calculate_single_estimate(
            activity_id=activity_id,
            parameters=parameters,
            region=region,
            year=year
        )
        
        # Classify scope
        scope = scope_classifier.classify(activity_type, sub_type)
        
        # Normalize response
        normalized = {
            "co2e_kg": float(result.get("co2e", 0)),
            "co2e_unit": result.get("co2e_unit", "kg"),
            "calculation_method": result.get("co2e_calculation_method", "ipcc_ar6_gwp100"),
            "constituent_gases": result.get("constituent_gases", {}),
            "emission_factor_id": activity_id,
            "scope": scope,
            "activity_type": activity_type,
            "sub_type": sub_type,
            "region": region,
            "year": year,
            "source_dataset": result.get("emission_factor", {}).get("source", None),
            "input_data": {
                "activity_id": activity_id,
                "parameters": parameters,
                "region": region,
                "year": year
            },
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        # Cache result
        if use_cache and cache_key:
            await cache_manager.set(cache_key, normalized)
        
        return normalized
    
    async def calculate_batch_emissions(
        self,
        activities: List[Dict[str, Any]],
        use_cache: bool = False  # Batch operations typically skip cache
    ) -> List[Dict[str, Any]]:
        """
        Calculate batch emissions
        
        Args:
            activities: List of activity definitions
            use_cache: Whether to attempt caching (usually False for batches)
            
        Returns:
            List of calculation results
        """
        # Prepare batch request
        estimates = []
        for activity in activities:
            estimates.append({
                "emission_factor": {
                    "activity_id": activity["activity_id"],
                    "data_version": settings.CLIMATIQ_DATA_VERSION,
                    "region": activity.get("region"),
                    "year": activity.get("year")
                },
                "parameters": activity["parameters"]
            })
        
        # Execute batch calculation
        batch_result = await self.climatiq_service.calculate_batch_estimates(estimates)
        
        # Process results
        results = []
        for idx, result in enumerate(batch_result.get("results", [])):
            activity = activities[idx]
            
            if "error" in result:
                # Handle individual failure
                results.append({
                    "success": False,
                    "error": result.get("error"),
                    "row_index": idx,
                    "activity_id": activity.get("activity_id")
                })
            else:
                # Success - normalize
                scope = scope_classifier.classify(
                    activity.get("activity_type", "unknown"),
                    activity.get("sub_type")
                )
                
                results.append({
                    "success": True,
                    "co2e_kg": float(result.get("co2e", 0)),
                    "scope": scope,
                    "activity_type": activity.get("activity_type"),
                    "input_data": activity,
                    "row_index": idx
                })
        
        return results
    
    async def calculate_travel(
        self,
        travel_mode: str,
        origin: str,
        destination: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Simplified travel calculation interface
        
        Args:
            travel_mode: air, car, rail, bus
            origin: Origin location
            destination: Destination location
            **kwargs: Mode-specific parameters (cabin_class, car_size, car_type, year)
            
        Returns:
            Travel calculation result
        """
        result = await self.climatiq_service.calculate_travel_distance(
            travel_mode=travel_mode,
            origin=origin,
            destination=destination,
            year=kwargs.get("year"),
            flight_class=kwargs.get("cabin_class", "economy") if travel_mode == "air" else None,
            car_size=kwargs.get("car_size") if travel_mode == "car" else None,
            car_type=kwargs.get("car_type") if travel_mode == "car" else None
        )
        
        # Normalize response
        return {
            "co2e_kg": float(result.get("co2e", 0)),
            "distance_km": float(result.get("distance_km", result.get("distance", 0))),
            "scope": "Scope 3",
            "activity_type": "travel",
            "sub_type": travel_mode
        }


# Global calculation engine instance
calculation_engine = CalculationEngine()
