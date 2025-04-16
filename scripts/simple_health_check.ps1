# Simple PowerShell Health Check Script

Write-Host "Starting health checks..." -ForegroundColor Yellow

# Check API endpoints
Write-Host "`nChecking API endpoints..." -ForegroundColor Yellow

try {
    $healthResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing
    if ($healthResponse.StatusCode -eq 200) {
        Write-Host "✓ Health endpoint is working correctly" -ForegroundColor Green
    }
}
catch {
    Write-Host "✗ Health endpoint is not responding correctly" -ForegroundColor Red
}

try {
    $servicesResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/services" -UseBasicParsing
    if ($servicesResponse.StatusCode -eq 200) {
        Write-Host "✓ Services endpoint is working correctly" -ForegroundColor Green
    }
}
catch {
    Write-Host "✗ Services endpoint is not responding correctly" -ForegroundColor Red
}

# Check if metrics are available
Write-Host "`nChecking metrics..." -ForegroundColor Yellow
try {
    $metricsResponse = Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing -ErrorAction Stop
    if ($metricsResponse.StatusCode -eq 200) {
        Write-Host "✓ Metrics endpoint is working correctly" -ForegroundColor Green
    }
}
catch {
    Write-Host "✗ Metrics endpoint is not available" -ForegroundColor Red
    Write-Host "Note: You can setup Prometheus metrics by configuring the application for monitoring." -ForegroundColor Yellow
}

Write-Host "`nHealth check completed." -ForegroundColor Green 