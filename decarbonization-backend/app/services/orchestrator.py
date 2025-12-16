from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.state_service import StateService
from app.models.agents import AgentState
import logging

logger = logging.getLogger(__name__)

class WorkflowManager:
    """
    Core Orchestrator for the Agentic Workflow.
    Manages transitions through the DAG:
    Ingest -> Detect_Gap -> Ask_User -> Validate -> Calculate -> Store
    """
    
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.state_service = StateService(db)
        # Import here to avoid circular dependencies if any, or at top if safe. 
        # For now, I'll instantiate inside methods or here if imported at top.
        # But I need to import AnalystService. 

    def determine_next_step(self, current_node: str, current_state: Dict[str, Any]) -> str:
        """
        Determines the next node in the DAG based on current node and state.
        DAG Structure:
        - Ingest -> Detect_Gap
        - Detect_Gap -> Ask_User (if gaps) OR Validate (if no gaps)
        - Ask_User -> Validate
        - Validate -> Calculate (if valid) OR Ask_User (if invalid)
        - Calculate -> Store
        - Store -> END
        """
        if not current_node or current_node == "START":
            return "Ingest"
        
        if current_node == "Ingest":
            return "Detect_Gap"
        
        if current_node == "Detect_Gap":
            # Check for gaps in state
            has_gaps = current_state.get("has_gaps", False)
            if has_gaps:
                return "Ask_User"
            else:
                return "Validate"
        
        if current_node == "Ask_User":
            return "Validate"
            
        if current_node == "Validate":
            # State must rely on the result of the validation that just happened
            # But determine_next_step is purely logic based on state flags.
            # So process_event must update state['is_valid'] before calling this? 
            # OR process_event handles the branching logic?
            # The pattern here seems to be: process_event does work -> updates state -> calls determine_next_step -> updates state with next_node.
            
            is_valid = current_state.get("is_valid", False)
            if is_valid:
                return "Calculate"
            else:
                return "Ask_User"
            
        if current_node == "Calculate":
            return "Store"
            
        if current_node == "Store":
            return "END"
            
        return "END"

    async def process_event(self, event_id: str, user_id: str, thread_id: str, current_state: Dict[str, Any]) -> AgentState:
        """
        Takes an event_id and current_state.
        Executes logic for the CURRENT node (if any work needs to be done BEFORE moving on).
        Then determines the next_step.
        Updates the AgentState table.
        """
        from app.services.analyst_service import AnalystService # Lazy import
        analyst = AnalystService(self.db)

        # Get existing state to know where we are (Or rely on passed current_state which assumes it's the latest Input for this step?)
        # IMPORTANT: The prompt implies `process_event` IS the execution of the step.
        existing_agent_state = await self.state_service.retrieve_thread(thread_id)
        current_node = existing_agent_state.current_node if existing_agent_state else "START"
        
        logger.info(f"Processing logic for node {current_node} (Event: {event_id})")
        
        updated_state = current_state.copy()

        # --- EXECUTE NODE LOGIC ---
        if current_node == "Validate":
            # Analyst validates the data
            # Data usually in 'user_response' or just 'data' from previous steps
            data_to_validate = current_state.get("data", {})
            if "user_response" in current_state:
                # Merge user response if it's the source of correction
                 # Simple merging logic for MVP
                 data_to_validate.update(current_state["user_response"])
            
            is_valid = await analyst.validate_input(data_to_validate)
            updated_state["is_valid"] = is_valid
            updated_state["data"] = data_to_validate # Persist the data being worked on
            
            if not is_valid:
                updated_state["error_message"] = "Invalid input data. Please check values and units."

        elif current_node == "Calculate":
            # Analyst executes calculation
            data_to_calc = current_state.get("data", {})
            # We assume it's valid now
            try:
                # Execute calculation and commit
                transaction = await analyst.execute_calculation(event_id, data_to_calc, user_id)
                updated_state["transaction_id"] = transaction.id
                updated_state["status"] = "success"
            except Exception as e:
                logger.error(f"Calculation step failed: {e}")
                updated_state["status"] = "error"
                updated_state["error_message"] = str(e)
                # Maybe stay on Calculate or go to failure state? 
                # For now proceed to Store (which might handle logging) or just generic error handling
        
        # --- DETERMINE NEXT STEP ---
        next_step = self.determine_next_step(current_node, updated_state)
        
        logger.info(f"Transitioning from {current_node} to {next_step}")
        
        # Update state in DB
        agent_state = await self.state_service.checkpoint_state(
            thread_id=thread_id,
            state=updated_state,
            current_node=next_step,
            user_id=user_id
        )
        
        return agent_state
