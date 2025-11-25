import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.jwt_handler import create_access_token, verify_token

client = TestClient(app)

def test_login_success():
    response = client.post("/auth/token?username=demo&password=demo")
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_failure():
    response = client.post("/auth/token?username=wrong&password=wrong")
    assert response.status_code == 401

def test_protected_endpoint_with_valid_token():
    # Get token
    token_response = client.post("/auth/token?username=demo&password=demo")
    token = token_response.json()["access_token"]
    
    # Access protected endpoint
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Hello demo"

def test_protected_endpoint_without_token():
    response = client.get("/protected")
    assert response.status_code == 403

def test_protected_endpoint_with_invalid_token():
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 403

def test_token_creation_and_verification():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    token_data = verify_token(token)
    assert token_data.subject == "testuser"

def test_swagger_docs_accessible():
    response = client.get("/docs")
    assert response.status_code == 200
