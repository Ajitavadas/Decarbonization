#!/usr/bin/env python3
"""
End-to-End Test for Decarbonization Platform
Tests: Registration → Login → CSV Upload → Classification → Emissions Calculation
"""

import requests
import json
import time
import sys
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "email": f"test_user_{int(time.time())}@example.com",
    "password": "SecureTest123!",
    "full_name": "Test User",
    "organization_name": "Test Organization"
}

CSV_FILE = Path(__file__).parent / "test_activity_data.csv"

def print_step(step_num, description):
    """Print formatted test step"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print('='*60)

def print_result(success, message):
    """Print test result"""
    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"{status}: {message}")

def test_registration():
    """Step 1: Register a new user"""
    print_step(1, "USER REGISTRATION")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=TEST_USER,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            print_result(True, f"User registered")
            return True
        else:
            print_result(False, f"Registration failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Registration error: {str(e)}")
        return False

def test_login():
    """Step 2: Login and get access token"""
    print_step(2, "USER LOGIN")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_USER["email"],
                "password": TEST_USER["password"]
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print_result(True, f"Login successful")
            print(f"   Token type: {data.get('token_type')}")
            return token
        else:
            print_result(False, f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_result(False, f"Login error: {str(e)}")
        return None

def test_csv_upload(token):
    """Step 3: Upload CSV file"""
    print_step(3, "CSV FILE UPLOAD")
    
    if not CSV_FILE.exists():
        print_result(False, f"CSV file not found: {CSV_FILE}")
        return None
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        with open(CSV_FILE, 'rb') as f:
            files = {'file': ('test_activity_data.csv', f, 'text/csv')}
            response = requests.post(
                f"{BASE_URL}/upload/csv",
                headers=headers,
                files=files,
                timeout=30
            )
        
        if response.status_code in [200, 201, 202]:
            data = response.json()
            print_result(True, "CSV uploaded successfully")
            print(f"   Status: {data.get('status')}")
            print(f"   Total rows: {data.get('total_rows')}")
            return data
        else:
            print_result(False, f"Upload failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_result(False, f"Upload error: {str(e)}")
        return None

def test_classification_and_calculation(token):
    """Step 4: Check classification and emission calculation results"""
    print_step(4, "CHECKING CLASSIFICATION & EMISSIONS CALCULATION")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Give it a moment to process
        print("   Waiting for processing...")
        time.sleep(3)
        
        # First, get the project
        print("\n   Fetching projects...")
        response = requests.get(
            f"{BASE_URL}/projects",
            headers=headers,
            timeout=10
        )
        
        project_id = None
        if response.status_code == 200:
            projects = response.json()
            if isinstance(projects, list) and len(projects) > 0:
                project_id = projects[0].get('id')
                print(f"   Using project: {projects[0].get('name')}")
            elif isinstance(projects, dict):
                items = projects.get('items', projects.get('projects', []))
                if items:
                    project_id = items[0].get('id')
                    print(f"   Using project: {items[0].get('name')}")
        
        if not project_id:
            print("   No project found, fetching activities without project_id...")
        
        # Get activities
        print("\n   Fetching activities...")
        params = {'limit': 20}
        if project_id:
            params['project_id'] = project_id
            
        response = requests.get(
            f"{BASE_URL}/activities",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            activities = response.json()
            
            if isinstance(activities, dict):
                activities = activities.get('items', activities.get('activities', activities.get('data', [])))
            
            if not activities:
                print_result(False, "No activities found")
                return False
            
            print_result(True, f"Retrieved {len(activities)} activities")
            
            # Display sample activities
            print(f"\n   Sample Activities:")
            for i, activity in enumerate(activities[:3], 1):
                print(f"\n   Activity {i}:")
                print(f"      Description: {activity.get('description', 'N/A')}")
                print(f"      Scope: {activity.get('scope', 'N/A')}")
                print(f"      Category: {activity.get('category', 'N/A')}")
                co2e = activity.get('co2e_kg') or activity.get('carbon_footprint') or activity.get('co2_kg')
                print(f"      CO2e (kg): {co2e if co2e is not None else 'N/A'}")
                print(f"      Amount: {activity.get('amount', 'N/A')} {activity.get('unit', '')}")
            
            # Verify key fields
            has_scope = sum(1 for a in activities if a.get('scope')) > 0
            has_emissions = sum(1 for a in activities if (a.get('co2e_kg') or a.get('carbon_footprint') or a.get('co2_kg'))) > 0
            
            if has_scope:
                print_result(True, "Activities have AI classification (Scope)")
            else:
                print_result(False, "No activities have Scope classification")
            
            if has_emissions:
                print_result(True, "Activities have emissions calculations")
            else:
                print_result(False, "No activities have emissions calculations")
            
            return has_scope and has_emissions
        else:
            print_result(False, f"Failed to get activities: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def main():
    """Run full end-to-end test"""
    print("\n" + "="*60)
    print("DECARBONIZATION PLATFORM - END-TO-END TEST")
    print("="*60)
    print(f"Testing with user: {TEST_USER['email']}")
    print(f"CSV file: {CSV_FILE}")
    
    # Wait for services
    print("\nWaiting for services to be ready...")
    time.sleep(5)
    
    # Step 1: Registration
    if not test_registration():
        sys.exit(1)
    
    # Step 2: Login
    token = test_login()
    if not token:
        sys.exit(1)
    
    # Step 3: Upload CSV
    if not test_csv_upload(token):
        sys.exit(1)
    
    # Step 4: Verify Classification & Calculation
    if not test_classification_and_calculation(token):
        sys.exit(1)
    
    # Final Summary
    print("\n" + "="*60)
    print("🎉 ALL TESTS PASSED!")
    print("="*60)
    print("\nWorkflow Completed:")
    print("  ✅ User Registration")
    print("  ✅ User Login")
    print("  ✅ CSV/XLSX Upload")
    print("  ✅ AI Classification")
    print("  ✅ Carbon Emissions Calculation")
    print("\nPlatform is fully functional!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
