"""
Comprehensive Dry Run Integration Tests for Decarbonization Platform

Tests the complete workflow:
1. User registration
2. User login  
3. CSV file upload
4. AI-powered classification
5. Climatiq emission calculations
6. Results retrieval and validation

Run with: pytest tests/test_dry_run.py -v
"""

import os
import time
import requests
import pytest
from pathlib import Path


class TestDryRunWorkflow:
    """End-to-end dry run tests for the complete platform workflow"""
    
    # --- Authentication Tests ---
    
    def test_01_backend_health(self, api_url: str, wait_for_backend: None):
        """Verify backend is healthy before running tests"""
        health_url = api_url.replace("/api/v1", "/health")
        response = requests.get(health_url, timeout=10)
        
        assert response.status_code == 200, f"Backend unhealthy: {response.text}"
        print(f"✓ Backend is healthy at {api_url}")
    
    def test_02_user_registration_or_login(self, api_url: str, auth_token: str):
        """Verify user can register or login"""
        assert auth_token is not None, "Failed to obtain auth token"
        assert len(auth_token) > 20, "Auth token appears invalid"
        print(f"✓ Obtained auth token: {auth_token[:20]}...")
    
    def test_03_get_current_user(self, api_url: str, auth_headers: dict):
        """Verify authenticated user can access their profile"""
        response = requests.get(
            f"{api_url}/auth/me",
            headers=auth_headers,
            timeout=10
        )
        
        assert response.status_code == 200, f"Failed to get user: {response.text}"
        data = response.json()
        assert "email" in data, "User response missing email"
        print(f"✓ Authenticated as: {data.get('email')}")
    
    # --- Project Tests ---
    
    def test_04_create_project(self, api_url: str, project_id: str):
        """Verify project creation works"""
        assert project_id is not None, "Failed to create project"
        print(f"✓ Created project: {project_id}")
    
    # --- CSV Upload Tests ---
    
    def test_05_upload_csv_file(self, api_url: str, auth_headers: dict, project_id: str):
        """Test uploading CSV file with activity data"""
        test_csv_path = Path(__file__).parent / "test_data_comprehensive.csv"
        
        assert test_csv_path.exists(), f"Test CSV not found: {test_csv_path}"
        
        with open(test_csv_path, 'rb') as f:
            files = {"file": ("test_data_comprehensive.csv", f, "text/csv")}
            data = {"project_id": project_id}
            
            response = requests.post(
                f"{api_url}/upload/csv",
                headers=auth_headers,
                files=files,
                data=data,
                timeout=120  # Allow time for processing
            )
        
        assert response.status_code == 200, f"Upload failed: {response.status_code} - {response.text}"
        
        result = response.json()
        assert "job_id" in result or "total_rows" in result, f"Unexpected response: {result}"
        
        job_id = result.get("job_id")
        total_rows = result.get("total_rows", 0)
        
        print(f"✓ CSV uploaded successfully")
        print(f"  → Job ID: {job_id}")
        print(f"  → Total rows: {total_rows}")
        
        # Store for subsequent tests
        self.__class__.job_id = job_id
        self.__class__.total_rows = total_rows
    
    def test_06_poll_job_completion(self, api_url: str, auth_headers: dict):
        """Wait for batch job to complete processing"""
        job_id = getattr(self.__class__, 'job_id', None)
        
        if not job_id:
            pytest.skip("No job_id from previous test")
        
        max_attempts = 60  # 2 minutes max
        poll_interval = 2
        
        for attempt in range(max_attempts):
            response = requests.get(
                f"{api_url}/batch/jobs/{job_id}",
                headers=auth_headers,
                timeout=30
            )
            
            if response.status_code == 200:
                job = response.json()
                status = job.get("status")
                processed = job.get("processed_records", 0)
                total = job.get("total_records", 0)
                successful = job.get("successful_records", 0)
                failed = job.get("failed_records", 0)
                
                print(f"  → Status: {status} | {processed}/{total} processed | {successful} success | {failed} failed")
                
                if status == "completed":
                    print(f"✓ Job completed: {successful}/{total} successful")
                    self.__class__.successful_records = successful
                    return
                elif status == "failed":
                    pytest.fail(f"Job failed: {job.get('error_message')}")
            
            time.sleep(poll_interval)
        
        pytest.fail("Job did not complete within timeout")
    
    # --- Results Validation Tests ---
    
    def test_07_retrieve_activities(self, api_url: str, auth_headers: dict, project_id: str):
        """Verify activities were created with emissions data"""
        response = requests.get(
            f"{api_url}/activities/",
            headers=auth_headers,
            params={"project_id": project_id, "limit": 50},
            timeout=30
        )
        
        assert response.status_code == 200, f"Failed to get activities: {response.text}"
        
        activities = response.json()
        if isinstance(activities, dict):
            activities = activities.get("items", activities.get("activities", []))
        
        assert len(activities) > 0, "No activities found"
        
        print(f"✓ Retrieved {len(activities)} activities")
        
        # Validate key fields
        classified_count = sum(1 for a in activities if a.get("scope"))
        co2e_count = sum(1 for a in activities if self._get_co2e(a) > 0)
        
        print(f"  → {classified_count}/{len(activities)} have scope classification")
        print(f"  → {co2e_count}/{len(activities)} have CO2e calculations")
        
        # Store for summary
        self.__class__.activities = activities
    
    def test_08_verify_classifications(self, api_url: str):
        """Verify AI classification assigned scopes correctly"""
        activities = getattr(self.__class__, 'activities', [])
        
        if not activities:
            pytest.skip("No activities from previous test")
        
        scope_breakdown = {}
        for activity in activities:
            scope = activity.get("scope", "Unknown")
            scope_breakdown[scope] = scope_breakdown.get(scope, 0) + 1
        
        print(f"✓ Scope distribution:")
        for scope, count in sorted(scope_breakdown.items()):
            print(f"  → {scope}: {count} activities")
        
        # At least some activities should have scope classification
        classified = sum(1 for a in activities if a.get("scope") and a.get("scope") != "Unknown")
        assert classified > 0, "No activities were classified with a scope"
    
    def test_09_verify_emissions_calculations(self, api_url: str):
        """Verify CO2e emissions were calculated"""
        activities = getattr(self.__class__, 'activities', [])
        
        if not activities:
            pytest.skip("No activities from previous test")
        
        total_co2e = 0
        activity_results = []
        
        for activity in activities:
            co2e = self._get_co2e(activity)
            total_co2e += co2e
            
            if co2e > 0:
                desc = activity.get("description") or "N/A"
                activity_results.append({
                    "description": desc[:50] if desc else "N/A",
                    "co2e_kg": co2e,
                    "scope": activity.get("scope", "N/A")
                })
        
        print(f"✓ CO2e Calculation Results:")
        print(f"  → Total CO2e: {total_co2e:.2f} kg")
        
        if activity_results:
            print(f"  → Sample results:")
            for result in activity_results[:5]:
                print(f"     • {result['description']}: {result['co2e_kg']:.2f} kg ({result['scope']})")
        
        # At least some activities should have CO2e calculated
        assert total_co2e > 0, "No emissions were calculated"
    
    def test_10_project_summary(self, api_url: str, auth_headers: dict, project_id: str):
        """Get and verify project summary"""
        response = requests.get(
            f"{api_url}/activities/project/{project_id}/summary",
            headers=auth_headers,
            timeout=30
        )
        
        if response.status_code == 404:
            pytest.skip("Project summary endpoint not available")
        
        assert response.status_code == 200, f"Failed to get summary: {response.text}"
        
        summary = response.json()
        total_activities = summary.get("total_activities", 0)
        total_co2e = float(summary.get("total_co2e_kg", 0))
        
        print(f"✓ Project Summary:")
        print(f"  → Total activities: {total_activities}")
        print(f"  → Total CO2e: {total_co2e:.2f} kg")
        
        scope_breakdown = summary.get("scope_breakdown", {})
        if scope_breakdown:
            print(f"  → Scope breakdown:")
            for scope, co2e in scope_breakdown.items():
                print(f"     • {scope}: {float(co2e):.2f} kg CO2e")
    
    # --- Helper Methods ---
    
    def _get_co2e(self, activity: dict) -> float:
        """Extract CO2e value from activity, handling various field names"""
        for field in ["co2e_kg", "carbon_footprint", "co2_kg", "emissions_kg"]:
            value = activity.get(field)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    pass
        return 0.0


class TestXLSXUpload:
    """Test XLSX file upload support"""
    
    @pytest.mark.skip(reason="XLSX test data file not yet created")
    def test_upload_xlsx_file(self, api_url: str, auth_headers: dict, project_id: str):
        """Test uploading XLSX file with activity data"""
        # TODO: Create test_data.xlsx and enable this test
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
