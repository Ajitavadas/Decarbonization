"""Copilot Router - US-4.1"""

from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.auth.oauth2_scheme import get_current_user
from app.models.models import User
from app.services.copilot_service import CopilotService

router = APIRouter(prefix="/api/v1/copilot", tags=["copilot"])
copilot = CopilotService()

class CopilotQuery(BaseModel):
    query: str

@router.post("/query")
async def query_copilot(
    query_data: CopilotQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Query Carbon Copilot (US-4.1)
    
    AC:
    - Chatbot correctly answers 80% or more of questions
    - Responses in under 2 seconds
    - Handles 10+ question types
    """
    result = await copilot.process_query(
        db=db,
        org_id=current_user.organization_id,
        user_query=query_data.query,
        session_id=current_user.id
    )
    
    return result