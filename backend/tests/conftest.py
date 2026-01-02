"""
Pytest configuration and fixtures for dry run integration tests
"""

import os
import pytest
import requests
import time
from typing import Generator

# Support both local and docker environments
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


@pytest.fixture(scope="session")
def api_url() -> str:
    """Return the API base URL"""
    return API_BASE_URL


@pytest.fixture(scope="session")
def wait_for_backend(api_url: str) -> None:
    """Wait for backend to be healthy before running tests"""
    health_url = api_url.replace("/api/v1", "/health")
    max_attempts = 30
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                print(f"Backend is healthy after {attempt + 1} attempts")
                return
        except requests.exceptions.ConnectionError:
            pass
        
        print(f"Waiting for backend... (attempt {attempt + 1}/{max_attempts})")
        time.sleep(2)
    
    pytest.fail("Backend did not become healthy within timeout")


@pytest.fixture(scope="session")
def test_user() -> dict:
    """Generate unique test user credentials"""
    timestamp = int(time.time())
    return {
        "email": f"dryrun_test_{timestamp}@example.com",
        "password": "SecureTest123!",
        "full_name": "Dry Run Test User"
    }


@pytest.fixture(scope="session")
def auth_token(api_url: str, wait_for_backend: None, test_user: dict) -> str:
    """Register a test user and return auth token"""
    # Try to register
    response = requests.post(
        f"{api_url}/auth/register",
        json=test_user,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    if response.status_code in [200, 201]:
        data = response.json()
        return data.get("access_token")
    elif response.status_code == 400:
        # User exists, try login
        response = requests.post(
            f"{api_url}/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
    
    pytest.fail(f"Failed to get auth token: {response.status_code} - {response.text}")


@pytest.fixture(scope="session")
def project_id(api_url: str, auth_token: str) -> str:
    """Create a test project and return its ID"""
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    project_data = {
        "name": f"Dry Run Test Project {int(time.time())}",
        "description": "Integration test project",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "reporting_year": "2024"
    }
    
    response = requests.post(
        f"{api_url}/projects/",
        json=project_data,
        headers=headers,
        timeout=30
    )
    
    if response.status_code in [200, 201]:
        data = response.json()
        return data.get("id")
    
    pytest.fail(f"Failed to create project: {response.status_code} - {response.text}")


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Return authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}
