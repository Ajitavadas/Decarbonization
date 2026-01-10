"""
Carbon Accounting Auditor Service
Main orchestrator for anomaly detection and data gap auditing
Read-only access, organization-scoped
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.project import Project
from app.models.flagged_event import FlaggedEvent
from app.services.gap_detector import create_gap_detector
from app.services.anomaly_detector import create_anomaly_detector
from app.services.groq_service import GroqService
from app.core.archetype_config import get_archetype, infer_archetype_from_industry

logger = logging.getLogger(__name__)


class AuditorService:
    """
    Carbon Accounting Auditor Agent
    
    Orchestrates anomaly detection and data gap auditing with:
    - Read-only organization-scoped database access
    - Gap detection (temporal, scope, activity type)
    - Anomaly detection (statistical, implausible, zero values)
    - AI-powered contextual analysis via Gemini
    """
    
    def __init__(self, db: Session, organization_id: UUID):
        """
        Initialize auditor with organization scope
        
        Args:
            db: Database session
            organization_id: Organization to audit (enforces isolation)
        """
        self.db = db
        self.organization_id = organization_id
        self._organization: Optional[Organization] = None
    
    @property
    def organization(self) -> Organization:
        """Lazy load organization"""
        if self._organization is None:
            self._organization = self.db.query(Organization).filter(
                Organization.id == self.organization_id
            ).first()
            if not self._organization:
                raise ValueError(f"Organization {self.organization_id} not found")
        return self._organization
    
    @property
    def archetype(self) -> Optional[str]:
        """Get organization's archetype (or infer from industry)"""
        org = self.organization
        if org.emission_archetype:
            return org.emission_archetype
        return infer_archetype_from_industry(org.industry)
    
    async def run_audit(
        self,
        project_id: Optional[UUID] = None,
        include_ai_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Run full audit on organization's emission data
        
        Args:
            project_id: Optional specific project to audit
            include_ai_analysis: Whether to run Gemini AI analysis
            
        Returns:
            Audit results with findings
        """
        audit_run_id = uuid.uuid4()
        start_time = datetime.utcnow()
        
        logger.info(f"Starting audit run {audit_run_id} for organization {self.organization_id}")
        
        all_findings: List[Dict[str, Any]] = []
        
        # 1. Run Gap Detection
        gap_detector = create_gap_detector(self.db, self.organization_id)
        gap_findings = gap_detector.detect_all_gaps(
            project_id=project_id,
            archetype=self.archetype
        )
        all_findings.extend(gap_findings)
        logger.info(f"Gap detection found {len(gap_findings)} issues")
        
        # 2. Run Anomaly Detection
        anomaly_detector = create_anomaly_detector(self.db, self.organization_id)
        anomaly_findings = anomaly_detector.detect_all_anomalies(
            project_id=project_id,
            archetype=self.archetype
        )
        all_findings.extend(anomaly_findings)
        logger.info(f"Anomaly detection found {len(anomaly_findings)} issues")
        
        # 3. Run AI Analysis (if enabled and API key configured)
        ai_findings = []
        if include_ai_analysis:
            ai_findings = await self._run_ai_analysis(project_id)
            all_findings.extend(ai_findings)
            logger.info(f"AI analysis found {len(ai_findings)} additional issues")
        
        # 4. Persist findings to database
        persisted_count = self._persist_findings(all_findings, audit_run_id, project_id)
        
        end_time = datetime.utcnow()
        duration_seconds = (end_time - start_time).total_seconds()
        
        # 5. Compile results
        results = {
            "audit_run_id": str(audit_run_id),
            "organization_id": str(self.organization_id),
            "project_id": str(project_id) if project_id else None,
            "archetype": self.archetype,
            "started_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "duration_seconds": round(duration_seconds, 2),
            "summary": {
                "total_findings": len(all_findings),
                "gap_findings": len(gap_findings),
                "anomaly_findings": len(anomaly_findings),
                "ai_findings": len(ai_findings),
                "critical_count": sum(1 for f in all_findings if f.get("severity") == "critical"),
                "warning_count": sum(1 for f in all_findings if f.get("severity") == "warning"),
                "info_count": sum(1 for f in all_findings if f.get("severity") == "info"),
            },
            "findings": all_findings,
            "persisted_count": persisted_count
        }
        
        logger.info(f"Audit run {audit_run_id} completed: {len(all_findings)} findings in {duration_seconds:.2f}s")
        
        return results
    
    async def _run_ai_analysis(self, project_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Run AI-powered contextual analysis"""
        from app.models.activity import EmissionActivity
        
        # Get activities for analysis
        query = self.db.query(EmissionActivity).join(Project).filter(
            Project.organization_id == self.organization_id
        )
        
        if project_id:
            query = query.filter(Project.id == project_id)
        
        activities = query.limit(100).all()  # Limit for API token management
        
        if not activities:
            return []
        
        # Prepare data for Gemini
        activity_data = [
            {
                "id": str(a.id),
                "activity_type": a.activity_type,
                "scope": a.scope,
                "co2e_kg": float(a.co2e_kg) if a.co2e_kg else 0,
                "activity_date": a.activity_date.isoformat() if a.activity_date else None,
                "description": (a.input_data or {}).get("description", "")[:100],
                "amount": (a.input_data or {}).get("amount"),
                "unit": (a.input_data or {}).get("unit"),
            }
            for a in activities
        ]
        
        organization_context = {
            "industry": self.organization.industry,
            "country": self.organization.country,
            "name": self.organization.name
        }
        
        # Call Groq
        groq_service = GroqService()
        result = await groq_service.analyze_anomalies(
            activity_data=activity_data,
            archetype=self.archetype or "unknown",
            organization_context=organization_context
        )
        
        # Convert Groq findings to our format
        ai_findings = []
        for finding in result.get("findings", []):
            ai_findings.append({
                "flag_type": finding.get("type", "anomaly"),
                "severity": finding.get("severity", "info"),
                "rule_id": "ai_contextual_analysis",
                "title": finding.get("title", "AI-detected issue"),
                "description": finding.get("description", ""),
                "recommendation": finding.get("recommendation", ""),
                "evidence": {
                    "ai_provider": "groq",
                    "confidence": result.get("confidence", 0),
                    "affected_activities": finding.get("affected_activities", [])
                }
            })
        
        return ai_findings
    
    def _persist_findings(
        self,
        findings: List[Dict[str, Any]],
        audit_run_id: UUID,
        project_id: Optional[UUID] = None
    ) -> int:
        """
        Persist findings to FlaggedEvent table with deduplication.
        
        Deduplication logic:
        - For findings with activity_id: check if same rule_id + activity_id exists and is open
        - For findings without activity_id: check if same rule_id exists and is open
        - Skip if duplicate found (don't create multiple findings for same issue)
        """
        persisted = 0
        skipped = 0
        
        for finding in findings:
            try:
                # Get activity_id if present
                activity_id = finding.pop("activity_id", None)
                rule_id = finding["rule_id"]
                title = finding["title"]
                
                # Check for existing open finding with same rule_id
                existing_query = self.db.query(FlaggedEvent).filter(
                    FlaggedEvent.organization_id == self.organization_id,
                    FlaggedEvent.rule_id == rule_id,
                    FlaggedEvent.status == "open"
                )
                
                # For AI findings, also match on title since they share the same rule_id
                if rule_id == "ai_contextual_analysis":
                    existing_query = existing_query.filter(
                        FlaggedEvent.title == title
                    )
                # If activity-specific, also match on activity_id
                elif activity_id:
                    existing_query = existing_query.filter(
                        FlaggedEvent.activity_id == activity_id
                    )
                else:
                    # For non-activity findings (like archetype mismatch), 
                    # only allow one open finding per rule_id
                    existing_query = existing_query.filter(
                        FlaggedEvent.activity_id.is_(None)
                    )
                
                existing = existing_query.first()
                
                if existing:
                    # Skip duplicate - finding already exists and is open
                    skipped += 1
                    logger.debug(f"Skipping duplicate finding: {rule_id}")
                    continue
                
                flagged_event = FlaggedEvent(
                    organization_id=self.organization_id,
                    project_id=project_id,
                    activity_id=activity_id,
                    flag_type=finding["flag_type"],
                    severity=finding["severity"],
                    rule_id=rule_id,
                    title=finding["title"],
                    description=finding.get("description"),
                    recommendation=finding.get("recommendation"),
                    evidence=finding.get("evidence"),
                    audit_run_id=audit_run_id,
                    status="open"
                )
                
                self.db.add(flagged_event)
                persisted += 1
                
            except Exception as e:
                logger.error(f"Failed to persist finding: {e}")
        
        try:
            self.db.commit()
            if skipped > 0:
                logger.info(f"Persisted {persisted} findings, skipped {skipped} duplicates")
        except Exception as e:
            logger.error(f"Failed to commit findings: {e}")
            self.db.rollback()
            return 0
        
        return persisted
    
    def get_findings(
        self,
        status: Optional[str] = None,
        flag_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get flagged events for the organization
        
        Args:
            status: Filter by status (open, acknowledged, resolved, false_positive)
            flag_type: Filter by type (gap, anomaly, archetype_mismatch)
            severity: Filter by severity (info, warning, critical)
            limit: Maximum results to return
            offset: Pagination offset
            
        Returns:
            Dict with findings and pagination info
        """
        query = self.db.query(FlaggedEvent).filter(
            FlaggedEvent.organization_id == self.organization_id
        )
        
        if status:
            query = query.filter(FlaggedEvent.status == status)
        if flag_type:
            query = query.filter(FlaggedEvent.flag_type == flag_type)
        if severity:
            query = query.filter(FlaggedEvent.severity == severity)
        
        total = query.count()
        
        findings = query.order_by(
            FlaggedEvent.severity.desc(),  # Critical first
            FlaggedEvent.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "findings": [
                {
                    "id": str(f.id),
                    "flag_type": f.flag_type,
                    "severity": f.severity,
                    "rule_id": f.rule_id,
                    "title": f.title,
                    "description": f.description,
                    "recommendation": f.recommendation,
                    "evidence": f.evidence,
                    "status": f.status,
                    "project_id": str(f.project_id) if f.project_id else None,
                    "activity_id": str(f.activity_id) if f.activity_id else None,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                    "resolved_at": f.resolved_at.isoformat() if f.resolved_at else None,
                }
                for f in findings
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def resolve_finding(
        self,
        finding_id: UUID,
        user_id: UUID,
        status: str,
        notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve or update status of a finding
        
        Args:
            finding_id: ID of the finding to update
            user_id: User making the resolution
            status: New status (acknowledged, resolved, false_positive)
            notes: Optional resolution notes
            
        Returns:
            Updated finding or None if not found
        """
        finding = self.db.query(FlaggedEvent).filter(
            FlaggedEvent.id == finding_id,
            FlaggedEvent.organization_id == self.organization_id  # Ensure org isolation
        ).first()
        
        if not finding:
            return None
        
        finding.status = status
        finding.resolved_by = user_id
        finding.resolution_notes = notes
        
        if status in ["resolved", "false_positive"]:
            finding.resolved_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "id": str(finding.id),
            "status": finding.status,
            "resolved_by": str(finding.resolved_by),
            "resolution_notes": finding.resolution_notes,
            "resolved_at": finding.resolved_at.isoformat() if finding.resolved_at else None
        }


# Factory function
def create_auditor_service(db: Session, organization_id: UUID) -> AuditorService:
    """Create an auditor service instance scoped to an organization"""
    return AuditorService(db, organization_id)
