# =============================================================================
# DECARBONIZATION PLATFORM - COMPLETE BACKEND API COMMANDS
# =============================================================================
# This file contains all commands to test and traverse the backend API
# Run these commands in order for a complete E2E test

# =============================================================================
# 1. INITIALIZATION
# =============================================================================

# Start all services
cd /home/dasaj/dev/ai_residency/Decarbonization_v2
docker compose up -d

# Check services are running
docker compose ps

# View backend logs (in separate terminal)
docker compose logs -f backend


# =============================================================================
# 2. AUTHENTICATION - REGISTER NEW USER
# =============================================================================

# Register a new user
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "SecurePass@123",
    "full_name": "Test User",
    "organization_name": "Test Organization"
  }' | python3 -m json.tool


# =============================================================================
# 3. AUTHENTICATION - LOGIN & GET TOKEN
# =============================================================================

# Login and extract token (one-liner)
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "testuser@example.com", "password": "SecurePass@123"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "TOKEN=$TOKEN"

# Verify token is set
echo $TOKEN


# =============================================================================
# 4. USER PROFILE
# =============================================================================

# Get current user info
curl -s -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool


# =============================================================================
# 5. PROJECTS - CREATE
# =============================================================================

# Create a new project
curl -s -X POST http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "2025 Q1 Emissions Report",
    "description": "Quarterly emissions calculation",
    "start_date": "2025-01-01",
    "end_date": "2025-03-31",
    "reporting_year": 2025
  }' | python3 -m json.tool

# Save the project ID from response
# export PROJECT_ID="<paste_project_id_here>"


# =============================================================================
# 6. PROJECTS - LIST & VIEW
# =============================================================================

# List all projects for current user
curl -s -X GET "http://localhost:8000/api/v1/projects/" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Get single project by ID
curl -s -X GET "http://localhost:8000/api/v1/projects/$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool


# =============================================================================
# 7. CSV UPLOAD - EMISSIONS CALCULATION
# =============================================================================

# Upload test_fresh.csv and calculate emissions
curl -s -X POST http://localhost:8000/api/v1/upload/csv \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_fresh.csv" \
  -F "project_id=$PROJECT_ID" | python3 -m json.tool


# =============================================================================
# 8. BATCH JOBS - CHECK STATUS
# =============================================================================

# List all batch jobs
curl -s -X GET "http://localhost:8000/api/v1/batch/jobs" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Get specific batch job status (replace JOB_ID)
curl -s -X GET "http://localhost:8000/api/v1/batch/jobs/$JOB_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool


# =============================================================================
# 9. ACTIVITIES - LIST & VIEW
# =============================================================================

# List all activities for a project
curl -s -X GET "http://localhost:8000/api/v1/activities/?project_id=$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Get single activity by ID
curl -s -X GET "http://localhost:8000/api/v1/activities/$ACTIVITY_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool


# =============================================================================
# 10. ACTIVITIES - PROJECT SUMMARY
# =============================================================================

# Get project summary with scope breakdown
curl -s -X GET "http://localhost:8000/api/v1/activities/project/$PROJECT_ID/summary" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool


# =============================================================================
# 11. ACTIVITIES - DELETE
# =============================================================================

# Delete an activity by ID
curl -s -X DELETE "http://localhost:8000/api/v1/activities/$ACTIVITY_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool


# =============================================================================
# 12. DATABASE VERIFICATION QUERIES
# =============================================================================

# Connect to database
docker exec -it decarbonization-db psql -U carbon_user -d decarbonization_db

# -- Inside psql:

# View all activities for a project
SELECT 
    input_data->>'description' as description,
    input_data->>'amount' as amount,
    input_data->>'unit' as unit,
    scope, activity_type, 
    ROUND(co2e_kg::numeric, 2) as co2e_kg
FROM emission_activities 
WHERE project_id = '<PROJECT_ID>'
ORDER BY created_at;

# View scope totals for a project
SELECT scope, COUNT(*), ROUND(SUM(co2e_kg)::numeric, 2) as total_kg 
FROM emission_activities 
WHERE project_id = '<PROJECT_ID>'
GROUP BY scope ORDER BY scope;

# View activity type breakdown
SELECT activity_type, COUNT(*) as count, ROUND(SUM(co2e_kg)::numeric, 2) as total_kg
FROM emission_activities 
WHERE project_id = '<PROJECT_ID>'
GROUP BY activity_type ORDER BY total_kg DESC;

# View all users
SELECT id, email, full_name, organization_id, created_at FROM users;

# View all organizations
SELECT id, name, created_at FROM organizations;

# View all projects
SELECT id, name, organization_id, reporting_year, created_at FROM projects;

# View global emissions summary by scope
SELECT scope, COUNT(*), ROUND(SUM(co2e_kg)::numeric, 2) as total_kg 
FROM emission_activities 
GROUP BY scope ORDER BY scope;


# =============================================================================
# 13. COMPLETE AUTOMATED E2E TEST
# =============================================================================

# Run the full E2E test script with new user/org
cd /home/dasaj/dev/ai_residency/Decarbonization_v2
python3 tests/test_fresh_e2e.py


# =============================================================================
# 14. HEALTH CHECK
# =============================================================================

# Backend health check
curl -s http://localhost:8000/health | python3 -m json.tool

# API docs (Swagger UI)
# Open in browser: http://localhost:8000/docs


# =============================================================================
# 15. DATA ISOLATION TEST
# =============================================================================

# Run data isolation tests (multi-org security)
cd /home/dasaj/dev/ai_residency/Decarbonization_v2
python3 tests/test_isolation.py


# =============================================================================
# 16. QUICK ONE-LINER E2E TEST
# =============================================================================

# Complete E2E in one command (register + login + create project + upload + summary)
EMAIL="quick$(date +%s)@test.com" && \
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"QuickTest@123\", \"full_name\": \"Quick Test\", \"organization_name\": \"Quick Org\"}" > /dev/null && \
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"QuickTest@123\"}" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])") && \
PROJECT_ID=$(curl -s -X POST http://localhost:8000/api/v1/projects/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Quick Test", "description": "Quick test", "start_date": "2025-01-01", "end_date": "2025-12-31", "reporting_year": 2025}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])") && \
curl -s -X POST http://localhost:8000/api/v1/upload/csv \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_fresh.csv" \
  -F "project_id=$PROJECT_ID" > /dev/null && \
sleep 3 && \
echo "=== SUMMARY ===" && \
curl -s -X GET "http://localhost:8000/api/v1/activities/project/$PROJECT_ID/summary" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool


# =============================================================================
# 17. SHUTDOWN
# =============================================================================

# Stop all services
docker compose down

# Stop and remove volumes (CAUTION: deletes all data)
docker compose down -v
