"""
Copilot Service
Context-aware Carbon Copilot with SQL-first responses and optional LLM explanation.

Design Principles:
1. Deterministic First: All facts come from SQL, never from LLM
2. LLM as Explainer: LLM only summarizes/explains structured data
3. Offline Fallback: Always works even when LLM unavailable
4. Budget Conscious: Respects Groq free tier limits
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models.activity import EmissionActivity
from app.models.project import Project
from app.models.reduction_target import ReductionTarget
from app.models.flagged_event import FlaggedEvent
from app.models.organization import Organization
from app.services.llm_router import LLMRouter, LLMTask, create_llm_router
from app.core.archetype_config import get_archetype

logger = logging.getLogger(__name__)


class Intent:
    """User intent categories"""
    TOTAL_EMISSIONS = "total_emissions"
    SCOPE_BREAKDOWN = "scope_breakdown"
    TREND = "trend"
    TARGET_PROGRESS = "target_progress"
    FINDINGS = "findings"
    EXPLAIN = "explain"
    SUGGEST = "suggest"
    DATA_STATUS = "data_status"
    PROJECTION = "projection"  # NEW: "What will my emissions be in 2030?"
    UNKNOWN = "unknown"


# Offline response templates (used when LLM unavailable)
OFFLINE_TEMPLATES = {
    Intent.TOTAL_EMISSIONS: "Your total emissions are {total:,.0f} kg CO₂e. {scope_breakdown}",
    Intent.SCOPE_BREAKDOWN: "Scope breakdown: {breakdown}",
    Intent.TREND: "Emissions {direction} by {pct:.1f}% compared to {period}.",
    Intent.TARGET_PROGRESS: "Target '{name}' is {progress:.0f}% complete. Status: {status}.",
    Intent.FINDINGS: "You have {count} open findings{critical_note}.",
    Intent.DATA_STATUS: "Data completeness: {completeness:.0f}%. {missing_note}",
    Intent.SUGGEST: "Based on your {archetype} profile, focus areas include: {areas}.",
    Intent.UNKNOWN: "I found the following data: {data}"
}

# Intent detection keywords
INTENT_KEYWORDS = {
    Intent.TOTAL_EMISSIONS: ["total", "emissions", "how much", "co2", "carbon footprint"],
    Intent.SCOPE_BREAKDOWN: ["scope", "breakdown", "by scope", "scope 1", "scope 2", "scope 3"],
    Intent.TREND: ["trend", "increasing", "decreasing", "change", "compared to", "over time"],
    Intent.TARGET_PROGRESS: ["target", "goal", "progress", "on track", "reduction target"],
    Intent.FINDINGS: ["finding", "anomaly", "issue", "problem", "alert", "warning"],
    Intent.EXPLAIN: ["explain", "why", "what does", "tell me about", "analyze"],
    Intent.SUGGEST: ["suggest", "recommend", "should i", "how can i", "what can i do", "reduce", "biggest", "largest", "top", "sources", "main", "major"],
    Intent.DATA_STATUS: ["data", "complete", "missing", "upload", "coverage"],
    Intent.PROJECTION: ["project", "forecast", "predict", "future", "will be", "2025", "2030", "next year"],
}


class CopilotService:
    """
    Context-aware Carbon Copilot Service
    
    Features:
    - SQL-first data retrieval (100% deterministic)
    - Intent classification (keyword-based, no LLM)
    - Optional LLM explanation (user-triggered, cached)
    - Graceful offline fallback
    """
    
    def __init__(self, db: Session, organization_id: UUID, redis_client=None):
        self.db = db
        self.organization_id = organization_id
        self.llm_router = create_llm_router(redis_client=redis_client, org_id=organization_id)
        self._organization = None
    
    @property
    def organization(self) -> Organization:
        if self._organization is None:
            self._organization = self.db.query(Organization).filter(
                Organization.id == self.organization_id
            ).first()
        return self._organization
    
    async def chat(
        self,
        message: str,
        history: Optional[List[Dict]] = None,
        include_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Process a chat message and return LLM-generated response with RAG context.
        
        Architecture: LLM-first with deterministic fallback
        1. Classify intent (keyword-based)
        2. Gather relevant facts from database (RAG context)
        3. Generate response via Groq LLM using facts as context
        4. Fallback to deterministic response only if LLM fails
        
        Args:
            message: User's chat message
            history: Previous conversation messages
            include_llm: Whether to use LLM (True by default)
            
        Returns:
            Response dict with text, data, and metadata
        """
        history = history or []
        
        # 1. Classify intent (deterministic - for data gathering)
        intent = self._classify_intent(message)
        logger.info(f"Copilot intent classified: {intent}")
        
        # 2. Gather comprehensive facts from SQL for RAG context
        facts = await self._get_facts_for_intent(intent)
        
        # 3. Prepare fallback response (used only if LLM fails)
        fallback_response = self._format_offline_response(intent, facts)
        
        response = {
            "text": fallback_response,
            "intent": intent,
            "data": facts,
            "source": "deterministic",
            "model": None,
            "suggestions": self._get_quick_suggestions(intent, facts)
        }
        
        # 4. PRIMARY: Generate response via Groq LLM with RAG context
        if include_llm:
            try:
                llm_response = await self._get_llm_explanation(message, facts, intent)
                
                if llm_response and llm_response.text:
                    response["text"] = llm_response.text
                    response["source"] = llm_response.source
                    response["model"] = llm_response.model
                else:
                    logger.warning("LLM returned empty response, using fallback")
            except Exception as e:
                logger.error(f"LLM call failed, using fallback: {e}")
                response["source"] = "error_fallback"
        
        return response
    
    def _classify_intent(self, message: str) -> str:
        """Classify user intent using keyword matching (no LLM)"""
        message_lower = message.lower()
        
        # Score each intent based on keyword matches
        scores = {}
        for intent, keywords in INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in message_lower)
            if score > 0:
                scores[intent] = score
        
        if not scores:
            return Intent.UNKNOWN
        
        # Return highest scoring intent
        return max(scores, key=scores.get)
    
    async def _get_facts_for_intent(self, intent: str) -> Dict[str, Any]:
        """Get relevant facts from database based on intent"""
        facts = {
            "organization": self.organization.name if self.organization else "Unknown",
            "archetype": self.organization.emission_archetype if self.organization else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Always include total emissions
        total = self._get_total_emissions()
        facts["total_emissions"] = total
        
        # Always include archetype info for RAG context
        facts["archetype_info"] = self._get_archetype_info()
        facts["org_profile"] = self._get_org_profile()
        
        if intent in [Intent.TOTAL_EMISSIONS, Intent.SCOPE_BREAKDOWN, Intent.EXPLAIN]:
            facts["by_scope"] = self._get_scope_breakdown()
            facts["by_category"] = self._get_category_breakdown()
        
        if intent == Intent.TREND:
            facts["trend"] = self._get_emission_trend()
        
        if intent == Intent.TARGET_PROGRESS:
            facts["targets"] = self._get_active_targets()
        
        if intent == Intent.FINDINGS:
            facts["findings"] = self._get_findings_summary()
            facts["recent_anomalies"] = self._get_recent_anomalies(limit=5)
        
        if intent == Intent.DATA_STATUS:
            facts["completeness"] = self._get_data_completeness()
        
        if intent == Intent.SUGGEST:
            facts["top_sources"] = self._get_top_emission_sources()
        
        if intent == Intent.PROJECTION:
            facts["targets"] = self._get_active_targets()
            facts["projections"] = self._get_projection_data()
            facts["trend"] = self._get_emission_trend()
        
        return facts
    
    def _get_total_emissions(self) -> float:
        """Get total emissions for organization"""
        result = self.db.query(func.sum(EmissionActivity.co2e_kg)).join(
            Project
        ).filter(
            Project.organization_id == self.organization_id
        ).scalar()
        return float(result) if result else 0.0
    
    def _get_scope_breakdown(self) -> Dict[str, float]:
        """Get emissions breakdown by scope"""
        results = self.db.query(
            EmissionActivity.scope,
            func.sum(EmissionActivity.co2e_kg)
        ).join(Project).filter(
            Project.organization_id == self.organization_id
        ).group_by(EmissionActivity.scope).all()
        
        return {scope: float(total) for scope, total in results if scope}
    
    def _get_category_breakdown(self) -> Dict[str, float]:
        """Get emissions breakdown by activity type"""
        results = self.db.query(
            EmissionActivity.activity_type,
            func.sum(EmissionActivity.co2e_kg)
        ).join(Project).filter(
            Project.organization_id == self.organization_id
        ).group_by(EmissionActivity.activity_type).all()
        
        return {cat: float(total) for cat, total in results if cat}
    
    def _get_emission_trend(self) -> Dict[str, Any]:
        """Get emission trend (compare current quarter to previous)"""
        now = datetime.utcnow()
        current_quarter_start = datetime(now.year, ((now.month - 1) // 3) * 3 + 1, 1)
        prev_quarter_start = current_quarter_start - timedelta(days=90)
        
        def get_quarter_total(start, end):
            result = self.db.query(func.sum(EmissionActivity.co2e_kg)).join(
                Project
            ).filter(
                Project.organization_id == self.organization_id,
                EmissionActivity.activity_date >= start,
                EmissionActivity.activity_date < end
            ).scalar()
            return float(result) if result else 0
        
        current = get_quarter_total(current_quarter_start, now)
        previous = get_quarter_total(prev_quarter_start, current_quarter_start)
        
        if previous > 0:
            change_pct = ((current - previous) / previous) * 100
        else:
            change_pct = 0
        
        return {
            "current_period": current,
            "previous_period": previous,
            "change_pct": round(change_pct, 1),
            "direction": "increased" if change_pct > 5 else "decreased" if change_pct < -5 else "stable",
            "period": "quarter"
        }
    
    def _get_active_targets(self) -> List[Dict[str, Any]]:
        """Get active reduction targets with detailed progress"""
        targets = self.db.query(ReductionTarget).filter(
            ReductionTarget.organization_id == self.organization_id,
            ReductionTarget.is_active == True
        ).limit(5).all()
        
        return [
            {
                "name": t.name,
                "progress": float(t.progress_percentage) if t.progress_percentage else 0,
                "status": t.status,
                "target_year": t.target_year,
                "baseline_year": t.baseline_year,
                "baseline_value": float(t.baseline_value) if t.baseline_value else 0,
                "target_value": float(t.target_value) if t.target_value else 0,
                "current_value": float(t.current_value) if t.current_value else None,
                "current_reduction_pct": float(t.current_reduction_pct) if t.current_reduction_pct else None,
                "target_type": t.target_type,
                "scope": t.scope
            }
            for t in targets
        ]
    
    def _get_findings_summary(self) -> Dict[str, Any]:
        """Get summary of audit findings"""
        open_count = self.db.query(func.count(FlaggedEvent.id)).filter(
            FlaggedEvent.organization_id == self.organization_id,
            FlaggedEvent.status == "open"
        ).scalar() or 0
        
        critical_count = self.db.query(func.count(FlaggedEvent.id)).filter(
            FlaggedEvent.organization_id == self.organization_id,
            FlaggedEvent.status == "open",
            FlaggedEvent.severity == "critical"
        ).scalar() or 0
        
        return {
            "open": open_count,
            "critical": critical_count,
            "has_critical": critical_count > 0
        }
    
    def _get_data_completeness(self) -> Dict[str, Any]:
        """Get data completeness metrics"""
        activity_count = self.db.query(func.count(EmissionActivity.id)).join(
            Project
        ).filter(
            Project.organization_id == self.organization_id
        ).scalar() or 0
        
        # Get months with data
        months_with_data = self.db.query(
            func.distinct(func.date_trunc('month', EmissionActivity.activity_date))
        ).join(Project).filter(
            Project.organization_id == self.organization_id
        ).count()
        
        # Calculate completeness score
        completeness = min((activity_count / 50) * 100, 100)  # 50 activities = 100%
        
        return {
            "activity_count": activity_count,
            "months_with_data": months_with_data,
            "completeness_pct": round(completeness, 1),
            "is_complete": completeness >= 80
        }
    
    def _get_org_profile(self) -> Dict[str, Any]:
        """Get organization profile for context"""
        if not self.organization:
            return {}
        return {
            "name": self.organization.name,
            "industry": self.organization.industry,
            "country": self.organization.country,
            "emission_archetype": self.organization.emission_archetype
        }
    
    def _get_projection_data(self) -> Dict[str, Any]:
        """Get trajectory projections for active targets"""
        try:
            from app.services.trajectory_service import create_trajectory_service
            trajectory_service = create_trajectory_service(self.db, self.organization_id)
            
            # Get all target trajectories
            trajectories = trajectory_service.get_all_target_trajectories()
            return {
                "projections": trajectories,
                "has_projections": len(trajectories) > 0
            }
        except Exception as e:
            logger.warning(f"Failed to get projection data: {e}")
            return {"projections": [], "has_projections": False}
    
    def _get_recent_anomalies(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent flagged events/anomalies for context"""
        events = self.db.query(FlaggedEvent).filter(
            FlaggedEvent.organization_id == self.organization_id,
            FlaggedEvent.status == "open"
        ).order_by(FlaggedEvent.created_at.desc()).limit(limit).all()
        
        return [
            {
                "title": e.title,
                "severity": e.severity,
                "flag_type": e.flag_type,
                "description": e.description[:200] if e.description else None
            }
            for e in events
        ]
    
    def _get_top_emission_sources(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top emission sources"""
        results = self.db.query(
            EmissionActivity.activity_type,
            func.sum(EmissionActivity.co2e_kg).label('total')
        ).join(Project).filter(
            Project.organization_id == self.organization_id
        ).group_by(
            EmissionActivity.activity_type
        ).order_by(
            func.sum(EmissionActivity.co2e_kg).desc()
        ).limit(limit).all()
        
        total = self._get_total_emissions()
        
        return [
            {
                "source": activity_type,
                "emissions": float(emissions),
                "percentage": round((float(emissions) / total) * 100, 1) if total > 0 else 0
            }
            for activity_type, emissions in results
        ]
    
    def _get_archetype_info(self) -> Optional[Dict[str, Any]]:
        """Get detailed archetype-specific information from config"""
        archetype = self.organization.emission_archetype if self.organization else None
        if not archetype:
            return None
        
        fingerprint = get_archetype(archetype)
        if not fingerprint:
            return None
        
        # Return full fingerprint for rich RAG context
        return {
            "name": fingerprint.display_name,
            "archetype_id": fingerprint.name,
            "industries": fingerprint.corresponding_industries,
            "expected_activity_types": fingerprint.expected_activity_types,
            "expected_scopes": fingerprint.expected_scopes,
            "scope_distribution": fingerprint.scope_distribution,
            "key_emission_signals": fingerprint.key_emission_signals,
            "seasonal_patterns": fingerprint.seasonal_patterns,
            "thresholds": fingerprint.thresholds
        }
    
    def _format_offline_response(self, intent: str, facts: Dict[str, Any]) -> str:
        """Format a deterministic response without LLM"""
        template = OFFLINE_TEMPLATES.get(intent, OFFLINE_TEMPLATES[Intent.UNKNOWN])
        
        try:
            if intent == Intent.TOTAL_EMISSIONS:
                by_scope = facts.get("by_scope", {})
                scope_str = ", ".join([f"{k}: {v:,.0f} kg" for k, v in by_scope.items()])
                return template.format(
                    total=facts.get("total_emissions", 0),
                    scope_breakdown=scope_str or "No scope breakdown available."
                )
            
            elif intent == Intent.SCOPE_BREAKDOWN:
                by_scope = facts.get("by_scope", {})
                breakdown = ", ".join([f"{k}: {v:,.0f} kg CO₂e" for k, v in by_scope.items()])
                return template.format(breakdown=breakdown or "No data available.")
            
            elif intent == Intent.TREND:
                trend = facts.get("trend", {})
                return template.format(
                    direction=trend.get("direction", "remained stable"),
                    pct=abs(trend.get("change_pct", 0)),
                    period=f"the previous {trend.get('period', 'period')}"
                )
            
            elif intent == Intent.TARGET_PROGRESS:
                targets = facts.get("targets", [])
                if targets:
                    t = targets[0]
                    return template.format(
                        name=t.get("name", "Target"),
                        progress=t.get("progress", 0),
                        status=t.get("status", "unknown")
                    )
                return "No active reduction targets found."
            
            elif intent == Intent.FINDINGS:
                findings = facts.get("findings", {})
                critical_note = f" ({findings.get('critical', 0)} critical)" if findings.get("has_critical") else ""
                return template.format(
                    count=findings.get("open", 0),
                    critical_note=critical_note
                )
            
            elif intent == Intent.DATA_STATUS:
                comp = facts.get("completeness", {})
                missing_note = ""
                if comp.get("completeness_pct", 0) < 80:
                    missing_note = "Consider uploading more data for a complete picture."
                return template.format(
                    completeness=comp.get("completeness_pct", 0),
                    missing_note=missing_note
                )
            
            elif intent == Intent.SUGGEST:
                archetype_info = facts.get("archetype_info", {})
                top_sources = facts.get("top_sources", [])
                areas = ", ".join([s["source"] for s in top_sources[:3]]) or "energy efficiency"
                return template.format(
                    archetype=archetype_info.get("name", "your") if archetype_info else "your",
                    areas=areas
                )
            
            else:
                # Unknown intent - return summary
                return f"Your total emissions are {facts.get('total_emissions', 0):,.0f} kg CO₂e."
                
        except Exception as e:
            logger.warning(f"Template formatting failed: {e}")
            return f"Your total emissions are {facts.get('total_emissions', 0):,.0f} kg CO₂e."
    
    def _should_use_llm(self, intent: str, history: List[Dict]) -> bool:
        """Determine if LLM should be used for this request"""
        # Use LLM for all meaningful intents to provide semantic responses
        # Only skip for UNKNOWN where we have no context
        if intent == Intent.UNKNOWN:
            return False
        
        # Limit LLM calls in conversation (max 2 per 5 messages to avoid quota issues)
        recent_llm = sum(1 for m in history[-5:] if m.get("source") == "llm")
        return recent_llm < 2
    
    async def _get_llm_explanation(
        self,
        message: str,
        facts: Dict[str, Any],
        intent: str
    ) -> Any:
        """Get LLM explanation for the facts"""
        
        # Build context-aware prompt
        prompt = self._build_explanation_prompt(message, facts)
        
        # Use cache key based on message and key facts
        cache_key = f"{self.organization_id}:{intent}:{facts.get('total_emissions', 0):.0f}"
        
        return await self.llm_router.call(
            task=LLMTask.CHAT_EXPLAIN,
            prompt=prompt,
            cache_key=cache_key
        )
    
    def _build_explanation_prompt(self, message: str, facts: Dict[str, Any]) -> str:
        """Build a comprehensive prompt for LLM with full RAG context"""
        
        # Build org profile section
        org_profile = facts.get("org_profile", {})
        org_section = f"""## Organization Profile
- Name: {org_profile.get('name', 'Unknown')}
- Industry: {org_profile.get('industry', 'Not specified')}
- Country: {org_profile.get('country', 'Not specified')}
- Archetype: {org_profile.get('emission_archetype', 'Not specified')}"""
        
        # Build archetype context section
        archetype_info = facts.get("archetype_info", {})
        archetype_section = ""
        if archetype_info:
            archetype_section = f"""
## Industry Archetype: {archetype_info.get('name', 'Unknown')}
- Typical Industries: {', '.join(archetype_info.get('industries', [])[:3])}
- Expected Activity Types: {', '.join(archetype_info.get('expected_activity_types', []))}
- Expected Scope Distribution: {json.dumps(archetype_info.get('scope_distribution', {}), default=str)}
- Key Emission Signals: {', '.join(archetype_info.get('key_emission_signals', [])[:4])}"""
        
        # Build targets section if available
        targets = facts.get("targets", [])
        targets_section = ""
        if targets:
            target_lines = []
            for t in targets[:3]:
                status = t.get('status', 'unknown')
                progress = t.get('progress', 0)
                target_lines.append(
                    f"  - {t.get('name')}: {progress:.0f}% complete, status={status}, target year={t.get('target_year')}"
                )
            targets_section = f"""
## Reduction Targets
{chr(10).join(target_lines)}"""
        
        # Build projections section if available
        projections = facts.get("projections", {})
        proj_section = ""
        if projections.get("has_projections"):
            proj_list = projections.get("projections", [])
            if proj_list:
                proj_lines = []
                for p in proj_list[:3]:
                    will_achieve = "WILL achieve" if p.get("status") == "on_track" else "may MISS"
                    proj_lines.append(f"  - {p.get('target_name', 'Target')}: {will_achieve} target at current rate")
                proj_section = f"""
## Trajectory Projections
{chr(10).join(proj_lines)}"""
        
        # Build anomalies section if available
        anomalies = facts.get("recent_anomalies", [])
        anomalies_section = ""
        if anomalies:
            anomaly_lines = [f"  - [{a.get('severity', 'info').upper()}] {a.get('title', 'Unknown')}" for a in anomalies[:3]]
            anomalies_section = f"""
## Recent Findings ({len(anomalies)} open)
{chr(10).join(anomaly_lines)}"""
        
        return f"""You are Carbon Copilot, an expert carbon accounting assistant for {org_profile.get('name', 'this organization')}. 
Based on the ACTUAL DATA below, answer the user's question with insight and context.

{org_section}
{archetype_section}

## Emissions Data (FACTS - do not hallucinate)
- Total Emissions: {facts.get('total_emissions', 0):,.0f} kg CO₂e
- Scope Breakdown: {json.dumps(facts.get('by_scope', {}), default=str)}
- Top Sources: {json.dumps(facts.get('top_sources', [])[:3], default=str)}
{targets_section}
{proj_section}
{anomalies_section}

## User Question
{message}

## Instructions
- ONLY use the data provided above - NEVER make up numbers
- Provide specific, actionable insights based on the organization's archetype and data
- Reference specific values when relevant
- Be concise but informative (2-4 sentences)
- If asked about projections/forecasts, use the trajectory data if available
"""
    
    def _get_quick_suggestions(self, intent: str, facts: Dict[str, Any]) -> List[str]:
        """Get follow-up suggestions based on context"""
        suggestions = []
        
        if facts.get("total_emissions", 0) == 0:
            suggestions.append("Upload emission data to get started")
        
        elif intent == Intent.TOTAL_EMISSIONS:
            suggestions.append("Show me the trend")
            suggestions.append("What are my biggest emission sources?")
        
        elif intent == Intent.TREND:
            suggestions.append("How can I reduce emissions?")
            suggestions.append("Show my targets")
        
        elif intent == Intent.TARGET_PROGRESS:
            targets = facts.get("targets", [])
            if any(t.get("status") == "at_risk" for t in targets):
                suggestions.append("Generate reduction strategies")
        
        elif intent == Intent.FINDINGS:
            findings = facts.get("findings", {})
            if findings.get("critical", 0) > 0:
                suggestions.append("Explain critical findings")
        
        return suggestions[:3]  # Max 3 suggestions


def create_copilot_service(db: Session, organization_id: UUID, redis_client=None) -> CopilotService:
    """Factory function for CopilotService"""
    return CopilotService(db, organization_id, redis_client)
