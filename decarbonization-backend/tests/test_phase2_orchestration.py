import pytest
from app.services.state_service import StateService
from app.services.orchestrator import WorkflowManager
from app.models.agents import AgentState
import uuid

@pytest.mark.asyncio
async def test_state_persistence(db_session, test_user):
    service = StateService(db_session)
    thread_id = str(uuid.uuid4())
    state = {"key": "value"}
    
    # 1. Checkpoint (Create)
    agent_state = await service.checkpoint_state(
        thread_id=thread_id,
        state=state,
        current_node="START",
        user_id=test_user.id
    )
    assert agent_state.thread_id == thread_id
    assert agent_state.state == state
    assert agent_state.current_node == "START"
    assert agent_state.user_id == test_user.id
    
    # 2. Retrieve
    retrieved = await service.retrieve_thread(thread_id)
    assert retrieved is not None
    assert retrieved.thread_id == thread_id
    assert retrieved.state["key"] == "value"
    
    # 3. Update
    new_state = {"key": "updated", "step": 2}
    updated = await service.checkpoint_state(
        thread_id=thread_id,
        state=new_state,
        current_node="Ingest",
        user_id=test_user.id
    )
    assert updated.state["key"] == "updated"
    assert updated.current_node == "Ingest"

@pytest.mark.asyncio
async def test_orchestrator_flow(db_session, test_user):
    manager = WorkflowManager(db_session)
    thread_id = str(uuid.uuid4())
    
    # 1. Start -> Ingest
    # Initial state creation is implicit if not exists, but orchestrator uses retrieve_thread.
    # process_event logic: retrieves existing, if None defaults current_node="START".
    # Then determine_next_step("START") -> "Ingest"
    
    state_start = {}
    result = await manager.process_event("event1", test_user.id, thread_id, state_start)
    assert result.current_node == "Ingest"
    
    # 2. Ingest -> Detect_Gap
    result = await manager.process_event("event2", test_user.id, thread_id, state_start)
    assert result.current_node == "Detect_Gap"
    
    # 3. Detect_Gap -> Validate (no gaps)
    state_no_gaps = {"has_gaps": False}
    result = await manager.process_event("event3", test_user.id, thread_id, state_no_gaps)
    assert result.current_node == "Validate"
    
    # 3b. Detect_Gap -> Ask_User (has gaps)
    # Manually reset to Detect_Gap to test branching
    await manager.state_service.checkpoint_state(thread_id, {}, "Detect_Gap", test_user.id)
    state_has_gaps = {"has_gaps": True}
    result = await manager.process_event("event3b", test_user.id, thread_id, state_has_gaps)
    assert result.current_node == "Ask_User"
    
    # 4. Ask_User -> Validate
    result = await manager.process_event("event4", test_user.id, thread_id, state_has_gaps)
    assert result.current_node == "Validate"
    
    # 5. Validate -> Calculate
    result = await manager.process_event("event5", test_user.id, thread_id, {})
    assert result.current_node == "Calculate"
    
    # 6. Calculate -> Store
    result = await manager.process_event("event6", test_user.id, thread_id, {})
    assert result.current_node == "Store"
    
    # 7. Store -> END
    result = await manager.process_event("event7", test_user.id, thread_id, {})
    assert result.current_node == "END"
