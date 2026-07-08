#!/usr/bin/env python3
"""
E2E Test with test_data_20_rows.csv - New user, new org, verify calculations
"""

import requests
import json
import random
import time
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"
CSV_FILE = str(Path(__file__).resolve().parent / "data" / "test_data_20_rows.csv")
RANDOM_SUFFIX = random.randint(10000, 99999)

def main():
    print("\n" + "="*70)
    print("🌍 E2E TEST: Fresh CSV with New User and Organization")
    print("="*70 + "\n")
    
    # Step 1: Register new user
    print("📝 Step 1: Registering new user...")
    email = f"tester{RANDOM_SUFFIX}@neworg.test"
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": "TestPass123!",
            "full_name": f"Test User {RANDOM_SUFFIX}"
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
            "name": f"Fresh CSV Test {RANDOM_SUFFIX}",
            "description": "Testing all emission types",
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
    
    # Step 3: Upload CSV
    print(f"\n📤 Step 3: Uploading {CSV_FILE}...")
    with open(CSV_FILE, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/upload/csv",
            headers=headers,
            files={"file": (CSV_FILE, f, "text/csv")},
            data={"project_id": project_id}
        )
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.text}")
        return
    
    upload_result = response.json()
    print(f"✅ Upload successful!")
    print(f"   Total records: {upload_result.get('total_records')}")
    print(f"   Job ID: {upload_result.get('job_id')}")
    
    # Wait for processing
    time.sleep(2)
    
    # Step 4: Get activities
    print("\n📋 Step 4: Fetching calculated activities...")
    response = requests.get(
        f"{BASE_URL}/activities/",
        headers=headers,
        params={"project_id": project_id}
    )
    
    activities = response.json()
    print(f"\n{'='*70}")
    print("📊 CARBON CALCULATION & CLASSIFICATION RESULTS")
    print("="*70)
    
    for i, activity in enumerate(activities, 1):
        input_data = activity.get("input_data", {})
        print(f"\n🔹 Activity {i}:")
        print(f"   Description: {input_data.get('description', 'N/A')[:50]}")
        print(f"   Input: {input_data.get('amount')} {input_data.get('unit')}")
        print(f"   ──────────────────────────────")
        print(f"   Scope: {activity.get('scope')}")
        print(f"   Activity Type: {activity.get('activity_type')}")
        print(f"   CO2e (kg): {activity.get('co2e_kg')}")
        print(f"   Region: {activity.get('region')}")
    
    # Step 5: Get summary
    print(f"\n{'='*70}")
    print("📈 PROJECT SUMMARY")
    print("="*70)
    
    response = requests.get(
        f"{BASE_URL}/activities/project/{project_id}/summary",
        headers=headers
    )
    summary = response.json()
    
    print(f"\n   Total Activities: {summary.get('total_activities')}")
    print(f"   Total CO2e (kg): {summary.get('total_co2e_kg')}")
    
    print("\n   Scope Breakdown:")
    for scope, value in summary.get("scope_breakdown", {}).items():
        print(f"     • {scope}: {value} kg")
    
    print("\n   Activity Type Breakdown:")
    for atype, value in summary.get("activity_type_breakdown", {}).items():
        print(f"     • {atype}: {value} kg")
    
    # Output verification commands
    print(f"\n{'='*70}")
    print("🔍 VERIFICATION COMMANDS")
    print("="*70)
    print(f"""
To verify in the database directly:

# Connect to database:
docker exec -it decarbonization-db psql -U carbon_user -d decarbonization_db

# View all activities for this project:
SELECT activity_type, scope, co2e_kg, region, input_data->>'description' as description
FROM emission_activities 
WHERE project_id = '{project_id}'
ORDER BY created_at;

# View scope totals:
SELECT scope, SUM(co2e_kg) as total_co2e
FROM emission_activities 
WHERE project_id = '{project_id}'
GROUP BY scope;

# View activity type totals:
SELECT activity_type, COUNT(*) as count, SUM(co2e_kg) as total_co2e
FROM emission_activities 
WHERE project_id = '{project_id}'
GROUP BY activity_type;

# API commands (in terminal):
export TOKEN="{token}"
export PROJECT="{project_id}"

# List activities:
curl -s -H "Authorization: Bearer $TOKEN" \\
  "http://localhost:8000/api/v1/activities/?project_id=$PROJECT" | jq .

# Get summary:
curl -s -H "Authorization: Bearer $TOKEN" \\
  "http://localhost:8000/api/v1/activities/project/$PROJECT/summary" | jq .
""")
    
    print("="*70)
    print("✅ TEST COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
