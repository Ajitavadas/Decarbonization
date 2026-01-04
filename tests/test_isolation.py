"""
Test script to verify organization data isolation.
Creates two users in different organizations and verifies they can't access each other's data.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

# Test users for two different organizations
ORG_A = {
    "name": "Alpha Corp",
    "user": {
        "email": "alice@alphacorp.test",
        "password": "AlphaTest123!",
        "full_name": "Alice Alpha"
    }
}

ORG_B = {
    "name": "Beta Inc", 
    "user": {
        "email": "bob@betainc.test",
        "password": "BetaTest123!",
        "full_name": "Bob Beta"
    }
}


def register_user(user_data: dict, org_name: str) -> dict:
    """Register a new user with organization"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
            "full_name": user_data["full_name"],
            "organization_name": org_name
        }
    )
    if response.status_code == 201:
        print(f"✅ Registered: {user_data['email']} in {org_name}")
        return response.json()
    elif response.status_code == 400 and "already registered" in response.text.lower():
        print(f"ℹ️  User already exists: {user_data['email']}")
        return None
    else:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return None


def login_user(email: str, password: str) -> str:
    """Login and return access token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"✅ Logged in: {email}")
        return token
    else:
        print(f"❌ Login failed for {email}: {response.status_code} - {response.text[:200]}")
        return None


def get_headers(token: str) -> dict:
    """Get auth headers"""
    return {"Authorization": f"Bearer {token}"}


def create_project(token: str, name: str) -> dict:
    """Create a project"""
    response = requests.post(
        f"{BASE_URL}/api/v1/projects/",
        headers=get_headers(token),
        json={
            "name": name,
            "description": f"Test project for {name}",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "reporting_year": "2024"
        }
    )
    if response.status_code == 201:
        project = response.json()
        print(f"✅ Created project: {name} (ID: {project['id'][:8]}...)")
        return project
    else:
        print(f"❌ Create project failed: {response.status_code} - {response.text[:200]}")
        return None


def list_projects(token: str) -> list:
    """List projects"""
    response = requests.get(
        f"{BASE_URL}/api/v1/projects/",
        headers=get_headers(token)
    )
    if response.status_code == 200:
        projects = response.json()
        print(f"  📁 Found {len(projects)} projects")
        return projects
    else:
        print(f"❌ List projects failed: {response.status_code}")
        return []


def get_project(token: str, project_id: str) -> tuple:
    """Try to get a specific project - returns (success, response)"""
    response = requests.get(
        f"{BASE_URL}/api/v1/projects/{project_id}",
        headers=get_headers(token)
    )
    return response.status_code, response.json() if response.status_code == 200 else response.text


def list_batch_jobs(token: str) -> list:
    """List batch jobs for user's org"""
    response = requests.get(
        f"{BASE_URL}/api/v1/batch/jobs",
        headers=get_headers(token)
    )
    if response.status_code == 200:
        jobs = response.json()
        print(f"  📋 Found {len(jobs)} batch jobs")
        return jobs
    else:
        print(f"❌ List batch jobs failed: {response.status_code}")
        return []


def upload_csv(token: str, project_id: str, csv_content: str) -> dict:
    """Upload CSV to project"""
    files = {"file": ("test.csv", csv_content, "text/csv")}
    data = {"project_id": project_id}
    
    response = requests.post(
        f"{BASE_URL}/api/v1/upload/csv",
        headers=get_headers(token),
        files=files,
        data=data
    )
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Upload successful: {result.get('message', 'OK')}")
        return result
    else:
        print(f"❌ Upload failed: {response.status_code} - {response.text}")
        return None


def main():
    print("\n" + "="*60)
    print("🔒 ORGANIZATION DATA ISOLATION TEST")
    print("="*60 + "\n")
    
    # Step 1: Register users
    print("📝 Step 1: Register test users")
    print("-" * 40)
    register_user(ORG_A["user"], ORG_A["name"])
    register_user(ORG_B["user"], ORG_B["name"])
    
    # Step 2: Login both users
    print("\n🔐 Step 2: Login users")
    print("-" * 40)
    token_a = login_user(ORG_A["user"]["email"], ORG_A["user"]["password"])
    token_b = login_user(ORG_B["user"]["email"], ORG_B["user"]["password"])
    
    if not token_a or not token_b:
        print("❌ Cannot proceed without both tokens")
        return
    
    # Step 3: Create projects for each org
    print("\n📁 Step 3: Create projects")
    print("-" * 40)
    project_a = create_project(token_a, "Alpha Corp Emissions 2024")
    project_b = create_project(token_b, "Beta Inc Carbon Report")
    
    if not project_a or not project_b:
        print("❌ Cannot proceed without both projects")
        return
    
    # Step 4: Upload data to each project
    print("\n📤 Step 4: Upload data to each project")
    print("-" * 40)
    
    csv_a = """description,amount,unit,region,year,activity_date
Office electricity usage,5000,kWh,US,2024,2024-01-15
Natural gas heating,1000,therms,US,2024,2024-02-01"""
    
    csv_b = """description,amount,unit,region,year,activity_date
Factory power consumption,25000,kWh,DE,2024,2024-01-20
Diesel generator fuel,500,gallons,DE,2024,2024-03-10"""
    
    print("Uploading to Alpha Corp project...")
    upload_csv(token_a, project_a["id"], csv_a)
    
    print("Uploading to Beta Inc project...")
    upload_csv(token_b, project_b["id"], csv_b)
    
    # Give time for processing
    time.sleep(2)
    
    # Step 5: Verify data isolation
    print("\n🔒 Step 5: VERIFY DATA ISOLATION")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 5a: Each user should only see their own projects
    print("\n📋 Test 5a: Project listing isolation")
    print("-" * 40)
    
    print("  Alice (Alpha Corp) projects:")
    projects_a = list_projects(token_a)
    for p in projects_a:
        print(f"    - {p['name']}")
    
    print("  Bob (Beta Inc) projects:")
    projects_b = list_projects(token_b)
    for p in projects_b:
        print(f"    - {p['name']}")
    
    # Verify no cross-contamination in listings
    project_a_ids = {p["id"] for p in projects_a}
    project_b_ids = {p["id"] for p in projects_b}
    
    if project_a_ids.isdisjoint(project_b_ids):
        print("  ✅ PASS: Project listings are isolated")
        tests_passed += 1
    else:
        print("  ❌ FAIL: Project listings overlap!")
        tests_failed += 1
    
    # Test 5b: Cross-org project access should fail
    print("\n🚫 Test 5b: Cross-org project access blocked")
    print("-" * 40)
    
    # Alice tries to access Bob's project
    print(f"  Alice trying to access Beta Inc project ({project_b['id'][:8]}...)...")
    status, resp = get_project(token_a, project_b["id"])
    if status == 404:
        print(f"  ✅ PASS: Access denied (404)")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Got status {status} instead of 404")
        tests_failed += 1
    
    # Bob tries to access Alice's project
    print(f"  Bob trying to access Alpha Corp project ({project_a['id'][:8]}...)...")
    status, resp = get_project(token_b, project_a["id"])
    if status == 404:
        print(f"  ✅ PASS: Access denied (404)")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Got status {status} instead of 404")
        tests_failed += 1
    
    # Test 5c: Batch job isolation
    print("\n📋 Test 5c: Batch job isolation")
    print("-" * 40)
    
    print("  Alice's batch jobs:")
    jobs_a = list_batch_jobs(token_a)
    
    print("  Bob's batch jobs:")
    jobs_b = list_batch_jobs(token_b)
    
    # Verify no overlap
    job_a_ids = {j["id"] for j in jobs_a}
    job_b_ids = {j["id"] for j in jobs_b}
    
    if job_a_ids.isdisjoint(job_b_ids):
        print("  ✅ PASS: Batch job listings are isolated")
        tests_passed += 1
    else:
        print("  ❌ FAIL: Batch job listings overlap!")
        tests_failed += 1
    
    # Test 5d: Cross-org upload should fail
    print("\n🚫 Test 5d: Cross-org upload blocked")
    print("-" * 40)
    
    print("  Alice trying to upload to Beta Inc project...")
    result = upload_csv(token_a, project_b["id"], "description,amount,unit\nHack attempt,999,kWh")
    if result is None:
        print("  ✅ PASS: Upload blocked")
        tests_passed += 1
    else:
        print("  ❌ FAIL: Upload succeeded when it should have failed!")
        tests_failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"  ✅ Passed: {tests_passed}")
    print(f"  ❌ Failed: {tests_failed}")
    
    if tests_failed == 0:
        print("\n🎉 ALL TESTS PASSED - Data isolation is working correctly!")
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed - Review needed")
    
    print()


if __name__ == "__main__":
    main()
