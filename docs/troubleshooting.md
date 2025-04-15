# Troubleshooting Guide

This guide provides solutions for common issues you might encounter while setting up, deploying, or using the Salon Assistant application.

## Table of Contents
1. [Installation Issues](#installation-issues)
2. [Database Problems](#database-problems)
3. [API and Backend Issues](#api-and-backend-issues)
4. [Notification System Issues](#notification-system-issues)
5. [Docker and Deployment Issues](#docker-and-deployment-issues)
6. [Performance Problems](#performance-problems)
7. [Authentication and Security Issues](#authentication-and-security-issues)
8. [Common Error Messages](#common-error-messages)

## Installation Issues

### Python Environment Problems

**Issue**: Errors when installing dependencies or running the application.

**Solutions**:
1. Ensure you're using Python 3.8 or higher:
   ```bash
   python --version
   ```

2. Check if your virtual environment is activated:
   ```bash
   # On Linux/Mac
   source .venv/bin/activate
   
   # On Windows
   .venv\Scripts\activate
   ```

3. Update pip:
   ```bash
   pip install --upgrade pip
   ```

4. Install dependencies with verbose output:
   ```bash
   pip install -r requirements.txt -v
   ```

### Missing Environment Variables

**Issue**: Application fails with reference to missing environment variables.

**Solutions**:
1. Check if your `.env` file exists and contains all required variables.
2. Copy the example file and customize:
   ```bash
   cp .env.example .env
   ```
3. Verify environment variables are loaded correctly:
   ```bash
   python -c "from app.core.config import settings; print('SECRET_KEY exists:', bool(settings.SECRET_KEY))"
   ```

## Database Problems

### Connection Issues

**Issue**: Cannot connect to the database.

**Solutions**:
1. Verify database service is running:
   ```bash
   # For Docker deployment
   docker-compose ps db
   
   # For direct installation
   systemctl status postgresql
   ```

2. Check database connection string:
   ```bash
   # Test connection using psql
   psql "postgresql://user:password@host:port/dbname"
   ```

3. Check network connectivity:
   ```bash
   # For Docker
   docker-compose exec web ping db
   ```

### Migration Errors

**Issue**: Alembic migration fails.

**Solutions**:
1. Check migration history:
   ```bash
   alembic history
   ```

2. Verify database schema is consistent:
   ```bash
   alembic check
   ```

3. For critical issues, reset migrations:
   ```bash
   # Only as a last resort!
   alembic downgrade base
   alembic upgrade head
   ```

### Data Integrity Issues

**Issue**: Inconsistent or missing data.

**Solutions**:
1. Check database constraints:
   ```sql
   -- In PostgreSQL
   SELECT conname, contype, pg_get_constraintdef(oid)
   FROM pg_constraint
   WHERE conrelid = 'table_name'::regclass;
   ```

2. Restore from backup if necessary:
   ```bash
   # For Docker deployment
   docker-compose exec -T db pg_restore -U postgres -d salon_assistant < backup_file.dump
   ```

## API and Backend Issues

### API Returns Errors

**Issue**: API endpoints return unexpected errors.

**Solutions**:
1. Check API logs:
   ```bash
   # For Docker deployment
   docker-compose logs -f web
   ```

2. Verify request format:
   ```bash
   # Use curl to test endpoint with verbose option
   curl -v http://localhost:8000/api/v1/health
   ```

3. Check for rate limiting or authentication issues:
   ```bash
   # Add authorization header
   curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/protected-endpoint
   ```

### Service Unavailable

**Issue**: The application is unreachable or returns 503 errors.

**Solutions**:
1. Check if all services are running:
   ```bash
   docker-compose ps
   ```

2. Verify Nginx configuration:
   ```bash
   nginx -t
   ```

3. Check resource usage:
   ```bash
   docker stats
   ```

## Notification System Issues

### SMS or Email Not Sending

**Issue**: Notifications are not being sent to clients.

**Solutions**:
1. Verify external service credentials (Twilio, SMTP):
   ```bash
   # Test Twilio credentials
   python -c "from twilio.rest import Client; client = Client('YOUR_ACCOUNT_SID', 'YOUR_AUTH_TOKEN'); print(client.api.account.get().sid)"
   ```

2. Check notification service logs:
   ```bash
   grep "notification" logs/app.log
   ```

3. Verify client contact information is correct:
   ```sql
   -- In PostgreSQL
   SELECT email, phone FROM clients WHERE id = X;
   ```

4. Check notification preferences:
   ```sql
   -- In PostgreSQL
   SELECT * FROM notification_preferences WHERE client_id = X;
   ```

### Scheduled Reminders Not Working

**Issue**: Automatic reminders are not being sent.

**Solutions**:
1. Check scheduler status:
   ```bash
   # For Docker deployment
   docker-compose logs -f scheduler
   ```

2. Verify cron jobs are running:
   ```bash
   crontab -l
   ```

3. Manually trigger reminder processing:
   ```bash
   python -m app.tasks.process_reminders
   ```

## Docker and Deployment Issues

### Container Fails to Start

**Issue**: Docker containers exit immediately after starting.

**Solutions**:
1. Check container logs:
   ```bash
   docker-compose logs web
   ```

2. Verify environment variables:
   ```bash
   docker-compose config
   ```

3. Check for port conflicts:
   ```bash
   netstat -tulpn | grep 8000
   ```

### Volume Permissions

**Issue**: Permission denied when accessing volumes.

**Solutions**:
1. Check volume ownership:
   ```bash
   ls -la ./volumes
   ```

2. Fix permissions:
   ```bash
   sudo chown -R 1000:1000 ./volumes
   ```

3. Use Docker user mapping:
   ```bash
   # Add to docker-compose.yml
   user: "$(id -u):$(id -g)"
   ```

## Performance Problems

### Slow Response Times

**Issue**: API responses are slow.

**Solutions**:
1. Enable query logging to identify slow queries:
   ```python
   # In app/db/session.py
   engine = create_engine(
       DATABASE_URL, 
       echo=True, 
       echo_pool=True,
       pool_pre_ping=True
   )
   ```

2. Check resource usage:
   ```bash
   htop
   ```

3. Optimize database queries:
   - Add appropriate indexes
   - Review JOIN operations
   - Implement caching

### Memory Leaks

**Issue**: Application memory usage grows over time.

**Solutions**:
1. Monitor memory usage:
   ```bash
   docker stats
   ```

2. Check database connection pooling:
   ```python
   # Verify connection pooling settings in app/db/session.py
   engine = create_engine(
       DATABASE_URL,
       pool_size=5,  # Adjust as needed
       max_overflow=10,
       pool_recycle=3600,
   )
   ```

3. Restart services periodically if needed:
   ```bash
   # Add to crontab
   0 4 * * * docker-compose restart web
   ```

## Authentication and Security Issues

### Token Validation Problems

**Issue**: JWT tokens are not being validated correctly.

**Solutions**:
1. Check JWT secret and algorithm configuration:
   ```bash
   # Verify secret is properly set
   grep -r "SECRET_KEY" .env*
   ```

2. Verify token expiration:
   ```python
   # Debug token expiration
   import jwt
   token = "YOUR_TOKEN"
   decoded = jwt.decode(token, verify=False)
   import datetime
   print("Expires at:", datetime.datetime.fromtimestamp(decoded["exp"]))
   ```

3. Check for clock skew between servers.

### Unauthorized Access Attempts

**Issue**: Suspicious login attempts or API access.

**Solutions**:
1. Check authentication logs:
   ```bash
   grep "auth" logs/app.log
   ```

2. Implement or verify rate limiting:
   ```python
   # In app/api/deps.py
   from fastapi import Depends, HTTPException, status
   from slowapi import Limiter
   
   limiter = Limiter(key_func=get_remote_address)
   
   @app.get("/api/endpoint")
   @limiter.limit("5/minute")
   async def endpoint():
       return {"message": "Rate limited endpoint"}
   ```

3. Check for brute force protection.

## Common Error Messages

### "ImportError: No module named X"

**Cause**: Missing Python dependency or incorrect Python path.

**Solution**:
1. Install missing dependency:
   ```bash
   pip install X
   ```
2. Check your Python path:
   ```bash
   python -c "import sys; print(sys.path)"
   ```

### "psycopg2.OperationalError: could not connect to server"

**Cause**: PostgreSQL connection issue.

**Solution**:
1. Check if PostgreSQL is running:
   ```bash
   systemctl status postgresql
   ```
2. Verify connection parameters:
   ```bash
   psql -h localhost -U username -d database_name
   ```

### "ValueError: Invalid JWT token"

**Cause**: Token is expired, malformed, or signature is invalid.

**Solution**:
1. Check if token is expired
2. Verify secret key matches between token generation and validation
3. Check algorithm type (HS256, RS256, etc.)

### "redis.exceptions.ConnectionError: Error X connecting to localhost:6379"

**Cause**: Cannot connect to Redis server.

**Solution**:
1. Verify Redis is running:
   ```bash
   systemctl status redis
   ```
2. Check Redis connection parameters:
   ```bash
   redis-cli ping
   ```

### "RuntimeError: SQLite object created in a different thread"

**Cause**: SQLite database access from multiple threads.

**Solution**:
1. Use `check_same_thread=False` in SQLite connection:
   ```python
   engine = create_engine(
       "sqlite:///./app.db", 
       connect_args={"check_same_thread": False}
   )
   ```
2. Better solution: Use PostgreSQL for multi-threaded environments

---

If you encounter an issue not covered in this guide, please submit it to our issue tracker for assistance. 