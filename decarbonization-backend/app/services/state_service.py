from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agents import AgentState
from typing import Dict, Any, Optional
import uuid

class StateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def retrieve_thread(self, thread_id: str) -> Optional[AgentState]:
        """
        Retrieve existing agent state by thread_id.
        """
        result = await self.db.execute(select(AgentState).where(AgentState.thread_id == thread_id))
        return result.scalar_one_or_none()

    async def checkpoint_state(self, thread_id: str, state: Dict[str, Any], current_node: str, user_id: str = None) -> AgentState:
        """
        Persist the state to the database. Creates a new record if thread_id doesn't exist.
        If creating, user_id is required.
        """
        agent_state = await self.retrieve_thread(thread_id)

        if agent_state:
            agent_state.state = state
            agent_state.current_node = current_node
            # Update updated_at is handled by onupdate in model
        else:
            if not user_id:
                raise ValueError("user_id is required when creating a new state checkpoint")
            
            agent_state = AgentState(
                thread_id=thread_id,
                user_id=user_id,
                state=state,
                current_node=current_node
            )
            self.db.add(agent_state)
        
        await self.db.commit()
        await self.db.refresh(agent_state)
        return agent_state
