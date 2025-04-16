# Salon Assistant Monitoring Guide

This guide provides detailed information about monitoring the Salon Assistant application, including available metrics, alerts, and visualization dashboards.

## Monitoring Architecture

The monitoring stack consists of:

- **Prometheus**: For collecting and storing metrics
- **Grafana**: For visualizing metrics and setting up dashboards
- **Application Metrics**: Custom metrics exposed by the application

## Available Metrics

The application exposes the following metrics at the `/metrics` endpoint:

### HTTP Metrics

- `http_requests_total`: Total number of HTTP requests (labeled by method, endpoint, status_code)
- `http_request_duration_seconds`: HTTP request duration in seconds (labeled by method, endpoint)
- `http_requests_in_progress`: Number of HTTP requests currently in progress (labeled by method, endpoint)
- `http_errors_total`: Total number of HTTP errors (labeled by method, endpoint, status_code)

### Application Metrics

- `db_connections`: Number of active database connections
- `active_users`: Number of active users on the platform

## Prometheus Configuration

Prometheus is configured to scrape metrics from:

- The application (`app:8000/metrics`)
- Prometheus itself (`prometheus:9090`)
- Host metrics (if node_exporter is installed)

### Alert Rules

The following alert rules are configured in Prometheus:

1. **HighErrorRate**: Triggers when the HTTP error rate exceeds 5% for 5 minutes
2. **HighLatency**: Triggers when the average request latency exceeds 2 seconds for 5 minutes
3. **TooManyDBConnections**: Triggers when the number of database connections exceeds 100 for 5 minutes
4. **HighActiveUsers**: Triggers when the number of active users exceeds 1000 for 5 minutes

## Grafana Dashboards

The following dashboards are available in Grafana:

### Main Dashboard

The main "Salon Assistant Dashboard" includes the following panels:

- **Request Rate**: Shows the rate of HTTP requests by method and endpoint
- **Average Response Time**: Shows the average response time of HTTP requests
- **Requests In Progress**: Shows the number of HTTP requests currently in progress
- **Error Rate**: Shows the rate of HTTP errors
- **Database Connections**: Shows the number of active database connections
- **Active Users**: Shows the number of active users on the platform

## Setting Up Monitoring

### Prerequisites

- Docker and Docker Compose installed
- The application configured to expose metrics (included in the default configuration)

### Steps

1. Ensure the Prometheus and Grafana services are included in your docker-compose.yml file
2. Configure Prometheus to scrape your application's metrics (included in the default configuration)
3. Start the services:
   ```bash
   docker-compose up -d prometheus grafana
   ```
4. Access Grafana at http://localhost:3000 (default credentials: admin/admin)
5. The Salon Assistant Dashboard should be automatically provisioned

## Monitoring Best Practices

1. **Regular Dashboard Review**: Check the dashboards daily for anomalies or performance issues
2. **Alert Thresholds**: Adjust alert thresholds based on your application's normal behavior
3. **Metric Retention**: Configure appropriate retention periods for metrics (default: 15 days)
4. **Dashboard Updates**: Update dashboards as new features are added to the application

## Troubleshooting Monitoring Issues

### Prometheus Not Scraping Metrics

Check the following:
1. The application is exposing metrics at the `/metrics` endpoint
2. Prometheus can reach the application (check network configuration)
3. Prometheus configuration is correct (check `prometheus.yml`)

### Grafana Not Showing Metrics

Check the following:
1. Grafana can connect to Prometheus (check datasource configuration)
2. The dashboard is properly configured
3. Prometheus has collected data for the requested time range

### Alert Not Firing

Check the following:
1. The alert rule is correctly defined
2. The alert condition is actually met (check the expression in Prometheus)
3. Alertmanager is properly configured (if using)

## Extending Monitoring

To add new metrics to the application:

1. Define new metrics in `app/middleware/metrics.py`
2. Instrument your code to update the metrics
3. Restart the application to expose the new metrics
4. Update dashboards in Grafana to include the new metrics

## Reference

- [Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)
- [Grafana Documentation](https://grafana.com/docs/)
- [FastAPI Monitoring Guide](https://fastapi.tiangolo.com/advanced/monitoring/) 