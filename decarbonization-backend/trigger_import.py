import requests
import time
import sys
import json

API_URL = "http://localhost:8000/api/v1"
FILE_PATH = "test_real_import.csv"

def run_import():
    print(f"Uploading {FILE_PATH} to {API_URL}/import/csv...")
    
    # login if needed? Assuming dev environment might have open auth or we use fixed token?
    # The API requires auth (Depends(get_current_user)). 
    # I need to get a token first.
    
    # 1. Login (using the test user created in README or DB seed)
    # Default: testuser / password (from README if seeded, but let's check or create)
    # Actually, let's try to register/login.
    
    session = requests.Session()
    
    display_password = "Password123!"
    login_data = {"username": "testuser", "password": display_password} 
    # If not exists, register.
    
    print("Attempting to get token...")
    # Register/Login flow
    try:
        # Register
        reg_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": display_password,
            "organization_name": "Test Org"
        }
        resp = session.post(f"{API_URL}/auth/register", json=reg_data)
        if resp.status_code == 201:
            print("Registered test user.")
        elif resp.status_code == 400 and "already exists" in resp.text:
            print("User already exists, logging in.")
        else:
            print(f"Registration failed: {resp.status_code} {resp.text}")
            
        # Login
        resp = session.post(f"{API_URL}/auth/token", data={"username": "testuser", "password": display_password})
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            sys.exit(1)
            
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Got auth token.")
        
    except Exception as e:
        print(f"Auth error: {e}")
        sys.exit(1)

    # 2. Upload
    with open(FILE_PATH, 'rb') as f:
        files = {'file': (FILE_PATH, f, 'text/csv')}
        resp = session.post(f"{API_URL}/import/csv", headers=headers, files=files)
        
    if resp.status_code != 202:
        print(f"Upload failed: {resp.status_code} {resp.text}")
        sys.exit(1)
        
    import_id = resp.json()["import_id"]
    print(f"Import started. ID: {import_id}")
    
    # 3. Poll Status
    print("Polling status...")
    for _ in range(30): # 30 seconds max
        time.sleep(1)
        resp = session.get(f"{API_URL}/import/csv/{import_id}", headers=headers)
        data = resp.json()
        status = data.get("status")
        print(f"Status: {status}")
        
        if status in ["completed", "failed"]:
            print("\nFinal Result:")
            print(json.dumps(data, indent=2))
            
            if status == "completed":
                # Verify specific checks
                if data["successful_rows"] == 1:
                    print("✅ SUCCESS: 1 row imported.")
                else:
                    print(f"⚠️ Warning: Expected 1 success, got {data['successful_rows']}")
            return

    print("Timed out waiting for import.")

if __name__ == "__main__":
    run_import()
