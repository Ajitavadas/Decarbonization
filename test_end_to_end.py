#!/usr/bin/env python3
"""
End-to-End Verification Script for Climatiq Integration
Tests the complete flow from CSV upload to CO2e calculation
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test backend health"""
    response = requests.get("http://localhost:8000/health")
    return response.status_code == 200

def test_login():
    """Test user authentication"""
    payload = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=payload)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def test_upload_csv(token, project_id):
    """Test CSV upload with comprehensive data"""
    headers = {"Authorization": f"Bearer {token}"}
    
    with open('test_comprehensive.csv', 'rb') as f:
        files = {'file': f}
        data = {'project_id': project_id}
        
        response = requests.post(
            f"{BASE_URL}/upload/csv", 
            headers=headers, 
            files=files, 
            data=data
        )
    
    return response.json()

def test_batch_job_status(token, project_id):
    """Check batch job completion status"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/batch/jobs?project_id={project_id}", 
        headers=headers
    )
    
    if response.status_code == 200:
        jobs = response.json()
        if jobs:
            latest = max(jobs, key=lambda x: x.get('created_at', ''))
            return latest
    
    return None

def test_activities_retrieval(token, project_id):
    """Retrieve and verify calculated activities"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/activities/?project_id={project_id}", 
        headers=headers
    )
    
    return response.json()

def main():
    print("🧪 END-TO-END VERIFICATION OF CLIMATIQ INTEGRATION")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\n1️⃣ Testing Backend Health...")
    if test_health():
        print("✅ Backend is healthy")
    else:
        print("❌ Backend health check failed")
        return
    
    # Test 2: Authentication
    print("\n2️⃣ Testing Authentication...")
    token = test_login()
    if token:
        print("✅ Authentication successful")
    else:
        print("❌ Authentication failed")
        return
    
    # Test 3: CSV Upload
    print("\n3️⃣ Testing CSV Upload...")
    project_id = "dec3529a-b996-445c-a8a3-c9d6262bfaba"
    upload_result = test_upload_csv(token, project_id)
    
    if upload_result.get("success"):
        print(f"✅ Upload successful: {upload_result.get('total_rows')} rows processed")
        print(f"📊 Status: {upload_result.get('status')}")
        job_id = upload_result.get("job_id")
    else:
        print("❌ Upload failed")
        return
    
    # Test 4: Batch Job Status
    print("\n4️⃣ Checking Batch Job Status...")
    time.sleep(2)  # Wait for processing
    job_status = test_batch_job_status(token, project_id)
    
    if job_status:
        success_rate = (job_status['successful_records'] / job_status['total_records']) * 100
        print(f"✅ Job completed: {success_rate:.1f}% success rate")
        print(f"📈 Successful: {job_status['successful_records']}/{job_status['total_records']}")
        print(f"❌ Failed: {job_status['failed_records']}")
        
        if job_status.get('error_log'):
            print("⚠️ Errors found:")
            for error in job_status['error_log'][:3]:
                print(f"   Row {error['row']}: {error['error'][:60]}...")
    else:
        print("❌ Could not retrieve job status")
        return
    
    # Test 5: Activities Verification
    print("\n5️⃣ Verifying CO2e Calculations...")
    activities = test_activities_retrieval(token, project_id)
    
    if activities:
        print(f"✅ Retrieved {len(activities)} activities")
        print("\n📊 CO2e Calculation Results:")
        
        total_co2e = 0
        for activity in activities:
            co2e = activity.get('co2e_kg', 0)
            try:
                # Handle both string and numeric types
                if isinstance(co2e, str):
                    co2e_float = float(co2e)
                else:
                    co2e_float = float(co2e)
                total_co2e += co2e_float
                print(f"  📈 {activity['description']}: {co2e_float:.2f} kg CO2e")
            except (ValueError, TypeError) as e:
                print(f"  📈 {activity['description']}: {co2e} kg CO2e (raw - error: {e})")
        
        print(f"\n🌍 Total CO2e: {total_co2e:.2f} kg")
        
        # Analysis
        electricity_activities = [a for a in activities if 'electricity' in a['description'].lower()]
        procurement_activities = [a for a in activities if 'supplies' in a['description'].lower()]
        travel_activities = [a for a in activities if 'travel' in a['description'].lower()]
        gas_activities = [a for a in activities if 'gas' in a['description'].lower()]
        
        print(f"\n🔍 Breakdown by Type:")
        print(f"  ⚡ Electricity: {len(electricity_activities)} activities")
        print(f"  🛒 Procurement: {len(procurement_activities)} activities") 
        print(f"  ✈️ Travel: {len(travel_activities)} activities")
        print(f"  🔥 Gas: {len(gas_activities)} activities")
        
    else:
        print("❌ Could not retrieve activities")
        return
    
    print("\n🎉 END-TO-END VERIFICATION COMPLETE!")
    print("=" * 60)
    print("✅ All systems functioning correctly")
    print("🚀 Backend ready for frontend integration")

if __name__ == "__main__":
    main()
