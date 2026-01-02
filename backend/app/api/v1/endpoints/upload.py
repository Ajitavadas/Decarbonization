"""
CSV Upload and Processing Endpoint
Handles CSV file uploads, unit normalization, and emission calculations
"""

import io
import csv
import hashlib
import pandas as pd
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.activity import EmissionActivity
from app.models.batch_job import BatchJob
from app.services.unit_normalizer import UnitNormalizer
from app.services.ai_classifier_service import AIScopeClassifierService
from app.integration.climatiq.service import ClimatiqService
from app.db.session import get_db
import logging

router = APIRouter()

logger = logging.getLogger(__name__)


def compute_activity_hash(project_id: str, description: str, amount: float, unit: str, activity_date: str, region: str = None) -> str:
    """
    Compute a unique hash for an activity to prevent duplicates.
    
    Note: project_id is accepted but NOT used in hash computation.
    This enables global deduplication across all projects to prevent
    the same activity data from inflating totals.
    
    Args:
        project_id: The project this activity belongs to (not used in hash)
        description: Activity description
        amount: Activity amount
        unit: Unit of measurement
        activity_date: Date of activity
        region: Optional region
        
    Returns:
        SHA256 hash string
    """
    # Normalize values for consistent hashing
    # Note: project_id deliberately excluded to enable global deduplication
    hash_input = f"{description.strip().lower()}|{amount}|{unit.lower()}|{activity_date}|{region or ''}"
    return hashlib.sha256(hash_input.encode()).hexdigest()

def extract_co2e_from_response(result: Dict[str, Any], endpoint_type: str = "autopilot") -> float:
    """
    Extract CO2e from different Climatiq endpoint response structures
    
    Args:
        result: Response from Climatiq API
        endpoint_type: Type of endpoint that was called
        
    Returns:
        CO2e value as float
    """
    if not result:
        return 0.0
    
    # Energy endpoints (electricity, fuel) return direct response, not wrapped in 'estimate'
    if endpoint_type in ["energy", "fuel"]:
        # Electricity endpoint returns location.consumption.co2e
        if "location" in result and "consumption" in result.get("location", {}):
            return float(result["location"]["consumption"].get("co2e", 0))
        
        # Direct response from Energy endpoints
        if "co2e" in result:
            return float(result["co2e"])
        
        # Fuel endpoint returns co2e inside combustion object
        if endpoint_type == "fuel" and "combustion" in result:
            if "co2e" in result["combustion"]:
                return float(result["combustion"]["co2e"])
        
        # Check for nested structures in Energy endpoints (for complex electricity responses)
        if "direct" in result and isinstance(result["direct"], dict) and "co2e" in result["direct"]:
            return float(result["direct"]["co2e"])
        
        if "market" in result and isinstance(result["market"], dict):
            if "consumption" in result["market"] and "co2e" in result["market"]["consumption"]:
                return float(result["market"]["consumption"]["co2e"])
            elif "co2e" in result["market"]:
                return float(result["market"]["co2e"])
        
        # Check for any co2e in nested structures
        for key in ["direct", "market", "well_to_tank", "transmission_and_distribution"]:
            if key in result and isinstance(result[key], dict) and "co2e" in result[key]:
                return float(result[key]["co2e"])
    
    # Travel endpoints return direct response
    elif endpoint_type in ["travel", "travel_spend", "travel_distance"]:
        # Travel endpoints return direct co2e
        if "co2e" in result:
            return float(result["co2e"])
        elif "estimate" in result and "co2e" in result["estimate"]:
            return float(result["estimate"]["co2e"])
    
    # Procurement endpoint returns direct response
    elif endpoint_type in ["procurement"]:
        # Procurement returns direct co2e
        if "co2e" in result:
            return float(result["co2e"])
        elif "estimate" in result and "co2e" in result["estimate"]:
            return float(result["estimate"]["co2e"])
    
    # Freight endpoint returns direct response
    elif endpoint_type in ["freight"]:
        # Freight returns direct co2e
        if "co2e" in result:
            return float(result["co2e"])
        elif "estimate" in result and "co2e" in result["estimate"]:
            return float(result["estimate"]["co2e"])
    
    # Autopilot and Estimate endpoints
    elif endpoint_type in ["autopilot", "estimate"]:
        if "estimate" not in result:
            return 0.0
            
        estimate = result["estimate"]
        
        # Check for direct CO2e
        if "co2e" in estimate and estimate["co2e"] > 0:
            return float(estimate["co2e"])
        
        # Check for nested structures
        if "direct" in estimate and isinstance(estimate["direct"], dict) and "co2e" in estimate["direct"]:
            return float(estimate["direct"]["co2e"])
        
        if "market" in estimate and isinstance(estimate["market"], dict):
            if "consumption" in estimate["market"] and "co2e" in estimate["market"]["consumption"]:
                return float(estimate["market"]["consumption"]["co2e"])
            elif "co2e" in estimate["market"]:
                return float(estimate["market"]["co2e"])
        
        # Check for any co2e in nested structures
        for key in ["direct", "market", "well_to_tank", "transmission_and_distribution"]:
            if key in estimate and isinstance(estimate[key], dict) and "co2e" in estimate[key]:
                return float(estimate[key]["co2e"])
    
    return 0.0


@router.post("/csv")
async def upload_csv(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process CSV file for emission calculations
    """
    try:
        # Validate project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Initialize services
        unit_normalizer = UnitNormalizer()
        ai_classifier = AIScopeClassifierService()
        climatiq_service = ClimatiqService()
        
        # Create batch job
        batch_job = BatchJob(
            project_id=project.id,
            job_type="csv_upload",
            status="processing",
            total_records=len(df),
            processed_records=0,
            successful_records=0,
            failed_records=0
        )
        db.add(batch_job)
        db.commit()  # Commit to get the ID
        
        # Normalize units to Climatiq-compatible formats
        print(f"Normalizing units for {len(df)} rows...")
        for idx in df.index:
            if 'unit' in df.columns and pd.notna(df.at[idx, 'unit']):
                original_unit = str(df.at[idx, 'unit']).lower()
                normalized_unit = unit_normalizer.normalize(original_unit)
                
                # Handle unit conversions
                if original_unit in ['therm', 'therms'] and normalized_unit == 'kWh':
                    # Convert therms to kWh (1 therm = 29.3 kWh)
                    original_amount = float(df.at[idx, 'amount']) if pd.notna(df.at[idx, 'amount']) else 0
                    converted_amount = original_amount * 29.3
                    df.at[idx, 'amount'] = converted_amount
                    print(f"  Row {idx}: {original_amount} {original_unit} → {converted_amount} kWh")
                elif original_unit != normalized_unit:
                    print(f"  Row {idx}: {original_unit} → {normalized_unit}")
                
                df.at[idx, 'unit'] = normalized_unit
        
        # Process each row
        successful_count = 0
        failed_count = 0
        error_log = []
        
        for idx, row in df.iterrows():
            try:
                # Extract and validate data
                description = str(row.get("description", ""))
                amount = float(row.get("amount", 0))
                unit = str(row.get("unit", ""))
                region = str(row.get("region", "")) if pd.notna(row.get("region")) else None
                year = int(row.get("year")) if pd.notna(row.get("year")) else datetime.now().year
                activity_date_str = str(row.get("activity_date", "")) if pd.notna(row.get("activity_date")) else None
                
                print(f"DEBUG - Row {idx}: extracted unit='{unit}' (after normalization)")
                
                # Parse activity date
                if activity_date_str:
                    try:
                        activity_date = datetime.strptime(activity_date_str, "%Y-%m-%d").date()
                    except ValueError:
                        activity_date = datetime.now().date()
                else:
                    activity_date = datetime.now().date()
                
                # Determine unit type (comprehensive detection)
                unit_lower = unit.lower()
                if unit_lower in ['kwh', 'mwh', 'gwh', 'wh', 'mj', 'gj', 'btu', 'therm', 'therms', 'mmbtu']:
                    unit_type = "energy"
                elif unit_lower in ['kg', 't', 'ton', 'tonne', 'lb', 'lbs', 'g', 'gram', 'grams']:
                    unit_type = "weight"
                elif unit_lower in ['l', 'liter', 'liters', 'm3', 'm³', 'cubic meter', 'gal', 'gallon', 'gallons', 'ml', 'milliliter']:
                    unit_type = "volume"
                elif unit_lower in ['eur', 'usd', 'gbp', 'chf', 'cad', 'aud', 'jpy', 'cny', 'inr', 'aed', 'sar', 'sek', 'nok', 'dkk']:
                    unit_type = "money"
                elif unit_lower in ['km', 'kilometer', 'kilometre', 'mile', 'miles', 'm', 'meter', 'metre']:
                    unit_type = "distance"  # For travel
                else:
                    unit_type = "money"  # Default fallback
                
                # AI Classification
                classification = None
                try:
                    # Use the correct method signature: classify_transaction(description, category, supplier_name)
                    category = str(row.get("category", "")) if pd.notna(row.get("category")) else ""
                    supplier_name = str(row.get("supplier_name", "")) if pd.notna(row.get("supplier_name")) else None
                    classification = await ai_classifier.classify_transaction(description, category, supplier_name)
                    print(f"  AI Classification result: {classification}")
                except Exception as e:
                    print(f"  AI Classification failed: {e}")
                    # Fallback to basic classification
                    classification = (3, 0.0, True)  # Default to Scope 3
                
                # Calculate emissions using Climatiq
                autopilot_result = await climatiq_service.calculate_with_ai_suggestion(
                    text=description,
                    amount=amount,
                    unit=unit,  # This is already normalized by unit_normalizer
                    unit_type=unit_type,
                    region=region,
                    year=year
                )
                
                # Extract co2e
                estimate = autopilot_result.get("estimate", {})
                
                # Extract co2e using the new function
                endpoint_type = autopilot_result.get("endpoint_type", "autopilot")
                co2e = extract_co2e_from_response(autopilot_result, endpoint_type)
                
                # Debug: print the response structure and endpoint type
                print(f"DEBUG - Endpoint type: {endpoint_type}")
                print(f"DEBUG - Autopilot result keys: {list(autopilot_result.keys())}")
                if "estimate" in autopilot_result:
                    print(f"DEBUG - Estimate keys: {list(autopilot_result['estimate'].keys())}")
                print(f"DEBUG - CO2e value: {co2e}")
                print(f"DEBUG - Full autopilot result: {autopilot_result}")
                
                # Get scope from classification or Autopilot
                if classification:
                    # classification is a tuple: (scope, confidence, needs_review)
                    scope_num, confidence, needs_review = classification
                    scope = f"Scope {scope_num}"
                else:
                    scope = "Scope 3"
                
                # Compute content hash for deduplication
                activity_date_str_for_hash = str(activity_date) if activity_date else ""
                content_hash = compute_activity_hash(
                    project_id=str(project.id),
                    description=description,
                    amount=amount,
                    unit=unit,
                    activity_date=activity_date_str_for_hash,
                    region=region
                )
                
                # Check if activity already exists (deduplication)
                existing_activity = db.query(EmissionActivity).filter(
                    EmissionActivity.content_hash == content_hash
                ).first()
                
                if existing_activity:
                    print(f"  Skipping duplicate activity: {description[:50]}...")
                    # Count as successful but don't add again
                    successful_count += 1
                    continue
                
                # Create activity
                activity = EmissionActivity(
                    project_id=project.id,
                    batch_job_id=batch_job.id,
                    activity_type="procurement",  # Default, can be refined
                    sub_type=None,  # scope3Category not available in tuple return
                    scope=scope,
                    activity_date=activity_date,
                    co2e_kg=co2e,
                    region=region,
                    year=str(year),
                    content_hash=content_hash,  # Add hash for future dedup checks
                    input_data={
                        "description": description,
                        "amount": amount,
                        "unit": unit,
                        "unit_type": unit_type,
                        "classification": classification,
                        "autopilot_response": autopilot_result
                    }
                )
                
                db.add(activity)
                successful_count += 1
                
            except Exception as e:
                failed_count += 1
                error_log.append({
                    "row": idx,
                    "error": str(e),
                    "data": row.to_dict()
                })
                print(f"  Error processing row {idx}: {e}")
        
        # Update batch job
        batch_job.status = "completed"
        batch_job.processed_records = len(df)
        batch_job.successful_records = successful_count
        batch_job.failed_records = failed_count
        batch_job.error_log = error_log
        batch_job.completed_at = datetime.now()
        db.commit()
        
        logger.info(f"CSV upload completed: {successful_count} successful, {failed_count} failed")
        
        return {
            "success": True,
            "job_id": str(batch_job.id),
            "message": f"Processed {successful_count} activities successfully",
            "total_records": len(df),
            "status": batch_job.status
        }
        
    except Exception as e:
        logger.error(f"CSV upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/batch/jobs")
async def get_batch_jobs(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get batch jobs for a project
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    jobs = db.query(BatchJob).filter(
        BatchJob.project_id == project.id
    ).order_by(BatchJob.created_at.desc()).all()
    
    return [
        {
            "id": str(job.id),
            "status": job.status,
            "total_records": job.total_records,
            "processed_records": job.processed_records,
            "successful_records": job.successful_records,
            "failed_records": job.failed_records,
            "error_log": job.error_log,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
        for job in jobs
    ]
