# PowerShell script to start monitoring services
Write-Host "Starting monitoring services..." -ForegroundColor Cyan

# Check if docker-compose is available
try {
    $dockerComposeVersion = docker-compose --version
    Write-Host "Found Docker Compose: $dockerComposeVersion" -ForegroundColor Green
}
catch {
    Write-Host "Error: Docker Compose not found. Please install Docker Compose before continuing." -ForegroundColor Red
    exit 1
}

# Verify docker is running
try {
    $dockerInfo = docker info
    Write-Host "Docker is running" -ForegroundColor Green
}
catch {
    Write-Host "Error: Docker is not running. Please start Docker Desktop or Docker service." -ForegroundColor Red
    exit 1
}

# Start monitoring services
Write-Host "`nStarting Prometheus, Pushgateway, and Grafana..." -ForegroundColor Cyan
docker-compose up -d prometheus pushgateway grafana

# Check if services are running
Write-Host "`nVerifying services..." -ForegroundColor Cyan
$services = docker-compose ps
Write-Host $services

# Provide instructions
Write-Host "`nMonitoring services are now running!" -ForegroundColor Green
Write-Host "`nAccess points:" -ForegroundColor Yellow
Write-Host "- Prometheus: http://localhost:9090" -ForegroundColor Yellow
Write-Host "- Pushgateway: http://localhost:9091" -ForegroundColor Yellow
Write-Host "- Grafana: http://localhost:3000 (login with admin/admin)" -ForegroundColor Yellow
Write-Host "`nTo verify the setup:" -ForegroundColor Yellow
Write-Host "1. In Prometheus UI, go to Status > Targets to verify application scraping" -ForegroundColor Yellow
Write-Host "2. In Grafana, go to Dashboards to verify Salon Assistant dashboard is present" -ForegroundColor Yellow
Write-Host "3. Generate some requests to the application and check metrics in Grafana" -ForegroundColor Yellow
Write-Host "4. Use the test_metrics.ps1 script to generate traffic" -ForegroundColor Yellow
Write-Host "5. Use the generate_test_metrics.py script to push custom metrics" -ForegroundColor Yellow

Write-Host "`nTo stop the services:" -ForegroundColor Yellow
Write-Host "docker-compose down" -ForegroundColor Yellow 