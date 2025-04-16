#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Generate test traffic to the API to produce metrics
.DESCRIPTION
    This script sends a series of requests to various API endpoints
    to generate traffic that will be reflected in the metrics
.PARAMETER Duration
    Duration in seconds to run the test (default: 60)
.PARAMETER Interval
    Interval in milliseconds between requests (default: 500)
.PARAMETER BaseUrl
    Base URL of the API (default: http://localhost:8000)
#>

param(
    [int]$Duration = 60,
    [int]$Interval = 500,
    [string]$BaseUrl = "http://localhost:8000"
)

# Define API endpoints to test
$endpoints = @(
    "/api/v1/health",
    "/api/v1/services",
    "/api/v1/clients",
    "/docs",
    "/api/v1/appointments",
    "/api/v1/nonexistent"  # This will generate 404 errors
)

# Display test parameters
Write-Host "Starting API test traffic generator:"
Write-Host "  - Duration: $Duration seconds"
Write-Host "  - Interval: $Interval milliseconds"
Write-Host "  - Base URL: $BaseUrl"
Write-Host "  - Press Ctrl+C to stop"

# Calculate end time
$startTime = Get-Date
$endTime = $startTime.AddSeconds($Duration)

# Counters for statistics
$requestCount = 0
$successCount = 0
$errorCount = 0

try {
    while ((Get-Date) -lt $endTime) {
        # Pick a random endpoint
        $endpoint = $endpoints | Get-Random
        $url = "$BaseUrl$endpoint"
        
        # Send the request
        try {
            $response = Invoke-WebRequest -Uri $url -TimeoutSec 2 -ErrorAction SilentlyContinue
            $statusCode = $response.StatusCode
            $successCount++
        }
        catch [System.Net.WebException] {
            if ($_.Exception.Response) {
                $statusCode = [int]$_.Exception.Response.StatusCode
            }
            else {
                $statusCode = 0
            }
            $errorCount++
        }
        catch {
            $statusCode = 999
            $errorCount++
        }
        
        $requestCount++
        
        # Display progress
        $elapsedTime = ((Get-Date) - $startTime).TotalSeconds
        $percentComplete = [Math]::Min(100, [Math]::Round(($elapsedTime / $Duration) * 100, 1))
        
        Write-Host ("[{0:HH:mm:ss}] Request #{1}: {2} - Status: {3}" -f (Get-Date), $requestCount, $url, $statusCode)
        
        # Wait for the next interval
        Start-Sleep -Milliseconds $Interval
    }
}
catch [System.Management.Automation.PipelineStoppedException] {
    # This is thrown when the user presses Ctrl+C
    Write-Host "`nTest interrupted by user" -ForegroundColor Yellow
}
finally {
    # Calculate statistics
    $elapsedTime = ((Get-Date) - $startTime).TotalSeconds
    
    Write-Host "`nTest Summary:" -ForegroundColor Cyan
    Write-Host "  Duration: $elapsedTime seconds"
    Write-Host "  Total Requests: $requestCount"
    Write-Host "  Successful Requests: $successCount"
    Write-Host "  Failed Requests: $errorCount"
    Write-Host "  Success Rate: $([Math]::Round(($successCount / [Math]::Max(1, $requestCount)) * 100, 1))%"
    Write-Host "  Average RPS: $([Math]::Round($requestCount / [Math]::Max(1, $elapsedTime), 2))"
} 