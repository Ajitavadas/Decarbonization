"""
Test CO2e Calculation Engine (US-2.2)

Acceptance Criteria:
- All calculations are accurate to 3 decimal places
- Audit trail shows source factor for every calculation
- Process 1,000+ transactions per minute
- Handles edge cases and invalid inputs without crashing
"""

import pytest
from decimal import Decimal

from app.services.calculation_service import CalculationService


def test_basic_calculation_accuracy():
    """US-2.2 AC1: Calculations accurate to 3 decimal places"""
    co2e_kg, co2e_tonnes, audit = CalculationService.calculate_co2e(
        activity_value=100.0,
        emission_factor=0.5,
        activity_unit="kwh"
    )
    
    assert co2e_kg == 50.0
    assert co2e_tonnes == 0.05
    assert isinstance(co2e_kg, float)
    
    # Test precision
    co2e_kg, co2e_tonnes, audit = CalculationService.calculate_co2e(
        activity_value=123.456,
        emission_factor=0.789,
        activity_unit="kwh"
    )
    
    expected = round(123.456 * 0.789, 3)
    assert co2e_kg == expected


def test_audit_trail_completeness():
    """US-2.2 AC2: Audit trail shows source factor"""
    co2e_kg, co2e_tonnes, audit = CalculationService.calculate_co2e(
        activity_value=100.0,
        emission_factor=0.386,
        activity_unit="kwh"
    )
    
    # Verify audit trail contains all required fields
    assert "original_activity_value" in audit
    assert "emission_factor" in audit
    assert "co2e_kg" in audit
    assert "co2e_tonnes" in audit
    assert "calculation_timestamp" in audit
    
    assert audit["emission_factor"] == 0.386
    assert audit["original_activity_value"] == 100.0


def test_unit_conversion():
    """Test various unit conversions"""
    # Test MWh to kWh
    co2e_kg_mwh, _, _ = CalculationService.calculate_co2e(
        activity_value=1.0,
        emission_factor=0.386,
        activity_unit="mwh"
    )
    
    co2e_kg_kwh, _, _ = CalculationService.calculate_co2e(
        activity_value=1000.0,
        emission_factor=0.386,
        activity_unit="kwh"
    )
    
    assert co2e_kg_mwh == co2e_kg_kwh
    
    # Test gallon to liter conversion
    co2e_gal, _, _ = CalculationService.calculate_co2e(
        activity_value=1.0,
        emission_factor=2.31,
        activity_unit="gallon"
    )
    
    co2e_liter, _, _ = CalculationService.calculate_co2e(
        activity_value=3.78541,
        emission_factor=2.31,
        activity_unit="liter"
    )
    
    assert abs(co2e_gal - co2e_liter) < 0.01  # Allow small rounding difference


def test_batch_calculation_performance():
    """US-2.2 AC3: Process 1,000+ transactions per minute"""
    import time
    
    # Create 1000 test transactions
    transactions = [
        {
            "activity_value": 100.0 + i,
            "emission_factor": 0.5,
            "activity_unit": "kwh"
        }
        for i in range(1000)
    ]
    
    start_time = time.time()
    results = CalculationService.batch_calculate(transactions)
    elapsed_time = time.time() - start_time
    
    # Should complete in under 60 seconds (1000+ per minute)
    assert elapsed_time < 60, f"Batch took {elapsed_time:.2f}s, should be under 60s"
    assert len(results) == 1000
    assert all(r["status"] == "success" for r in results)


def test_edge_case_handling():
    """US-2.2 AC4: Handles edge cases without crashing"""
    # Test zero activity value
    with pytest.raises(ValueError):
        CalculationService.calculate_co2e(
            activity_value=0.0,
            emission_factor=0.5
        )
    
    # Test negative values
    with pytest.raises(ValueError):
        CalculationService.calculate_co2e(
            activity_value=-100.0,
            emission_factor=0.5
        )
    
    # Test very large numbers
    co2e_kg, _, _ = CalculationService.calculate_co2e(
        activity_value=1000000.0,
        emission_factor=0.5
    )
    assert co2e_kg == 500000.0
    
    # Test very small numbers
    co2e_kg, _, _ = CalculationService.calculate_co2e(
        activity_value=0.001,
        emission_factor=0.5
    )
    assert co2e_kg == 0.001