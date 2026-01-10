#!/bin/bash
# End-to-end test script for Carbon Auditor functionality
# Run from the Decarbonization_v2 directory

set -e

API_URL="http://localhost:8000/api/v1"
FRONTEND_URL="http://localhost:3000"

echo "=========================================="
echo "Carbon Auditor End-to-End Test"
echo "=========================================="
echo ""

# Step 1: Fresh login
echo "Step 1: Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpassword123"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Login failed: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ Login successful"
echo ""

# Step 2: Get or create a project
echo "Step 2: Getting/creating test project..."
PROJECTS=$(curl -s "$API_URL/projects/" -H "Authorization: Bearer $TOKEN")
PROJECT_ID=$(echo $PROJECTS | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$PROJECT_ID" ]; then
    echo "Creating new test project..."
    PROJECT_RESPONSE=$(curl -s -X POST "$API_URL/projects/" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Anomaly Test Project",
        "description": "Test project for anomaly detection",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "reporting_year": "2024"
      }')
    PROJECT_ID=$(echo $PROJECT_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
fi

echo "✅ Using project: $PROJECT_ID"
echo ""

# Step 3: Upload test CSV files
echo "Step 3: Uploading test CSV files..."

echo "  Uploading test_anomalies_1.csv (electricity spike + zero gas)..."
UPLOAD1=$(curl -s -X POST "$API_URL/upload/csv" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/home/dasaj/dev/ai_residency/Decarbonization_v2/backend/tests/test_anomalies_1.csv" \
  -F "project_id=$PROJECT_ID")
echo "  Response: $(echo $UPLOAD1 | head -c 200)"

sleep 3

echo "  Uploading test_anomalies_2.csv (varied activities)..."
UPLOAD2=$(curl -s -X POST "$API_URL/upload/csv" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/home/dasaj/dev/ai_residency/Decarbonization_v2/backend/tests/test_anomalies_2.csv" \
  -F "project_id=$PROJECT_ID")
echo "  Response: $(echo $UPLOAD2 | head -c 200)"

sleep 3

echo "  Uploading test_anomalies_3.csv (procurement + waste)..."
UPLOAD3=$(curl -s -X POST "$API_URL/upload/csv" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/home/dasaj/dev/ai_residency/Decarbonization_v2/backend/tests/test_anomalies_3.csv" \
  -F "project_id=$PROJECT_ID")
echo "  Response: $(echo $UPLOAD3 | head -c 200)"

echo ""
echo "✅ CSV uploads complete"
echo ""

# Wait for processing
echo "Step 4: Waiting for batch processing..."
sleep 5
echo ""

# Step 5: Run audit (without AI to speed up testing)
echo "Step 5: Running Carbon Audit (rule-based only)..."
AUDIT_RESPONSE=$(curl -s -X POST "$API_URL/audit/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"include_ai_analysis": false}')

echo "Audit Response:"
echo "$AUDIT_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d.get('summary', {}), indent=2))"
echo ""

TOTAL_FINDINGS=$(echo $AUDIT_RESPONSE | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('summary',{}).get('total_findings', 0))")
echo "✅ Audit found $TOTAL_FINDINGS findings"
echo ""

# Step 6: Get audit summary
echo "Step 6: Getting audit summary..."
SUMMARY=$(curl -s "$API_URL/audit/summary" -H "Authorization: Bearer $TOKEN")
echo "$SUMMARY" | python3 -m json.tool
echo ""

# Step 7: List findings
echo "Step 7: Listing open findings..."
FINDINGS=$(curl -s "$API_URL/audit/findings?status=open&limit=5" -H "Authorization: Bearer $TOKEN")
echo "First 5 open findings:"
echo "$FINDINGS" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f'  - [{f[\"severity\"]}] {f[\"title\"]}') for f in d.get('findings',[])]"
echo ""

# Step 8: Test resolving a finding
echo "Step 8: Testing finding resolution..."
FIRST_FINDING=$(echo $FINDINGS | python3 -c "import sys,json; d=json.load(sys.stdin); findings=d.get('findings',[]); print(findings[0]['id'] if findings else '')")

if [ -n "$FIRST_FINDING" ]; then
    RESOLVE_RESPONSE=$(curl -s -X PATCH "$API_URL/audit/findings/$FIRST_FINDING/resolve" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"status": "resolved", "notes": "Reviewed and confirmed as expected behavior during testing"}')
    echo "Resolved finding: $FIRST_FINDING"
    echo "Response: $RESOLVE_RESPONSE"
else
    echo "No findings to resolve"
fi
echo ""

# Step 9: Verify updated summary
echo "Step 9: Verifying updated summary after resolution..."
SUMMARY_AFTER=$(curl -s "$API_URL/audit/summary" -H "Authorization: Bearer $TOKEN")
echo "$SUMMARY_AFTER" | python3 -m json.tool
echo ""

# Step 10: Test filtering
echo "Step 10: Testing filters..."
echo "  By type (anomaly):"
curl -s "$API_URL/audit/findings?flag_type=anomaly&limit=3" -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'    Found {d.get(\"total\",0)} anomaly findings')"

echo "  By severity (warning):"
curl -s "$API_URL/audit/findings?severity=warning&limit=3" -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'    Found {d.get(\"total\",0)} warning findings')"

echo "  By status (resolved):"
curl -s "$API_URL/audit/findings?status=resolved&limit=3" -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'    Found {d.get(\"total\",0)} resolved findings')"
echo ""

echo "=========================================="
echo "✅ End-to-End Test Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Open browser at $FRONTEND_URL/login"
echo "  2. Login with test@example.com / testpassword123"
echo "  3. Navigate to $FRONTEND_URL/anomalies"
echo "  4. Review the findings in the UI"
