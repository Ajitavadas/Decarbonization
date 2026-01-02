"""
Integration test for end-to-end workflow:
1. User registration
2. User login
3. CSV file upload
4. AI classification
5. Emission calculation
6. Results retrieval
"""

import requests
import json
import time
import csv
import io
from typing import Dict, Any

# Support both local and docker environments
import os
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
# In docker, backend service name is 'backend'
if os.path.exists("/.dockerenv"):
    BASE_URL = "http://backend:8000/api/v1"

# Test configuration
TEST_USER = {
    "email": "integration_test@example.com",
    "password": "testpass123",
    "full_name": "Integration Test User"
}

def print_test(name: str):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print('='*60)

def print_success(message: str):
    print(f"✓ {message}")

def print_error(message: str):
    print(f"✗ {message}")

def print_info(message: str):
    print(f"→ {message}")

class IntegrationTest:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.project_id = None
        self.job_id = None
    
    def test_1_register(self) -> bool:
        """Test user registration"""
        print_test("1. User Registration")
        try:
            response = requests.post(
                f"{BASE_URL}/auth/register",
                json=TEST_USER,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                print_success(f"User registered: {TEST_USER['email']}")
                print_info(f"User ID: {self.user_id}")
                return True
            elif response.status_code == 400:
                print_info("User already exists, attempting login...")
                return self.test_2_login()
            else:
                print_error(f"Registration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print_error(f"Registration error: {str(e)}")
            return False
    
    def test_2_login(self) -> bool:
        """Test user login"""
        print_test("2. User Login")
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"]
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                print_success("Login successful")
                print_info(f"Token: {self.token[:20]}...")
                return True
            else:
                print_error(f"Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print_error(f"Login error: {str(e)}")
            return False
    
    def test_3_create_project(self) -> bool:
        """Test project creation"""
        print_test("3. Create Project")
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            project_data = {
                "name": "Integration Test Project 2024",
                "description": "Test project for integration testing",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "reporting_year": "2024"
            }
            
            response = requests.post(
                f"{BASE_URL}/projects/",
                json=project_data,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.project_id = data.get("id")
                print_success(f"Project created: {data.get('name')}")
                print_info(f"Project ID: {self.project_id}")
                return True
            else:
                print_error(f"Project creation failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print_error(f"Project creation error: {str(e)}")
            return False
    
    def test_4_create_test_csv(self) -> io.BytesIO:
        """Create a test CSV file in memory"""
        print_test("4. Create Test CSV File")
        try:
            csv_data = [
                {
                    "description": "Electricity consumption",
                    "category": "Energy",
                    "amount": "10000",
                    "unit": "kWh",
                    "region": "US",
                    "year": "2024"
                },
                {
                    "description": "Business travel flight",
                    "category": "Travel",
                    "amount": "5000",
                    "unit": "USD",
                    "region": "US",
                    "year": "2024"
                },
                {
                    "description": "Office supplies procurement",
                    "category": "Procurement",
                    "supplier_name": "Office Depot",
                    "amount": "2000",
                    "unit": "USD",
                    "region": "US",
                    "year": "2024"
                },
                {
                    "description": "Natural gas heating",
                    "category": "Energy",
                    "amount": "5000",
                    "unit": "kWh",
                    "region": "US",
                    "year": "2024"
                },
                {
                    "description": "Freight shipping",
                    "category": "Logistics",
                    "amount": "1000",
                    "unit": "kg",
                    "region": "US",
                    "year": "2024"
                }
            ]
            
            # Collect all unique fieldnames from all rows
            all_fieldnames = set()
            for row in csv_data:
                all_fieldnames.update(row.keys())
            fieldnames = sorted(all_fieldnames)
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
            
            csv_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
            print_success(f"Created test CSV with {len(csv_data)} rows")
            return csv_bytes
        except Exception as e:
            print_error(f"CSV creation error: {str(e)}")
            return None
    
    def test_5_upload_csv(self, csv_file: io.BytesIO) -> bool:
        """Test CSV file upload"""
        print_test("5. Upload CSV File")
        try:
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            
            files = {
                "file": ("test_activities.csv", csv_file, "text/csv")
            }
            
            data = {}
            if self.project_id:
                data["project_id"] = self.project_id
            
            response = requests.post(
                f"{BASE_URL}/upload/csv",
                files=files,
                data=data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                self.job_id = result.get("job_id")
                print_success(f"File uploaded successfully")
                print_info(f"Job ID: {self.job_id}")
                print_info(f"Total rows: {result.get('total_rows')}")
                print_info(f"Status: {result.get('status')}")
                return True
            else:
                print_error(f"Upload failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print_error(f"Upload error: {str(e)}")
            return False
    
    def test_6_poll_job_status(self) -> bool:
        """Poll job status until completion"""
        print_test("6. Poll Job Status")
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            max_attempts = 30
            attempt = 0
            
            while attempt < max_attempts:
                response = requests.get(
                    f"{BASE_URL}/batch/jobs/{self.job_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    job = response.json()
                    status = job.get("status")
                    processed = job.get("processed_records", 0)
                    total = job.get("total_records", 0)
                    successful = job.get("successful_records", 0)
                    failed = job.get("failed_records", 0)
                    
                    print_info(f"Status: {status} | Processed: {processed}/{total} | Success: {successful} | Failed: {failed}")
                    
                    if status == "completed":
                        print_success("Job completed successfully")
                        print_info(f"Successful records: {successful}")
                        print_info(f"Failed records: {failed}")
                        return True
                    elif status == "failed":
                        print_error(f"Job failed: {job.get('error_message', 'Unknown error')}")
                        return False
                    
                    time.sleep(2)
                    attempt += 1
                else:
                    print_error(f"Failed to get job status: {response.status_code}")
                    return False
            
            print_error("Job did not complete within timeout")
            return False
        except Exception as e:
            print_error(f"Job polling error: {str(e)}")
            return False
    
    def test_7_verify_activities(self) -> bool:
        """Verify activities were created"""
        print_test("7. Verify Activities Created")
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{BASE_URL}/activities/?project_id={self.project_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                activities = response.json()
                print_success(f"Found {len(activities)} activities")
                
                if activities:
                    total_co2e = sum(float(a.get("co2e_kg", 0)) for a in activities)
                    print_info(f"Total CO2e: {total_co2e:.2f} kg")
                    
                    # Group by scope
                    scope_breakdown = {}
                    for activity in activities:
                        scope = activity.get("scope", "Unknown")
                        scope_breakdown[scope] = scope_breakdown.get(scope, 0) + float(activity.get("co2e_kg", 0))
                    
                    print_info("Scope breakdown:")
                    for scope, co2e in scope_breakdown.items():
                        print_info(f"  {scope}: {co2e:.2f} kg CO2e")
                
                return len(activities) > 0
            else:
                print_error(f"Failed to get activities: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print_error(f"Activities verification error: {str(e)}")
            return False
    
    def test_8_project_summary(self) -> bool:
        """Get project summary"""
        print_test("8. Get Project Summary")
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{BASE_URL}/activities/project/{self.project_id}/summary",
                headers=headers
            )
            
            if response.status_code == 200:
                summary = response.json()
                print_success("Project summary retrieved")
                print_info(f"Total activities: {summary.get('total_activities')}")
                
                # Handle total_co2e_kg which might be string, Decimal, or float
                total_co2e = summary.get('total_co2e_kg', 0)
                if isinstance(total_co2e, str):
                    total_co2e = float(total_co2e)
                else:
                    total_co2e = float(total_co2e)
                print_info(f"Total CO2e: {total_co2e:.2f} kg")
                
                scope_breakdown = summary.get('scope_breakdown', {})
                if scope_breakdown:
                    print_info("Scope breakdown:")
                    for scope, co2e in scope_breakdown.items():
                        # Handle co2e which might be string, Decimal, or float
                        if isinstance(co2e, str):
                            co2e = float(co2e)
                        else:
                            co2e = float(co2e)
                        print_info(f"  {scope}: {co2e:.2f} kg CO2e")
                
                return True
            else:
                print_error(f"Failed to get summary: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print_error(f"Summary error: {str(e)}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all integration tests"""
        print("\n" + "="*60)
        print("INTEGRATION TEST SUITE")
        print("End-to-End Workflow Test")
        print("="*60)
        
        tests = [
            ("Registration", self.test_1_register),
            ("Login", self.test_2_login),
            ("Create Project", self.test_3_create_project),
        ]
        
        # Run initial tests
        for name, test_func in tests:
            if not test_func():
                print_error(f"Test '{name}' failed. Aborting.")
                return False
        
        # Create CSV
        csv_file = self.test_4_create_test_csv()
        if not csv_file:
            print_error("Failed to create test CSV. Aborting.")
            return False
        
        # Reset file pointer
        csv_file.seek(0)
        
        # Upload and process
        upload_tests = [
            ("Upload CSV", lambda: self.test_5_upload_csv(csv_file)),
            ("Poll Job Status", self.test_6_poll_job_status),
            ("Verify Activities", self.test_7_verify_activities),
            ("Project Summary", self.test_8_project_summary),
        ]
        
        for name, test_func in upload_tests:
            if not test_func():
                print_error(f"Test '{name}' failed.")
                return False
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED! ✓")
        print("="*60)
        return True


if __name__ == "__main__":
    import sys
    
    test = IntegrationTest()
    success = test.run_all_tests()
    
    sys.exit(0 if success else 1)

