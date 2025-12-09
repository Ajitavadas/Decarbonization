"""Copilot Router - US-4.1"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.oauth2_scheme import get_current_user
from app.models.models import User
from app.services.copilot_service import CopilotService

router = APIRouter(prefix="/api/v1/copilot", tags=["copilot"])
copilot = CopilotService()


@router.post("/query")
async def query_copilot(
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Query Carbon Copilot (US-4.1)
    
    AC:
    - Chatbot correctly answers 80% or more of questions
    - Responses in under 2 seconds
    - Handles 10+ question types
    """
    # Get user's organization
    user_result = await db.execute(select(User).where(User.id == current_user))
    user = user_result.scalar_one_or_none()
    
    result = await copilot.process_query(
        db=db,
        org_id=user.organization_id,
        user_query=query,
        session_id=current_user
    )
    
    return result