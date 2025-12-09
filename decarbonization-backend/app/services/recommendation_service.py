"""
Reduction Recommendations - US-4.3
AI-powered emission reduction recommendations
"""

import logging
from typing import List, Dict
import json

import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Emission Reduction Recommendations (US-4.3)
    
    AC:
    - Top 5 recommendations appear on dashboard
    - Each recommendation includes expected impact and cost
    - Recommendations are specific and actionable
    - ROI calculations based on industry data
    """
    
    # Industry benchmark data (tonnes CO2e per $M revenue)
    INDUSTRY_BENCHMARKS = {
        "technology": 50,
        "manufacturing": 300,
        "retail": 100,
        "finance": 30,
        "healthcare": 150,
        "default": 100
    }
    
    # Reduction playbook (common interventions)
    REDUCTION_PLAYBOOK = [
        {
            "name": "Switch to renewable electricity",
            "applicable_to": ["Purchased Electricity", "Scope 2"],
            "typical_reduction": 0.90,  # 90% reduction
            "cost_per_tonne": 30,
            "payback_years": 5
        },
        {
            "name": "Upgrade to LED lighting",
            "applicable_to": ["Purchased Electricity"],
            "typical_reduction": 0.60,
            "cost_per_tonne": 20,
            "payback_years": 2
        },
        {
            "name": "Implement remote work policy",
            "applicable_to": ["Employee Commuting", "Scope 3"],
            "typical_reduction": 0.50,
            "cost_per_tonne": 0,  # Cost savings
            "payback_years": 0
        },
        {
            "name": "Optimize HVAC systems",
            "applicable_to": ["Purchased Electricity", "Natural Gas"],
            "typical_reduction": 0.20,
            "cost_per_tonne": 15,
            "payback_years": 3
        },
        {
            "name": "Switch to electric vehicles",
            "applicable_to": ["Mobile Combustion", "Fuel", "Scope 1"],
            "typical_reduction": 0.70,
            "cost_per_tonne": 50,
            "payback_years": 7
        }
    ]
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def generate_recommendations(
        self,
        db: AsyncSession,
        org_id: str,
        industry: str = "default",
        annual_revenue: Optional[float] = None
    ) -> List[Dict]:
        """
        Generate top 5 reduction recommendations
        
        Returns:
            List of recommendations with impact and cost estimates
        """
        # Get emissions data
        total = await DashboardService.get_total_emissions(db, org_id)
        scope_breakdown = await DashboardService.get_scope_breakdown(db, org_id)
        categories = await DashboardService.get_category_breakdown(db, org_id, limit=10)
        
        # Identify 80/20 - which categories drive most emissions
        top_categories = sorted(categories, key=lambda x: x['emissions_tonnes'], reverse=True)[:3]
        
        # Get AI-powered recommendations
        recommendations = await self._generate_ai_recommendations(
            total_emissions=total,
            scope_breakdown=scope_breakdown,
            top_categories=top_categories,
            industry=industry
        )
        
        # Enhance with cost estimates
        enhanced_recommendations = []
        for rec in recommendations[:5]:
            # Calculate potential savings
            impact_tonnes = rec.get("impact_tonnes", 0)
            cost_per_tonne = rec.get("cost_per_tonne", 30)
            
            enhanced_recommendations.append({
                **rec,
                "total_cost_estimate": impact_tonnes * cost_per_tonne,
                "annual_savings_estimate": impact_tonnes * 50,  # Carbon credit value
                "roi_years": rec.get("payback_years", 3)
            })
        
        return enhanced_recommendations
    
    async def _generate_ai_recommendations(
        self,
        total_emissions: float,
        scope_breakdown: Dict,
        top_categories: List[Dict],
        industry: str
    ) -> List[Dict]:
        """Use Gemini to generate tailored recommendations"""
        
        prompt = f"""
        You are a carbon reduction strategy expert. Generate 5 specific, actionable recommendations.
        
        **Organization Profile:**
        - Total Emissions: {total_emissions} tonnes CO2e/year
        - Scope Breakdown: Scope 1: {scope_breakdown.get(1, 0)}, Scope 2: {scope_breakdown.get(2, 0)}, Scope 3: {scope_breakdown.get(3, 0)}
        - Top Categories: {', '.join([c['category'] for c in top_categories])}
        - Industry: {industry}
        
        **Requirements:**
        1. Focus on the 80/20 rule - target biggest emission sources
        2. Provide specific, actionable steps
        3. Estimate CO2e reduction potential
        4. Include cost estimates and payback period
        5. Prioritize by ROI
        
        Return ONLY this JSON array format:
        [
            {{
                "title": "<concise title>",
                "description": "<detailed action steps>",
                "target_category": "<emission category>",
                "impact_tonnes": <estimated annual CO2e reduction>,
                "cost_per_tonne": <cost in USD per tonne reduced>,
                "payback_years": <years to break even>,
                "priority": "<high/medium/low>"
            }}
        ]
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            result_text = response.text.strip()
            
            # Clean JSON
            if result_text.startswith("```json"):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith("```"):
                result_text = result_text[3:-3].strip()
            
            recommendations = json.loads(result_text)
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {str(e)}")
            return []