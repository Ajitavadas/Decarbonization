"""
Report Generation API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.security import get_current_user
from app.core.authorization import verify_project_access
from app.services.report_generator import ReportGenerator

router = APIRouter()


@router.get("/projects/{project_id}/report")
async def generate_report(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate comprehensive carbon footprint PDF report with visualizations
    """
    # Verify user has access to this project
    verify_project_access(db, project_id, current_user)
    
    try:
        # Generate PDF report
        generator = ReportGenerator(db, project_id)
        report_buffer = generator.generate()
        
        return StreamingResponse(
            report_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=carbon_report_{project_id}.pdf"
            }
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/projects/{project_id}/report-summary")
async def get_report_summary(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get JSON summary data for charts (without full report generation)
    """
    # Verify user has access to this project
    verify_project_access(db, project_id, current_user)
    
    try:
        # Generate report data only (no PDF)
        generator = ReportGenerator(db, project_id)
        generator._fetch_data()
        generator._calculate_summary()
        
        return {
            "project": generator.project_data,
            "summary": {
                "total_co2e_kg": generator.summary['total_co2e_kg'],
                "total_activities": generator.summary['total_activities'],
                "scope_breakdown": generator.summary['scope_breakdown'],
                "scope_percentages": generator.summary['scope_percentages'],
                "activity_breakdown": generator.summary['activity_breakdown'],
                "top_activities": [
                    {
                        "type": a['type'],
                        "scope": a['scope'],
                        "co2e_kg": a['co2e_kg'],
                        "date": a['date'],
                        "region": a['region']
                    }
                    for a in generator.summary['top_activities']
                ]
            }
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")
