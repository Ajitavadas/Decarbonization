#!/bin/bash
# Dry Run Integration Test Script
# Runs the complete E2E workflow test in Docker

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "DECARBONIZATION PLATFORM - DRY RUN TEST"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${YELLOW}→ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Step 1: Check for .env file
print_step "Checking environment configuration..."
if [ ! -f "backend/.env" ]; then
    print_error "backend/.env file not found!"
    echo "Please create backend/.env with required API keys (CLIMATIQ_API_KEY, MISTRAL_API_KEY)"
    exit 1
fi

# Check for required API keys
if ! grep -q "CLIMATIQ_API_KEY" backend/.env || grep -q "CLIMATIQ_API_KEY=your_" backend/.env; then
    print_error "CLIMATIQ_API_KEY not configured in backend/.env"
    exit 1
fi
print_success "Environment configuration found"

# Step 2: Build and start services
print_step "Starting Docker services..."
docker-compose down --remove-orphans 2>/dev/null || true
docker-compose up -d --build postgres redis backend

# Step 3: Wait for backend health
print_step "Waiting for backend to be healthy..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend is healthy"
        break
    fi
    attempt=$((attempt + 1))
    echo "  Waiting... (attempt $attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    print_error "Backend did not become healthy within timeout"
    docker-compose logs backend --tail=50
    exit 1
fi

# Step 4: Run integration tests
print_step "Running dry run integration tests..."
echo ""

# Run the tests inside the backend container
docker-compose exec -T backend pip install pytest pytest-asyncio --quiet 2>/dev/null || true
docker-compose exec -T backend python -m pytest tests/test_dry_run.py -v --tb=short

test_result=$?

# Step 5: Summary
echo ""
echo "=============================================="
if [ $test_result -eq 0 ]; then
    print_success "DRY RUN COMPLETE - ALL TESTS PASSED!"
else
    print_error "DRY RUN FAILED - Check logs above"
fi
echo "=============================================="

# Optional: Show service status
echo ""
print_step "Service Status:"
docker-compose ps

exit $test_result
