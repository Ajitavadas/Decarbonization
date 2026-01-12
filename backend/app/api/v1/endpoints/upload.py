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
from app.models.flagged_event import FlaggedEvent
from app.services.unit_normalizer import UnitNormalizer
from app.services.ai_classifier_service import AIScopeClassifierService
from app.integration.climatiq.service import ClimatiqService
from app.core.authorization import verify_project_access
from app.db.session import get_db
import logging

router = APIRouter()

logger = logging.getLogger(__name__)


def parse_number(value) -> float:
    """
    Parse a number that may contain comma separators or other formatting.
    
    Handles formats like:
    - "85,000" → 85000.0
    - "1,234,567.89" → 1234567.89
    - "12.5" → 12.5
    - 12.5 → 12.5
    - "1 234" (European spacing) → 1234.0
    
    Args:
        value: The value to parse (string or numeric)
        
    Returns:
        float value
        
    Raises:
        ValueError: If the value cannot be parsed as a number
    """
    if value is None:
        return 0.0
    
    # If already a number, just convert
    if isinstance(value, (int, float)):
        return float(value)
    
    # Convert to string and clean
    str_value = str(value).strip()
    
    if not str_value:
        return 0.0
    
    # Remove thousand separators (commas and spaces)
    # Be careful with European format where comma is decimal separator
    # Check if there's a period - if so, commas are likely thousand separators
    if '.' in str_value:
        # e.g., "1,234,567.89" → "1234567.89"
        cleaned = str_value.replace(',', '').replace(' ', '')
    elif str_value.count(',') == 1:
        # Could be European decimal (e.g., "12,5" for 12.5) or thousand separator (e.g., "1,000")
        # Check position: if comma is followed by exactly 3 digits at end, it's a thousand separator
        parts = str_value.split(',')
        if len(parts[1]) == 3 and parts[1].isdigit():
            # Thousand separator: "1,000" → "1000"
            cleaned = str_value.replace(',', '').replace(' ', '')
        else:
            # European decimal: "12,5" → "12.5"
            cleaned = str_value.replace(' ', '').replace(',', '.')
    else:
        # Multiple commas = thousand separators: "1,234,567" → "1234567"
        cleaned = str_value.replace(',', '').replace(' ', '')
    
    return float(cleaned)


def compute_activity_hash(project_id: str, description: str, amount: float, unit: str, activity_date: str, region: str = None) -> str:
    """
    Compute a unique hash for an activity to prevent duplicates within a project.
    
    Note: project_id IS included in hash computation to scope deduplication
    per-project (and thus per-organization). Different organizations can have
    the same activity data without triggering cross-org deduplication.
    
    Args:
        project_id: The project this activity belongs to (INCLUDED in hash)
        description: Activity description
        amount: Activity amount
        unit: Unit of measurement
        activity_date: Date of activity
        region: Optional region
        
    Returns:
        SHA256 hash string
    """
    # Normalize values for consistent hashing
    # project_id included to scope deduplication per-project/organization
    hash_input = f"{project_id}|{description.strip().lower()}|{amount}|{unit.lower()}|{activity_date}|{region or ''}"
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
        # First check if response is wrapped in "estimate" (from our service wrapper)
        if "estimate" in result and isinstance(result["estimate"], dict):
            estimate = result["estimate"]
            if "co2e" in estimate and estimate["co2e"] > 0:
                return float(estimate["co2e"])
        
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
    
    # Autopilot and Estimate endpoints (including estimate_natural_gas, estimate_flight)
    elif endpoint_type in ["autopilot", "estimate", "estimate_natural_gas", "fuel_natural_gas", "estimate_flight"]:
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
    
    # UNIVERSAL FALLBACK: Try all possible CO2e locations for any endpoint type
    # This ensures new endpoint types don't fail silently
    else:
        # 1. Direct co2e at root
        if "co2e" in result and result["co2e"] and result["co2e"] > 0:
            return float(result["co2e"])
        
        # 2. Nested in "estimate" object
        if "estimate" in result and isinstance(result["estimate"], dict):
            est = result["estimate"]
            if "co2e" in est and est["co2e"] and est["co2e"] > 0:
                return float(est["co2e"])
        
        # 3. Nested in "combustion" 
        if "combustion" in result and isinstance(result["combustion"], dict):
            comb = result["combustion"]
            if "co2e" in comb and comb["co2e"] and comb["co2e"] > 0:
                return float(comb["co2e"])
        
        # 4. Check all known nested keys
        for key in ["location", "direct", "market", "well_to_tank", "consumption"]:
            if key in result and isinstance(result[key], dict):
                nested = result[key]
                if "co2e" in nested and nested["co2e"] and nested["co2e"] > 0:
                    return float(nested["co2e"])
                if "consumption" in nested and isinstance(nested["consumption"], dict):
                    if "co2e" in nested["consumption"] and nested["consumption"]["co2e"] > 0:
                        return float(nested["consumption"]["co2e"])
    
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
        # Validate project AND verify ownership
        project = verify_project_access(db, project_id, current_user)
        
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Normalize column names to lowercase for case-insensitive matching
        # This handles CSV files with varying column name cases (e.g., "Description" vs "description")
        df.columns = df.columns.str.lower().str.strip()
        
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
                    original_amount = parse_number(df.at[idx, 'amount']) if pd.notna(df.at[idx, 'amount']) else 0
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
                amount = parse_number(row.get("amount", 0))
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
                elif unit_lower in ['km', 'kilometer', 'kilometre', 'mi', 'mile', 'miles', 'm', 'meter', 'metre']:
                    unit_type = "distance"  # For travel
                else:
                    unit_type = "money"  # Default fallback
                
                # AI Classification for Climatiq routing
                climatiq_classification = None
                scope = "Scope 3"  # Default
                try:
                    # Get category from CSV if available
                    category = str(row.get("category", "")) if pd.notna(row.get("category")) else ""
                    
                    # Use the new comprehensive classification method
                    climatiq_classification = await ai_classifier.classify_for_climatiq(
                        description=description,
                        unit=unit,
                        category=category,
                        region=region or "US"
                    )
                    print(f"  AI Classification result: {climatiq_classification}")
                    
                    # Extract scope from classification
                    scope_num = climatiq_classification.get("scope", 3)
                    scope = f"Scope {scope_num}"
                    
                except Exception as e:
                    print(f"  AI Classification failed: {e}")
                    # Fallback classification
                    climatiq_classification = {
                        "scope": 3,
                        "endpoint": "autopilot",
                        "parameter_type": unit_type,
                        "activity_search": description,
                        "normalized_description": description
                    }
                
                # Calculate emissions using the new classification-based routing
                try:
                    # For freight activities with km unit, convert to tkm using AI-provided weight
                    calc_amount = amount
                    calc_unit = unit
                    
                    endpoint = climatiq_classification.get("endpoint", "")
                    param_type = climatiq_classification.get("parameter_type", "")
                    freight_weight = climatiq_classification.get("freight_weight_tonnes")
                    
                    # Convert km to tkm for freight activities
                    if (endpoint == "freight" or param_type == "weight_distance") and unit.lower() in ["km", "miles", "mi"]:
                        if freight_weight and freight_weight > 0:
                            # Convert distance to tonne-km using AI-estimated weight
                            if unit.lower() in ["miles", "mi"]:
                                calc_amount = amount * 1.60934 * freight_weight  # miles to km, then to tkm
                            else:
                                calc_amount = amount * freight_weight  # km * tonnes = tkm
                            calc_unit = "tkm"
                            print(f"  🚛 Freight conversion: {amount} {unit} × {freight_weight} tonnes = {calc_amount} tkm")
                        else:
                            # Default weight estimate if not provided
                            default_weight = 10  # tonnes per truck load
                            if unit.lower() in ["miles", "mi"]:
                                calc_amount = amount * 1.60934 * default_weight
                            else:
                                calc_amount = amount * default_weight
                            calc_unit = "tkm"
                            print(f"  🚛 Freight conversion (default weight): {amount} {unit} × {default_weight} tonnes = {calc_amount} tkm")
                    
                    calculation_result = await climatiq_service.calculate_with_classification(
                        classification=climatiq_classification,
                        amount=calc_amount,
                        unit=calc_unit,
                        region=region,
                        year=year
                    )
                except Exception as e:
                    print(f"  Climatiq calculation failed: {e}, trying fallback")
                    # Fallback to old method
                    calculation_result = await climatiq_service.calculate_with_ai_suggestion(
                        text=description,
                        amount=amount,
                        unit=unit,
                        unit_type=unit_type,
                        region=region,
                        year=year
                    )
                
                # Extract co2e
                estimate = calculation_result.get("estimate", {})
                endpoint_type = calculation_result.get("endpoint_type", "autopilot")
                co2e = estimate.get("co2e", 0)
                
                # Debug output
                print(f"DEBUG - Endpoint type: {endpoint_type}")
                print(f"DEBUG - CO2e value: {co2e}")
                
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
                
                # Determine activity_type based on unit_type and description
                desc_lower = description.lower()
                if unit_type == "energy":
                    if any(word in desc_lower for word in ['electricity', 'electric', 'power', 'grid', 'server']):
                        activity_type_val = "electricity"
                    elif any(word in desc_lower for word in ['gas', 'heating', 'heat']):
                        activity_type_val = "stationary_combustion"
                    else:
                        activity_type_val = "electricity"
                elif unit_type == "volume":
                    if any(word in desc_lower for word in ['diesel', 'fuel', 'gasoline', 'petrol', 'generator']):
                        activity_type_val = "stationary_combustion"
                    else:
                        activity_type_val = "fuel"
                elif unit_type == "distance":
                    if any(word in desc_lower for word in ['flight', 'fly', 'air', 'plane']):
                        activity_type_val = "business_travel"
                    elif any(word in desc_lower for word in ['commute', 'employee']):
                        activity_type_val = "employee_commuting"
                    elif any(word in desc_lower for word in ['car', 'rental', 'vehicle', 'drive']):
                        activity_type_val = "business_travel"
                    else:
                        activity_type_val = "transportation"
                elif unit_type == "money":
                    activity_type_val = "procurement"
                else:
                    activity_type_val = "other"
                
                # Override activity_type from AI classification endpoint for more accuracy
                if climatiq_classification:
                    endpoint = climatiq_classification.get("endpoint", "")
                    if endpoint == "fuel":
                        activity_type_val = "stationary_combustion"
                    elif endpoint == "electricity":
                        activity_type_val = "electricity"
                    elif endpoint == "heat_steam":
                        activity_type_val = "purchased_heat"
                    elif endpoint == "estimate" and "flight" in climatiq_classification.get("activity_search", "").lower():
                        activity_type_val = "business_travel"
                    elif endpoint == "estimate" and "commute" in climatiq_classification.get("activity_search", "").lower():
                        activity_type_val = "employee_commuting"
                    elif endpoint == "freight":
                        activity_type_val = "freight"
                
                activity = EmissionActivity(
                    project_id=project.id,
                    batch_job_id=batch_job.id,
                    activity_type=activity_type_val,
                    # Handle activity_search which may be a string or list, and truncate to 50 chars
                    sub_type=(
                        (" ".join(climatiq_classification.get("activity_search", [])) 
                         if isinstance(climatiq_classification.get("activity_search"), list) 
                         else str(climatiq_classification.get("activity_search", "")))[:50]
                        if climatiq_classification else None
                    ),
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
                        "classification": climatiq_classification,
                        "calculation_response": calculation_result
                    }
                )
                
                db.add(activity)
                db.flush()  # Get activity.id before creating flagged event
                
                # Create a flagged event if CO2e is 0 (emission factor not found)
                if co2e == 0 or co2e is None:
                    endpoint_type = calculation_result.get("endpoint_type", "unknown") if calculation_result else "error"
                    error_msg = ""
                    if calculation_result:
                        estimate_data = calculation_result.get("estimate", {})
                        error_msg = estimate_data.get("error", "No emission factor found for this activity")
                    
                    flagged_event = FlaggedEvent(
                        organization_id=project.organization_id,
                        project_id=project.id,
                        activity_id=activity.id,
                        flag_type="emission_factor_missing",
                        severity="high",
                        rule_id="climatiq_ef_not_found",
                        title=f"No emission factor found: {description[:50]}",
                        description=f"Could not calculate emissions for '{description}' with amount {amount} {unit}. "
                                   f"The Climatiq API ({endpoint_type}) could not find a matching emission factor. {error_msg}",
                        recommendation=f"Verify the activity description is accurate, or consider using a manual emission factor.",
                        evidence={
                            "description": description,
                            "amount": amount,
                            "unit": unit,
                            "classification": climatiq_classification,
                            "endpoint_type": endpoint_type,
                            "api_response": calculation_result
                        },
                        status="open",
                        confidence_score=0.0
                    )
                    db.add(flagged_event)
                    print(f"  ⚠️ Created anomaly flag for zero-emission activity: {description[:50]}")
                
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
    # Verify project ownership
    project = verify_project_access(db, project_id, current_user)
    
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
