#!/usr/bin/env python3
"""
Test Report Generation Feature
Tests PDF and HTML report generation with real data
"""

import requests
import json
import random
import time
import os
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"
CSV_FILE = str(Path(__file__).resolve().parent.parent / "test_fresh.csv")
RANDOM_SUFFIX = random.randint(10000, 99999)

def main():
    print("\n" + "="*70)
    print("📊 TESTING REPORT GENERATION FEATURE")
    print("="*70 + "\n")
    
    # Step 1: Register new user
    print("📝 Step 1: Registering test user...")
    email = f"report_test{RANDOM_SUFFIX}@test.com"
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": "TestPass123!",
            "full_name": f"Report Test User {RANDOM_SUFFIX}"
        }
    )
    
    if response.status_code != 201:
        print(f"❌ Registration failed: {response.text}")
        return
    
    token = response.json().get("access_token")
    user_id = response.json().get("user", {}).get("id")
    print(f"✅ Registered: {email}")
    print(f"   User ID: {user_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Create project
    print("\n📁 Step 2: Creating project...")
    response = requests.post(
        f"{BASE_URL}/projects/",
        headers=headers,
        json={
            "name": f"Report Test Project {RANDOM_SUFFIX}",
            "description": "Testing report generation feature",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "reporting_year": "2025"
        }
    )
    
    if response.status_code != 201:
        print(f"❌ Project creation failed: {response.text}")
        return
    
    project = response.json()
    project_id = project["id"]
    print(f"✅ Project created: {project['name']}")
    print(f"   Project ID: {project_id}")
    
    # Step 3: Upload CSV with sample data
    print(f"\n📤 Step 3: Uploading test CSV...")
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "rb") as f:
            response = requests.post(
                f"{BASE_URL}/upload/csv",
                headers=headers,
                files={"file": (CSV_FILE, f, "text/csv")},
                data={"project_id": project_id}
            )
    else:
        print(f"⚠️  {CSV_FILE} not found, skipping upload step")
        print("   You can manually upload data via the frontend or create sample activities")
        response = None
    
    if response and response.status_code == 200:
        upload_result = response.json()
        print(f"✅ Upload successful!")
        print(f"   Total records: {upload_result.get('total_records')}")
        time.sleep(3)  # Wait for processing
    
    # Step 4: Test Report Summary JSON endpoint
    print("\n📊 Step 4: Testing Report Summary (JSON)...")
    response = requests.get(
        f"{BASE_URL}/projects/{project_id}/report-summary",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Report summary failed: {response.text}")
        return
    
    summary = response.json()
    print(f"✅ Report summary generated!")
    print(f"   Total Activities: {summary['summary']['total_activities']}")
    print(f"   Total CO2e: {summary['summary']['total_co2e_kg']:.2f} kg")
    print(f"   Scope Breakdown: {summary['summary']['scope_breakdown']}")
    
    # Step 5: Test PDF Report Generation
    print("\n📄 Step 5: Testing PDF Report Generation...")
    response = requests.get(
        f"{BASE_URL}/projects/{project_id}/report?format=pdf",
        headers=headers,
        stream=True
    )
    
    if response.status_code != 200:
        print(f"❌ PDF report generation failed: {response.text}")
        return
    
    pdf_filename = f"carbon_report_{project_id}.pdf"
    with open(pdf_filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    file_size = os.path.getsize(pdf_filename)
    print(f"✅ PDF report generated successfully!")
    print(f"   File: {pdf_filename}")
    print(f"   Size: {file_size:,} bytes")
    print(f"   Content-Type: {response.headers.get('Content-Type')}")
    
    # Step 6: Test HTML Report Generation
    print("\n🌐 Step 6: Testing HTML Report Generation...")
    response = requests.get(
        f"{BASE_URL}/projects/{project_id}/report?format=html",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ HTML report generation failed: {response.text}")
        return
    
    html_filename = f"carbon_report_{project_id}.html"
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    file_size = os.path.getsize(html_filename)
    print(f"✅ HTML report generated successfully!")
    print(f"   File: {html_filename}")
    print(f"   Size: {file_size:,} bytes")
    print(f"   Content-Type: {response.headers.get('Content-Type')}")
    
    # Summary
    print("\n" + "="*70)
    print("✅ REPORT GENERATION TEST COMPLETED SUCCESSFULLY")
    print("="*70)
    print("\n📋 Test Results:")
    print(f"   ✓ User Registration")
    print(f"   ✓ Project Creation")
    print(f"   ✓ Report Summary JSON")
    print(f"   ✓ PDF Report Generation")
    print(f"   ✓ HTML Report Generation")
    print(f"\n📁 Generated Files:")
    print(f"   • {pdf_filename}")
    print(f"   • {html_filename}")
    print("\n💡 You can open these files to verify the report format!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
