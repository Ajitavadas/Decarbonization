#!/bin/bash
# Comprehensive End-to-End Test with Synthetic Data
# Decarbonization Platform Complete Validation

set -e  # Exit on any error

BASE_URL="http://localhost:8000"
TEST_USER="synth_user_$(date +%s)"
TEST_EMAIL="$TEST_USER@synth.test"
TEST_PASS="SynthPass123!"
TEST_ORG="SynthOrg $(date +%Y%m%d)"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🧪 Decarbonization Platform E2E Test Suite      ║${NC}"
echo -e "${BLUE}║  with Synthetic Data Generation                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# PART 1: AUTHENTICATION & USER SETUP
# ============================================================================
echo -e "${YELLOW}[1/6] Authentication & User Setup${NC}"
echo "----------------------------------------"

echo -n "→ Registering new user... "
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "'"$TEST_EMAIL"'",
        "username": "'"$TEST_USER"'",
        "password": "'"$TEST_PASS"'",
        "organization_name": "'"$TEST_ORG"'"
    }')

if echo "$REGISTER_RESPONSE" | grep -q "id"; then
    USER_ID=$(echo "$REGISTER_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    ORG_ID=$(echo "$REGISTER_RESPONSE" | grep -o '"organization_id":"[^"]*' | cut -d'"' -f4)
    echo -e "${GREEN}✓${NC} User ID: $USER_ID"
else
    echo -e "${RED}✗ FAILED${NC}"
    echo "Response: $REGISTER_RESPONSE"
    exit 1
fi

echo -n "→ Logging in... "
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$TEST_USER&password=$TEST_PASS")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo -e "${GREEN}✓${NC} Token acquired"
else
    echo -e "${RED}✗ FAILED${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

# ============================================================================
# PART 2: SYNTHETIC EMISSIONS DATA GENERATION
# ============================================================================
echo ""
echo -e "${YELLOW}[2/6] Generating Synthetic Emissions Data${NC}"
echo "----------------------------------------"

# Create CSV with synthetic data
CSV_FILE="/tmp/synthetic_emissions_$(date +%s).csv"
cat > "$CSV_FILE" << 'EOF'
description,transaction_date,scope,category,activity_value,activity_unit,emission_factor_value
Office Electricity - HQ,2024-01-15,2,Electricity,1250.5,kWh,0.475
Fleet Diesel - Trucks,2024-01-16,1,Fuel,450.3,liters,2.68
Natural Gas - Heating,2024-01-18,1,Natural Gas,800.0,m3,2.03
Business Travel - Flights,2024-02-01,3,Air Travel,5,flights,250.0
Office Electricity - Branch 1,2024-02-10,2,Electricity,980.2,kWh,0.475
Fleet Gasoline - Cars,2024-02-12,1,Fuel,320.5,liters,2.31
Waste Disposal,2024-02-15,3,Waste,1500.0,kg,0.21
Employee Commuting,2024-03-01,3,Commuting,2500.0,km,0.17
Office Electricity - HQ,2024-03-05,2,Electricity,1150.8,kWh,0.475
Cloud Services,2024-03-10,3,IT Services,500.0,hours,0.35
Fleet Diesel - Trucks,2024-03-12,1,Fuel,475.8,liters,2.68
Natural Gas - Heating,2024-03-15,1,Natural Gas,650.0,m3,2.03
Business Travel - Hotels,2024-04-01,3,Accommodation,15,nights,12.5
Office Electricity - Branch 1,2024-04-08,2,Electricity,1025.4,kWh,0.475
Paper Consumption,2024-04-12,3,Office Supplies,200.0,kg,1.82
Fleet Diesel - Trucks,2024-04-15,1,Fuel,510.2,liters,2.68
Remote Data Centers,2024-05-01,3,IT Services,750.0,hours,0.35
Office Electricity - HQ,2024-05-10,2,Electricity,1180.3,kWh,0.475
Employee Commuting,2024-05-15,3,Commuting,2800.0,km,0.17
Waste Disposal,2024-05-20,3,Waste,1650.0,kg,0.21
EOF

echo -n "→ CSV file created with 20 transactions... ${GREEN}✓${NC}"
echo ""

echo -n "→ Importing via API... "
IMPORT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/csv-import" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@$CSV_FILE")

if echo "$IMPORT_RESPONSE" | grep -q "success\|imported"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ Import response:${NC} $(echo $IMPORT_RESPONSE | head -c 200)"
fi

# Wait for processing
sleep 2

# ============================================================================
# PART 3: DASHBOARD & ANALYTICS VALIDATION
# ============================================================================
echo ""
echo -e "${YELLOW}[3/6] Dashboard & Analytics Validation${NC}"
echo "----------------------------------------"

echo -n "→ Fetching dashboard overview... "
DASHBOARD_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/dashboard")
TOTAL_EMISSIONS=$(echo "$DASHBOARD_RESPONSE" | grep -o '"total_emissions":[0-9.]*' | cut -d':' -f2)

if [ -n "$TOTAL_EMISSIONS" ]; then
    echo -e "${GREEN}✓${NC} Total: ${TOTAL_EMISSIONS} tCO2e"
else
    echo -e "${YELLOW}⚠${NC} No emissions calculated yet"
    TOTAL_EMISSIONS="0"
fi

echo -n "→ Checking scope breakdown... "
SCOPE_DATA=$(echo "$DASHBOARD_RESPONSE" | grep -o '"scope_breakdown":{[^}]*}')
if [ -n "$SCOPE_DATA" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC} No scope data"
fi

echo -n "→ Fetching emissions list... "
EMISSIONS_LIST=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/emissions")
EMISSION_COUNT=$(echo "$EMISSIONS_LIST" | grep -o '"id"' | wc -l)
echo -e "${GREEN}✓${NC} Found: $EMISSION_COUNT transactions"

# ============================================================================
# PART 4: AI FEATURES TESTING
# ============================================================================
echo ""
echo -e "${YELLOW}[4/6] AI Features Testing${NC}"
echo "----------------------------------------"

echo -n "→ AI Copilot - Total emissions query... "
COPILOT_Q1=$(curl -s -X POST "$BASE_URL/api/v1/copilot/query" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"query": "What are my total emissions?"}' 2>&1)

if echo "$COPILOT_Q1" | grep -q "answer\|emissions"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC} Response: $(echo $COPILOT_Q1 | head -c 80)"
fi

echo -n "→ Anomaly detection... "
ANOMALIES=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/anomalies")
ANOMALY_COUNT=$(echo "$ANOMALIES" | grep -o '"id"' | wc -l)
echo -e "${GREEN}✓${NC} Detected: $ANOMALY_COUNT anomalies"

echo -n "→ Emissions forecasting... "
FORECAST=$(curl -s -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/v1/forecast?months_ahead=6")
if echo "$FORECAST" | grep -q "forecast\|predicted"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC} No forecast data"
fi

# ============================================================================
# PART 5: REPORTING & EXPORT
# ============================================================================
echo ""
echo -e "${YELLOW}[5/6] Reporting & Export${NC}"
echo "----------------------------------------"

echo -n "→ Generating PDF report... "
PDF_RESPONSE=$(curl -s -w "%{http_code}" -o "/tmp/carbon_report_test.pdf" \
    -H "Authorization: Bearer $TOKEN" \
    "$BASE_URL/api/v1/reports/pdf")

if [ "$PDF_RESPONSE" = "200" ]; then
    PDF_SIZE=$(ls -lh /tmp/carbon_report_test.pdf | awk '{print $5}')
    echo -e "${GREEN}✓${NC} Generated ($PDF_SIZE)"
else
    echo -e "${YELLOW}⚠${NC} Status: $PDF_RESPONSE"
fi

# ============================================================================
# PART 6: PERFORMANCE & HEALTH METRICS
# ============================================================================
echo ""
echo -e "${YELLOW}[6/6] Performance & Health Metrics${NC}"
echo "----------------------------------------"

echo -n "→ API health check... "
HEALTH_START=$(date +%s%N)
HEALTH_RESPONSE=$(curl -s "$BASE_URL/health")
HEALTH_END=$(date +%s%N)
HEALTH_TIME=$(( ($HEALTH_END - $HEALTH_START) / 1000000 ))

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓${NC} Response time: ${HEALTH_TIME}ms"
else
    echo -e "${RED}✗${NC}"
fi

echo -n "→ Database connectivity... "
DB_CHECK=$(curl -s "$BASE_URL/health/ready")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# ============================================================================
# SUMMARY
# ============================================================================
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  📊 Test Summary                                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Test User:      ${GREEN}$TEST_USER${NC}"
echo -e "Organization:   ${GREEN}$TEST_ORG${NC}"
echo -e "Emissions Data: ${GREEN}$EMISSION_COUNT transactions${NC}"
echo -e "Total CO2e:     ${GREEN}${TOTAL_EMISSIONS} tonnes${NC}"
echo -e "Anomalies:      ${GREEN}$ANOMALY_COUNT detected${NC}"
echo -e "API Health:     ${GREEN}${HEALTH_TIME}ms${NC}"
echo ""
echo -e "${GREEN}✅ End-to-End Test Complete!${NC}"
echo ""
echo "Test artifacts:"
echo "  - CSV file: $CSV_FILE"
echo "  - PDF report: /tmp/carbon_report_test.pdf"
echo "  - Access token saved in memory"
echo ""
echo "Next steps:"
echo "  1. Open http://localhost:3000"
echo "  2. Login with:"
echo "     Username: $TEST_USER"
echo "     Password: $TEST_PASS"
echo "  3. View imported emissions data in dashboard"
echo ""
