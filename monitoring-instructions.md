# Salon Assistant Monitoring System

This document provides instructions for using the monitoring system set up for the Salon Assistant application.

## Monitoring Components

The monitoring system consists of:

1. **Prometheus**: Time-series database for storing metrics
2. **Grafana**: Visualization tool for creating dashboards
3. **Pushgateway**: Component that allows pushing metrics to Prometheus
4. **Application Metrics**: Custom metrics collected by the FastAPI application

## Starting the Monitoring System

### Option 1: Start All Services Together

```bash
# Start all services including the application, database, Redis, Prometheus, and Grafana
docker-compose up -d
```

### Option 2: Start Just the Monitoring Services

```bash
# Start only Prometheus, Pushgateway, and Grafana
powershell -ExecutionPolicy Bypass -File scripts/start_monitoring.ps1
```

## Accessing Monitoring Tools

- **Prometheus**: [http://localhost:9090](http://localhost:9090)
- **Pushgateway**: [http://localhost:9091](http://localhost:9091)
- **Grafana**: [http://localhost:3000](http://localhost:3000) (login with admin/admin)

## Testing the Monitoring System

### Generate Test Traffic

To generate test HTTP traffic and see metrics in action:

```bash
# Start the FastAPI application if not already running
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Generate test traffic
powershell -ExecutionPolicy Bypass -File scripts/test_metrics.ps1
```

### Generate Test Metrics

To generate test data for DB connections and active users metrics:

```bash
# Run for 30 iterations with 10 seconds between updates
python scripts/generate_test_metrics.py 30 10
```

## Verifying Metrics Collection

### In Prometheus

1. Go to [http://localhost:9090/targets](http://localhost:9090/targets) to check if all targets are being scraped successfully
2. Try querying some metrics:
   - `http_requests_total`: Total HTTP requests
   - `http_request_duration_seconds_sum`: Sum of request durations
   - `db_connections`: Number of database connections
   - `active_users`: Number of active users

### In Grafana

1. Go to [http://localhost:3000](http://localhost:3000) and log in with admin/admin
2. Navigate to Dashboards to view the Salon Assistant Dashboard
3. You should see graphs and panels showing:
   - Request Rate
   - Average Response Time
   - Requests In Progress
   - Error Rate
   - Database Connections
   - Active Users

## Alerts

The system is configured with the following alerts:

1. **HighErrorRate**: Triggers when the HTTP error rate exceeds 5% for 5 minutes
2. **HighLatency**: Triggers when the average request latency exceeds 2 seconds for 5 minutes
3. **TooManyDBConnections**: Triggers when the number of database connections exceeds 100 for 5 minutes
4. **HighActiveUsers**: Triggers when the number of active users exceeds 1000 for 5 minutes

To view alert rules in Prometheus:
- Go to [http://localhost:9090/alerts](http://localhost:9090/alerts)

## Stopping the Monitoring System

```bash
# Stop all services
docker-compose down

# Or stop only specific services
docker-compose stop prometheus grafana pushgateway
```

## Adding Custom Metrics

To add new metrics to the application:

1. Define new metrics in `app/middleware/metrics.py`
2. Instrument your code to update the metrics
3. Restart the application to expose the new metrics
4. Update dashboards in Grafana to include the new metrics

## Troubleshooting

### Metrics Not Appearing in Prometheus

1. Check if the application is running and the metrics endpoint is accessible: `curl http://localhost:8000/metrics`
2. Verify Prometheus targets: [http://localhost:9090/targets](http://localhost:9090/targets)
3. Check Prometheus logs: `docker-compose logs prometheus`

### Dashboards Not Appearing in Grafana

1. Verify Grafana can connect to Prometheus: Check the data source configuration
2. Check if dashboards are provisioned: Look for any errors in Grafana logs `docker-compose logs grafana`
3. Manually import dashboards if needed: Import `grafana/dashboards/salon_dashboard.json`

### Metrics Middleware Errors

If you encounter errors related to the metrics middleware, such as:
```
AttributeError: 'CORSMiddleware' object has no attribute 'version'
```

This occurs because the middleware stack passes objects between middlewares that may not have all expected attributes. To fix:

1. Check that the most recent version of `app/middleware/metrics.py` is being used
2. Make sure the middleware is added in the correct order in `app/main.py`:
   ```python
   # Setup metrics middleware should be before other middlewares
   setup_metrics(app)
   
   # Add other middlewares after
   app.add_middleware(
       CORSMiddleware,
       # ...other middleware options
   )
   ```
3. Restart the application after making changes

### Pushgateway Connection Errors

If the `generate_test_metrics.py` script fails with connection errors to the Pushgateway:

1. Make sure the Pushgateway container is running: `docker-compose ps pushgateway`
2. Check if the Pushgateway is accessible from your machine: `curl http://localhost:9091`
3. Verify that the correct port is being used: default is 9091

## Restarting Services After Errors

If you encounter issues with any services, it's often helpful to restart them:

```bash
# Restart specific services
docker-compose restart prometheus grafana pushgateway

# Restart the application
# Stop the running uvicorn process (Ctrl+C) and start it again:
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
``` 