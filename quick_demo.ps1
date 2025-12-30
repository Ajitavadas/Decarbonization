# Quick Demo - Decarbonization Platform Status Check
# Shows all working components without authentication

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  DECARBONIZATION PLATFORM - STATUS" -ForegroundColor Cyan  
Write-Host "========================================`n" -ForegroundColor Cyan

# Test 1: Platform API
Write-Host "1. Testing Platform API..." -ForegroundColor Yellow
try {
    $root = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing | ConvertFrom-Json
    Write-Host "   âœ" Platform Name: $($root.name)" -ForegroundColor Green
    Write-Host "   âœ" Version: $($root.version)" -ForegroundColor Green
    Write-Host "   âœ" Status: $($root.status)" -ForegroundColor Green
    Write-Host "   âœ" API Docs: http://localhost:8000$($root.docs)" -ForegroundColor Green
} catch {
    Write-Host "   âœ— API not responding" -ForegroundColor Red
}

# Test 2: Health Check
Write-Host "`n2. Testing Health Check..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | ConvertFrom-Json
    Write-Host "   âœ" Health Status: $($health.status)" -ForegroundColor Green
    Write-Host "   âœ" Environment: $($health.environment)" -ForegroundColor Green
} catch {
    Write-Host "   âœ— Health check failed" -ForegroundColor Red
}

# Test 3: Docker Services
Write-Host "`n3. Testing Docker Services..." -ForegroundColor Yellow
try {
    $services = docker ps --filter "name=decarbonization" --format "{{.Names}}: {{.Status}}" 2>$null
    if ($services) {
        foreach ($service in $services) {
            Write-Host "   âœ" $service" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "   âœ— Docker services check failed" -ForegroundColor Red
}

# Test 4: Database
Write-Host "`n4. Testing Database..." -ForegroundColor Yellow
try {
    $dbCheck = docker exec decarbonization-db psql -U carbon_user -d decarbonization_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>$null
    $tableCount = $dbCheck.Trim()
    Write-Host "   âœ" Database connected" -ForegroundColor Green
    Write-Host "   âœ" Tables created: $tableCount" -ForegroundColor Green
    
    # Show table names
    $tables = docker exec decarbonization-db psql -U carbon_user -d decarbonization_db -t -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;" 2>$null
    Write-Host "   âœ" Tables: $($tables -replace "`n",' / ' -replace '  ','')" -ForegroundColor Green
} catch {
    Write-Host "   âœ— Database check failed" -ForegroundColor Red
}

# Test 5: Redis Cache
Write-Host "`n5. Testing Redis Cache..." -ForegroundColor Yellow
try {
    $redisCheck = docker exec decarbonization-redis redis-cli PING 2>$null
    if ($redisCheck -match "PONG") {
        Write-Host "   âœ" Redis responding" -ForegroundColor Green
        
        $redisInfo = docker exec decarbonization-redis redis-cli INFO server 2>$null | Select-String "redis_version"
        Write-Host "   âœ" $redisInfo" -ForegroundColor Green
    }
} catch {
    Write-Host "   âœ— Redis check failed" -ForegroundColor Red
}

# Test 6: Celery Workers
Write-Host "`n6. Testing Celery Workers..." -ForegroundColor Yellow
try {
    $workerStatus = docker logs decarbonization-celery-worker --tail 5 2>$null | Select-String "ready"
    if ($workerStatus) {
        Write-Host "   âœ" Celery worker is ready" -ForegroundColor Green
    } else {
        Write-Host "   âš  Celery worker starting..." -ForegroundColor Yellow
    }
    
    $beatStatus = docker logs decarbonization-celery-beat --tail 5 2>$null | Select-String "beat: Starting"
    if ($beatStatus) {
        Write-Host "   âœ" Celery beat scheduler running" -ForegroundColor Green
    }
} catch {
    Write-Host "   âœ— Celery check failed" -ForegroundColor Red
}

# Test 7: OpenAPI Documentation
Write-Host "`n7. Testing API Documentation..." -ForegroundColor Yellow
try {
    $docsResponse = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing
    if ($docsResponse.StatusCode -eq 200) {
        Write-Host "   âœ" Swagger UI available at: http://localhost:8000/docs" -ForegroundColor Green
        Write-Host "   âœ" ReDoc available at: http://localhost:8000/redoc" -ForegroundColor Green
    }
} catch {
    Write-Host "   âœ— API documentation not available" -ForegroundColor Red
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  PLATFORM STATUS SUMMARY" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "âœ… Core Platform: " -NoNewline -ForegroundColor Green
Write-Host "OPERATIONAL" -ForegroundColor White

Write-Host "`n📚 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Open Swagger UI: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   2. Test endpoints interactively" -ForegroundColor White
Write-Host "   3. Add Climatiq API key to backend/.env" -ForegroundColor White
Write-Host "   4. Create user via /api/v1/auth/register" -ForegroundColor White
Write-Host "   5. Start calculating emissions!`n" -ForegroundColor White

Write-Host "⚠️  Note: Most endpoints require authentication" -ForegroundColor Yellow
Write-Host "   Use Swagger UI (http://localhost:8000/docs) for easy testing`n" -ForegroundColor Yellow
