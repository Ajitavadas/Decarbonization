"""
Report Generation API Endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.user import User
from app.core.security import get_current_user
from app.core.authorization import verify_project_access
from app.services.report_generator import ReportGenerator


class TableConfig(BaseModel):
    """Configuration for a single table in custom report"""
    type: str = Field(..., description="Table type: activity_data, emission_factors, gas_breakdown, activity_type_breakdown, detailed_list")
    title: Optional[str] = Field(None, description="Custom title for the table")
    columns: list[str] = Field(..., description="List of column names to include")
    page_break_after: bool = Field(False, description="Add page break after this table")


class ReportConfig(BaseModel):
    """Configuration for custom report generation"""
    format_type: str = Field("standard", description="Report format: 'standard' or 'custom'")
    include_charts: bool = Field(True, description="Include visualization charts")
    include_executive_summary: bool = Field(True, description="Include executive summary section")
    tables: list[TableConfig] = Field(default_factory=list, description="List of tables to include in custom format")


router = APIRouter()


@router.post("/projects/{project_id}/report")
async def generate_report(
    project_id: str,
    config: Optional[ReportConfig] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate carbon footprint PDF report
    
    - Standard format: Professional report with all sections (default)
    - Custom format: User-configured tables and columns
    """
    # Verify user has access to this project
    verify_project_access(db, project_id, current_user)
    
    try:
        # Generate PDF report
        generator = ReportGenerator(db, project_id)
        
        # Use custom config if provided, otherwise standard format
        if config and config.format_type == "custom":
            report_buffer = generator.generate_custom(config.dict())
        else:
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


@router.get("/projects/{project_id}/report/available-columns")
async def get_available_columns(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available columns for each table type in custom reports
    """
    verify_project_access(db, project_id, current_user)
    
    return {
        "activity_data": {
            "name": "Activity Data by Scope",
            "columns": ["Activity", "Emission Source", "Activity Data", "Unit", "Scope"]
        },
        "emission_factors": {
            "name": "Emission Factors Used",
            "columns": ["Scope", "Emission Source", "Unit", "kgCO2e per Unit", "Data Source"]
        },
        "gas_breakdown": {
            "name": "GHG Emissions by Scope and Gas",
            "columns": ["Scope", "Emission Source", "CO2e (kg)", "CO2 (kg)", "CH4 (kg)", "N2O (kg)", "Other GHGs (kg)"]
        },
        "activity_type_breakdown": {
            "name": "Activity Type Breakdown",
            "columns": ["Activity Type", "CO2e (kg)", "Count"]
        },
        "detailed_list": {
            "name": "Detailed Activity List",
            "columns": ["#", "Type", "Emission Source", "Scope", "Quantity", "Unit", "EF (kgCO2e/unit)", "CO2e (kg)", "Calc Method", "Region", "Date"]
        }
    }
