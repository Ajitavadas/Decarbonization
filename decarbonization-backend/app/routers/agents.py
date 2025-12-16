
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database import get_db
from app.services.analyst_service import AnalystService
from app.models.models import User 

router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("/analyst/process")
async def process_analyst_request(
    payload: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger Analyst processing (Validation -> Calculation).
    Payload should contain:
    - event_id: str (optional, if resolving a flag)
    - data: Dict (activity_value, unit, etc.)
    - user_id: str (for audit)
    """
    try:
        analyst = AnalystService(db)
        
        data = payload.get("data", {})
        event_id = payload.get("event_id")
        user_id = payload.get("user_id", "manual_test_user") # Default for testing

        # 1. Validate
        is_valid = await analyst.validate_input(data)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid input data")

        # 2. Calculate & Commit
        transaction = await analyst.execute_calculation(event_id, data, user_id)
        
        return {
            "status": "success",
            "transaction_id": transaction.id,
            "co2e_kg": transaction.co2e_kg,
            "resolved_event_id": event_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
