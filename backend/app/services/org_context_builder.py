"""
Organization Context Builder Service
Builds comprehensive organization context for AI prompt injection

Features:
- Stratified activity sampling (top 10 + random mid + recent + suspects)
- Aggregates computation (by scope, type, month, project)
- Reduction target context with progress
- Regional factor integration
- Flag history for context
"""

import logging
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import UUID
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.activity import EmissionActivity
from app.models.project import Project
from app.models.organization import Organization
from app.models.reduction_target import ReductionTarget
from app.models.flagged_event import FlaggedEvent
from app.models.regional_factor import RegionalFactor
from app.core.archetype_config import get_archetype

logger = logging.getLogger(__name__)


@dataclass
class ActivitySample:
    """Represents a sampled activity for AI context"""
    id: str
    activity_type: str
    sub_type: Optional[str]
    scope: str
    co2e_kg: float
    activity_date: str
    description: str
    amount: Optional[float]
    unit: Optional[str]
    region: Optional[str]
    pct_of_total: float
    sample_category: str  # "top_emitter", "random_mid", "recent", "previously_flagged"
    emission_factor_id: Optional[str] = None
    source_dataset: Optional[str] = None


@dataclass
class ScopeAggregates:
    """Aggregated emissions by scope"""
    scope1_kg: float = 0.0
    scope2_kg: float = 0.0
    scope3_kg: float = 0.0
    total_kg: float = 0.0
    
    @property
    def scope1_pct(self) -> float:
        return (self.scope1_kg / self.total_kg * 100) if self.total_kg > 0 else 0.0
    
    @property
    def scope2_pct(self) -> float:
        return (self.scope2_kg / self.total_kg * 100) if self.total_kg > 0 else 0.0
    
    @property
    def scope3_pct(self) -> float:
        return (self.scope3_kg / self.total_kg * 100) if self.total_kg > 0 else 0.0


@dataclass
class TypeAggregates:
    """Aggregated emissions by activity type"""
    by_type: Dict[str, float] = field(default_factory=dict)
    by_type_pct: Dict[str, float] = field(default_factory=dict)


@dataclass
class TrendData:
    """Month-over-month and year-over-year trends"""
    mom_change_pct: Optional[float] = None  # Month over month
    yoy_change_pct: Optional[float] = None  # Year over year
    top_growing_types: List[Dict[str, Any]] = field(default_factory=list)
    top_declining_types: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TargetContext:
    """Reduction target context for AI"""
    target_id: str
    name: str
    target_type: str
    scope: Optional[str]
    baseline_year: str
    baseline_value: float
    target_year: str
    target_value: float
    current_value: Optional[float]
    progress_pct: Optional[float]
    status: str


@dataclass
class FlagContext:
    """Recent flag context for AI"""
    flag_id: str
    flag_type: str
    severity: str
    rule_id: str
    title: str
    status: str
    activity_id: Optional[str]
    created_at: str
    resolved_at: Optional[str]
    ai_verdict: Optional[str]


@dataclass
class OrgContext:
    """
    Complete organization context for AI prompt injection
    
    This dataclass contains all the rich context needed for
    generating high-quality AI responses.
    """
    # Organization basics
    org_id: str
    org_name: str
    country: Optional[str]
    industry: Optional[str]
    archetype: Optional[str]
    archetype_display_name: Optional[str]
    
    # Time period
    period_start: str
    period_end: str
    
    # Aggregates
    scope_aggregates: ScopeAggregates
    type_aggregates: TypeAggregates
    
    # Top contributors (with % of total)
    top_contributors: List[Dict[str, Any]]
    
    # Trends
    trends: TrendData
    
    # Stratified samples
    stratified_activities: List[ActivitySample]
    
    # Reduction targets
    active_targets: List[TargetContext]
    
    # Recent flags
    recent_flags: List[FlagContext]
    
    # Regional context
    regional_context: Optional[Dict[str, Any]]
    
    # Archetype fingerprint
    archetype_context: Optional[Dict[str, Any]]
    
    def to_ai_payload(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for AI prompt injection"""
        return {
            "org_id": self.org_id,
            "org_name": self.org_name,
            "country": self.country,
            "industry": self.industry,
            "archetype": self.archetype,
            "archetype_display_name": self.archetype_display_name,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "aggregates": {
                "scope1_kg": round(self.scope_aggregates.scope1_kg, 2),
                "scope1_pct": round(self.scope_aggregates.scope1_pct, 1),
                "scope2_kg": round(self.scope_aggregates.scope2_kg, 2),
                "scope2_pct": round(self.scope_aggregates.scope2_pct, 1),
                "scope3_kg": round(self.scope_aggregates.scope3_kg, 2),
                "scope3_pct": round(self.scope_aggregates.scope3_pct, 1),
                "total_kg": round(self.scope_aggregates.total_kg, 2),
            },
            "type_breakdown": self.type_aggregates.by_type_pct,
            "top_contributors": self.top_contributors[:10],
            "trends": {
                "mom_change_pct": self.trends.mom_change_pct,
                "yoy_change_pct": self.trends.yoy_change_pct,
                "top_growing": self.trends.top_growing_types[:3],
                "top_declining": self.trends.top_declining_types[:3],
            },
            "sample_activities": [
                {
                    "id": a.id,
                    "type": a.activity_type,
                    "scope": a.scope,
                    "co2e_kg": round(a.co2e_kg, 2),
                    "date": a.activity_date,
                    "description": a.description[:100] if a.description else "",
                    "amount": a.amount,
                    "unit": a.unit,
                    "region": a.region,
                    "pct_of_total": round(a.pct_of_total, 2),
                    "category": a.sample_category,
                    "ef_id": a.emission_factor_id,
                }
                for a in self.stratified_activities
            ],
            "reduction_targets": [
                {
                    "id": t.target_id,
                    "name": t.name,
                    "type": t.target_type,
                    "scope": t.scope,
                    "baseline": f"{t.baseline_value:,.0f} kg ({t.baseline_year})",
                    "target": f"{t.target_value}{'%' if t.target_type == 'percentage' else ' kg'} ({t.target_year})",
                    "current": f"{t.current_value:,.0f} kg" if t.current_value else "Not calculated",
                    "progress": f"{t.progress_pct:.1f}%" if t.progress_pct else "N/A",
                    "status": t.status,
                }
                for t in self.active_targets
            ],
            "recent_flags": [
                {
                    "id": f.flag_id,
                    "type": f.flag_type,
                    "severity": f.severity,
                    "title": f.title,
                    "status": f.status,
                    "verdict": f.ai_verdict,
                    "created": f.created_at,
                }
                for f in self.recent_flags
            ],
            "regional_context": self.regional_context,
            "archetype_context": self.archetype_context,
        }
    
    def format_activities_for_prompt(self) -> str:
        """Format stratified activities as human-readable lines for prompt"""
        lines = []
        for a in self.stratified_activities:
            region_str = f" | region: {a.region}" if a.region else ""
            lines.append(
                f"{a.activity_date} | {a.activity_type} | {a.amount or 'N/A'} {a.unit or ''} | "
                f"{a.co2e_kg:,.2f} kgCO2e | {a.pct_of_total:.1f}% of total{region_str} | "
                f"[{a.sample_category}]"
            )
        return "\n".join(lines)
    
    def format_aggregates_for_prompt(self) -> str:
        """Format aggregates as readable text"""
        return f"""Total Emissions: {self.scope_aggregates.total_kg:,.0f} kgCO2e
- Scope 1: {self.scope_aggregates.scope1_kg:,.0f} kgCO2e ({self.scope_aggregates.scope1_pct:.1f}%)
- Scope 2: {self.scope_aggregates.scope2_kg:,.0f} kgCO2e ({self.scope_aggregates.scope2_pct:.1f}%)
- Scope 3: {self.scope_aggregates.scope3_kg:,.0f} kgCO2e ({self.scope_aggregates.scope3_pct:.1f}%)"""


class OrgContextBuilder:
    """
    Builds comprehensive organization context for AI prompt injection
    
    Features:
    - Stratified activity sampling (top 10 + random mid + recent + suspects)
    - Aggregates computation (by scope, type, month, project)
    - Reduction target context with progress
    - Regional factor integration
    - Flag history for context
    """
    
    def __init__(self, db: Session, organization_id: UUID):
        self.db = db
        self.organization_id = organization_id
        self._organization: Optional[Organization] = None
        self._activities: Optional[List[EmissionActivity]] = None
        self._total_co2e: float = 0.0
    
    @property
    def organization(self) -> Organization:
        """Lazy load organization"""
        if self._organization is None:
            self._organization = self.db.query(Organization).filter(
                Organization.id == self.organization_id
            ).first()
        return self._organization
    
    def build_context(self, project_id: Optional[UUID] = None) -> OrgContext:
        """
        Build comprehensive organization context
        
        Args:
            project_id: Optional specific project to scope context to
            
        Returns:
            OrgContext with all data for AI prompt injection
        """
        logger.info(f"Building org context for organization {self.organization_id}")
        
        # Load all activities once
        self._load_activities(project_id)
        
        # Calculate total for percentage calculations
        self._total_co2e = sum(float(a.co2e_kg or 0) for a in self._activities)
        
        # Get date range
        period_start, period_end = self._get_period_range()
        
        # Get archetype info
        archetype = self.organization.emission_archetype if self.organization else None
        archetype_info = get_archetype(archetype) if archetype else None
        
        return OrgContext(
            org_id=str(self.organization_id),
            org_name=self.organization.name if self.organization else "Unknown",
            country=self.organization.country if self.organization else None,
            industry=self.organization.industry if self.organization else None,
            archetype=archetype,
            archetype_display_name=archetype_info.display_name if archetype_info else None,
            period_start=period_start,
            period_end=period_end,
            scope_aggregates=self._compute_scope_aggregates(),
            type_aggregates=self._compute_type_aggregates(),
            top_contributors=self._get_top_contributors(limit=10),
            trends=self._compute_trends(),
            stratified_activities=self._get_stratified_samples(),
            active_targets=self._get_active_targets(),
            recent_flags=self._get_recent_flags(limit=6),
            regional_context=self._get_regional_context(),
            archetype_context=self._get_archetype_context(archetype_info),
        )
    
    def _load_activities(self, project_id: Optional[UUID] = None) -> None:
        """Load all activities for the organization"""
        query = self.db.query(EmissionActivity).join(Project).filter(
            Project.organization_id == self.organization_id
        )
        
        if project_id:
            query = query.filter(Project.id == project_id)
        
        self._activities = query.all()
        logger.info(f"Loaded {len(self._activities)} activities")
    
    def _get_period_range(self) -> tuple:
        """Get the date range of activities"""
        if not self._activities:
            now = datetime.utcnow()
            return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")
        
        dates = [a.activity_date for a in self._activities if a.activity_date]
        if not dates:
            now = datetime.utcnow()
            return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")
        
        return min(dates).strftime("%Y-%m-%d"), max(dates).strftime("%Y-%m-%d")
    
    def _compute_scope_aggregates(self) -> ScopeAggregates:
        """Compute emissions aggregated by scope"""
        aggregates = ScopeAggregates()
        
        for activity in self._activities:
            co2e = float(activity.co2e_kg or 0)
            if activity.scope == "Scope 1":
                aggregates.scope1_kg += co2e
            elif activity.scope == "Scope 2":
                aggregates.scope2_kg += co2e
            elif activity.scope == "Scope 3":
                aggregates.scope3_kg += co2e
        
        aggregates.total_kg = aggregates.scope1_kg + aggregates.scope2_kg + aggregates.scope3_kg
        return aggregates
    
    def _compute_type_aggregates(self) -> TypeAggregates:
        """Compute emissions aggregated by activity type"""
        by_type: Dict[str, float] = defaultdict(float)
        
        for activity in self._activities:
            co2e = float(activity.co2e_kg or 0)
            by_type[activity.activity_type] += co2e
        
        # Calculate percentages
        by_type_pct = {}
        if self._total_co2e > 0:
            for atype, value in by_type.items():
                by_type_pct[atype] = round(value / self._total_co2e * 100, 1)
        
        return TypeAggregates(by_type=dict(by_type), by_type_pct=by_type_pct)
    
    def _get_top_contributors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top N activities by CO2e contribution"""
        sorted_activities = sorted(
            self._activities,
            key=lambda a: float(a.co2e_kg or 0),
            reverse=True
        )[:limit]
        
        contributors = []
        for i, activity in enumerate(sorted_activities):
            co2e = float(activity.co2e_kg or 0)
            pct = (co2e / self._total_co2e * 100) if self._total_co2e > 0 else 0
            input_data = activity.input_data or {}
            
            contributors.append({
                "rank": i + 1,
                "activity_id": str(activity.id),
                "activity_type": activity.activity_type,
                "scope": activity.scope,
                "co2e_kg": round(co2e, 2),
                "pct_of_total": round(pct, 2),
                "description": input_data.get("description", "")[:50],
                "date": activity.activity_date.strftime("%Y-%m-%d") if activity.activity_date else None,
            })
        
        return contributors
    
    def _compute_trends(self) -> TrendData:
        """Compute MoM and YoY trends"""
        if not self._activities:
            return TrendData()
        
        # Group by month
        by_month: Dict[str, float] = defaultdict(float)
        by_type_month: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        for activity in self._activities:
            if not activity.activity_date:
                continue
            month_key = activity.activity_date.strftime("%Y-%m")
            co2e = float(activity.co2e_kg or 0)
            by_month[month_key] += co2e
            by_type_month[activity.activity_type][month_key] += co2e
        
        if not by_month:
            return TrendData()
        
        # Sort months
        sorted_months = sorted(by_month.keys())
        
        # MoM change (last two months)
        mom_change = None
        if len(sorted_months) >= 2:
            last_month = by_month[sorted_months[-1]]
            prev_month = by_month[sorted_months[-2]]
            if prev_month > 0:
                mom_change = round((last_month - prev_month) / prev_month * 100, 1)
        
        # YoY change
        yoy_change = None
        if len(sorted_months) >= 12:
            current = by_month[sorted_months[-1]]
            year_ago = by_month[sorted_months[-12]]
            if year_ago > 0:
                yoy_change = round((current - year_ago) / year_ago * 100, 1)
        
        # Find growing and declining types
        type_changes = []
        for atype, months_data in by_type_month.items():
            sorted_type_months = sorted(months_data.keys())
            if len(sorted_type_months) >= 2:
                last = months_data[sorted_type_months[-1]]
                prev = months_data[sorted_type_months[-2]]
                if prev > 0:
                    change = (last - prev) / prev * 100
                    type_changes.append({"type": atype, "change_pct": round(change, 1)})
        
        type_changes.sort(key=lambda x: x["change_pct"], reverse=True)
        
        return TrendData(
            mom_change_pct=mom_change,
            yoy_change_pct=yoy_change,
            top_growing_types=type_changes[:3],
            top_declining_types=type_changes[-3:][::-1] if len(type_changes) >= 3 else [],
        )
    
    def _get_stratified_samples(self) -> List[ActivitySample]:
        """
        Get stratified sample of activities:
        - Top 10 emitters
        - 5 random mid-range emitters
        - 5 most recent activities
        - 5 previously flagged activities
        """
        samples: List[ActivitySample] = []
        used_ids = set()
        
        # 1. Top 10 emitters
        sorted_by_co2e = sorted(
            self._activities,
            key=lambda a: float(a.co2e_kg or 0),
            reverse=True
        )
        
        for activity in sorted_by_co2e[:10]:
            if activity.id not in used_ids:
                samples.append(self._activity_to_sample(activity, "top_emitter"))
                used_ids.add(activity.id)
        
        # 2. 5 random mid-range emitters (25th-75th percentile)
        if len(sorted_by_co2e) > 20:
            mid_start = len(sorted_by_co2e) // 4
            mid_end = 3 * len(sorted_by_co2e) // 4
            mid_range = [a for a in sorted_by_co2e[mid_start:mid_end] if a.id not in used_ids]
            
            for activity in random.sample(mid_range, min(5, len(mid_range))):
                samples.append(self._activity_to_sample(activity, "random_mid"))
                used_ids.add(activity.id)
        
        # 3. 5 most recent activities
        sorted_by_date = sorted(
            [a for a in self._activities if a.activity_date],
            key=lambda a: a.activity_date,
            reverse=True
        )
        
        for activity in sorted_by_date[:5]:
            if activity.id not in used_ids:
                samples.append(self._activity_to_sample(activity, "recent"))
                used_ids.add(activity.id)
        
        # 4. 5 previously flagged activities
        flagged_activity_ids = self.db.query(FlaggedEvent.activity_id).filter(
            FlaggedEvent.organization_id == self.organization_id,
            FlaggedEvent.activity_id.isnot(None)
        ).order_by(desc(FlaggedEvent.created_at)).limit(10).all()
        
        flagged_ids = {f[0] for f in flagged_activity_ids}
        flagged_activities = [a for a in self._activities if a.id in flagged_ids and a.id not in used_ids]
        
        for activity in flagged_activities[:5]:
            samples.append(self._activity_to_sample(activity, "previously_flagged"))
            used_ids.add(activity.id)
        
        return samples
    
    def _activity_to_sample(self, activity: EmissionActivity, category: str) -> ActivitySample:
        """Convert activity to sample dataclass"""
        co2e = float(activity.co2e_kg or 0)
        pct = (co2e / self._total_co2e * 100) if self._total_co2e > 0 else 0
        input_data = activity.input_data or {}
        
        return ActivitySample(
            id=str(activity.id),
            activity_type=activity.activity_type,
            sub_type=activity.sub_type,
            scope=activity.scope,
            co2e_kg=co2e,
            activity_date=activity.activity_date.strftime("%Y-%m-%d") if activity.activity_date else "",
            description=input_data.get("description", ""),
            amount=input_data.get("amount"),
            unit=input_data.get("unit"),
            region=activity.region,
            pct_of_total=pct,
            sample_category=category,
            emission_factor_id=activity.emission_factor_id,
            source_dataset=activity.source_dataset,
        )
    
    def _get_active_targets(self) -> List[TargetContext]:
        """Get active reduction targets with progress"""
        targets = self.db.query(ReductionTarget).filter(
            ReductionTarget.organization_id == self.organization_id,
            ReductionTarget.is_active == True
        ).order_by(desc(ReductionTarget.created_at)).limit(5).all()
        
        return [
            TargetContext(
                target_id=str(t.id),
                name=t.name,
                target_type=t.target_type,
                scope=t.scope,
                baseline_year=t.baseline_year,
                baseline_value=float(t.baseline_value),
                target_year=t.target_year,
                target_value=float(t.target_value),
                current_value=float(t.current_value) if t.current_value else None,
                progress_pct=float(t.progress_percentage) if t.progress_percentage else None,
                status=t.status,
            )
            for t in targets
        ]
    
    def _get_recent_flags(self, limit: int = 6) -> List[FlagContext]:
        """Get recent flagged events"""
        flags = self.db.query(FlaggedEvent).filter(
            FlaggedEvent.organization_id == self.organization_id
        ).order_by(desc(FlaggedEvent.created_at)).limit(limit).all()
        
        return [
            FlagContext(
                flag_id=str(f.id),
                flag_type=f.flag_type,
                severity=f.severity,
                rule_id=f.rule_id,
                title=f.title,
                status=f.status,
                activity_id=str(f.activity_id) if f.activity_id else None,
                created_at=f.created_at.strftime("%Y-%m-%d") if f.created_at else "",
                resolved_at=f.resolved_at.strftime("%Y-%m-%d") if f.resolved_at else None,
                ai_verdict=f.ai_verdict,
            )
            for f in flags
        ]
    
    def _get_regional_context(self) -> Optional[Dict[str, Any]]:
        """Get regional factors for the organization's country"""
        if not self.organization or not self.organization.country:
            return None
        
        regional_factor = self.db.query(RegionalFactor).filter(
            RegionalFactor.country_code == self.organization.country,
            RegionalFactor.is_active == True
        ).first()
        
        if not regional_factor:
            return None
        
        archetype = self.organization.emission_archetype
        return regional_factor.to_ai_context(archetype)
    
    def _get_archetype_context(self, archetype_info) -> Optional[Dict[str, Any]]:
        """Get archetype fingerprint context"""
        if not archetype_info:
            return None
        
        return {
            "name": archetype_info.name,
            "display_name": archetype_info.display_name,
            "industries": archetype_info.corresponding_industries,
            "expected_activity_types": archetype_info.expected_activity_types,
            "expected_scopes": archetype_info.expected_scopes,
            "expected_scope_distribution": archetype_info.scope_distribution,
            "key_emission_signals": archetype_info.key_emission_signals,
            "seasonal_patterns": archetype_info.seasonal_patterns,
            "thresholds": archetype_info.thresholds,
        }


def create_org_context_builder(db: Session, organization_id: UUID) -> OrgContextBuilder:
    """Factory function for OrgContextBuilder"""
    return OrgContextBuilder(db, organization_id)
