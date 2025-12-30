"""
Reporting tasks
Automated report generation
"""

from datetime import datetime
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.project import Project
from app.crud.crud_activity import crud_activity


@celery_app.task(name="app.tasks.reporting.generate_monthly_reports")
def generate_monthly_reports():
    """
    Generate monthly emission reports for all active projects
    
    Scheduled to run on 1st of each month
    """
    db = SessionLocal()
    
    try:
        projects = db.query(Project).all()
        
        for project in projects:
            # Get emissions summary
            total_emissions = crud_activity.get_total_emissions(db, project_id=str(project.id))
            scope_breakdown = crud_activity.get_emissions_by_scope(db, project_id=str(project.id))
            
            # TODO: Generate PDF report, send email notifications, etc.
            print(f"Report for {project.name}: {total_emissions} kg CO2e")
            print(f"Scope breakdown: {scope_breakdown}")
        
        return {"status": "completed", "projects_processed": len(projects)}
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}
        
    finally:
        db.close()
