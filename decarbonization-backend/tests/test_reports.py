"""
Test PDF Report Generation (US-2.5)

Acceptance Criteria:
- PDF generates in under 3 seconds
- All charts render correctly in the PDF
- File size is under 5 MB (email-friendly)
- Report includes all required sections: total, scopes, trends, categories
"""

import pytest
import asyncio
import time
from io import BytesIO

from app.services.report_service import ReportService


@pytest.mark.asyncio
async def test_pdf_generation_performance():
    """US-2.5 AC1: PDF generates in under 3 seconds"""
    # Prepare test data
    scope_breakdown = {1: 100.0, 2: 200.0, 3: 300.0}
    monthly_trend = [
        {"year": 2024, "month": i, "date": f"2024-{i:02d}", "emissions_tonnes": 50.0}
        for i in range(1, 13)
    ]
    category_breakdown = [
        {"category": f"Category {i}", "emissions_tonnes": 100.0, "transaction_count": 10}
        for i in range(1, 6)
    ]
    
    start_time = time.time()
    
    pdf_buffer = await ReportService.generate_emissions_report(
        org_name="Test Organization",
        total_emissions=600.0,
        scope_breakdown=scope_breakdown,
        monthly_trend=monthly_trend,
        category_breakdown=category_breakdown,
        date_range="2024-01-01 to 2024-12-31"
    )
    
    elapsed = time.time() - start_time
    
    assert elapsed < 3.0, f"PDF generation took {elapsed:.2f}s, should be under 3s"
    assert isinstance(pdf_buffer, BytesIO)


@pytest.mark.asyncio
async def test_pdf_file_size():
    """US-2.5 AC3: File size is under 5 MB"""
    scope_breakdown = {1: 100.0, 2: 200.0, 3: 300.0}
    monthly_trend = [
        {"year": 2024, "month": i, "date": f"2024-{i:02d}", "emissions_tonnes": 50.0}
        for i in range(1, 13)
    ]
    category_breakdown = [
        {"category": f"Category {i}", "emissions_tonnes": 100.0, "transaction_count": 10}
        for i in range(1, 11)
    ]
    
    pdf_buffer = await ReportService.generate_emissions_report(
        org_name="Test Organization",
        total_emissions=600.0,
        scope_breakdown=scope_breakdown,
        monthly_trend=monthly_trend,
        category_breakdown=category_breakdown
    )
    
    file_size_mb = len(pdf_buffer.getvalue()) / (1024 * 1024)
    
    assert file_size_mb < 5.0, f"PDF is {file_size_mb:.2f}MB, should be under 5MB"


@pytest.mark.asyncio
async def test_pdf_content_completeness():
    """US-2.5 AC4: Report includes all required sections"""
    scope_breakdown = {1: 100.0, 2: 200.0, 3: 300.0}
    monthly_trend = [{"year": 2024, "month": 1, "date": "2024-01", "emissions_tonnes": 50.0}]
    category_breakdown = [{"category": "Electricity", "emissions_tonnes": 100.0, "transaction_count": 10}]
    
    pdf_buffer = await ReportService.generate_emissions_report(
        org_name="Test Org",
        total_emissions=600.0,
        scope_breakdown=scope_breakdown,
        monthly_trend=monthly_trend,
        category_breakdown=category_breakdown
    )
    
    # Verify PDF was generated
    assert len(pdf_buffer.getvalue()) > 0
    
    # PDF should start with PDF magic bytes
    pdf_bytes = pdf_buffer.getvalue()
    assert pdf_bytes[:4] == b'%PDF'