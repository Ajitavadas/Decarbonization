"""
Additional tests to boost coverage to 70%+
"""

import pytest
from unittest.mock import patch, MagicMock
import google.generativeai as genai

pytestmark = pytest.mark.asyncio


class TestAuthEdgeCases:
    """Boost coverage for auth module"""
    
    async def test_jwt_handler_create_and_verify(self):
        """Test JWT creation and verification"""
        from app.auth.jwt_handler import create_access_token, verify_token, TokenData
        
        token = create_access_token(data={"sub": "test-user-123"})
        assert token is not None
        
        token_data = verify_token(token)
        assert token_data.subject == "test-user-123"
        
        # Test invalid token
        assert verify_token("invalid-token") is None
    
    async def test_password_utils(self):
        """Test password hashing and verification"""
        from app.utils import get_password_hash, verify_password
        
        password = "TestPass123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPass", hashed) is False


class TestHealthEndpoints:
    """Boost coverage for health module"""
    
    async def test_all_health_checks(self, client):
        """Test all health endpoints"""
        # API health
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "healthy", "service": "api"}
        
        # DB health
        resp = await client.get("/health/db")
        assert resp.status_code == 200
        assert "postgres" in resp.json()
        
        # Redis health
        resp = await client.get("/health/redis")
        assert resp.status_code == 200
        assert "redis" in resp.json()
        
        # All services
        resp = await client.get("/health/all")
        assert resp.status_code == 200
        json_data = resp.json()
        assert "overall_status" in json_data
        assert "services" in json_data


class TestAIClassifierEdgeCases:
    """Boost coverage for AI classifier"""
    
    async def test_ai_classifier_invalid_response(self, mock_gemini):
        """Test handling of invalid Gemini responses"""
        from app.services.ai_classifier_service import AIScopeClassifierService
        
        # Mock invalid JSON
        mock_response = MagicMock()
        mock_response.text = "invalid json {"
        
        with patch.object(genai.GenerativeModel, 'generate_content_async', return_value=mock_response):
            service = AIScopeClassifierService()
            scope, confidence, needs_review = await service.classify_transaction("test", "Fuel")
            
            # Should fallback to safe defaults
            assert scope == 3
            assert confidence == 0.0
            assert needs_review is True
    
    async def test_ai_classifier_markdown_json(self, mock_gemini):
        """Test parsing JSON wrapped in markdown"""
        from app.services.ai_classifier_service import AIScopeClassifierService
        
        mock_response = MagicMock()
        mock_response.text = '```json\n{"scope": 1, "confidence": 0.85}\n```'
        
        with patch.object(genai, 'configure'), \
             patch.object(genai.GenerativeModel, 'generate_content_async', return_value=mock_response):
            
            service = AIScopeClassifierService()
            scope, confidence, needs_review = await service.classify_transaction("test", "Fuel")
            
            assert scope == 1
            assert confidence == 0.85


class TestCSVServiceValidation:
    """Boost coverage for CSV parsing validation"""
    
    async def test_formula_injection_detection(self):
        """Test detection of spreadsheet formula injection"""
        from app.services.csv_service import CSVParsingService
        
        # Test rows with potential formula injection
        malicious_rows = [
            {"description": "=SUM(A1:A10)", "transaction_date": "2025-01-15", "scope": "1", "category": "Fuel", "activity_value": "100", "activity_unit": "liters", "emission_factor_value": "2.3"},
            {"description": "+CMD|", "transaction_date": "2025-01-15", "scope": "1", "category": "Fuel", "activity_value": "100", "activity_unit": "liters", "emission_factor_value": "2.3"},
            {"description": "-HYPERLINK", "transaction_date": "2025-01-15", "scope": "1", "category": "Fuel", "activity_value": "100", "activity_unit": "liters", "emission_factor_value": "2.3"},
            {"description": "@IMPORT", "transaction_date": "2025-01-15", "scope": "1", "category": "Fuel", "activity_value": "100", "activity_unit": "liters", "emission_factor_value": "2.3"},
        ]
        
        for i, row in enumerate(malicious_rows):
            is_valid, error = CSVParsingService.validate_row(row, i)
            assert is_valid is False
            assert "formula injection" in error.lower()
    
    async def test_all_field_length_validations(self):
        """Test all field length validation rules"""
        from app.services.csv_service import CSVParsingService
        
        # Test description too long
        row = {
            "description": "x" * 501,  # Max 500
            "transaction_date": "2025-01-15",
            "scope": "1",
            "category": "Fuel",
            "activity_value": "100",
            "activity_unit": "liters",
            "emission_factor_value": "2.3"
        }
        is_valid, error = CSVParsingService.validate_row(row, 1)
        assert is_valid is False
        assert "Description exceeds 500 characters" in error
        
        # Test category too long
        row["description"] = "Valid"
        row["category"] = "y" * 101  # Max 100
        is_valid, error = CSVParsingService.validate_row(row, 1)
        assert is_valid is False
        assert "Category exceeds 100 characters" in error


class TestOrganizationEndpoints:
    """Boost coverage for organization router"""
    
    async def test_create_and_get_organization(self, client, auth_headers, db_session):
        """Test organization creation and retrieval"""
        # Create organization
        create_data = {
            "name": "Test Org Created",
            "slug": "test-org-created",
            "description": "Test organization"
        }
        
        create_resp = await client.post("/organizations", json=create_data, headers=auth_headers)
        assert create_resp.status_code == 201
        org_data = create_resp.json()
        org_id = org_data["id"]
        
        # Get organization
        get_resp = await client.get(f"/organizations/{org_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == org_id
        assert get_resp.json()["name"] == create_data["name"]
        
        # List organizations
        list_resp = await client.get("/organizations", headers=auth_headers)
        assert list_resp.status_code == 200
        assert isinstance(list_resp.json(), list)
        assert len(list_resp.json()) > 0
    
    async def test_duplicate_slug_error(self, client, auth_headers, test_org):
        """Test error for duplicate organization slug"""
        duplicate_data = {
            "name": "Duplicate Org",
            "slug": test_org.slug,  # Already exists
            "description": "Duplicate"
        }
        
        resp = await client.post("/organizations", json=duplicate_data, headers=auth_headers)
        assert resp.status_code == 409  # Conflict


class TestImportService:
    """Boost coverage for import service"""
    
    async def test_bulk_insert_batching(self, db_session):
        """Test that bulk insert uses batching correctly"""
        from app.services.import_service import ImportService
        from app.models.models import EmissionTransaction
        
        # Create test transactions (more than batch size)
        transactions = []
        for i in range(1500):  # > default batch size of 1000
            tx = EmissionTransaction(
                id=f"tx-{i}",
                organization_id="test-org-123",
                description=f"Transaction {i}",
                transaction_date=datetime.now(timezone.utc),
                scope=1,
                category="Fuel",
                activity_value=100.0,
                activity_unit="liters",
                emission_factor_value=2.3,
                co2e_kg=230.0,
                co2e_tonnes=0.23,
                created_by_user_id="test-user-123"
            )
            transactions.append(tx)
        
        # Ensure test org and user exist
        from app.models.models import Organization, User
        org = Organization(id="test-org-123", name="Test Org", slug="test-org", is_active=True)
        user = User(
            id="test-user-123",
            email="bulk@test.com",
            username="bulkuser",
            hashed_password="dummy",
            organization_id="test-org-123"
        )
        db_session.add_all([org, user])
        await db_session.flush()
        
        # Perform bulk insert
        successful, errors = await ImportService.bulk_insert_transactions(db_session, transactions)
        
        assert successful == 1500
        assert len(errors) == 0
        
        # Verify in database
        stmt = select(EmissionTransaction).where(EmissionTransaction.organization_id == "test-org-123")
        result = await db_session.execute(stmt)
        count = len(result.scalars().all())
        assert count == 1500