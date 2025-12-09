#!/bin/bash
set -e

echo "🧪 Week 1 Test Suite - AI Carbon Accounting Platform"
echo "===================================================="

# Ensure test DB is ready
docker compose exec postgres psql -U decarb_user -c "DROP DATABASE IF EXISTS decarb_test_db;" 2>/dev/null || true
docker compose exec postgres psql -U decarb_user -c "CREATE DATABASE decarb_test_db;" 2>/dev/null || true

cd /app
# Run comprehensive tests
pytest tests/ \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-fail-under=70 \
    -v \
    --tb=short \
    --strict-markers

echo ""
echo "✅ Week 1 Complete! Coverage report: htmlcov/index.html"