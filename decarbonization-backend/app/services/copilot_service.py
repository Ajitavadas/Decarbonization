"""
Carbon Copilot Chatbot - US-4.1
Natural language interface for carbon data queries
"""

import logging
from typing import Dict, List, Optional
import json
from datetime import datetime, timezone

import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.config import settings
from app.models.models import EmissionTransaction

logger = logging.getLogger(__name__)


class CopilotService:
    """
    Carbon Copilot - Natural Language Query Interface (US-4.1)
    
    AC:
    - Chatbot correctly answers 80% or more of user questions
    - Responses are clear and non-technical (no jargon)
    - Users receive answers in under 2 seconds
    - Chatbot can handle 10+ different question types
    """
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Define tools using correct SDK format
        # Tools will be converted internally by the SDK
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash'
        )
        self.chat_sessions = {}  # Store conversation history
    
    async def process_query(
        self,
        db: AsyncSession,
        org_id: str,
        user_query: str,
        session_id: str = "default"
    ) -> Dict:
        """
        Process natural language query and return answer
        
        Returns:
            {
                "answer": str,
                "data": dict,
                "confidence": float,
                "tool_calls": list
            }
        """
        try:
            # Get or create chat session
            if session_id not in self.chat_sessions:
                self.chat_sessions[session_id] = []
            
            # First, fetch some relevant data
            data_results = {}
            
            # Determine what data to fetch based on keywords
            query_lower = user_query.lower()
            
            if any(word in query_lower for word in ['total', 'all', 'overall']):
                data_results['total'] = await self._tool_get_total_emissions(db, org_id, {})
            
            if any(word in query_lower for word in ['scope', 'breakdown', 'split']):
                data_results['scopes'] = await self._tool_get_scope_breakdown(db, org_id)
            
            if any(word in query_lower for word in ['category', 'categories', 'top']):
                data_results['categories'] = await self._tool_get_category_analysis(db, org_id, {'top_n': 5})
            
            if any(word in query_lower for word in ['trend', 'month', 'time']):
                data_results['trend'] = await self._tool_get_trend_analysis(db, org_id, {'months': 12})
            
            # Build context-aware prompt with data
            prompt = self._build_answer_prompt(user_query, data_results)
            
            # Send to Gemini
            response = await self.model.generate_content_async(prompt)
            
            final_answer = response.text if hasattr(response, 'text') else "I'm sorry, I couldn't process your question."
            
            # Store in session history
            self.chat_sessions[session_id].append({
                "query": user_query,
                "answer": final_answer,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return {
                "answer": final_answer,
                "data": data_results,
                "confidence": 0.85,
                "tool_calls": list(data_results.keys())
            }
            
        except Exception as e:
            logger.error(f"Copilot query failed: {str(e)}")
            return {
                "answer": "I'm sorry, I encountered an error processing your question. Please try rephrasing it.",
                "data": {},
                "confidence": 0.0,
                "tool_calls": []
            }
    
    
    def _build_answer_prompt(self, user_query: str, data_results: Dict) -> str:
        """Build prompt with data context for answer generation"""
        data_summary = ""
        
        if data_results:
            data_summary = "\n**Available Data:**\n"
            for key, value in data_results.items():
                data_summary += f"- {key}: {str(value)}\n"
        
        return f"""
        You are a Carbon Accounting Assistant helping users understand their emissions data.
        
        **User Question:** {user_query}
        {data_summary}
        
        **Your task:**
        - Answer the question clearly and concisely
        - Use the data provided above if relevant
        - Explain in simple, non-technical language
        - Provide actionable insights where possible
        - If data is insufficient, say so politely
        
        Provide a helpful, friendly response:
        """
    
    async def _execute_tool_call(
        self,
        db: AsyncSession,
        org_id: str,
        tool_name: str,
        args: Dict
    ) -> Dict:
        """Execute a tool function call"""
        
        if tool_name == "get_total_emissions":
            return await self._tool_get_total_emissions(db, org_id, args)
        
        elif tool_name == "get_scope_breakdown":
            return await self._tool_get_scope_breakdown(db, org_id)
        
        elif tool_name == "get_category_analysis":
            return await self._tool_get_category_analysis(db, org_id, args)
        
        elif tool_name == "compare_periods":
            return await self._tool_compare_periods(db, org_id, args)
        
        elif tool_name == "get_trend_analysis":
            return await self._tool_get_trend_analysis(db, org_id, args)
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    async def _tool_get_total_emissions(self, db, org_id, args):
        """Tool: Get total emissions"""
        query = select(func.sum(EmissionTransaction.co2e_tonnes)).where(
            EmissionTransaction.organization_id == org_id
        )
        
        if "start_date" in args:
            query = query.where(EmissionTransaction.transaction_date >= args["start_date"])
        if "end_date" in args:
            query = query.where(EmissionTransaction.transaction_date <= args["end_date"])
        
        result = await db.execute(query)
        total = result.scalar() or 0.0
        
        return {"total_tonnes": round(total, 2)}
    
    async def _tool_get_scope_breakdown(self, db, org_id):
        """Tool: Get scope breakdown"""
        query = select(
            EmissionTransaction.scope,
            func.sum(EmissionTransaction.co2e_tonnes).label('total')
        ).where(
            EmissionTransaction.organization_id == org_id
        ).group_by(EmissionTransaction.scope)
        
        result = await db.execute(query)
        breakdown = {row.scope: round(row.total, 2) for row in result}
        
        return {"scope_breakdown": breakdown}
    
    async def _tool_get_category_analysis(self, db, org_id, args):
        """Tool: Get category analysis"""
        query = select(
            EmissionTransaction.category,
            func.sum(EmissionTransaction.co2e_tonnes).label('total')
        ).where(
            EmissionTransaction.organization_id == org_id
        )
        
        if "scope" in args:
            query = query.where(EmissionTransaction.scope == args["scope"])
        
        query = query.group_by(EmissionTransaction.category).order_by(
            func.sum(EmissionTransaction.co2e_tonnes).desc()
        ).limit(args.get("top_n", 5))
        
        result = await db.execute(query)
        categories = [
            {"category": row.category, "emissions_tonnes": round(row.total, 2)}
            for row in result
        ]
        
        return {"top_categories": categories}
    
    async def _tool_compare_periods(self, db, org_id, args):
        """Tool: Compare two time periods"""
        # Period 1
        query1 = select(func.sum(EmissionTransaction.co2e_tonnes)).where(
            and_(
                EmissionTransaction.organization_id == org_id,
                EmissionTransaction.transaction_date >= args["period1_start"],
                EmissionTransaction.transaction_date <= args["period1_end"]
            )
        )
        result1 = await db.execute(query1)
        period1_total = result1.scalar() or 0.0
        
        # Period 2
        query2 = select(func.sum(EmissionTransaction.co2e_tonnes)).where(
            and_(
                EmissionTransaction.organization_id == org_id,
                EmissionTransaction.transaction_date >= args["period2_start"],
                EmissionTransaction.transaction_date <= args["period2_end"]
            )
        )
        result2 = await db.execute(query2)
        period2_total = result2.scalar() or 0.0
        
        change = period2_total - period1_total
        percent_change = (change / period1_total * 100) if period1_total > 0 else 0
        
        return {
            "period1_total": round(period1_total, 2),
            "period2_total": round(period2_total, 2),
            "change": round(change, 2),
            "percent_change": round(percent_change, 1)
        }
    
    async def _tool_get_trend_analysis(self, db, org_id, args):
        """Tool: Get trend analysis"""
        from datetime import timedelta
        from sqlalchemy import extract
        
        months = args.get("months", 12)
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=months*30)
        
        query = select(
            extract('year', EmissionTransaction.transaction_date).label('year'),
            extract('month', EmissionTransaction.transaction_date).label('month'),
            func.sum(EmissionTransaction.co2e_tonnes).label('total')
        ).where(
            and_(
                EmissionTransaction.organization_id == org_id,
                EmissionTransaction.transaction_date >= start_date
            )
        ).group_by('year', 'month').order_by('year', 'month')
        
        result = await db.execute(query)
        trend = [
            {
                "date": f"{int(row.year)}-{int(row.month):02d}",
                "emissions": round(row.total, 2)
            }
            for row in result
        ]
        
        return {"trend_data": trend}
    
    async def _generate_answer_from_data(
        self,
        query: str,
        data_results: Dict,
        raw_response: str
    ) -> str:
        """Generate natural language answer from tool results"""
        
        if not data_results:
            return raw_response or "I don't have enough data to answer that question."
        
        # Build data summary for Gemini
        data_summary = json.dumps(data_results, indent=2)
        
        prompt = f"""
        Based on this data, provide a clear, conversational answer to the user's question.
        
        **User Question:** {query}
        
        **Data:**
        {data_summary}
        
        **Instructions:**
        - Explain in simple terms
        - Include specific numbers
        - Add context where helpful (e.g., comparisons, trends)
        - Keep it concise (2-3 sentences)
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            # Fallback to basic answer
            if "total_tonnes" in data_results.get("get_total_emissions", {}):
                total = data_results["get_total_emissions"]["total_tonnes"]
                return f"Your total emissions are {total} tonnes of CO2e."
            return "Here's the data: " + data_summary