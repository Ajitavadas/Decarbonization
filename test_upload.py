#!/usr/bin/env python3
"""
Test script for login and file upload functionality
"""
import requests
import json

API_URL = "http://localhost:8000/api/v1"

# Test credentials
EMAIL = "ajit@example.com"
PASSWORD = "12345678"

def test_login():
    """Test login functionality"""
    print("=" * 60)
    print("Testing Login")
    print("=" * 60)

    response = requests.post(
        f"{API_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("[OK] Login successful!")
        print(f"Access Token: {data.get('access_token', '')[:50]}...")
        return data.get('access_token')
    else:
        print(f"[ERROR] Login failed: {response.text}")
        return None

def test_get_projects(token):
    """Get list of projects"""
    print("\n" + "=" * 60)
    print("Getting Projects")
    print("=" * 60)

    response = requests.get(
        f"{API_URL}/projects/",
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        projects = response.json()
        print(f"[OK] Found {len(projects)} project(s)")
        for project in projects:
            print(f"  - {project.get('name')} (ID: {project.get('id')})")
        return projects[0]['id'] if projects else None
    else:
        print(f"[ERROR] Failed to get projects: {response.text}")
        return None

def test_upload_csv(token, project_id):
    """Test CSV file upload"""
    print("\n" + "=" * 60)
    print("Testing CSV Upload")
    print("=" * 60)

    if not project_id:
        print("[ERROR] No project ID available")
        return

    with open("test_data_20_rows.csv", "rb") as f:
        files = {"file": ("test_data_20_rows.csv", f, "text/csv")}
        data = {"project_id": project_id}

        response = requests.post(
            f"{API_URL}/upload/csv",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("[OK] Upload successful!")
        print(f"Job ID: {result.get('job_id')}")
        print(f"Message: {result.get('message')}")
        print(f"Total Records: {result.get('total_records')}")
        return result.get('job_id')
    else:
        print(f"[ERROR] Upload failed: {response.text}")
        return None

def test_batch_jobs(token):
    """Test getting batch jobs"""
    print("\n" + "=" * 60)
    print("Getting Batch Jobs")
    print("=" * 60)

    response = requests.get(
        f"{API_URL}/batch/jobs",
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        jobs = response.json()
        print(f"[OK] Found {len(jobs)} job(s)")
        for job in jobs:
            print(f"  - {job.get('file_name', 'Unknown')} | Status: {job.get('status')} | {job.get('successful_records')}/{job.get('total_records')} successful")
    else:
        print(f"[ERROR] Failed to get batch jobs: {response.text}")

def main():
    """Run all tests"""
    print("\nStarting End-to-End Tests\n")

    # Test login
    token = test_login()
    if not token:
        print("\n[ERROR] Cannot proceed without authentication")
        return

    # Get projects
    project_id = test_get_projects(token)

    # Test upload
    test_upload_csv(token, project_id)

    # Check batch jobs
    import time
    print("\nWaiting 3 seconds for processing...")
    time.sleep(3)
    test_batch_jobs(token)

    print("\nTests completed!\n")

if __name__ == "__main__":
    main()
