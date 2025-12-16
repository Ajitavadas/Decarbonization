
import asyncio
import logging
from datetime import datetime, timezone
import sys
import os
import uuid

# In Docker /app is root, so typical imports work
# We don't need sys.path hacks if running from /app

from app.database import async_session
from app.services.auditor_service import AuditorService
from app.services.gap_service import GapService
from app.models.models import EmissionTransaction, FlaggedEvent, EmissionFactor
from app.services.orchestrator import WorkflowManager
from app.models.agents import AgentState
from sqlalchemy import select, text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_phase2_integration():
    """
    Test Phase 2 Trinity:
    1. Seed data that creates a 'Gap'.
    2. Run Auditor -> Detect Gap -> Flag Event.
    3. Verify Notification/Interrogator trigger (mocked).
    4. Run Orchestrator to simulate picking up the flagged event.
    """
    logger.info("Starting Phase 2 Integration Test (Internal)")
    
    async with async_session() as db:
        # Cleanup
        await db.execute(text("DELETE FROM flagged_events"))
        await db.execute(text("DELETE FROM emission_transactions"))
        await db.execute(text("DELETE FROM agent_states"))
        await db.execute(text("DELETE FROM users WHERE id = 'test-user-phase2'"))
        await db.execute(text("DELETE FROM organizations WHERE id = 'test-org-phase2'"))
        await db.commit()
        
        # 1. Setup Data: Cold Region (US-NE) in Jan, but only Electricity
        from app.models.models import Organization, User
        
        # Create Org
        org = Organization(
            id="test-org-phase2",
            name="Test Org Phase 2",
            slug="test-org-phase2"
        )
        db.add(org)
        
        # Create User
        user = User(
            id="test-user-phase2",
            email="test-phase2@example.com",
            username="test-user-phase2",
            hashed_password="hashed_secret",
            organization_id=org.id
        )
        db.add(user)
        await db.flush()
        
        org_id = org.id
        user_id = user.id
        
        # Create Mock Transaction
        tx = EmissionTransaction(
            organization_id=org_id,
            description="Office Lights",
            transaction_date=datetime(2025, 1, 15, tzinfo=timezone.utc),
            scope=2,
            category="Purchased Electricity",
            activity_value=100,
            activity_unit="kwh",
            emission_factor_value=0.5,
            co2e_kg=50.0,
            co2e_tonnes=0.05,
            created_by_user_id=user_id
        )
        # We need an EF to link to US-NE
        ef = EmissionFactor(
             name="Grid NE",
             source="EPA",
             scope=2,
             category="Electricity",
             factor_value=0.5,
             factor_unit="kg/kwh",
             region="US-NE", # Crucial for Gap Detection
             effective_date=datetime(2023,1,1, tzinfo=timezone.utc)
        )
        db.add(ef)
        await db.flush()
        
        tx.emission_factor_id = ef.id
        db.add(tx)
        await db.commit()
        
        logger.info("✅ Seeded Data: 1 Electricity TX in US-NE (Jan)")
        
        # 2. Run Auditor
        logger.info("🏃 Running Auditor...")
        results = await AuditorService.run_audit(db, org_id, user_id=user_id)
        
        logger.info(f"Auditor Results: {results}")
        
        # Verify Gap Detected
        if results["gaps"] > 0:
            logger.info("✅ Gap Detected")
        else:
            logger.error("❌ No Gap Detected")
            return
            
        # Verify Flagged Event in DB
        stmt = select(FlaggedEvent).where(FlaggedEvent.type == 'gap')
        result = await db.execute(stmt)
        event = result.scalars().first()
        
        if event:
             logger.info(f"✅ FlaggedEvent Persisted: {event.description}")
        else:
             logger.error("❌ FlaggedEvent not found in DB")
             return

        # 3. Simulate Orchestrator Pickup
        orchestrator = WorkflowManager(db)
        input_data = {
            "event_id": event.id, 
            "user_response": "Here is the gas bill",
            "has_gaps": True # Simulate that valid gap was detected
        }
        
        logger.info("🏃 Starting Orchestrator Workflow...")
        import uuid
        thread_id = str(uuid.uuid4())
        
        try:
            # First transition: START -> Ingest
            state = await orchestrator.process_event(
                event_id=str(event.id),
                user_id=user_id,
                thread_id=thread_id,
                current_state=input_data
            )
            logger.info(f"✅ Workflow Step 1: {state.current_node}") # Should be 'Ingest'
            
            # Second transition: Ingest -> Detect_Gap
            state = await orchestrator.process_event(
                event_id=str(event.id),
                user_id=user_id,
                thread_id=thread_id,
                current_state=state.state
            )
            logger.info(f"✅ Workflow Step 2: {state.current_node}") # Should be 'Detect_Gap'
            
            # Third transition: Detect_Gap -> Ask_User (since has_gaps=True)
            state = await orchestrator.process_event(
                event_id=str(event.id),
                user_id=user_id,
                thread_id=thread_id,
                current_state=state.state
            )
            logger.info(f"✅ Workflow Step 3: {state.current_node}")
            
            if state.current_node == "Ask_User":
                logger.info("✅ Orchestrator correctly routed to Ask_User based on gap detection.")
            else:
                logger.error(f"❌ Orchestrator Validation Failed. Expected 'Ask_User', got '{state.current_node}'")

        except Exception as e:
            logger.error(f"Orchestrator failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_phase2_integration())
