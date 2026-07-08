"""
Batch processing functions (converted from Celery tasks)
Synchronous processing of emission calculation batches
"""

from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.db.session import SessionLocal
from app.models.batch_job import BatchJob
from app.models.activity import EmissionActivity

logger = logging.getLogger(__name__)


def process_batch_estimates(job_id: str, project_id: str, estimates: List[Dict[str, Any]]):
    """
    Process batch emission estimates
    
    Args:
        job_id: Batch job ID for tracking
        project_id: Project to associate activities with
        estimates: List of emission calculation requests
    """
    db = SessionLocal()
    
    try:
        # Update job status
        job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
        if not job:
            return {"error": "Job not found"}
        
        job.status = "processing"
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Process estimates in chunks
        results = []
        errors = []
        
        for idx, estimate in enumerate(estimates):
            try:
                # Calculate emission using Climatiq service directly
                import asyncio
                from app.integration.climatiq.service import ClimatiqService
                climatiq_service = ClimatiqService()
                
                result = asyncio.run(climatiq_service.calculate_autopilot(
                    text=estimate.get("description", ""),
                    amount=estimate["parameters"].get("amount", 0),
                    unit=estimate["parameters"].get("unit", "kWh"),
                    region=estimate.get("region", "US"),
                    year=estimate.get("year", 2024)
                ))
                
                # Save activity
                activity = EmissionActivity(
                    project_id=project_id,
                    batch_job_id=job_id,
                    activity_type=estimate.get("activity_type", "unknown"),
                    sub_type=estimate.get("sub_type"),
                    scope=result["scope"],
                    activity_date=datetime.fromisoformat(estimate["activity_date"]) if "activity_date" in estimate else datetime.utcnow(),
                    co2e_kg=result["co2e_kg"],
                    co2e_unit=result["co2e_unit"],
                    calculation_method=result["calculation_method"],
                    input_data=estimate,
                    emission_factor_id=estimate["activity_id"],
                    region=estimate.get("region"),
                    year=str(estimate.get("year")) if estimate.get("year") else None
                )
                db.add(activity)
                db.commit()
                
                job.successful_records += 1
                results.append({"row": idx, "co2e_kg": result["co2e_kg"], "activity_id": str(activity.id)})
                
            except Exception as e:
                job.failed_records += 1
                error_entry = {"row": idx, "error": str(e)}
                errors.append(error_entry)
                job.error_log.append(error_entry)
            
            finally:
                job.processed_records += 1
                db.commit()

                # Log progress
                logger.info(
                    f"Batch job {job_id}: {job.processed_records}/{job.total_records} "
                    f"({job.progress_percentage:.1f}%)"
                )
        
        # Mark job as completed
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.results = {"successful": results, "failed": errors}
        db.commit()
        
        return {
            "status": "completed",
            "total": job.total_records,
            "successful": job.successful_records,
            "failed": job.failed_records
        }
        
    except Exception as e:
        # Mark job as failed
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()
        
        return {"status": "failed", "error": str(e)}
        
    finally:
        db.close()


def process_csv_upload(job_id: str, project_id: str, file_path: str):
    """
    Process CSV file upload for batch emissions
    
    Args:
        job_id: Batch job ID
        project_id: Project ID
        file_path: Path to uploaded CSV file
    """
    import csv
    
    db = SessionLocal()
    
    try:
        job = db.query(BatchJob).filter(BatchJob.id == job_id).first()
        if not job:
            return {"error": "Job not found"}
        
        job.status = "processing"
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Read CSV file
        estimates = []
        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert CSV row to estimate request format
                estimate = {
                    "activity_id": row.get("activity_id"),
                    "activity_type": row.get("activity_type"),
                    "parameters": {
                        "energy": float(row["energy"]) if "energy" in row else None,
                        "energy_unit": row.get("energy_unit"),
                        "weight": float(row["weight"]) if "weight" in row else None,
                        "weight_unit": row.get("weight_unit"),
                        "money": float(row["money"]) if "money" in row else None,
                        "money_unit": row.get("money_unit")
                    },
                    "region": row.get("region"),
                    "year": int(row["year"]) if "year" in row else None,
                    "activity_date": row.get("activity_date")
                }
                # Remove None values from parameters
                estimate["parameters"] = {k: v for k, v in estimate["parameters"].items() if v is not None}
                estimates.append(estimate)
        
        job.total_records = len(estimates)
        db.commit()
        
        # Process estimates
        return process_batch_estimates(job_id, project_id, estimates)
        
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()
        return {"status": "failed", "error": str(e)}
        
    finally:
        db.close()
