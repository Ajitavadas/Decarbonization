#!/usr/bin/env python3
"""
End-to-End Production Test for Decarbonization Platform
Tests: Registration, Upload, Emissions, Anomalies, Targets, Carbon Copilot
Archetype: Digital Services (Tech/SaaS company)
"""

import requests
import json
import time
import random

BASE_URL = "http://localhost:8000/api/v1"
CSV_FILE = "digital_services_test.csv"
RANDOM_SUFFIX = random.randint(10000, 99999)

# Test user details
TEST_EMAIL = f"sustainability.analyst.{RANDOM_SUFFIX}@techcorp.test"
TEST_PASSWORD = "SustainTest2025!"
TEST_ORG_NAME = f"TechCorp Solutions {RANDOM_SUFFIX}"

def print_section(title):
    print(f"\n{'='*70}")
    print(f"🔹 {title}")
    print("="*70)

def main():
    print("\n" + "="*70)
    print("🌍 END-TO-END PRODUCTION TEST: Digital Services Archetype")
    print("="*70)
    
    # ========== STEP 1: Register New User ==========
    print_section("Step 1: Registering New User")
    
    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": f"Sarah Chen - Sustainability Analyst"
        }
    )
    
    if register_response.status_code != 201:
        print(f"❌ Registration failed: {register_response.text}")
        return
    
    auth_data = register_response.json()
    token = auth_data.get("access_token")
    user_id = auth_data.get("user", {}).get("id")
    org_id = auth_data.get("organization", {}).get("id")
    
    print(f"✅ Registered: {TEST_EMAIL}")
    print(f"   User ID: {user_id}")
    print(f"   Organization ID: {org_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # ========== STEP 2: Update Organization with Archetype ==========
    print_section("Step 2: Configuring Organization (Digital Services Archetype)")
    
    # First update org name and industry
    org_update_response = requests.put(
        f"{BASE_URL}/organizations/me",
        headers=headers,
        json={
            "name": TEST_ORG_NAME,
            "industry": "Technology",
            "country": "US"
        }
    )
    
    if org_update_response.status_code == 200:
        org_data = org_update_response.json()
        print(f"✅ Organization updated:")
        print(f"   Name: {org_data.get('name')}")
        print(f"   Industry: {org_data.get('industry')}")
    else:
        print(f"⚠️ Organization update failed: {org_update_response.text}")
    
    # Set archetype separately
    archetype_response = requests.patch(
        f"{BASE_URL}/organizations/archetype",
        headers=headers,
        json={"archetype": "digital_service"}
    )
    
    if archetype_response.status_code == 200:
        print(f"   Archetype: digital_service ✅")
    else:
        print(f"⚠️ Archetype update failed: {archetype_response.text}")
    
    # ========== STEP 3: Create Project ==========
    print_section("Step 3: Creating Project")
    
    project_response = requests.post(
        f"{BASE_URL}/projects/",
        headers=headers,
        json={
            "name": "2025 Carbon Footprint - TechCorp",
            "description": "Comprehensive carbon accounting for FY2025",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "reporting_year": "2025"
        }
    )
    
    if project_response.status_code != 201:
        print(f"❌ Project creation failed: {project_response.text}")
        return
    
    project = project_response.json()
    project_id = project["id"]
    print(f"✅ Project created: {project['name']}")
    print(f"   Project ID: {project_id}")
    
    # ========== STEP 4: Upload CSV ==========
    print_section("Step 4: Uploading Activity Data CSV")
    
    with open(CSV_FILE, "rb") as f:
        upload_response = requests.post(
            f"{BASE_URL}/upload/csv",
            headers=headers,
            files={"file": (CSV_FILE, f, "text/csv")},
            data={"project_id": project_id}
        )
    
    if upload_response.status_code != 200:
        print(f"❌ Upload failed: {upload_response.text}")
        return
    
    upload_result = upload_response.json()
    print(f"✅ Upload successful!")
    print(f"   Total records: {upload_result.get('total_records')}")
    print(f"   Status: {upload_result.get('status')}")
    
    # Wait for processing
    print("   ⏳ Waiting for calculations...")
    time.sleep(5)
    
    # ========== STEP 5: Verify Emissions ==========
    print_section("Step 5: Verifying Calculated Emissions")
    
    activities_response = requests.get(
        f"{BASE_URL}/activities/",
        headers=headers,
        params={"project_id": project_id}
    )
    
    activities = activities_response.json()
    print(f"\n📊 Total Activities Calculated: {len(activities)}")
    
    # Scope breakdown
    scope_totals = {}
    type_totals = {}
    
    for activity in activities:
        scope = activity.get("scope", "Unknown")
        atype = activity.get("activity_type", "unknown")
        co2e_raw = activity.get("co2e_kg", 0)
        co2e = float(co2e_raw) if co2e_raw else 0.0
        
        scope_totals[scope] = scope_totals.get(scope, 0) + co2e
        type_totals[atype] = type_totals.get(atype, 0) + co2e
    
    print("\n📋 Scope Breakdown:")
    for scope, total in sorted(scope_totals.items()):
        print(f"   {scope}: {total:,.2f} kg CO₂e")
    
    print("\n📋 Activity Type Breakdown:")
    for atype, total in sorted(type_totals.items(), key=lambda x: -x[1]):
        print(f"   {atype}: {total:,.2f} kg CO₂e")
    
    total_emissions = sum(scope_totals.values())
    print(f"\n📈 Total Emissions: {total_emissions:,.2f} kg CO₂e")
    
    # ========== STEP 6: Check Anomalies ==========
    print_section("Step 6: Checking Anomaly Detection")
    
    # Run audit
    audit_response = requests.post(
        f"{BASE_URL}/audit/run",
        headers=headers
    )
    
    if audit_response.status_code == 200:
        audit_result = audit_response.json()
        print(f"✅ Audit completed")
        
        # Get flagged events
        flagged_response = requests.get(
            f"{BASE_URL}/audit/flagged-events",
            headers=headers
        )
        
        if flagged_response.status_code == 200:
            events = flagged_response.json()
            print(f"\n🚨 Flagged Events: {len(events)}")
            for event in events[:5]:
                print(f"   - [{event.get('severity', 'info').upper()}] {event.get('title')}")
        else:
            print(f"   No flagged events or audit not ready")
    else:
        print(f"⚠️ Audit response: {audit_response.text}")
    
    # ========== STEP 7: Create Reduction Target ==========
    print_section("Step 7: Creating Reduction Target")
    
    target_response = requests.post(
        f"{BASE_URL}/targets/",
        headers=headers,
        json={
            "name": "Net Zero 2030",
            "description": "Achieve net zero emissions by 2030",
            "target_type": "percentage",
            "scope": "all",
            "baseline_year": "2025",
            "baseline_value": total_emissions,
            "target_year": "2030",
            "target_value": 50,  # 50% reduction
            "milestones": [
                {"year": "2027", "value": 25, "achieved": False},
                {"year": "2029", "value": 40, "achieved": False}
            ]
        }
    )
    
    if target_response.status_code == 200:
        target = target_response.json()
        print(f"✅ Target created: {target.get('name')}")
        print(f"   Baseline ({target.get('baseline_year')}): {target.get('baseline_value'):,.0f} kg CO₂e")
        print(f"   Target ({target.get('target_year')}): {target.get('target_value')}% reduction")
    else:
        print(f"⚠️ Target creation: {target_response.text}")
    
    # ========== STEP 8: Carbon Copilot Roleplay ==========
    print_section("Step 8: Carbon Copilot - Sustainability Analyst Roleplay")
    
    copilot_questions = [
        "What are my total emissions?",
        "Show me my scope breakdown",
        "What are my biggest emission sources?",
        "Am I on track for my 2030 net zero target?",
        "How can I reduce emissions as a tech company?",
        "What anomalies should I investigate?"
    ]
    
    for i, question in enumerate(copilot_questions, 1):
        print(f"\n💬 [{i}] Analyst asks: \"{question}\"")
        
        copilot_response = requests.post(
            f"{BASE_URL}/copilot/chat",
            headers=headers,
            json={
                "message": question,
                "include_llm": True
            }
        )
        
        if copilot_response.status_code == 200:
            response = copilot_response.json()
            text = response.get("text", "No response")
            source = response.get("source", "unknown")
            model = response.get("model", "N/A")
            intent = response.get("intent", "unknown")
            
            print(f"   🤖 Copilot [{source}/{model}] (intent: {intent}):")
            print(f"   \"{text[:500]}{'...' if len(text) > 500 else ''}\"")
            
            # Check if RAG context was used
            data = response.get("data", {})
            if data.get("archetype_info"):
                print(f"   ✅ RAG: Archetype info included ({data['archetype_info'].get('name', 'N/A')})")
            if data.get("org_profile"):
                print(f"   ✅ RAG: Org profile included ({data['org_profile'].get('industry', 'N/A')})")
        else:
            print(f"   ❌ Copilot error: {copilot_response.text}")
        
        time.sleep(1)  # Rate limiting
    
    # ========== FINAL SUMMARY ==========
    print_section("TEST COMPLETE - SUMMARY")
    
    print(f"""
📊 Test Results:
   User: {TEST_EMAIL}
   Organization: {TEST_ORG_NAME}
   Archetype: Digital Services
   
   Activities Uploaded: {len(activities)}
   Total Emissions: {total_emissions:,.2f} kg CO₂e
   
   Scope Distribution:
""")
    for scope, total in sorted(scope_totals.items()):
        pct = (total / total_emissions * 100) if total_emissions > 0 else 0
        print(f"      {scope}: {pct:.1f}%")
    
    print(f"""
   Expected for Digital Services:
      Scope 1: ~5%
      Scope 2: ~25%
      Scope 3: ~70%
      
🔗 Login to verify in UI:
   URL: http://localhost:3000
   Email: {TEST_EMAIL}
   Password: {TEST_PASSWORD}
""")
    
    # Save credentials for manual testing
    with open("test_credentials.txt", "w") as f:
        f.write(f"Email: {TEST_EMAIL}\n")
        f.write(f"Password: {TEST_PASSWORD}\n")
        f.write(f"Token: {token}\n")
        f.write(f"Project ID: {project_id}\n")
    
    print("✅ Credentials saved to test_credentials.txt")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
