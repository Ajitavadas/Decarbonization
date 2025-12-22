"""
Carbon Copilot Chatbot - US-4.1
Natural language interface for carbon data queries
"""

import logging
from typing import Dict, List, Optional
import json
from datetime import datetime, timezone
import uuid

import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.config import settings
from app.models.models import EmissionEvent, CalculationLedger

from app.services.ai_base_service import AIBaseService

logger = logging.getLogger(__name__)


class CopilotService(AIBaseService):
    """
    Carbon Copilot - Natural Language Query Interface (US-4.1)
    """
    
    def __init__(self):
        super().__init__()
        self.chat_sessions = {}
    
    async def process_query(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_query: str,
        session_id: str = "default"
    ) -> Dict:
        try:
            if session_id not in self.chat_sessions:
                self.chat_sessions[session_id] = []
            
            data_results = {}
            query_lower = user_query.lower()
            
            if any(word in query_lower for word in ['total', 'all', 'overall', 'how much']):
                data_results['total'] = await self._tool_get_total_emissions(db, org_id, {})
            
            if any(word in query_lower for word in ['scope', 'breakdown', 'split']):
                data_results['scopes'] = await self._tool_get_scope_breakdown(db, org_id)
            
            if any(word in query_lower for word in ['category', 'categories', 'top']):
                data_results['categories'] = await self._tool_get_category_analysis(db, org_id, {'top_n': 5})
            
            if any(word in query_lower for word in ['trend', 'month', 'time', 'increase', 'decrease']):
                data_results['trend'] = await self._tool_get_trend_analysis(db, org_id, {'months': 12})
            
            try:
                prompt = self._build_answer_prompt(user_query, data_results)
                answer = await self.call_ai(prompt, json_mode=False, preferred_provider="gemini")
            except Exception as e:
                logger.error(f"AI response generation failed: {e}")
                # Fallback if AI fails completely
                answer = "I'm sorry, I'm having trouble with my AI brain right now, but here is the data I found: " + json.dumps(data_results)
            
            self.chat_sessions[session_id].append({
                "query": user_query,
                "answer": answer,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return {
                "answer": answer,
                "data": data_results,
                "confidence": 0.85,
                "tool_calls": list(data_results.keys())
            }
            
        except Exception as e:
            logger.error(f"Copilot query failed: {str(e)}")
            return {
                "answer": "I'm sorry, I encountered an error. Please try again.",
                "data": {},
                "confidence": 0.0
            }
    
    def _build_answer_prompt(self, user_query: str, data_results: Dict) -> str:
        data_summary = ""
        if data_results:
            data_summary = "\n**Available Data (Units in tonnes CO2e):**\n"
            for key, value in data_results.items():
                data_summary += f"- {key}: {str(value)}\n"
        
        return f"""
        You are a Carbon Accounting Assistant.
        
        **User Question:** {user_query}
        {data_summary}
        
        **Instructions:**
        - Answer clearly and concisely using the provided data.
        - Explain in simple terms.
        - If data is missing or zero, explain why (e.g. "no data uploaded yet").
        """

    async def _tool_get_total_emissions(self, db, org_id, args):
        query = select(func.sum(CalculationLedger.result_kg_co2e)).where(
            CalculationLedger.organization_id == org_id
        )
        # Handle date filters if we join with EmissionEvent
        if "start_date" in args or "end_date" in args:
            query = query.join(EmissionEvent, CalculationLedger.emission_event_id == EmissionEvent.id)
            if "start_date" in args:
                query = query.where(EmissionEvent.activity_date >= args["start_date"])
            if "end_date" in args:
                query = query.where(EmissionEvent.activity_date <= args["end_date"])
        
        result = await db.execute(query)
        total_kg = result.scalar() or 0.0
        return {"total_tonnes": round(float(total_kg) / 1000.0, 2)}

    async def _tool_get_scope_breakdown(self, db, org_id):
        query = (
            select(
                EmissionEvent.scope,
                func.sum(CalculationLedger.result_kg_co2e).label('total')
            )
            .join(CalculationLedger, CalculationLedger.emission_event_id == EmissionEvent.id)
            .where(CalculationLedger.organization_id == org_id)
            .group_by(EmissionEvent.scope)
        )
        result = await db.execute(query)
        breakdown = {row.scope: round(float(row.total) / 1000.0, 2) for row in result}
        return {"scope_breakdown": breakdown}

    async def _tool_get_category_analysis(self, db, org_id, args):
        query = (
            select(
                EmissionEvent.scope_3_category,
                func.sum(CalculationLedger.result_kg_co2e).label('total')
            )
            .join(CalculationLedger, CalculationLedger.emission_event_id == EmissionEvent.id)
            .where(CalculationLedger.organization_id == org_id)
            .group_by(EmissionEvent.scope_3_category)
            .order_by(desc('total'))
            .limit(args.get("top_n", 5))
        )
        result = await db.execute(query)
        categories = [
            {"category": row.scope_3_category or "Main", "tonnes": round(float(row.total) / 1000.0, 2)}
            for row in result
        ]
        return {"top_categories": categories}

    async def _tool_get_trend_analysis(self, db, org_id, args):
        from sqlalchemy import extract
        query = (
            select(
                extract('year', EmissionEvent.activity_date).label('year'),
                extract('month', EmissionEvent.activity_date).label('month'),
                func.sum(CalculationLedger.result_kg_co2e).label('total')
            )
            .join(CalculationLedger, CalculationLedger.emission_event_id == EmissionEvent.id)
            .where(CalculationLedger.organization_id == org_id)
            .group_by('year', 'month')
            .order_by('year', 'month')
        )
        result = await db.execute(query)
        trend = [
            {
                "date": f"{int(row.year)}-{int(row.month):02d}",
                "tonnes": round(float(row.total) / 1000.0, 2)
            }
            for row in result
        ]
        return {"trend_data": trend}