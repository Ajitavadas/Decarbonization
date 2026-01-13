"""
Copilot Service - LLM-Powered Carbon Copilot with Dynamic SQL Generation

Architecture:
1. LLM Intent Understanding: Groq understands natural language questions
2. Dynamic SQL Generation: Groq generates safe read-only queries
3. Safe Execution: Queries validated and executed with org isolation
4. Natural Response: Groq generates human-friendly responses with context
5. Rate Limiting: Per-org tracking with cooldown notifications
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID
from decimal import Decimal
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError

from app.models.activity import EmissionActivity
from app.models.project import Project
from app.models.reduction_target import ReductionTarget
from app.models.flagged_event import FlaggedEvent
from app.models.organization import Organization
from app.core.config import settings
from app.core.archetype_config import get_archetype

logger = logging.getLogger(__name__)


# Database schema for LLM context
DATABASE_SCHEMA = """
Available Tables:

1. emission_activities - Individual emission records
   Columns:
   - id (UUID): Unique identifier
   - activity_type (str): 'electricity', 'natural_gas', 'fuel', 'travel', 'freight', 'waste', 'procurement'
   - sub_type (str): Sub-classification
   - scope (str): 'Scope 1', 'Scope 2', or 'Scope 3'
   - activity_date (datetime): When activity occurred
   - co2e_kg (numeric): Calculated emissions in kg CO2e
   - region (str): Geographic region code
   - description (str): Human-readable activity description
   - input_data (JSONB): Contains 'description', 'amount', 'unit' fields
   - project_id (UUID): Links to projects
   - emission_factor_id (str): Climatiq factor used

2. projects - Project containers for activities
   Columns:
   - id (UUID): Project identifier
   - name (str): Project name
   - organization_id (UUID): Owner organization

3. flagged_events - Anomalies and findings
   Columns:
   - id (UUID): Finding identifier
   - flag_type (str): 'gap', 'anomaly', 'archetype_mismatch', 'emission_factor_missing'
   - severity (str): 'info', 'warning', 'critical', 'high'
   - status (str): 'open', 'acknowledged', 'resolved', 'false_positive'
   - title (str): Short summary
   - description (text): Full issue description
   - recommendation (text): Action to resolve - includes valid activity structure
   - rule_id (str): Detection rule identifier
   - evidence (JSONB): Supporting data
   - activity_id (UUID): Linked activity if applicable
   - organization_id (UUID): Owner
   - created_at (datetime): When flagged

4. reduction_targets - Emission reduction goals
   Columns:
   - id (UUID): Target identifier
   - name (str): Target name
   - target_type (str): 'absolute' or 'percentage'
   - scope (str): Target scope or 'all'
   - baseline_year (str): Starting year
   - baseline_value (numeric): Baseline emissions kg
   - target_year (str): Goal year
   - target_value (numeric): Target value
   - current_value (numeric): Latest emissions
   - progress_percentage (numeric): 0-100
   - status (str): 'on_track', 'at_risk', 'off_track', 'achieved'
   - is_active (bool): Active status
   - organization_id (UUID): Owner
"""

# SQL blocklist for safety
SQL_BLOCKLIST = [
    'DELETE', 'UPDATE', 'INSERT', 'DROP', 'TRUNCATE', 'ALTER', 
    'CREATE', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK', 'EXECUTE',
    'EXEC', 'INTO', ';--', 'UNION'
]

# In-memory rate limit tracking (per org)
_rate_limit_tracker: Dict[str, Dict] = defaultdict(lambda: {"count": 0, "reset_at": None})


class CopilotService:
    """
    LLM-Powered Carbon Copilot Service
    
    Features:
    - Natural language understanding via Groq
    - Dynamic SQL query generation
    - Safe read-only execution with org isolation
    - Rate limiting with cooldown notifications
    """
    
    def __init__(self, db: Session, organization_id: UUID, redis_client=None):
        self.db = db
        self.organization_id = organization_id
        self.redis_client = redis_client
        self._organization = None
        self._groq_client = None
    
    @property
    def organization(self) -> Organization:
        if self._organization is None:
            self._organization = self.db.query(Organization).filter(
                Organization.id == self.organization_id
            ).first()
        return self._organization
    
    @property
    def groq_client(self):
        """Lazy load Groq client"""
        if self._groq_client is None:
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=settings.GROQ_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
        return self._groq_client
    
    def _check_rate_limit(self) -> Tuple[bool, Optional[datetime]]:
        """Check if organization has exceeded rate limit"""
        org_key = str(self.organization_id)
        now = datetime.utcnow()
        
        tracker = _rate_limit_tracker[org_key]
        
        # Reset if window expired
        if tracker["reset_at"] is None or now >= tracker["reset_at"]:
            tracker["count"] = 0
            tracker["reset_at"] = now + timedelta(seconds=settings.COPILOT_RATE_LIMIT_WINDOW_SECONDS)
        
        # Check if over limit
        if tracker["count"] >= settings.COPILOT_MAX_QUERIES_PER_HOUR:
            return False, tracker["reset_at"]
        
        return True, None
    
    def _increment_usage(self):
        """Increment rate limit counter"""
        org_key = str(self.organization_id)
        _rate_limit_tracker[org_key]["count"] += 1
    
    async def chat(
        self,
        message: str,
        history: Optional[List[Dict]] = None,
        include_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Process a chat message using LLM-powered understanding and dynamic SQL.
        
        Flow:
        1. Check rate limit
        2. Gather base context
        3. Generate SQL with Groq LLM
        4. Execute query safely
        5. Generate response with Groq
        """
        history = history or []
        
        # 1. Check rate limit
        allowed, reset_time = self._check_rate_limit()
        if not allowed:
            reset_str = reset_time.strftime("%H:%M UTC") if reset_time else "soon"
            return {
                "text": f"Rate limit reached. Carbon Copilot will be available again at {reset_str}. "
                        f"You have {settings.COPILOT_MAX_QUERIES_PER_HOUR} queries per hour.",
                "intent": "rate_limited",
                "data": {},
                "source": "rate_limit",
                "model": None,
                "suggestions": ["Try again later"],
                "rate_limited": True,
                "reset_at": reset_time.isoformat() if reset_time else None
            }
        
        # 2. Gather base context
        context = self._get_base_context()
        
        # 3. Generate SQL with Groq LLM
        try:
            query_result = await self._generate_sql_with_llm(message, context)
            intent = query_result.get("intent", "unknown")
            sql_query = query_result.get("sql_query")
            
            # 4. Execute query safely (if provided)
            query_data = []
            query_error = None
            rows_returned = 0
            
            if sql_query:
                query_data, query_error = self._execute_safe_query(sql_query)
                rows_returned = len(query_data)
                
                if query_error:
                    logger.warning(f"Query execution failed: {query_error}")
            
            # Add base context data
            all_data = {
                "organization": context.get("org_name"),
                "total_emissions_kg": context.get("total_emissions"),
                "query_results": query_data,
                "rows_returned": rows_returned
            }
            
            # 5. Generate natural language response
            response_text = await self._generate_response_with_llm(
                message, context, query_data, query_error, intent
            )
            
            # 6. Track usage
            self._increment_usage()
            
            return {
                "text": response_text,
                "intent": intent,
                "data": all_data,
                "source": "llm",
                "model": settings.COPILOT_MODEL,
                "suggestions": self._get_suggestions(intent, query_data),
                "query_executed": sql_query if sql_query else None,
                "rows_returned": rows_returned,
                "rate_limited": False,
                "reset_at": None
            }
            
        except Exception as e:
            logger.error(f"Copilot chat error: {e}", exc_info=True)
            self._increment_usage()
            
            return {
                "text": f"I encountered an issue processing your question. Please try rephrasing. Error: {str(e)[:100]}",
                "intent": "error",
                "data": {"error": str(e)},
                "source": "error",
                "model": None,
                "suggestions": ["Try a simpler question", "Ask about total emissions"],
                "rate_limited": False,
                "reset_at": None
            }
    
    def _get_base_context(self) -> Dict[str, Any]:
        """Gather base context for LLM"""
        org = self.organization
        
        # Total emissions
        total = self.db.query(func.sum(EmissionActivity.co2e_kg)).join(
            Project
        ).filter(
            Project.organization_id == self.organization_id
        ).scalar()
        
        # Scope breakdown
        scope_results = self.db.query(
            EmissionActivity.scope,
            func.sum(EmissionActivity.co2e_kg)
        ).join(Project).filter(
            Project.organization_id == self.organization_id
        ).group_by(EmissionActivity.scope).all()
        
        by_scope = {scope: float(total_kg) for scope, total_kg in scope_results if scope}
        
        # Activity count
        activity_count = self.db.query(func.count(EmissionActivity.id)).join(
            Project
        ).filter(
            Project.organization_id == self.organization_id
        ).scalar() or 0
        
        # Open findings count
        findings_count = self.db.query(func.count(FlaggedEvent.id)).filter(
            FlaggedEvent.organization_id == self.organization_id,
            FlaggedEvent.status == "open"
        ).scalar() or 0
        
        # Active targets count
        targets_count = self.db.query(func.count(ReductionTarget.id)).filter(
            ReductionTarget.organization_id == self.organization_id,
            ReductionTarget.is_active == True
        ).scalar() or 0
        
        # Get archetype info
        archetype = org.emission_archetype if org else None
        archetype_info = get_archetype(archetype) if archetype else None
        
        return {
            "org_id": str(self.organization_id),
            "org_name": org.name if org else "Unknown",
            "industry": org.industry if org else None,
            "archetype": archetype,
            "archetype_display": archetype_info.display_name if archetype_info else None,
            "total_emissions": float(total) if total else 0.0,
            "by_scope": by_scope,
            "activity_count": activity_count,
            "open_findings": findings_count,
            "active_targets": targets_count
        }
    
    async def _generate_sql_with_llm(self, message: str, context: Dict) -> Dict[str, Any]:
        """Use Groq to understand intent and generate safe SQL"""
        
        prompt = f"""You are Carbon Copilot, a carbon accounting assistant for {context.get('org_name', 'this organization')}.

{DATABASE_SCHEMA}

ORGANIZATION CONTEXT:
- Organization ID: {context.get('org_id')}
- Total Emissions: {context.get('total_emissions', 0):,.0f} kg CO2e
- Activity Count: {context.get('activity_count', 0)}
- Open Findings: {context.get('open_findings', 0)}
- Active Targets: {context.get('active_targets', 0)}

CRITICAL SQL RULES - YOU MUST FOLLOW THESE EXACTLY:
1. ONLY generate SELECT queries (read-only)
2. For emission_activities, you MUST JOIN with projects table:
   SELECT ea.* FROM emission_activities ea 
   JOIN projects p ON p.id = ea.project_id 
   WHERE p.organization_id = '{context.get('org_id')}'
3. For flagged_events and reduction_targets, filter directly:
   WHERE organization_id = '{context.get('org_id')}'
4. Use LIMIT 50 maximum
5. Return null for sql_query if no query needed

EXAMPLE QUERIES:

Query for specific activity type (e.g., "natural gas", "electricity", "fuel", "travel"):
SELECT ea.activity_type, ea.description, ea.co2e_kg, ea.scope, ea.activity_date 
FROM emission_activities ea 
JOIN projects p ON p.id = ea.project_id 
WHERE p.organization_id = '{context.get('org_id')}' 
AND (ea.activity_type ILIKE '%natural_gas%' OR ea.description ILIKE '%natural gas%')
LIMIT 50

Query for top emissions:
SELECT ea.activity_type, ea.description, ea.co2e_kg, ea.scope 
FROM emission_activities ea 
JOIN projects p ON p.id = ea.project_id 
WHERE p.organization_id = '{context.get('org_id')}' 
ORDER BY ea.co2e_kg DESC LIMIT 10

Query for anomalies:
SELECT title, description, recommendation, severity, flag_type 
FROM flagged_events 
WHERE organization_id = '{context.get('org_id')}' AND status = 'open' 
LIMIT 50

USER QUESTION: {message}

Respond with valid JSON only:
{{
  "intent": "brief description (e.g., 'activity_query', 'top_emissions', 'anomalies', 'targets')",
  "sql_query": "SELECT ... FROM ... WHERE ... LIMIT 50" or null,
  "explanation": "what this query does"
}}"""

        try:
            if not self.groq_client:
                return {"intent": "error", "sql_query": None, "explanation": "Groq client unavailable"}
            
            response = self.groq_client.chat.completions.create(
                model=settings.COPILOT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            logger.info(f"LLM generated intent: {result.get('intent')}, SQL: {result.get('sql_query', 'None')[:100] if result.get('sql_query') else 'None'}")
            
            return result
            
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return {"intent": "error", "sql_query": None, "explanation": f"Failed to understand: {e}"}
    
    def _execute_safe_query(self, sql: str) -> Tuple[List[Dict], Optional[str]]:
        """Execute validated read-only query with safety checks"""
        
        if not sql:
            return [], None
        
        sql_upper = sql.upper()
        
        # Check for blocked operations
        for blocked in SQL_BLOCKLIST:
            if blocked in sql_upper:
                return [], f"Blocked operation detected: {blocked}"
        
        # Must be a SELECT
        if not sql_upper.strip().startswith('SELECT'):
            return [], "Only SELECT queries are allowed"
        
        # Check for organization filter (security)
        org_id_str = str(self.organization_id)
        if org_id_str not in sql:
            return [], "Query must filter by organization_id"
        
        # Add LIMIT if not present
        if 'LIMIT' not in sql_upper:
            sql = sql.rstrip(';') + ' LIMIT 50'
        
        try:
            result = self.db.execute(text(sql))
            rows = result.fetchall()
            columns = result.keys()
            
            # Convert to list of dicts
            data = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Handle special types
                    if isinstance(value, Decimal):
                        value = float(value)
                    elif isinstance(value, datetime):
                        value = value.isoformat()
                    elif isinstance(value, UUID):
                        value = str(value)
                    row_dict[col] = value
                data.append(row_dict)
            
            logger.info(f"Query executed successfully, returned {len(data)} rows")
            return data, None
            
        except SQLAlchemyError as e:
            logger.error(f"Query execution error: {e}")
            return [], f"Query error: {str(e)[:100]}"
    
    async def _generate_response_with_llm(
        self,
        message: str,
        context: Dict,
        query_data: List[Dict],
        query_error: Optional[str],
        intent: str
    ) -> str:
        """Generate natural language response using Groq"""
        
        # Build data summary
        data_summary = ""
        if query_error:
            data_summary = f"Query failed: {query_error}"
        elif query_data:
            # Summarize first few rows
            sample = query_data[:10]
            data_summary = f"Query returned {len(query_data)} results:\n{json.dumps(sample, indent=2, default=str)}"
        else:
            data_summary = "No specific query data retrieved."
        
        prompt = f"""You are Carbon Copilot for {context.get('org_name')}.

ORGANIZATION SUMMARY:
- Total Emissions: {context.get('total_emissions', 0):,.0f} kg CO2e
- Scope Breakdown: {json.dumps(context.get('by_scope', {}), default=str)}
- Activities: {context.get('activity_count', 0)}
- Open Findings: {context.get('open_findings', 0)}
- Active Targets: {context.get('active_targets', 0)}

QUERY RESULTS:
{data_summary}

USER QUESTION: {message}

INSTRUCTIONS:
- Answer the question directly based on the data above
- NEVER make up numbers - only use provided data
- Be concise (2-4 sentences)
- If this is about anomalies/findings, explain what the issue is and how to fix it
- For emission_factor_missing findings, guide user on valid activity format for Climatiq calculation
- Use metrics and specifics when available

Respond naturally:"""

        try:
            if not self.groq_client:
                return "I'm unable to generate a response at this time."
            
            response = self.groq_client.chat.completions.create(
                model=settings.COPILOT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            
            # Fallback response
            if query_data:
                return f"Found {len(query_data)} results for your query. Total emissions: {context.get('total_emissions', 0):,.0f} kg CO2e."
            return f"Your organization has {context.get('total_emissions', 0):,.0f} kg CO2e total emissions across {context.get('activity_count', 0)} activities."
    
    def _get_suggestions(self, intent: str, data: List[Dict]) -> List[str]:
        """Generate follow-up suggestions based on context"""
        suggestions = []
        
        if intent in ["top_emissions", "scope_breakdown", "unknown"]:
            suggestions.append("What are my anomalies?")
            suggestions.append("How are my reduction targets?")
        elif intent in ["anomalies", "findings"]:
            suggestions.append("Show my top emissions")
            suggestions.append("What's my Scope 3 breakdown?")
        elif intent in ["targets", "reduction"]:
            suggestions.append("What activities contribute most?")
            suggestions.append("Any issues to address?")
        else:
            suggestions.append("What are my total emissions?")
            suggestions.append("Show my anomalies")
        
        return suggestions[:3]


def create_copilot_service(db: Session, organization_id: UUID, redis_client=None) -> CopilotService:
    """Factory function for CopilotService"""
    return CopilotService(db, organization_id, redis_client)
