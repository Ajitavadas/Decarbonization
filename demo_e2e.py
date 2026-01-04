#!/usr/bin/env python3
"""
============================================================================
Decarbonization Platform - E2E Demo Script
============================================================================
This script demonstrates the complete workflow:
1. User Registration
2. Project Creation  
3. CSV Upload with Emissions Calculation
4. View Results and Summary
============================================================================
"""

import requests
import json
import random
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
CSV_FILE = "test_demo.csv"
RANDOM_SUFFIX = random.randint(1000, 9999)

# Colors for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

def print_json(data):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=2, default=str))

def main():
    print("")
    print("=" * 76)
    print(f"{Colors.BLUE}🌍 DECARBONIZATION PLATFORM - E2E DEMO{Colors.NC}")
    print("=" * 76)
    print("")
    
    # Store results for report
    results = {
        "timestamp": datetime.now().isoformat(),
        "steps": []
    }
    
    # -------------------------------------------------------------------------
    # STEP 1: Register a new user
    # -------------------------------------------------------------------------
    print(f"{Colors.YELLOW}📝 STEP 1: Registering new user...{Colors.NC}")
    print(f"   Endpoint: POST {BASE_URL}/auth/register")
    print("")
    
    register_data = {
        "email": f"demo{RANDOM_SUFFIX}@example.com",
        "password": "DemoPass@123",
        "full_name": f"Demo User {RANDOM_SUFFIX}"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=register_data,
            headers={"Content-Type": "application/json"}
        )
        register_response = response.json()
        print("   Response:")
        print_json(register_response)
        print("")
        
        token = register_response.get("access_token")
        if not token:
            print(f"{Colors.RED}❌ Failed to get access token. Exiting.{Colors.NC}")
            sys.exit(1)
        
        print(f"{Colors.GREEN}✅ User registered successfully!{Colors.NC}")
        print(f"   Token: {token[:50]}...")
        print("")
        
        results["steps"].append({
            "step": 1,
            "name": "User Registration",
            "status": "success",
            "email": register_data["email"],
            "response": register_response
        })
        
    except Exception as e:
        print(f"{Colors.RED}❌ Registration failed: {e}{Colors.NC}")
        sys.exit(1)
    
    # Auth header for subsequent requests
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # -------------------------------------------------------------------------
    # STEP 2: Create a project
    # -------------------------------------------------------------------------
    print(f"{Colors.YELLOW}📁 STEP 2: Creating project...{Colors.NC}")
    print(f"   Endpoint: POST {BASE_URL}/projects/")
    print("")
    
    project_data = {
        "name": f"Q1 2024 Emissions Report - Demo {RANDOM_SUFFIX}",
        "description": "Annual carbon emissions tracking and reporting",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "reporting_year": "2024"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/projects/",
            json=project_data,
            headers=headers
        )
        project_response = response.json()
        print("   Response:")
        print_json(project_response)
        print("")
        
        project_id = project_response.get("id")
        if not project_id:
            print(f"{Colors.RED}❌ Failed to create project. Exiting.{Colors.NC}")
            sys.exit(1)
        
        print(f"{Colors.GREEN}✅ Project created successfully!{Colors.NC}")
        print(f"   Project ID: {project_id}")
        print("")
        
        results["steps"].append({
            "step": 2,
            "name": "Project Creation",
            "status": "success",
            "project_id": project_id,
            "response": project_response
        })
        
    except Exception as e:
        print(f"{Colors.RED}❌ Project creation failed: {e}{Colors.NC}")
        sys.exit(1)
    
    # -------------------------------------------------------------------------
    # STEP 3: Upload CSV and calculate emissions
    # -------------------------------------------------------------------------
    print(f"{Colors.YELLOW}📊 STEP 3: Uploading CSV and calculating emissions...{Colors.NC}")
    print(f"   Endpoint: POST {BASE_URL}/upload/csv")
    print(f"   File: {CSV_FILE}")
    print("")
    print("   This step performs:")
    print("   - Unit normalization (e.g., therms → kWh)")
    print("   - AI-based scope classification")
    print("   - Climatiq API emissions calculation")
    print("")
    
    try:
        with open(CSV_FILE, "rb") as f:
            files = {"file": (CSV_FILE, f, "text/csv")}
            data = {"project_id": project_id}
            response = requests.post(
                f"{BASE_URL}/upload/csv",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {token}"}
            )
        
        upload_response = response.json()
        print("   Response:")
        print_json(upload_response)
        print("")
        
        success = upload_response.get("success", False)
        total_records = upload_response.get("total_records", 0)
        job_id = upload_response.get("job_id")
        
        if success:
            print(f"{Colors.GREEN}✅ CSV processed successfully!{Colors.NC}")
            print(f"   Total records processed: {total_records}")
            print(f"   Batch Job ID: {job_id}")
        else:
            print(f"{Colors.RED}❌ CSV processing failed.{Colors.NC}")
        print("")
        
        results["steps"].append({
            "step": 3,
            "name": "CSV Upload & Emissions Calculation",
            "status": "success" if success else "failed",
            "total_records": total_records,
            "job_id": job_id,
            "response": upload_response
        })
        
    except Exception as e:
        print(f"{Colors.RED}❌ CSV upload failed: {e}{Colors.NC}")
        results["steps"].append({
            "step": 3,
            "name": "CSV Upload & Emissions Calculation",
            "status": "failed",
            "error": str(e)
        })
    
    # -------------------------------------------------------------------------
    # STEP 4: View calculated activities
    # -------------------------------------------------------------------------
    print(f"{Colors.YELLOW}📋 STEP 4: Viewing calculated activities...{Colors.NC}")
    print(f"   Endpoint: GET {BASE_URL}/activities/?project_id={project_id}")
    print("")
    
    try:
        response = requests.get(
            f"{BASE_URL}/activities/",
            params={"project_id": project_id},
            headers=headers
        )
        activities_response = response.json()
        
        print("   Activities with CO2e calculations:")
        activity_summary = [
            {
                "activity_type": a.get("activity_type"),
                "scope": a.get("scope"),
                "co2e_kg": a.get("co2e_kg"),
                "region": a.get("region"),
                "activity_date": a.get("activity_date")
            }
            for a in activities_response
        ]
        print_json(activity_summary)
        print("")
        
        activity_count = len(activities_response)
        print(f"{Colors.GREEN}✅ Found {activity_count} activities with emissions data!{Colors.NC}")
        print("")
        
        results["steps"].append({
            "step": 4,
            "name": "View Activities",
            "status": "success",
            "activity_count": activity_count,
            "activities": activities_response
        })
        
    except Exception as e:
        print(f"{Colors.RED}❌ Failed to fetch activities: {e}{Colors.NC}")
        activity_count = 0
    
    # -------------------------------------------------------------------------
    # STEP 5: Get project summary
    # -------------------------------------------------------------------------
    print(f"{Colors.YELLOW}📈 STEP 5: Getting project summary...{Colors.NC}")
    print(f"   Endpoint: GET {BASE_URL}/activities/project/{project_id}/summary")
    print("")
    
    try:
        response = requests.get(
            f"{BASE_URL}/activities/project/{project_id}/summary",
            headers=headers
        )
        summary_response = response.json()
        
        print("   Project Summary:")
        print_json(summary_response)
        print("")
        
        total_co2e = summary_response.get("total_co2e_kg", 0)
        print(f"{Colors.GREEN}✅ Total CO2e emissions: {total_co2e} kg{Colors.NC}")
        print("")
        
        results["steps"].append({
            "step": 5,
            "name": "Project Summary",
            "status": "success",
            "summary": summary_response
        })
        
    except Exception as e:
        print(f"{Colors.RED}❌ Failed to fetch summary: {e}{Colors.NC}")
        total_co2e = 0
    
    # -------------------------------------------------------------------------
    # STEP 6: Get batch job status
    # -------------------------------------------------------------------------
    print(f"{Colors.YELLOW}📦 STEP 6: Getting batch job details...{Colors.NC}")
    print(f"   Endpoint: GET {BASE_URL}/upload/batch/jobs?project_id={project_id}")
    print("")
    
    try:
        response = requests.get(
            f"{BASE_URL}/upload/batch/jobs",
            params={"project_id": project_id},
            headers=headers
        )
        batch_response = response.json()
        
        if batch_response:
            job = batch_response[0]
            job_summary = {
                "id": job.get("id"),
                "status": job.get("status"),
                "total_records": job.get("total_records"),
                "successful_records": job.get("successful_records"),
                "failed_records": job.get("failed_records"),
                "created_at": job.get("created_at"),
                "completed_at": job.get("completed_at")
            }
            print("   Batch Job:")
            print_json(job_summary)
        print("")
        
        results["steps"].append({
            "step": 6,
            "name": "Batch Job Status",
            "status": "success",
            "jobs": batch_response
        })
        
    except Exception as e:
        print(f"{Colors.RED}❌ Failed to fetch batch jobs: {e}{Colors.NC}")
    
    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    print("")
    print("=" * 76)
    print(f"{Colors.GREEN}🎉 DEMO COMPLETE!{Colors.NC}")
    print("=" * 76)
    print("")
    print("Summary:")
    print(f"  - User Email: demo{RANDOM_SUFFIX}@example.com")
    print(f"  - Project ID: {project_id}")
    print(f"  - Activities Created: {activity_count}")
    print(f"  - Total CO2e: {total_co2e} kg")
    print("")
    print("Environment Variables for further testing:")
    print(f'  export TOKEN="{token}"')
    print(f'  export PROJECT_ID="{project_id}"')
    print("")
    
    # Save results to file for report
    results["summary"] = {
        "email": f"demo{RANDOM_SUFFIX}@example.com",
        "project_id": project_id,
        "activity_count": activity_count,
        "total_co2e_kg": total_co2e
    }
    
    with open("demo_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"{Colors.CYAN}📄 Results saved to demo_results.json{Colors.NC}")
    print("")
    
    return results

if __name__ == "__main__":
    main()
