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
    format: str = "pdf",  # pdf or html
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate comprehensive carbon footprint report
    
    Formats:
    - pdf: Professional PDF report with visualizations
    - html: Interactive HTML report with charts
    """
    # Verify user has access to this project
    verify_project_access(db, project_id, current_user)
    
    # Validate format
    if format not in ['pdf', 'html']:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'pdf' or 'html'")
    
    try:
        # Generate report
        generator = ReportGenerator(db, project_id, output_format=format)
        
        if format == 'pdf':
            report_buffer = generator.generate()
            return StreamingResponse(
                report_buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=carbon_report_{project_id}.pdf"
                }
            )
        else:  # html
            report_html = generator.generate()
            return StreamingResponse(
                iter([report_html]),
                media_type="text/html",
                headers={
                    "Content-Disposition": f"inline; filename=carbon_report_{project_id}.html"
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
        # Generate report data only (no PDF/HTML)
        generator = ReportGenerator(db, project_id, output_format='pdf')
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
    format: str = "pdf",  # pdf or html
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate comprehensive carbon footprint report
    
    Formats:
    - pdf: Professional PDF report with visualizations
    - html: Interactive HTML report with charts
    """
    # Verify user has access to this project
    verify_project_access(db, project_id, current_user)
    
    # Validate format
    if format not in ['pdf', 'html']:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'pdf' or 'html'")
    
    try:
        # Generate report
        generator = ReportGenerator(db, project_id, output_format=format)
        
        if format == 'pdf':
            report_buffer = generator.generate()
            return StreamingResponse(
                report_buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=carbon_report_{project_id}.pdf"
                }
            )
        else:  # html
            report_html = generator.generate()
            return StreamingResponse(
                iter([report_html]),
                media_type="text/html",
                headers={
                    "Content-Disposition": f"inline; filename=carbon_report_{project_id}.html"
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
        # Generate report data only (no PDF/HTML)
        generator = ReportGenerator(db, project_id, output_format='pdf')
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
