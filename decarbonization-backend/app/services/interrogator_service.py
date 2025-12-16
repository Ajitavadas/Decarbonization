"""
The Interrogator - Communication Service (Phase 2.3)
Transforms technical flags into conversational user prompts.
"""
import logging
import google.generativeai as genai
from app.config import settings
from app.schemas.schemas import FlaggedEvent

logger = logging.getLogger(__name__)

class InterrogatorService:
    """
    Service for transforming technical flags into conversational user prompts.
    """
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    async def generate_user_prompt(self, flagged_event: FlaggedEvent) -> str:
        """
        Uses Gemini to transform a technical FlaggedEvent into a conversational question.
        
        Args:
            flagged_event: The technical event flagged by the Auditor
            
        Returns:
            A conversational string question
        """
        prompt = f"""
        You are an intelligent Carbon Accounting Assistant.
        Your goal is to investigate a potential issue identified by the Auditor.
        
        **Technical Flag:**
        Type: {flagged_event.event_type}
        Description: {flagged_event.description}
        Details: {flagged_event.details}
        
        **Task:**
        Draft a polite, conversational, and specific question to ask the facility manager to clarify this issue.
        Do not sound accusatory. Be helpful.
        Example: "I noticed you have a facility in Boston but no heating records for January. Did you use natural gas?"
        
        **Question:**
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Failed to generate prompt: {e}")
            return f"We noticed an issue: {flagged_event.description}. Can you provide more details?"
