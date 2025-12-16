import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def login():
    print("Logging in...")
    # Try logging in as semantic_tester first
    try:
        return login_new()
    except Exception:
        pass

    print("Login failed, trying to register...")
    reg = requests.post(f"{BASE_URL}/api/v1/auth/register", json={
        "email": "semantic@test.com",
        "username": "semantic_tester",
        "password": "Password123!",
        "organization_name": "Semantic Corp"
    })
    
    if reg.status_code in [200, 201]:
        return login_new()
    elif reg.status_code == 409:
        print("User already exists, logging in...")
        return login_new()
    else:
        print(f"Registration failed: {reg.text}")
        sys.exit(1)

def login_new():
    response = requests.post(f"{BASE_URL}/api/v1/auth/token", data={
        "username": "semantic_tester",
        "password": "Password123!"
    })
    return response.json()["access_token"]

def verify_import():
    try:
        token = login_new()
    except Exception:
        try:
            token = login()
        except:
            print("Could not login.")
            return

    headers = {"Authorization": f"Bearer {token}"}
    
    print("Uploading semantic_test.csv...")
    files = {'file': ('semantic_test.csv', open('semantic_test.csv', 'rb'), 'text/csv')}
    
    response = requests.post(f"{BASE_URL}/api/v1/import/csv", headers=headers, files=files)
    
    if response.status_code != 202:
        print(f"Upload failed: {response.text}")
        sys.exit(1)
        
    import_id = response.json()["import_id"]
    print(f"Import started: {import_id}")
    
    # Poll
    for i in range(30):
        time.sleep(2)
        status_res = requests.get(f"{BASE_URL}/api/v1/import/csv/{import_id}", headers=headers)
        status = status_res.json()
        print(f"Status: {status.get('status')}")
        
        if status.get("status") in ["completed", "failed"]:
            break
            
    if status.get("status") == "completed":
        print("Success! Import completed.")
        print(f"Successful rows: {status.get('successful_rows')}")
        if status.get('successful_rows') == 3:
            print("VERIFICATION PASSED: All 3 rows imported despite weird headers.")
        else:
            print("VERIFICATION FAILED: Rows missing.")
            print(f"Errors: {status.get('errors')}")
    else:
        print("VERIFICATION FAILED: Import failed.")
        print(f"Error: {status.get('error')}")
        print(f"Errors list: {status.get('errors')}")

if __name__ == "__main__":
    verify_import()
