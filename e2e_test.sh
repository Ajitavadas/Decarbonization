#!/bin/bash
# E2E Test Script for Decarbonization Platform

set -e
API_URL="http://localhost:8000/api/v1"
TIMESTAMP=$(date +%s)
EMAIL="e2e_${TIMESTAMP}@example.com"

echo "========================================"
echo "E2E Test - Decarbonization Platform"
echo "========================================"
echo ""

# Step 1: Register
echo "1. REGISTER NEW USER"
echo "   Email: $EMAIL"
REG_RESULT=$(curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"TestPass123!\",\"full_name\":\"E2E Test User\",\"organization_name\":\"E2E Test Org\"}")
echo "   Result: $(echo "$REG_RESULT" | head -c 100)"
echo ""

# Step 2: Login
echo "2. LOGIN"
LOGIN_RESULT=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"TestPass123!\"}")
TOKEN=$(echo "$LOGIN_RESULT" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
if [ -z "$TOKEN" ]; then
  echo "   ERROR: Failed to get token"
  echo "   $LOGIN_RESULT"
  exit 1
fi
echo "   Token: ${TOKEN:0:30}..."
echo ""

# Step 3: Create Project
echo "3. CREATE PROJECT"
PROJECT_RESULT=$(curl -s -X POST "$API_URL/projects/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"E2E Full Test Project","description":"Testing complete workflow","start_date":"2024-01-01","end_date":"2024-12-31","reporting_year":"2024"}')
PROJECT_ID=$(echo "$PROJECT_RESULT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
if [ -z "$PROJECT_ID" ]; then
  echo "   ERROR: Failed to create project"
  echo "   $PROJECT_RESULT"
  exit 1
fi
echo "   Project ID: $PROJECT_ID"
echo "   Name: E2E Full Test Project"
echo ""

# Step 4: Upload CSV
echo "4. UPLOAD CSV"
UPLOAD_RESULT=$(curl -s -X POST "$API_URL/upload/csv" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_activity_data.csv" \
  -F "project_id=$PROJECT_ID")
JOB_ID=$(echo "$UPLOAD_RESULT" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
echo "   Job ID: $JOB_ID"
echo "   Response: $(echo "$UPLOAD_RESULT" | head -c 150)"
echo ""

# Step 5: Wait for processing
echo "5. WAITING FOR PROCESSING (30 seconds)..."
sleep 30

# Step 6: Check batch job status
echo "6. CHECK BATCH JOB STATUS"
JOB_STATUS=$(curl -s "$API_URL/batch/jobs/$JOB_ID" \
  -H "Authorization: Bearer $TOKEN")
echo "   $JOB_STATUS" | head -c 200
echo ""
echo ""

# Step 7: Get activities
echo "7. GET ACTIVITIES"
ACTIVITIES=$(curl -s "$API_URL/activities/?project_id=$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN")
ACTIVITY_COUNT=$(echo "$ACTIVITIES" | grep -o '"id"' | wc -l)
echo "   Activity count: $ACTIVITY_COUNT"
echo ""

# Step 8: Get project summary
echo "8. GET PROJECT SUMMARY"
SUMMARY=$(curl -s "$API_URL/activities/project/$PROJECT_ID/summary" \
  -H "Authorization: Bearer $TOKEN")
echo "   $SUMMARY"
echo ""

echo "========================================"
echo "E2E TEST COMPLETE"
echo "========================================"
echo ""
echo "Frontend URLs to verify:"
echo "  Dashboard: http://localhost:3000"
echo "  Projects:  http://localhost:3000/projects"
echo "  Project:   http://localhost:3000/projects/$PROJECT_ID"
echo "  Upload:    http://localhost:3000/upload"
echo "  Emissions: http://localhost:3000/emissions"
echo "  Scope:     http://localhost:3000/scope-analysis"
