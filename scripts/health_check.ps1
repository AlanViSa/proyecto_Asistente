# PowerShell Health Check Script for Salon Assistant

# Functions for colored output
function Write-GreenOutput {
    param([string]$message)
    Write-Host $message -ForegroundColor Green
}

function Write-RedOutput {
    param([string]$message)
    Write-Host $message -ForegroundColor Red
}

function Write-YellowOutput {
    param([string]$message)
    Write-Host $message -ForegroundColor Yellow
}

# Function to check an endpoint
function Test-Endpoint {
    param(
        [string]$url,
        [string]$name
    )
    
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-GreenOutput "✓ $name is working correctly"
            return $true
        }
        else {
            Write-RedOutput "✗ $name is not responding correctly (Code: $($response.StatusCode))"
            return $false
        }
    }
    catch {
        Write-RedOutput "✗ $name is not responding correctly: $($_.Exception.Message)"
        return $false
    }
}

# Verify we're in the correct directory
if (-not (Test-Path "docker-compose.yml")) {
    Write-RedOutput "Error: docker-compose.yml not found. Make sure you are in the root directory of the project."
    exit 1
}

Write-YellowOutput "Starting system health check..."

# Check API endpoints
Write-YellowOutput "`nChecking API endpoints..."
Test-Endpoint "http://localhost:8000/api/health" "Health endpoint"
Test-Endpoint "http://localhost:8000/api/services" "Services endpoint"

# Check if local development server is accessible
Write-YellowOutput "`nChecking local development server..."
Test-Endpoint "http://localhost:8000/" "Main application"

# Check database connection (assuming application is running and database is accessible)
Write-YellowOutput "`nChecking database connectivity (via API)..."
Test-Endpoint "http://localhost:8000/api/health" "API health (includes database check)"

# Check metrics if available
Write-YellowOutput "`nChecking metrics..."
$metricsAvailable = Test-Endpoint "http://localhost:8000/metrics" "Prometheus metrics endpoint"

if (-not $metricsAvailable) {
    Write-YellowOutput "Note: Metrics endpoint not available or not configured."
    Write-YellowOutput "You can setup Prometheus metrics by configuring the application for monitoring."
}

# Final summary
Write-GreenOutput "`nHealth check completed." 