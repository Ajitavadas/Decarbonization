
import asyncio
import httpx
import uuid
import json
import time

# Colors for output
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

BASE_URL = "http://localhost:8000"

async def demo():
    print(f"{BLUE}=== Decarbonization Platform Agentic Demo ==={RESET}")
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        
        # 1. Registration
        print(f"\n{YELLOW}1. Creating User & Organization...{RESET}")
        email = f"demo_{uuid.uuid4().hex[:6]}@example.com"
        password = "DemoPass123!"
        username = email.split("@")[0]
        
        try:
            reg = await client.post("/api/v1/auth/register", json={
                "email": email,
                "username": username,
                "password": password,
                "organization_name": "Demo Corp"
            })
            if reg.status_code != 201:
                print(f"{RED}Registration failed: {reg.text}{RESET}")
                return
            print(f"{GREEN}✔ Registered {email}{RESET}")

            # Login
            login = await client.post("/api/v1/auth/token", data={
                "username": email,
                "password": password
            })
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print(f"{GREEN}✔ Logged in.{RESET}")

        except Exception as e:
            print(f"{RED}Auth Error: {e}{RESET}")
            return

        # 2. Ingest Data (CSV Import)
        print(f"\n{YELLOW}2. Ingesting Emission Data (Phase 1)...{RESET}")
        csv_content = """description,transaction_date,scope,category,activity_value,activity_unit
Electric Bill Jan,2025-01-15,2,Electricity,1000,kWh
Diesel Generator,2025-01-20,1,Fuel,50,gallons
"""
        files = {"file": ("demo_data.csv", csv_content, "text/csv")}
        
        try:
            upload = await client.post("/api/v1/import/csv", files=files, headers=headers)
            import_id = upload.json()["import_id"]
            print(f"{GREEN}✔ Uploaded CSV (Job: {import_id}){RESET}")
            
            # Poll for completion
            print(f"{BLUE}Waiting for AI processing...{RESET}", end="")
            for _ in range(10):
                await asyncio.sleep(1)
                print(".", end="", flush=True)
                status_res = await client.get(f"/api/v1/import/csv/{import_id}", headers=headers)
                if status_res.json()["status"] in ["completed", "failed"]:
                    break
            print()
            
            res = status_res.json()
            if res["status"] == "completed":
                print(f"{GREEN}✔ Import Completed: {res['successful_rows']} rows processed.{RESET}")
            else:
                 print(f"{RED}Import Failed: {res}{RESET}")

        except Exception as e:
            print(f"{RED}Import Error: {e}{RESET}")

        # 3. Analyst Agent (Phase 2)
        print(f"\n{YELLOW}3. Triggering Analyst Agent (The Computer)...{RESET}")
        # Scenario: User manually triggers analyst with a "fix" for a gap
        # We simulate a "User Response" that Analyst picks up
        
        analyst_payload = {
            "data": {
                "organization_id": res["org_id"],
                "activity_value": 500,
                "activity_unit": "therms",
                "activity_type": "natural_gas",
                "description": "Manual Entry via Analyst Agent"
            },
            "user_id": res["user_id"] # reusing the user from import
        }
        
        try:
            # Call the specific Analyst endpoint
            resp = await client.post("/agents/analyst/process", json=analyst_payload, headers=headers)
            
            if resp.status_code == 200:
                result = resp.json()
                print(f"{GREEN}✔ Analyst Agent Success!{RESET}")
                print(f"   Transaction ID: {result['transaction_id']}")
                print(f"   Calculated Emissions: {result['co2e_kg']} kgCO2e")
            else:
                print(f"{RED}Analyst Failed: {resp.text}{RESET}")

        except Exception as e:
             print(f"{RED}Analyst Error: {e}{RESET}")

        print(f"\n{BLUE}=== Demo Complete ==={RESET}")

if __name__ == "__main__":
    asyncio.run(demo())
