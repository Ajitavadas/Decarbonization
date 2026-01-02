# PowerShell script to run integration tests inside the docker backend container

Write-Host "=========================================="
Write-Host "Running Integration Tests in Docker"
Write-Host "=========================================="
Write-Host ""

# Check if backend container is running
$backendRunning = docker ps | Select-String -Pattern "decarbonization-backend"
if (-not $backendRunning) {
    Write-Host "Error: Backend container is not running" -ForegroundColor Red
    Write-Host "Please run 'docker-compose up -d' first"
    exit 1
}

# Copy test file to container
Write-Host "Copying test file to container..."
docker cp test_integration.py decarbonization-backend:/app/test_integration.py

# Run tests inside container
Write-Host "Running integration tests..."
Write-Host ""

docker exec -it decarbonization-backend python test_integration.py

# Get exit code
$EXIT_CODE = $LASTEXITCODE

Write-Host ""
if ($EXIT_CODE -eq 0) {
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "✓ All tests passed!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
} else {
    Write-Host "==========================================" -ForegroundColor Red
    Write-Host "✗ Some tests failed (exit code: $EXIT_CODE)" -ForegroundColor Red
    Write-Host "==========================================" -ForegroundColor Red
}

exit $EXIT_CODE

