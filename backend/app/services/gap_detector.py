"""
Gap Detector Service
Detects missing or incomplete data based on expected patterns
"""

import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, date
from collections import defaultdict
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.models.activity import EmissionActivity
from app.models.project import Project
from app.core.archetype_config import get_archetype, ArchetypeFingerprint

logger = logging.getLogger(__name__)


class GapDetector:
    """
    Detects data gaps in emission activity data
    
    Gap Types:
    - Temporal: Missing months in reporting period
    - Scope Coverage: Expected scopes for archetype not present
    - Activity Type: Expected fingerprint activities missing
    """
    
    def __init__(self, db: Session, organization_id: UUID):
        self.db = db
        self.organization_id = organization_id
    
    def detect_all_gaps(
        self,
        project_id: Optional[UUID] = None,
        archetype: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Run all gap detection rules
        
        Args:
            project_id: Optional specific project to audit
            archetype: Organization's emission archetype
            
        Returns:
            List of gap findings
        """
        findings = []
        
        # Get activities scoped to organization
        query = self.db.query(EmissionActivity).join(Project).filter(
            Project.organization_id == self.organization_id
        )
        
        if project_id:
            query = query.filter(Project.id == project_id)
        
        activities = query.all()
        
        if not activities:
            findings.append({
                "flag_type": "gap",
                "severity": "critical",
                "rule_id": "no_data",
                "title": "No emission data found",
                "description": "No emission activities have been recorded for this organization/project.",
                "recommendation": "Upload emission activity data via CSV or manual entry.",
                "evidence": {"activity_count": 0}
            })
            return findings
        
        # Run detection rules
        findings.extend(self._detect_temporal_gaps(activities, project_id))
        findings.extend(self._detect_scope_coverage_gaps(activities, archetype))
        findings.extend(self._detect_activity_type_gaps(activities, archetype))
        
        return findings
    
    def _detect_temporal_gaps(
        self,
        activities: List[EmissionActivity],
        project_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect missing months in activity data
        
        Checks for gaps >= 2 months in recurring activity types
        """
        findings = []
        
        # Group activities by type and month
        activity_months: Dict[str, Set[tuple]] = defaultdict(set)  # {activity_type: {(year, month), ...}}
        
        for activity in activities:
            if activity.activity_date:
                key = (activity.activity_date.year, activity.activity_date.month)
                activity_months[activity.activity_type].add(key)
        
        # Recurring activity types that should appear monthly
        recurring_types = ["electricity", "stationary_combustion", "fuel"]
        
        for activity_type in recurring_types:
            if activity_type not in activity_months:
                continue
            
            months = sorted(activity_months[activity_type])
            if len(months) < 2:
                continue
            
            # Find gaps between consecutive months
            for i in range(1, len(months)):
                prev_year, prev_month = months[i-1]
                curr_year, curr_month = months[i]
                
                # Calculate month difference
                prev_total = prev_year * 12 + prev_month
                curr_total = curr_year * 12 + curr_month
                gap = curr_total - prev_total - 1
                
                if gap >= 2:
                    missing_months = []
                    for m in range(prev_total + 1, curr_total):
                        y = m // 12
                        mo = m % 12 or 12
                        if mo == 12:
                            y -= 1
                        missing_months.append(f"{y}-{mo:02d}")
                    
                    findings.append({
                        "flag_type": "gap",
                        "severity": "warning" if gap <= 3 else "critical",
                        "rule_id": f"temporal_gap_{activity_type}",
                        "title": f"Missing {gap} months of {activity_type} data",
                        "description": f"Data gap detected between {prev_year}-{prev_month:02d} and {curr_year}-{curr_month:02d} for {activity_type} activities.",
                        "recommendation": f"Review and upload {activity_type} data for the missing period: {', '.join(missing_months)}",
                        "evidence": {
                            "activity_type": activity_type,
                            "gap_months": gap,
                            "missing_months": missing_months,
                            "prev_month": f"{prev_year}-{prev_month:02d}",
                            "next_month": f"{curr_year}-{curr_month:02d}"
                        }
                    })
        
        return findings
    
    def _detect_scope_coverage_gaps(
        self,
        activities: List[EmissionActivity],
        archetype: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Detect missing scopes based on archetype expectations
        """
        findings = []
        
        if not archetype:
            return findings
        
        fingerprint = get_archetype(archetype)
        if not fingerprint:
            return findings
        
        # Get scopes present in data
        present_scopes = set(a.scope for a in activities if a.scope)
        expected_scopes = set(fingerprint.expected_scopes)
        
        missing_scopes = expected_scopes - present_scopes
        
        for scope in missing_scopes:
            findings.append({
                "flag_type": "gap",
                "severity": "warning",
                "rule_id": f"scope_coverage_{scope.replace(' ', '_').lower()}",
                "title": f"Missing {scope} emissions",
                "description": f"Based on the '{fingerprint.display_name}' archetype, {scope} emissions are expected but not found in the data.",
                "recommendation": f"Review and report {scope} emission sources typical for your industry: {', '.join(fingerprint.key_emission_signals[:3])}",
                "evidence": {
                    "archetype": archetype,
                    "expected_scopes": list(expected_scopes),
                    "present_scopes": list(present_scopes),
                    "missing_scope": scope
                }
            })
        
        return findings
    
    def _detect_activity_type_gaps(
        self,
        activities: List[EmissionActivity],
        archetype: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Detect missing activity types based on archetype fingerprint
        """
        findings = []
        
        if not archetype:
            return findings
        
        fingerprint = get_archetype(archetype)
        if not fingerprint:
            return findings
        
        # Get activity types present in data
        present_types = set(a.activity_type for a in activities if a.activity_type)
        expected_types = set(fingerprint.expected_activity_types)
        
        missing_types = expected_types - present_types
        
        # Only flag if significant types are missing
        for activity_type in missing_types:
            # Critical types for certain archetypes
            is_critical = False
            if archetype == "mover" and activity_type == "fuel":
                is_critical = True
            elif archetype == "material_transformer" and activity_type == "stationary_combustion":
                is_critical = True
            elif archetype == "energy_producer" and activity_type == "stationary_combustion":
                is_critical = True
            
            findings.append({
                "flag_type": "gap",
                "severity": "critical" if is_critical else "info",
                "rule_id": f"activity_type_gap_{activity_type}",
                "title": f"No {activity_type.replace('_', ' ')} activities reported",
                "description": f"The '{fingerprint.display_name}' archetype typically includes {activity_type.replace('_', ' ')} activities, but none were found.",
                "recommendation": f"Review whether your organization has {activity_type.replace('_', ' ')} emission sources that should be reported.",
                "evidence": {
                    "archetype": archetype,
                    "expected_activity_types": list(expected_types),
                    "present_activity_types": list(present_types),
                    "missing_type": activity_type
                }
            })
        
        return findings


# Factory function
def create_gap_detector(db: Session, organization_id: UUID) -> GapDetector:
    """Create a gap detector instance scoped to an organization"""
    return GapDetector(db, organization_id)
