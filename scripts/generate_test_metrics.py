#!/usr/bin/env python3
"""
Script to generate test metrics and push them to Prometheus Pushgateway
Usage: python generate_test_metrics.py [duration] [interval]
  duration: How long to run the test in seconds (default: 60)
  interval: Interval between metrics pushes in seconds (default: 5)
"""

import time
import random
import sys
import socket
import requests
from datetime import datetime

# Configure pushgateway URL
PUSHGATEWAY_URL = 'http://localhost:9091/metrics/job/test_metrics'

# Default values
DEFAULT_DURATION = 60  # seconds
DEFAULT_INTERVAL = 5   # seconds

def get_hostname():
    """Get the hostname of the machine."""
    return socket.gethostname()

def push_metrics(metrics):
    """Push metrics to Prometheus Pushgateway."""
    try:
        response = requests.post(PUSHGATEWAY_URL, data=metrics)
        if response.status_code == 200:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Metrics pushed successfully")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to push metrics: HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error pushing metrics: {e}")

def generate_metrics():
    """Generate test metrics in Prometheus exposition format."""
    hostname = get_hostname()
    
    # Generate random values
    active_users = random.randint(5, 100)
    response_time = random.uniform(0.05, 0.5)
    error_rate = random.uniform(0, 0.1)
    db_connections = random.randint(1, 20)
    
    # Create metric strings in Prometheus format
    metrics = []
    metrics.append(f"# HELP salon_test_active_users Current number of active users")
    metrics.append(f"# TYPE salon_test_active_users gauge")
    metrics.append(f"salon_test_active_users{{instance=\"{hostname}\", environment=\"test\"}} {active_users}")
    
    metrics.append(f"# HELP salon_test_response_time Response time in seconds")
    metrics.append(f"# TYPE salon_test_response_time gauge")
    metrics.append(f"salon_test_response_time{{instance=\"{hostname}\", environment=\"test\"}} {response_time}")
    
    metrics.append(f"# HELP salon_test_error_rate Error rate as a fraction")
    metrics.append(f"# TYPE salon_test_error_rate gauge")
    metrics.append(f"salon_test_error_rate{{instance=\"{hostname}\", environment=\"test\"}} {error_rate}")
    
    metrics.append(f"# HELP salon_test_db_connections Number of active database connections")
    metrics.append(f"# TYPE salon_test_db_connections gauge")
    metrics.append(f"salon_test_db_connections{{instance=\"{hostname}\", environment=\"test\"}} {db_connections}")
    
    return "\n".join(metrics)

def main():
    # Parse command line arguments
    duration = DEFAULT_DURATION
    interval = DEFAULT_INTERVAL
    
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            print(f"Invalid duration value. Using default: {duration} seconds")
    
    if len(sys.argv) > 2:
        try:
            interval = int(sys.argv[2])
        except ValueError:
            print(f"Invalid interval value. Using default: {interval} seconds")
    
    print(f"Starting test metrics generator:")
    print(f"  - Duration: {duration} seconds")
    print(f"  - Interval: {interval} seconds")
    print(f"  - Pushing to: {PUSHGATEWAY_URL}")
    print(f"  - Press Ctrl+C to stop")
    
    start_time = time.time()
    end_time = start_time + duration
    
    try:
        while time.time() < end_time:
            metrics = generate_metrics()
            push_metrics(metrics)
            time.sleep(interval)
        
        print(f"\nTest completed after {duration} seconds")
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\nTest interrupted after {elapsed:.1f} seconds")

if __name__ == "__main__":
    main() 