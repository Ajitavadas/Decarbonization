# 🎯 Meeting Demo Guide - Decarbonization Platform

## Quick Start (TL;DR)

```bash
cd /home/dasaj/dev/ai_residency/Decarbonization_v2
python3 demo_e2e.py
```

---

## Pre-Meeting Checklist

### 1. Ensure Services Are Running
```bash
cd /home/dasaj/dev/ai_residency/Decarbonization_v2
docker-compose up -d postgres redis backend
docker-compose ps  # Verify all healthy
```

### 2. Test API Health
```bash
curl http://localhost:8000/health | python3 -m json.tool
```

---

## Demo Option 1: Automated Python Script (Recommended)

**Run the complete demo with one command:**
```bash
python3 demo_e2e.py
```

This will:
1. Register a new user + organization
2. Create a project
3. Upload CSV and calculate emissions
4. Display results with scope breakdown

---

## Demo Option 2: Step-by-Step curl Commands

### Step 1: Register User
```bash
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "meeting_demo@example.com",
    "password": "Demo@123",
    "full_name": "Meeting Demo User"
  }')
echo $REGISTER_RESPONSE | python3 -m json.tool

# Extract token
TOKEN=$(echo $REGISTER_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "Token: $TOKEN"
```

### Step 2: Create Project
```bash
PROJECT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "2025 Annual Emissions Report",
    "description": "Company-wide carbon emissions tracking",
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "reporting_year": "2025"
  }')
echo $PROJECT_RESPONSE | python3 -m json.tool

# Extract project ID
PROJECT_ID=$(echo $PROJECT_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Project ID: $PROJECT_ID"
```

### Step 3: Upload CSV
```bash
curl -X POST http://localhost:8000/api/v1/upload/csv \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_fresh.csv" \
  -F "project_id=$PROJECT_ID" | python3 -m json.tool
```

### Step 4: View Results
```bash
# View all activities
curl -s "http://localhost:8000/api/v1/activities/?project_id=$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# View summary with scope breakdown
curl -s "http://localhost:8000/api/v1/activities/project/$PROJECT_ID/summary" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## Database Verification Commands

### Connect to Database
```bash
docker exec -it decarbonization-db psql -U carbon_user -d decarbonization_db
```

### View All Users
```sql
SELECT id, email, full_name, created_at FROM users ORDER BY created_at DESC LIMIT 5;
```

### View All Projects  
```sql
SELECT id, name, reporting_year, created_at FROM projects ORDER BY created_at DESC LIMIT 5;
```

### View Emission Activities
```sql
SELECT 
    scope, 
    co2e_kg::float as co2e_kg,
    region,
    activity_date
FROM emission_activities 
ORDER BY created_at DESC 
LIMIT 10;
```

### View Emissions Summary by Scope
```sql
SELECT 
    scope,
    COUNT(*) as count,
    ROUND(SUM(co2e_kg)::numeric, 2) as total_co2e_kg
FROM emission_activities 
GROUP BY scope
ORDER BY scope;
```

### View Latest Batch Job
```sql
SELECT 
    id, 
    status, 
    total_records, 
    successful_records, 
    completed_at - created_at as processing_time
FROM batch_jobs 
ORDER BY created_at DESC 
LIMIT 1;
```

### Exit Database
```sql
\q
```

---

## Sample Test Data (test_fresh.csv)

| Activity | Amount | Unit | Category | Expected Scope |
|----------|--------|------|----------|----------------|
| Quarterly electricity | 8,750 | kWh | Electricity | Scope 2 |
| Natural gas heating | 325 | therms | Heating | Scope 1 |
| Diesel for delivery | 620 | gallons | Transport | Scope 1 |
| Warehouse electricity | 32,000 | kWh | Manufacturing | Scope 2 |
| Business flight | 1,850 | miles | Travel | Scope 3 |
| Office heating | 180 | therms | Heating | Scope 1 |
| Employee commute | 12,500 | miles | Commute | Scope 3 |
| Server room power | 21,000 | kWh | IT | Scope 2 |
| Generator diesel | 250 | gallons | Combustion | Scope 1 |
| Rental car | 950 | miles | Travel | Scope 3 |

---

## Expected Results

| Metric | Value |
|--------|-------|
| **Total CO2e** | ~19,861 kg |
| **Scope 1** | ~12,559 kg (63%) |
| **Scope 2** | ~3,146 kg (16%) |
| **Scope 3** | ~4,156 kg (21%) |
| **Processing Time** | ~55 seconds |

---

## Troubleshooting

### Services not running?
```bash
docker-compose down && docker-compose up -d postgres redis backend
```

### Check backend logs
```bash
docker-compose logs -f backend
```

### View API docs
Open: http://localhost:8000/docs
