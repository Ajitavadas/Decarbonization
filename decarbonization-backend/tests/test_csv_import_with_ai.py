"""
Integration tests for CSV Import with AI Classification (US-1.4 & US-1.3 integration)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import tempfile
import os
from unittest.mock import patch, MagicMock
import google.generativeai as genai

from app.main import app
from app.database import get_db
from app.models.models import Base
from app.config import settings

# Test database
TEST_DATABASE_URL = "postgresql+asyncpg://decarb_user:decarb_password@postgres:5432/test_decarb_db"

@pytest.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield async_session()
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
def client(test_db):
    """Test client with mocked AI"""
    app.dependency_overrides[get_db] = lambda: test_db
    
    with patch.object(genai, 'configure'), \
         patch.object(genai.GenerativeModel, 'generate_content_async') as mock_ai:
        
        # Default mock response
        mock_response = MagicMock()
        mock_response.text = '{"scope": 2, "confidence": 0.90}'
        mock_ai.return_value = mock_response
        
        yield TestClient(app)
    
    app.dependency_overrides.clear()

def create_test_csv_content():
    """Create valid CSV content for testing"""
    return """description,transaction_date,scope,category,activity_value,activity_unit,emission_factor_value,supplier_name
Electricity for office,2025-01-15,2,Electricity,1000,kWh,0.5,GridCo
Gas for heating,2025-01-16,1,Fuel,500,liters,2.3,GasCompany
Flight to conference,2025-01-17,3,Business Travel,2000,miles,0.18,Airline"""

def test_csv_upload_with_ai_classification(client):
    """Test complete CSV upload flow with AI classification"""
    csv_content = create_test_csv_content()
    
    # Mock different responses for different transaction types
    def mock_ai_side_effect(*args, **kwargs):
        mock_response = MagicMock()
        description = kwargs.get('description', '')
        
        if 'Electricity' in description:
            mock_response.text = '{"scope": 2, "confidence": 0.95}'
        elif 'Gas' in description:
            mock_response.text = '{"scope": 1, "confidence": 0.92}'
        elif 'Flight' in description:
            mock_response.text = '{"scope": 3, "confidence": 0.88}'
        else:
            mock_response.text = '{"scope": 3, "confidence": 0.65}'  # Low confidence
            
        return mock_response
    
    with patch.object(genai.GenerativeModel, 'generate_content_async', 
                     side_effect=mock_ai_side_effect):
        
        # Login to get token
        response = client.post("/auth/token", data={
            "username": "test@example.com",
            "password": "TestPass123!"
        })
        token = response.json()["access_token"]
        
        # Upload CSV
        files = {
            "file": ("test_emissions.csv", csv_content, "text/csv")
        }
        
        response = client.post(
            "/api/v1/import/csv",
            files=files,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert "import_id" in data
        assert data["status"] == "pending"

def test_ai_low_confidence_flagging(client):
    """Test that low-confidence AI predictions are flagged for review"""
    csv_content = """description,transaction_date,scope,category,activity_value,activity_unit,emission_factor_value
Unknown purchase,2025-01-15,1,Miscellaneous,100,units,1.5"""
    
    # Mock low confidence response
    mock_response = MagicMock()
    mock_response.text = '{"scope": 3, "confidence": 0.60}'  # Below 80% threshold
    
    with patch.object(genai, 'configure'), \
         patch.object(genai.GenerativeModel, 'generate_content_async', 
                     return_value=mock_response):
        
        # Login and upload
        response = client.post("/auth/token", data={
            "username": "test@example.com",
            "password": "TestPass123!"
        })
        token = response.json()["access_token"]
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        response = client.post(
            "/api/v1/import/csv",
            files=files,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 202