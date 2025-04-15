#!/bin/bash

# Colors for messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to print messages
print_message() {
    echo -e "${2}${1}${NC}"
}

# Function to check an endpoint
check_endpoint() {
    local url=$1
    local name=$2
    local response=$(curl -s -w "\n%{http_code}" $url)
    local status_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')

    if [ "$status_code" = "200" ]; then
        print_message "✓ $name is working correctly" "$GREEN"
        return 0
    else
        print_message "✗ $name is not responding correctly (Code: $status_code)" "$RED"
        return 1
    fi
}

# Verify that we are in the correct directory
if [ ! -f "docker-compose.yml" ]; then
    print_message "Error: docker-compose.yml not found. Make sure you are in the root directory of the project." "$RED"
    exit 1
fi

print_message "Starting system health check..." "$YELLOW"

# Verify that the containers are running
print_message "\nChecking containers..." "$YELLOW"
if docker-compose ps | grep -q "Up"; then
    print_message "✓ All containers are running" "$GREEN"
else
    print_message "✗ Some containers are not running" "$RED"
    exit 1
fi

# Verify API endpoints
print_message "\nChecking API endpoints..." "$YELLOW"
check_endpoint "http://localhost:8000/health" "Health endpoint"
check_endpoint "http://localhost:8000/health/db" "Database health endpoint"

# Verify Prometheus
print_message "\nChecking Prometheus..." "$YELLOW"
check_endpoint "http://localhost:9090/-/healthy" "Prometheus"

# Verify Grafana
print_message "\nChecking Grafana..." "$YELLOW"
check_endpoint "http://localhost:3000/api/health" "Grafana"

# Verify database connection
print_message "\nChecking database connection..." "$YELLOW"
if docker-compose exec db pg_isready -U postgres > /dev/null 2>&1; then
    print_message "✓ Successful database connection" "$GREEN"
else
    print_message "✗ Could not connect to the database" "$RED"
    exit 1
fi

# Verify Redis
print_message "\nChecking Redis..." "$YELLOW"
if docker-compose exec redis redis-cli ping | grep -q "PONG"; then
    print_message "✓ Redis is working correctly" "$GREEN"
else
    print_message "✗ Redis is not responding" "$RED"
    exit 1
fi

# Verify metrics
print_message "\nChecking metrics..." "$YELLOW"
if curl -s http://localhost:8000/metrics | grep -q "http_requests_total"; then
    print_message "✓ Metrics are being collected" "$GREEN"
else
    print_message "✗ No metrics found" "$RED"
    exit 1
fi

print_message "\nHealth check completed." "$GREEN"