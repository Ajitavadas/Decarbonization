

from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from app.main import app
from app.schemas.schemas import FlaggedEvent

# Mock genai before importing service/routers that use it
with patch("google.generativeai.GenerativeModel") as mock_model_cls:
    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(return_value=MagicMock(text="Mocked conversational question?"))
    mock_model_cls.return_value = mock_model
    
    from app.routers.notifications import router, manager
    from app.services.interrogator_service import InterrogatorService

client = TestClient(app)

def test_websocket_notification_flow():
    user_id = "test_user_1"
    
    # Mock the interrogator service used by the router
    # We need to patch the instance in the router module
    with patch("app.routers.notifications.interrogator_service.generate_user_prompt", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = "Hey! We noticed missing heating data. Can you check?"
        
        # 1. Connect WebSocket
        with client.websocket_connect(f"/ws/notifications/{user_id}") as websocket:
            
            # 2. Trigger event
            event_data = {
                "event_id": "evt_001",
                "organization_id": "org_001",
                "event_type": "gap",
                "description": "Missing Scope 1 Heating",
                "severity": "medium",
                "details": {"facility": "Boston"},
                # Pydantic expects ISO format string for datetime in JSON
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            response = client.post(f"/ws/test-trigger/{user_id}", json=event_data)
            assert response.status_code == 200
            
            # 3. Verify WebSocket received the message
            data = websocket.receive_json()
            
            assert data["type"] == "prompt"
            assert data["user_id"] == user_id
            assert data["content"] == "Hey! We noticed missing heating data. Can you check?"
            assert data["event_ref"] == "evt_001"
            
            print("\n✅ WebSocket received correct notification:")
            print(data)

if __name__ == "__main__":
    test_websocket_notification_flow()
