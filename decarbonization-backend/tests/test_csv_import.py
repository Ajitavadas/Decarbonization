import pytest
from app.services.csv_service import CSVParsingService
from datetime import datetime, timezone

from app.models.models import EmissionTransaction
from sqlalchemy import select


class TestCSVParsing:
    """Tests for CSV parsing service"""
    
    def test_parse_valid_csv(self):
        """AC2: Test parsing valid CSV file"""
        csv_content = b"""description,transaction_date,scope,category,activity_value,activity_unit,emission_factor_value
Electricity usage,2025-01-15,2,Electricity,100,kWh,0.4
Fuel consumption,2025-01-16,1,Fuel,50,liters,2.3"""
        
        valid_rows, error_rows = CSVParsingService.parse_csv(csv_content)
        
        assert len(valid_rows) == 2, "Should parse 2 valid rows"
        assert len(error_rows) == 0, "Should have no errors"
        assert valid_rows[0]['description'] == 'Electricity usage'
        assert valid_rows[1]['scope'] == '1'
    
    def test_parse_csv_with_invalid_scope(self):
        """AC3: Test CSV with invalid scope value"""
        csv_content = b"""description,transaction_date,scope,category,activity_value,activity_unit,emission_factor_value
Test,2025-01-15,4,Electricity,100,kWh,0.4"""
        
        valid_rows, error_rows = CSVParsingService.parse_csv(csv_content)
        
        assert len(valid_rows) == 0, "Should reject invalid scope"
        assert len(error_rows) == 1, "Should report 1 error"
        assert "Scope must be 1, 2, or 3" in error_rows[0]['error']
    
    def test_parse_csv_missing_required_field(self):
        """AC3: Test CSV missing required field"""
        csv_content = b"""description,transaction_date,category,activity_value,activity_unit,emission_factor_value
Test,2025-01-15,Electricity,100,kWh,0.4"""
        
        valid_rows, error_rows = CSVParsingService.parse_csv(csv_content)
        
        assert len(error_rows) >= 1, "Should report error for missing field"
        assert any("scope" in e['error'].lower() for e in error_rows), "Should mention 'scope' field"
    
    def test_calculate_co2e(self):
        """Test CO2e calculation"""
        co2e_kg, co2e_tonnes = CSVParsingService.calculate_co2e(100, 0.4)
        
        assert co2e_kg == 40.0, f"Expected 40.0 kg CO2e, got {co2e_kg}"
        assert co2e_tonnes == 0.04, f"Expected 0.04 tonnes CO2e, got {co2e_tonnes}"
    
    def test_calculate_co2e_large_values(self):
        """Test CO2e calculation with large values"""
        co2e_kg, co2e_tonnes = CSVParsingService.calculate_co2e(1000, 2.5)
        
        assert co2e_kg == 2500.0
        assert co2e_tonnes == 2.5
    
    def test_validate_row_invalid_date(self):
        """AC3: Test validation with invalid date format"""
        row = {
            'description': 'Test',
            'transaction_date': '15-01-2025',  # Wrong format
            'scope': '1',
            'category': 'Fuel',
            'activity_value': '100',
            'activity_unit': 'liters',
            'emission_factor_value': '2.3'
        }
        
        is_valid, error_msg = CSVParsingService.validate_row(row, 2)
        
        assert is_valid == False, "Should reject invalid date"
        assert "Invalid date format" in error_msg
    
    def test_validate_row_negative_activity_value(self):
        """AC3: Test validation with negative activity value"""
        row = {
            'description': 'Test',
            'transaction_date': '2025-01-15',
            'scope': '1',
            'category': 'Fuel',
            'activity_value': '-100',
            'activity_unit': 'liters',
            'emission_factor_value': '2.3'
        }
        
        is_valid, error_msg = CSVParsingService.validate_row(row, 2)
        
        assert is_valid == False
        assert "must be positive" in error_msg
    
    def test_parse_1000_row_csv_performance(self):
        """AC2: Test parsing 1000-row CSV in <5 seconds"""
        import time
        
        # Create 1000-row CSV
        rows = ["description,transaction_date,scope,category,activity_value,activity_unit,emission_factor_value"]
        for i in range(1000):
            rows.append(f"Transaction {i},2025-01-15,1,Fuel,100,liters,2.3")
        
        csv_content = "\n".join(rows).encode('utf-8')
        
        start = time.time()
        valid_rows, error_rows = CSVParsingService.parse_csv(csv_content)
        elapsed = time.time() - start
        
        assert elapsed < 5, f"Parsing took {elapsed}s, expected < 5s"
        assert len(valid_rows) == 1000
        assert len(error_rows) == 0


class TestBulkInsertPerformance:
    """Tests related to bulk inserting emission transactions."""
    
    @pytest.mark.asyncio
    async def test_insert_1000_rows_under_10_seconds(self, db_session):
        """AC4: Insert 1000 rows in < 10 seconds."""
        import time
        
        transactions = []
        for i in range(1000):
            tx = EmissionTransaction(
                # Use a simple org id that exists in this isolated test DB
                organization_id="test-org",
                description=f"Transaction {i}",
                transaction_date=datetime.now(timezone.utc),
                scope=1,
                category="Fuel",
                activity_value=100.0,
                activity_unit="liters",
                emission_factor_value=2.3,
                co2e_kg=230.0,
                co2e_tonnes=0.23,
                created_by_user_id="test-user",
            )
            transactions.append(tx)
        
        # Ensure organization exists to satisfy FK constraint
        from app.models.models import Organization, User
        org = Organization(id="test-org", name="Test Org", slug="test-org")
        user = User(
            id="test-user",
            email="bulk@test.com",
            username="bulkuser",
            hashed_password="dummy",
            organization_id="test-org",
            is_active=True,
        )
        db_session.add_all([org, user])
        await db_session.commit()

        start = time.time()
        db_session.add_all(transactions)
        await db_session.commit()
        elapsed = time.time() - start
        
        assert elapsed < 10, f"Insert took {elapsed}s, expected < 10s"
        
        # Verify records persisted
        stmt = select(EmissionTransaction).where(EmissionTransaction.organization_id == "test-org")
        result = await db_session.execute(stmt)
        rows = result.scalars().all()
        assert len(rows) >= 1000