
import asyncio
import logging
from datetime import datetime, timezone
import sys
import os

# Add project root to path
# Structure: backend is in decarbonization-backend/
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../decarbonization-backend"))
sys.path.append(backend_path)

from app.database import async_session
from app.services.auditor_service import AuditorService
from app.services.gap_service import GapService
from app.models.models import EmissionTransaction, FlaggedEvent
from app.services.orchestrator import WorkflowManager
from app.models.agents import AgentState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_phase2_integration():
    """
    Test Phase 2 Trinity:
    1. Seed data that creates a 'Gap' (Winter in NE, no heating).
    2. Run Auditor -> Detect Gap -> Flag Event.
    3. Verify Notification/Interrogator trigger (mocked).
    4. Run Orchestrator to simulate picking up the flagged event.
    """
    logger.info("Starting Phase 2 Integration Test")
    
    async with async_session() as db:
        # Cleanup
        await db.execute("DELETE FROM flagged_events")
        await db.execute("DELETE FROM emission_transactions")
        await db.execute("DELETE FROM agent_states")
        await db.commit()
        
        # 1. Setup Data: Cold Region (US-NE) in Jan, but only Electricity
        # We need an EmissionFactor linked to US-NE to trigger the "Cold Region" logic
        # For simplicity, we assume GapService infers region from factor_id's region field if feasible
        # or we rely on the implementation details of GapService.
        
        # Checking implementation: GapService queries EmissionFactor.region
        # So we need to create an EF in US-NE and use it.
        
        from app.models.models import EmissionFactor, Organization, User
        
        # Ensure org exists
        org_id = "test-org-phase2"
        # Create Org if not exists logic omitted, assume clean DB or we create it
        # ...
        
        # Create Mock Transaction
        tx = EmissionTransaction(
            organization_id=org_id,
            description="Office Lights",
            transaction_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
            scope=2,
            category="Purchased Electricity",
            activity_value=100,
            activity_unit="kwh",
            emission_factor_value=0.5,
            co2e_kg=50.0,
            co2e_tonnes=0.05,
            created_by_user_id="test-user"
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
        # This calls GapService -> detects missing heating -> calls _create_flagged_event -> calls notify
        logger.info("🏃 Running Auditor...")
        results = await AuditorService.run_audit(db, org_id, user_id="test-user")
        
        logger.info(f"Auditor Results: {results}")
        
        # Verify Gap Detected
        if results["gaps"] > 0:
            logger.info("✅ Gap Detected")
        else:
            logger.error("❌ No Gap Detected")
            return
            
        # Verify Flagged Event in DB
        from sqlalchemy import select
        stmt = select(FlaggedEvent).where(FlaggedEvent.type == 'gap')
        result = await db.execute(stmt)
        event = result.scalars().first()
        
        if event:
             logger.info(f"✅ FlaggedEvent Persisted: {event.description}")
        else:
             logger.error("❌ FlaggedEvent not found in DB")
             return

        # 3. Simulate Orchestrator Pickup (User responds "Yes, I have gas bill")
        # Initialize Orchestrator
        orchestrator = WorkflowManager(db)
        input_data = {
            "event_id": event.id, 
            "user_response": "Here is the gas bill",
            "has_gaps": True # Simulate that valid gap was detected
        }
        
        # Start Workflow
        logger.info("🏃 Starting Orchestrator Workflow...")
        import uuid
        thread_id = str(uuid.uuid4())
        
        try:
            # First transition: START -> Ingest
            state = await orchestrator.process_event(
                event_id=str(event.id),
                user_id="test-user",
                thread_id=thread_id,
                current_state=input_data
            )
            logger.info(f"✅ Workflow Step 1: {state.current_node}") # Should be 'Ingest'
            
            # Second transition: Ingest -> Detect_Gap
            state = await orchestrator.process_event(
                event_id=str(event.id),
                user_id="test-user",
                thread_id=thread_id,
                current_state=state.state
            )
            logger.info(f"✅ Workflow Step 2: {state.current_node}") # Should be 'Detect_Gap'
            
            # Third transition: Detect_Gap -> Ask_User (since has_gaps=True)
            state = await orchestrator.process_event(
                event_id=str(event.id),
                user_id="test-user",
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
