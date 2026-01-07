"""
Audit API Endpoints
Carbon Accounting Auditor Agent REST API
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.services.auditor_service import create_auditor_service
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


# ========== Request/Response Schemas ==========

class AuditRunRequest(BaseModel):
    """Request to trigger an audit run"""
    project_id: Optional[UUID] = None
    include_ai_analysis: bool = True


class AuditRunResponse(BaseModel):
    """Response from an audit run"""
    audit_run_id: str
    organization_id: str
    project_id: Optional[str]
    archetype: Optional[str]
    started_at: str
    completed_at: str
    duration_seconds: float
    summary: dict
    findings: list
    persisted_count: int


class FindingResolveRequest(BaseModel):
    """Request to resolve a finding"""
    status: str  # acknowledged, resolved, false_positive
    notes: Optional[str] = None


class FindingResponse(BaseModel):
    """Single finding response"""
    id: str
    flag_type: str
    severity: str
    rule_id: str
    title: str
    description: Optional[str]
    recommendation: Optional[str]
    evidence: Optional[dict]
    status: str
    project_id: Optional[str]
    activity_id: Optional[str]
    created_at: Optional[str]
    resolved_at: Optional[str]


# ========== API Endpoints ==========

@router.post("/run", response_model=AuditRunResponse)
async def run_audit(
    request: AuditRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger an audit run for the current user's organization
    
    Runs all detection rules:
    - Gap detection (temporal, scope coverage, activity types)
    - Anomaly detection (statistical outliers, zero values, implausible values)
    - Archetype validation (scope distribution)
    - AI analysis (contextual patterns via Gemini)
    """
    try:
        organization_id = current_user.organization_id
        if not organization_id:
            raise HTTPException(status_code=400, detail="User not associated with an organization")
        
        auditor = create_auditor_service(db, organization_id)
        
        result = await auditor.run_audit(
            project_id=request.project_id,
            include_ai_analysis=request.include_ai_analysis
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Audit run failed: {e}")
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")


@router.get("/findings")
async def get_findings(
    status: Optional[str] = Query(None, description="Filter by status: open, acknowledged, resolved, false_positive"),
    flag_type: Optional[str] = Query(None, description="Filter by type: gap, anomaly, archetype_mismatch"),
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, critical"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get audit findings for the current user's organization
    
    Findings are sorted by severity (critical first) then by date (newest first)
    """
    try:
        organization_id = current_user.organization_id
        if not organization_id:
            raise HTTPException(status_code=400, detail="User not associated with an organization")
        
        auditor = create_auditor_service(db, organization_id)
        
        return auditor.get_findings(
            status=status,
            flag_type=flag_type,
            severity=severity,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Failed to get findings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get findings: {str(e)}")


@router.get("/findings/{finding_id}")
async def get_finding(
    finding_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific finding by ID
    """
    try:
        organization_id = current_user.organization_id
        if not organization_id:
            raise HTTPException(status_code=400, detail="User not associated with an organization")
        
        auditor = create_auditor_service(db, organization_id)
        
        result = auditor.get_findings(limit=1, offset=0)
        
        # Find specific finding
        from app.models.flagged_event import FlaggedEvent
        finding = db.query(FlaggedEvent).filter(
            FlaggedEvent.id == finding_id,
            FlaggedEvent.organization_id == organization_id
        ).first()
        
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        
        return {
            "id": str(finding.id),
            "flag_type": finding.flag_type,
            "severity": finding.severity,
            "rule_id": finding.rule_id,
            "title": finding.title,
            "description": finding.description,
            "recommendation": finding.recommendation,
            "evidence": finding.evidence,
            "status": finding.status,
            "project_id": str(finding.project_id) if finding.project_id else None,
            "activity_id": str(finding.activity_id) if finding.activity_id else None,
            "created_at": finding.created_at.isoformat() if finding.created_at else None,
            "resolved_at": finding.resolved_at.isoformat() if finding.resolved_at else None,
            "resolution_notes": finding.resolution_notes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get finding: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get finding: {str(e)}")


@router.patch("/findings/{finding_id}/resolve")
async def resolve_finding(
    finding_id: UUID,
    request: FindingResolveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Resolve or update status of a finding
    
    Valid statuses:
    - acknowledged: User has seen and noted the issue
    - resolved: Issue has been fixed
    - false_positive: Issue was incorrectly flagged
    """
    try:
        organization_id = current_user.organization_id
        if not organization_id:
            raise HTTPException(status_code=400, detail="User not associated with an organization")
        
        valid_statuses = ["acknowledged", "resolved", "false_positive"]
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        auditor = create_auditor_service(db, organization_id)
        
        result = auditor.resolve_finding(
            finding_id=finding_id,
            user_id=current_user.id,
            status=request.status,
            notes=request.notes
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Finding not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve finding: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve finding: {str(e)}")


@router.get("/summary")
async def get_audit_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get audit summary statistics for the organization
    """
    try:
        organization_id = current_user.organization_id
        if not organization_id:
            raise HTTPException(status_code=400, detail="User not associated with an organization")
        
        from app.models.flagged_event import FlaggedEvent
        from sqlalchemy import func
        
        # Count by status
        status_counts = db.query(
            FlaggedEvent.status,
            func.count(FlaggedEvent.id)
        ).filter(
            FlaggedEvent.organization_id == organization_id
        ).group_by(FlaggedEvent.status).all()
        
        # Count by severity
        severity_counts = db.query(
            FlaggedEvent.severity,
            func.count(FlaggedEvent.id)
        ).filter(
            FlaggedEvent.organization_id == organization_id
        ).group_by(FlaggedEvent.severity).all()
        
        # Count by flag type
        type_counts = db.query(
            FlaggedEvent.flag_type,
            func.count(FlaggedEvent.id)
        ).filter(
            FlaggedEvent.organization_id == organization_id
        ).group_by(FlaggedEvent.flag_type).all()
        
        total = db.query(func.count(FlaggedEvent.id)).filter(
            FlaggedEvent.organization_id == organization_id
        ).scalar() or 0
        
        return {
            "total_findings": total,
            "by_status": {status: count for status, count in status_counts},
            "by_severity": {severity: count for severity, count in severity_counts},
            "by_type": {flag_type: count for flag_type, count in type_counts},
            "open_critical": db.query(func.count(FlaggedEvent.id)).filter(
                FlaggedEvent.organization_id == organization_id,
                FlaggedEvent.status == "open",
                FlaggedEvent.severity == "critical"
            ).scalar() or 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")
