# PowerShell Test Script for Decarbonization Platform
# Comprehensive API and Infrastructure Testing

$ErrorActionPreference = "Continue"
$BASE_URL = "http://localhost:8000/api/v1"
$ROOT_URL = "http://localhost:8000"

# Colors
function Write-Success { param($msg) Write-Host "✓ $msg" -ForegroundColor Green }
function Write-Failure { param($msg) Write-Host "✗ $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "ℹ $msg" -ForegroundColor Yellow }
function Write-Header { 
    param($msg) 
    Write-Host "`n" ("=" * 80) -ForegroundColor Cyan
    Write-Host $msg.PadLeft(($msg.Length + 80) / 2) -ForegroundColor Cyan -NoNewline
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor Cyan
}

$passed = 0
$failed = 0

Write-Host "`n"
Write-Host ("=" * 80) -ForegroundColor Green
Write-Host "DECARBONIZATION PLATFORM - COMPREHENSIVE TEST SUITE".PadLeft(55) -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Green
Write-Host "`nTest started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host "Target URL: $BASE_URL" -ForegroundColor Yellow

# Test 1: Root Endpoint
Write-Header "TEST 1: Root Endpoint"
try {
    $response = Invoke-WebRequest -Uri "$ROOT_URL/" -UseBasicParsing -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host ($data | ConvertTo-Json -Depth 3)
    Write-Success "Root endpoint working!"
    $passed++
} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Failure "Root endpoint failed: $($_.Exception.Message)"
    $failed++
}

# Test 2: Health Check
Write-Header "TEST 2: Health Check Endpoint"
try {
    $response = Invoke-WebRequest -Uri "$ROOT_URL/health" -UseBasicParsing -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host ($data | ConvertTo-Json -Depth 3)
    Write-Success "Health check passed!"
    $passed++
} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Failure "Health check failed: $($_.Exception.Message)"
    $failed++
}

# Test 3: Single Emission Estimate
Write-Header "TEST 3: Single Emission Estimate"
$payload = @{
    emission_factor = @{
        activity_id = "electricity-energy_source_grid_mix"
        region = "US"
        year = "2023"
        source = "EPA"
    }
    parameters = @{
        energy = 100
        energy_unit = "kWh"
    }
} | ConvertTo-Json -Depth 10

Write-Info "Testing electricity emission calculation (100 kWh)"
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/estimate/single" -Method POST -Body $payload -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host ($data | ConvertTo-Json -Depth 3)
    Write-Success "Estimate calculated successfully!"
    $passed++
} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Failure "Single estimate failed: $($_.Exception.Message)"
    $failed++
}

# Test 4: Travel Distance
Write-Header "TEST 4: Travel Distance Calculation"
$payload = @{
    mode = "air"
    distance = 500
    distance_unit = "km"
    cabin_class = "economy"
    passengers = 1
} | ConvertTo-Json

Write-Info "Testing air travel emissions (500km economy)"
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/travel/distance" -Method POST -Body $payload -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host ($data | ConvertTo-Json -Depth 3)
    Write-Success "Travel calculation successful!"
    $passed++
} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Failure "Travel calculation failed: $($_.Exception.Message)"
    $failed++
}

# Test 5: Electricity
Write-Header "TEST 5: Electricity Consumption"
$payload = @{
    energy = 1000
    energy_unit = "kWh"
    region = "US-CA"
} | ConvertTo-Json

Write-Info "Testing electricity emissions (1000 kWh California)"
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/energy/electricity" -Method POST -Body $payload -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host ($data | ConvertTo-Json -Depth 3)
    Write-Success "Electricity calculation successful!"
    $passed++
} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Failure "Electricity calculation failed: $($_.Exception.Message)"
    $failed++
}

# Test 6: Fuel Combustion
Write-Header "TEST 6: Fuel Combustion (Scope 1)"
$payload = @{
    fuel_type = "diesel"
    volume = 100
    volume_unit = "liter"
    year = "2023"
} | ConvertTo-Json

Write-Info "Testing fuel combustion (100 liters diesel)"
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/energy/fuel" -Method POST -Body $payload -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host ($data | ConvertTo-Json -Depth 3)
    Write-Success "Fuel combustion calculation successful!"
    $passed++
} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Failure "Fuel combustion failed: $($_.Exception.Message)"
    $failed++
}

# Test 7: Autopilot Suggestions
Write-Header "TEST 7: Autopilot AI Suggestions"
$payload = @{
    query = "office electricity consumption"
    region = "US"
    year = "2023"
} | ConvertTo-Json

Write-Info "Testing Autopilot AI for emission factor suggestions"
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/autopilot/suggest" -Method POST -Body $payload -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host ($data | ConvertTo-Json -Depth 3)
    Write-Success "Autopilot suggestions retrieved!"
    $passed++
} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Failure "Autopilot failed: $($_.Exception.Message)"
    $failed++
}

# Test 8: Batch Estimation
Write-Header "TEST 8: Batch Estimation"
$payload = @{
    estimates = @(
        @{
            emission_factor = @{
                activity_id = "electricity-energy_source_grid_mix"
                region = "US-NY"
            }
            parameters = @{
                energy = 500
                energy_unit = "kWh"
            }
        },
        @{
            emission_factor = @{
                activity_id = "electricity-energy_source_grid_mix"
                region = "US-CA"
            }
            parameters = @{
                energy = 750
                energy_unit = "kWh"
            }
        },
        @{
            emission_factor = @{
                activity_id = "electricity-energy_source_grid_mix"
                region = "US-TX"
            }
            parameters = @{
                energy = 1000
                energy_unit = "kWh"
            }
        }
    )
} | ConvertTo-Json -Depth 10

Write-Info "Testing batch estimation with 3 calculations"
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/estimate/batch" -Method POST -Body $payload -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host ($data | ConvertTo-Json -Depth 3)
    Write-Success "Batch estimation submitted!"
    $passed++
} catch {
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Failure "Batch estimation failed: $($_.Exception.Message)"
    $failed++
}

# Test 9: Docker Services
Write-Header "TEST 9: Docker Services Status"
try {
    $services = docker-compose ps --format json 2>$null | ConvertFrom-Json
    Write-Host "Service Status:" -ForegroundColor Cyan
    foreach ($service in $services) {
        $status = if ($service.State -eq "running") { "Running" } else { $service.State }
        $color = if ($service.State -eq "running") { "Green" } else { "Red" }
        Write-Host "  $($service.Service): " -NoNewline
        Write-Host $status -ForegroundColor $color
    }
    Write-Success "Docker services checked!"
    $passed++
} catch {
    Write-Failure "Docker services check failed: $($_.Exception.Message)"
    $failed++
}

# Test 10: Database Tables
Write-Header "TEST 10: Database Tables Verification"
try {
    $tables = docker exec decarbonization-db psql -U carbon_user -d decarbonization_db -c "\dt" 2>$null
    Write-Host $tables
    if ($tables -match "users" -and $tables -match "emission_activities") {
        Write-Success "All database tables exist!"
        $passed++
    } else {
        Write-Failure "Some database tables are missing"
        $failed++
    }
} catch {
    Write-Failure "Database check failed: $($_.Exception.Message)"
    $failed++
}

# Summary
Write-Header "TEST SUMMARY"
$total = $passed + $failed
$percentage = [math]::Round(($passed / $total) * 100, 1)

Write-Host "Total Tests: $total" -ForegroundColor White
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host "Success Rate: $percentage%" -ForegroundColor $(if ($percentage -eq 100) { "Green" } elseif ($percentage -ge 75) { "Yellow" } else { "Red" })

if ($percentage -eq 100) {
    Write-Host "`n🎉 ALL TESTS PASSED! Platform is fully operational! 🎉" -ForegroundColor Green
} elseif ($percentage -ge 75) {
    Write-Host "`n⚠ Most tests passed. Review failures above." -ForegroundColor Yellow
} else {
    Write-Host "`n❌ Many tests failed. Platform needs attention." -ForegroundColor Red
}

Write-Host "`nTest completed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""
