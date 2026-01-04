#!/bin/bash
# ============================================================================
# Decarbonization Platform - E2E Demo Script
# ============================================================================
# This script demonstrates the complete workflow:
# 1. User Registration
# 2. Project Creation
# 3. CSV Upload with Emissions Calculation
# 4. View Results and Summary
# ============================================================================

set -e

# Configuration
BASE_URL="http://localhost:8000/api/v1"
CSV_FILE="test_activity_data.csv"
RANDOM_SUFFIX=$RANDOM

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "============================================================================"
echo -e "${BLUE}🌍 DECARBONIZATION PLATFORM - E2E DEMO${NC}"
echo "============================================================================"
echo ""

# ----------------------------------------------------------------------------
# STEP 1: Register a new user
# ----------------------------------------------------------------------------
echo -e "${YELLOW}📝 STEP 1: Registering new user...${NC}"
echo "   Endpoint: POST $BASE_URL/auth/register"
echo ""

REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"demo${RANDOM_SUFFIX}@example.com\",
    \"password\": \"DemoPass@123\",
    \"full_name\": \"Demo User ${RANDOM_SUFFIX}\"
  }")

echo "   Response:"
echo "$REGISTER_RESPONSE" | jq '.'
echo ""

# Extract token
TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Failed to get access token. Exiting.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ User registered successfully!${NC}"
echo "   Token: ${TOKEN:0:50}..."
echo ""

# ----------------------------------------------------------------------------
# STEP 2: Create a project
# ----------------------------------------------------------------------------
echo -e "${YELLOW}📁 STEP 2: Creating project...${NC}"
echo "   Endpoint: POST $BASE_URL/projects/"
echo ""

PROJECT_RESPONSE=$(curl -s -X POST "$BASE_URL/projects/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Q1 2024 Emissions Report - Demo ${RANDOM_SUFFIX}\",
    \"description\": \"Annual carbon emissions tracking and reporting\"
  }")

echo "   Response:"
echo "$PROJECT_RESPONSE" | jq '.'
echo ""

# Extract project ID
PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.id')

if [ "$PROJECT_ID" == "null" ] || [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Failed to create project. Exiting.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Project created successfully!${NC}"
echo "   Project ID: $PROJECT_ID"
echo ""

# ----------------------------------------------------------------------------
# STEP 3: Upload CSV and calculate emissions
# ----------------------------------------------------------------------------
echo -e "${YELLOW}📊 STEP 3: Uploading CSV and calculating emissions...${NC}"
echo "   Endpoint: POST $BASE_URL/upload/csv"
echo "   File: $CSV_FILE"
echo ""
echo "   This step performs:"
echo "   - Unit normalization (e.g., therms → kWh)"
echo "   - AI-based scope classification"
echo "   - Climatiq API emissions calculation"
echo ""

UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/upload/csv" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$CSV_FILE" \
  -F "project_id=$PROJECT_ID")

echo "   Response:"
echo "$UPLOAD_RESPONSE" | jq '.'
echo ""

# Extract job info
SUCCESS=$(echo "$UPLOAD_RESPONSE" | jq -r '.success')
TOTAL_RECORDS=$(echo "$UPLOAD_RESPONSE" | jq -r '.total_records')
JOB_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.job_id')

if [ "$SUCCESS" == "true" ]; then
    echo -e "${GREEN}✅ CSV processed successfully!${NC}"
    echo "   Total records processed: $TOTAL_RECORDS"
    echo "   Batch Job ID: $JOB_ID"
else
    echo -e "${RED}❌ CSV processing failed.${NC}"
fi
echo ""

# ----------------------------------------------------------------------------
# STEP 4: View calculated activities
# ----------------------------------------------------------------------------
echo -e "${YELLOW}📋 STEP 4: Viewing calculated activities...${NC}"
echo "   Endpoint: GET $BASE_URL/activities/?project_id=$PROJECT_ID"
echo ""

ACTIVITIES_RESPONSE=$(curl -s -X GET "$BASE_URL/activities/?project_id=$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "   Activities with CO2e calculations:"
echo "$ACTIVITIES_RESPONSE" | jq '[.[] | {
  activity_type: .activity_type,
  scope: .scope,
  co2e_kg: .co2e_kg,
  region: .region,
  activity_date: .activity_date
}]'
echo ""

ACTIVITY_COUNT=$(echo "$ACTIVITIES_RESPONSE" | jq 'length')
echo -e "${GREEN}✅ Found $ACTIVITY_COUNT activities with emissions data!${NC}"
echo ""

# ----------------------------------------------------------------------------
# STEP 5: Get project summary
# ----------------------------------------------------------------------------
echo -e "${YELLOW}📈 STEP 5: Getting project summary...${NC}"
echo "   Endpoint: GET $BASE_URL/activities/project/$PROJECT_ID/summary"
echo ""

SUMMARY_RESPONSE=$(curl -s -X GET "$BASE_URL/activities/project/$PROJECT_ID/summary" \
  -H "Authorization: Bearer $TOKEN")

echo "   Project Summary:"
echo "$SUMMARY_RESPONSE" | jq '.'
echo ""

TOTAL_CO2E=$(echo "$SUMMARY_RESPONSE" | jq -r '.total_co2e_kg')
echo -e "${GREEN}✅ Total CO2e emissions: ${TOTAL_CO2E} kg${NC}"
echo ""

# ----------------------------------------------------------------------------
# STEP 6: Get batch job status
# ----------------------------------------------------------------------------
echo -e "${YELLOW}📦 STEP 6: Getting batch job details...${NC}"
echo "   Endpoint: GET $BASE_URL/upload/batch/jobs?project_id=$PROJECT_ID"
echo ""

BATCH_RESPONSE=$(curl -s -X GET "$BASE_URL/upload/batch/jobs?project_id=$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "   Batch Jobs:"
echo "$BATCH_RESPONSE" | jq '.[0] | {
  id: .id,
  status: .status,
  total_records: .total_records,
  successful_records: .successful_records,
  failed_records: .failed_records,
  created_at: .created_at,
  completed_at: .completed_at
}'
echo ""

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
echo ""
echo "============================================================================"
echo -e "${GREEN}🎉 DEMO COMPLETE!${NC}"
echo "============================================================================"
echo ""
echo "Summary:"
echo "  - User Email: demo${RANDOM_SUFFIX}@example.com"
echo "  - Project ID: $PROJECT_ID"
echo "  - Activities Created: $ACTIVITY_COUNT"
echo "  - Total CO2e: ${TOTAL_CO2E} kg"
echo ""
echo "Environment Variables for further testing:"
echo "  export TOKEN=\"$TOKEN\""
echo "  export PROJECT_ID=\"$PROJECT_ID\""
echo ""
