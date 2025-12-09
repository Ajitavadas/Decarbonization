#!/bin/bash
# End-to-End Test Script for Decarbonization Platform

BASE_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

echo "🧪 Starting End-to-End Tests..."
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_count=0
pass_count=0
fail_count=0

# Function to run a test
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_status="$3"
    
    test_count=$((test_count + 1))
    echo -n "Test $test_count: $test_name... "
    
    response=$(eval "$command")
    status=$?
    
    if [ $status -eq 0 ] && [ "$expected_status" = "0" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        pass_count=$((pass_count + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Response: $response"
        fail_count=$((fail_count + 1))
        return 1
    fi
}

echo "📡 PART 1: INFRASTRUCTURE TESTS"
echo "================================"

# Test 1: Health check
run_test "Backend health check" \
    "curl -s $BASE_URL/health -w '%{http_code}' -o /dev/null | grep -q '200'" \
    "0"

# Test 2: Frontend availability
run_test "Frontend availability" \
    "curl -s $FRONTEND_URL -w '%{http_code}' -o /dev/null | grep -q '200'" \
    "0"

# Test 3: API docs available
run_test "API documentation" \
    "curl -s $BASE_URL/docs -w '%{http_code}' -o /dev/null | grep -q '200'" \
    "0"

echo ""
echo "👤 PART 2: AUTHENTICATION TESTS"
echo "================================"

# Generate unique test data
TIMESTAMP=$(date +%s)
TEST_EMAIL="test${TIMESTAMP}@example.com"
TEST_USERNAME="testuser${TIMESTAMP}"
TEST_PASSWORD="SecurePassword123!"
TEST_ORG="TestOrg${TIMESTAMP}"

# Test 4: User registration
echo -n "Test $((test_count + 1)): User registration... "
test_count=$((test_count + 1))

REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "'"$TEST_EMAIL"'",
        "username": "'"$TEST_USERNAME"'",
        "password": "'"$TEST_PASSWORD"'",
        "organization_name": "'"$TEST_ORG"'"
    }')

if echo "$REGISTER_RESPONSE" | grep -q "id"; then
    echo -e "${GREEN}✓ PASS${NC}"
    pass_count=$((pass_count + 1))
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Response: $REGISTER_RESPONSE"
    fail_count=$((fail_count + 1))
fi

# Test 5: User login
echo -n "Test $((test_count + 1)): User login... "
test_count=$((test_count + 1))

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$TEST_USERNAME&password=$TEST_PASSWORD")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ PASS${NC}"
    pass_count=$((pass_count + 1))
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Response: $LOGIN_RESPONSE"
    fail_count=$((fail_count + 1))
    ACCESS_TOKEN=""
fi

# Test 6: Get current user
if [ -n "$ACCESS_TOKEN" ]; then
    run_test "Get current user" \
        "curl -s -H 'Authorization: Bearer $ACCESS_TOKEN' $BASE_URL/auth/me | grep -q 'email'" \
        "0"
fi

echo ""
echo "📊 PART 3: DASHBOARD API TESTS"
echo "================================"

if [ -n "$ACCESS_TOKEN" ]; then
    # Test 7: Dashboard overview
    run_test "Dashboard overview" \
        "curl -s -H 'Authorization: Bearer $ACCESS_TOKEN' $BASE_URL/api/v1/dashboard -w '%{http_code}' -o /dev/null | grep -q '200'" \
        "0"
    
    # Test 8: Emissions list
    run_test "Emissions list" \
        "curl -s -H 'Authorization: Bearer $ACCESS_TOKEN' $BASE_URL/api/v1/emissions -w '%{http_code}' -o /dev/null | grep -q '200'" \
        "0"
else
    echo -e "${YELLOW}Skipping dashboard tests (no auth token)${NC}"
fi

echo ""
echo "🤖 PART 4: AI COPILOT TESTS"
echo "================================"

if [ -n "$ACCESS_TOKEN" ]; then
    # Test 9: Copilot query
    echo -n "Test $((test_count + 1)): AI Copilot query... "
    test_count=$((test_count + 1))
    
    COPILOT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/copilot/query" \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"query": "What are my total emissions?"}')
    
    if echo "$COPILOT_RESPONSE" | grep -q "answer"; then
        echo -e "${GREEN}✓ PASS${NC}"
        pass_count=$((pass_count + 1))
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Response: $COPILOT_RESPONSE"
        fail_count=$((fail_count + 1))
    fi
else
    echo -e "${YELLOW}Skipping AI tests (no auth token)${NC}"
fi

echo ""
echo "📈 PART 5: DATA ANALYSIS TESTS"
echo "================================"

if [ -n "$ACCESS_TOKEN" ]; then
    # Test 10: Anomalies endpoint
    run_test "Anomaly detection" \
        "curl -s -H 'Authorization: Bearer $ACCESS_TOKEN' $BASE_URL/api/v1/anomalies -w '%{http_code}' -o /dev/null | grep -q '200'" \
        "0"
    
    # Test 11: Forecast endpoint
    run_test "Emissions forecasting" \
        "curl -s -H 'Authorization: Bearer $ACCESS_TOKEN' '$BASE_URL/api/v1/forecast?months_ahead=12' -w '%{http_code}' -o /dev/null | grep -q '200'" \
        "0"
else
    echo -e "${YELLOW}Skipping analysis tests (no auth token)${NC}"
fi

echo ""
echo "📄 PART 6: REPORTING TESTS"
echo "================================"

if [ -n "$ACCESS_TOKEN" ]; then
    # Test 12: PDF report generation
    run_test "PDF report generation" \
        "curl -s -H 'Authorization: Bearer $ACCESS_TOKEN' $BASE_URL/api/v1/reports/pdf -w '%{http_code}' -o /dev/null | grep -q '200'" \
        "0"
else
    echo -e "${YELLOW}Skipping report tests (no auth token)${NC}"
fi

echo ""
echo "================================"
echo "📊 TEST SUMMARY"
echo "================================"
echo "Total Tests: $test_count"
echo -e "Passed: ${GREEN}$pass_count${NC}"
echo -e "Failed: ${RED}$fail_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    exit 1
fi
