#!/usr/bin/env python3
"""
Test script to verify backend components are working
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, '/workspace/Decarbonization/backend')

def test_imports():
    """Test that core modules can be imported"""
    try:
        from app.main import app
        print("✓ FastAPI app imported successfully")

        from app.core.config import settings
        print("✓ Configuration module imported successfully")
        print(f"✓ App name: {settings.APP_NAME}")
        print(f"✓ Environment: {settings.ENVIRONMENT}")

        # Test basic API endpoint
        from fastapi.testclient import TestClient
        client = TestClient(app)

        response = client.get("/")
        if response.status_code == 200:
            print("✓ Root endpoint accessible")
            data = response.json()
            print(f"✓ App info: {data['name']} v{data['version']}")

        response = client.get("/health")
        if response.status_code == 200:
            print("✓ Health check endpoint accessible")
            data = response.json()
            print(f"✓ Health status: {data['status']}")

        print("\n🎉 All backend components working correctly!")
        return True

    except Exception as e:
        print(f"❌ Error testing imports: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)