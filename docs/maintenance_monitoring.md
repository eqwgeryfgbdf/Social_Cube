# Maintenance and Monitoring Guide

This document provides guidance on maintaining and monitoring the Social Cube application in a production environment.

## Regular Maintenance Tasks

### Database Maintenance

#### 1. Backups

Regular database backups are crucial for data safety. The application includes an automated backup script.

**Automated Backup**:

The `scripts/backup.sh` script creates database backups. Configure it to run as a cron job:

```bash
# Example cron job for daily backups at 2:00 AM
0 2 * * * cd /path/to/social_cube && ./scripts/backup.sh
```

**Manual Backup**:

```bash
# Run from the project root
docker-compose exec db pg_dump -U postgres social_cube > backups/manual_backup_$(date +'%Y%m%d_%H%M%S').sql
```

#### 2. Database Vacuum

PostgreSQL needs regular vacuum operations to maintain performance:

```bash
# Run from the project root
docker-compose exec db psql -U postgres -d social_cube -c "VACUUM ANALYZE;"
```

Configure as a weekly cron job:

```bash
# Example cron job for weekly vacuum at 3:00 AM on Sundays
0 3 * * 0 docker-compose exec db psql -U postgres -d social_cube -c "VACUUM ANALYZE;"
```

#### 3. Index Maintenance

Periodically rebuild indexes to optimize performance:

```bash
# Run from the project root
docker-compose exec db psql -U postgres -d social_cube -c "REINDEX DATABASE social_cube;"
```

### Log Management

#### 1. Log Rotation

Configure log rotation to prevent logs from growing too large:

```bash
# Example logrotate configuration (/etc/logrotate.d/social_cube)
/path/to/social_cube/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        docker-compose restart web
    endscript
}
```

#### 2. Log Analysis

Periodically review logs for errors and issues:

```bash
# View recent errors in application logs
docker-compose exec web cat /app/logs/django-errors.log | tail -n 100

# View error logs from the database
docker-compose exec web python manage.py shell -c "from logging_system.models import ErrorLog; print('\n'.join([f'{log.timestamp} - {log.level}: {log.message}' for log in ErrorLog.objects.order_by('-timestamp')[:20]]))"
```

### SSL Certificate Maintenance

SSL certificates from Let's Encrypt are automatically renewed by Certbot. Monitor the renewal process:

```bash
# Check Certbot logs
docker-compose logs certbot

# Manually trigger certificate renewal
docker-compose run --rm certbot renew
```

### Docker Maintenance

#### 1. Image Updates

Regularly update Docker images to get security updates:

```bash
# Pull latest base images
docker-compose pull

# Rebuild application image
docker-compose build

# Restart services with new images
docker-compose down
docker-compose up -d
```

#### 2. Volume Cleanup

Clean up unused Docker volumes to free up disk space:

```bash
# Remove unused volumes
docker volume prune -f
```

#### 3. Container Health Checks

Monitor container health:

```bash
# Check container health
docker-compose ps

# View detailed health status
docker inspect --format "{{.Name}} - {{.State.Health.Status}}" $(docker-compose ps -q)
```

### Application Maintenance

#### 1. Django Migrations

Apply database migrations when updating the application:

```bash
# Run migrations
docker-compose exec web python manage.py migrate
```

#### 2. Static Files

Collect static files when updating the application:

```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

#### 3. Data Cleanup

Periodically clean up old data:

```bash
# Remove old command logs (older than 30 days)
docker-compose exec web python manage.py shell -c "from bot_management.models import CommandLog; from datetime import timedelta; from django.utils import timezone; CommandLog.objects.filter(timestamp__lt=timezone.now() - timedelta(days=30)).delete()"

# Remove old request logs (older than 7 days)
docker-compose exec web python manage.py shell -c "from logging_system.models import RequestLog; from datetime import timedelta; from django.utils import timezone; RequestLog.objects.filter(timestamp__lt=timezone.now() - timedelta(days=7)).delete()"
```

## Monitoring

### Health Checks

The application includes a health check endpoint at `/health/` that provides detailed status information.

**Monitoring Setup**:

Configure an external monitoring service to check the health endpoint regularly:

```
https://yourdomain.com/health/
```

**Expected Response** (Healthy):

```json
{
  "status": "ok",
  "components": {
    "database": true,
    "redis": true,
    "application": true
  },
  "errors": []
}
```

**Error Response**:

```json
{
  "status": "error",
  "components": {
    "database": false,
    "redis": true,
    "application": true
  },
  "errors": ["Database connection error: connection refused"]
}
```

### Performance Monitoring

#### 1. Application Performance

Monitor application performance metrics:

**Request Duration**:

```bash
# View average request duration by endpoint
docker-compose exec web python manage.py shell -c "from django.db import connection; from logging_system.models import RequestLog; print('Average request duration by endpoint:'); cursor = connection.cursor(); cursor.execute('SELECT path, AVG(duration), COUNT(*) FROM logging_system_requestlog GROUP BY path ORDER BY AVG(duration) DESC LIMIT 10'); for row in cursor.fetchall(): print(f'{row[0]} - {row[1]:.4f}s ({row[2]} requests)')"
```

**Error Rate**:

```bash
# View error rate by endpoint
docker-compose exec web python manage.py shell -c "from django.db import connection; from logging_system.models import RequestLog; print('Error rate by endpoint:'); cursor = connection.cursor(); cursor.execute('SELECT path, COUNT(*) AS total, SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS errors, (SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END)::float / COUNT(*)) * 100 AS error_rate FROM logging_system_requestlog GROUP BY path ORDER BY error_rate DESC LIMIT 10'); for row in cursor.fetchall(): print(f'{row[0]} - {row[3]:.2f}% errors ({row[2]} errors out of {row[1]} requests)')"
```

#### 2. Database Performance

Monitor database performance:

```bash
# View slow queries
docker-compose exec db psql -U postgres -d social_cube -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Reset query statistics
docker-compose exec db psql -U postgres -d social_cube -c "SELECT pg_stat_statements_reset();"
```

#### 3. Resource Usage

Monitor resource usage:

```bash
# View container resource usage
docker stats $(docker-compose ps -q)
```

### Logs Monitoring

#### 1. Real-time Log Monitoring

Monitor logs in real-time:

```bash
# View logs from all services
docker-compose logs -f

# View logs from a specific service
docker-compose logs -f web
```

#### 2. Log Analytics

Set up log analytics for better insights:

1. Configure the logging system to send logs to an external log analytics service (like ELK stack, Graylog, etc.)
2. Create dashboards for visualizing log data
3. Set up alerts for critical errors

### Bot Status Monitoring

Monitor the status of Discord bots:

```bash
# View bot status
docker-compose exec web python manage.py shell -c "from bot_management.models import Bot; print('\n'.join([f'{bot.name} - {bot.status} (Last active: {bot.last_active})' for bot in Bot.objects.all()]))"
```

The dashboard also provides real-time status monitoring for bots through the WebSocket connection.

## Alerting

### Email Alerts

The application can be configured to send email alerts for critical errors:

1. Configure email settings in the `.env` file
2. Set `ADMINS` in the Django settings to receive error emails

### External Alerting

Configure external alerting services:

1. Set up integration with incident management platforms (like PagerDuty, OpsGenie, etc.)
2. Configure alerts based on health check responses
3. Set up alerts for resource usage thresholds (CPU, memory, disk space)

## Disaster Recovery

### Database Recovery

In case of database corruption or loss:

1. Stop the application:
   ```bash
   docker-compose down
   ```

2. Restore from backup:
   ```bash
   # Create a temporary container for restoration
   docker run --rm -v $(pwd)/backups:/backups -v social_cube_postgres_data:/var/lib/postgresql/data postgres:14-alpine bash -c "pg_restore -U postgres -d social_cube /backups/backup_file.sql"
   ```

3. Start the application:
   ```bash
   docker-compose up -d
   ```

### Application Recovery

In case of application failure:

1. Check logs for errors:
   ```bash
   docker-compose logs web
   ```

2. Restart the application:
   ```bash
   docker-compose restart web
   ```

3. If issues persist, roll back to a known-good version:
   ```bash
   git checkout <previous-version>
   docker-compose build
   docker-compose down
   docker-compose up -d
   ```

## Performance Tuning

### Gunicorn Configuration

Optimize Gunicorn settings for better performance:

```bash
# Update the command in docker-compose.yml
command: gunicorn --bind 0.0.0.0:8000 --workers 4 --threads 2 --worker-class=gthread --worker-tmp-dir /dev/shm --timeout 120 config.wsgi:application
```

### Nginx Configuration

Optimize Nginx settings for better performance:

```nginx
# Update the Nginx configuration in nginx/default.conf
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    multi_accept on;
    use epoll;
}

http {
    # ... other settings ...
    
    keepalive_timeout 65;
    keepalive_requests 100;
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    
    gzip on;
    gzip_comp_level 5;
    gzip_min_length 256;
    gzip_proxied any;
    gzip_types
        application/javascript
        application/json
        application/xml
        text/css
        text/plain
        text/xml;
    
    # ... server block ...
}
```

### Database Tuning

Optimize PostgreSQL settings for better performance:

```bash
# Update PostgreSQL configuration
docker-compose exec db bash -c "echo 'shared_buffers = 1GB' >> /var/lib/postgresql/data/postgresql.conf"
docker-compose exec db bash -c "echo 'effective_cache_size = 3GB' >> /var/lib/postgresql/data/postgresql.conf"
docker-compose exec db bash -c "echo 'work_mem = 16MB' >> /var/lib/postgresql/data/postgresql.conf"
docker-compose exec db bash -c "echo 'maintenance_work_mem = 256MB' >> /var/lib/postgresql/data/postgresql.conf"
docker-compose exec db bash -c "echo 'random_page_cost = 1.1' >> /var/lib/postgresql/data/postgresql.conf"
docker-compose exec db bash -c "echo 'effective_io_concurrency = 200' >> /var/lib/postgresql/data/postgresql.conf"
docker-compose exec db bash -c "echo 'max_worker_processes = 4' >> /var/lib/postgresql/data/postgresql.conf"
docker-compose exec db bash -c "echo 'max_parallel_workers_per_gather = 2' >> /var/lib/postgresql/data/postgresql.conf"
docker-compose exec db bash -c "echo 'max_parallel_workers = 4' >> /var/lib/postgresql/data/postgresql.conf"

# Restart PostgreSQL to apply changes
docker-compose restart db
```

## Scaling

### Horizontal Scaling

For higher load, scale the web service horizontally:

```bash
# Scale the web service to 3 instances
docker-compose up -d --scale web=3
```

Update the Nginx configuration to load balance across instances.

### Vertical Scaling

Increase resources for Docker containers:

```bash
# Update resource limits in docker-compose.override.yml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
  db:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

## Security Maintenance

### Dependency Updates

Regularly update dependencies for security patches:

```bash
# Update Python dependencies
pip install --upgrade -r requirements.txt
```

### Security Scans

Run security scans periodically:

```bash
# Scan Docker images for vulnerabilities
docker scan social_cube_web
```

### Audit Logs Review

Regularly review audit logs for suspicious activity:

```bash
# View recent audit logs
docker-compose exec web python manage.py shell -c "from logging_system.models import AuditLog; print('\n'.join([f'{log.timestamp} - {log.user_id} - {log.action} - {log.entity_type}:{log.entity_id} - {log.description}' for log in AuditLog.objects.order_by('-timestamp')[:20]]))"
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

If the web service cannot connect to the database:

```bash
# Check database logs
docker-compose logs db

# Verify PostgreSQL is running
docker-compose exec db pg_isready -U postgres

# Restart the database
docker-compose restart db

# Restart the web service
docker-compose restart web
```

#### 2. Redis Connection Issues

If the web service cannot connect to Redis:

```bash
# Check Redis logs
docker-compose logs redis

# Verify Redis is running
docker-compose exec redis redis-cli ping

# Restart Redis
docker-compose restart redis

# Restart the web service
docker-compose restart web
```

#### 3. Static Files Not Loading

If static files are not loading correctly:

```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check Nginx configuration
docker-compose exec nginx nginx -t

# Restart Nginx
docker-compose restart nginx
```

#### 4. Bot Connection Issues

If bots are not connecting to Discord:

```bash
# Check bot logs
docker-compose logs web | grep "bot_manager"

# Restart bots
docker-compose exec web python manage.py shell -c "from bot_management.discord_bot.service import bot_manager; bot_manager.restart_all_bots()"
```

### Diagnostic Commands

#### 1. System Status

```bash
# View system status
docker-compose ps

# View container logs
docker-compose logs

# View container resource usage
docker stats $(docker-compose ps -q)
```

#### 2. Database Diagnostics

```bash
# Check database connections
docker-compose exec db psql -U postgres -c "SELECT datname, numbackends FROM pg_stat_database;"

# Check database size
docker-compose exec db psql -U postgres -c "SELECT pg_database_size('social_cube')/1024/1024 as size_mb;"

# Check table sizes
docker-compose exec db psql -U postgres -d social_cube -c "SELECT table_name, pg_total_relation_size(table_name::text)/1024/1024 as size_mb FROM information_schema.tables WHERE table_schema = 'public' ORDER BY size_mb DESC LIMIT 10;"
```

#### 3. Application Diagnostics

```bash
# Check Django settings
docker-compose exec web python manage.py shell -c "from django.conf import settings; print(f'Debug: {settings.DEBUG}'); print(f'Database: {settings.DATABASES}'); print(f'Static Root: {settings.STATIC_ROOT}')"

# Run Django checks
docker-compose exec web python manage.py check

# Test database connection
docker-compose exec web python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1'); print(cursor.fetchone())"
```

## Maintenance Checklist

### Daily Tasks

- [ ] Check container health (`docker-compose ps`)
- [ ] Review error logs
- [ ] Verify backups are running
- [ ] Check disk space usage

### Weekly Tasks

- [ ] Review performance metrics
- [ ] Run database VACUUM ANALYZE
- [ ] Check for dependency updates
- [ ] Review audit logs for suspicious activity

### Monthly Tasks

- [ ] Rebuild indexes
- [ ] Clean up old logs and data
- [ ] Update Docker images
- [ ] Run security scans
- [ ] Test disaster recovery procedures

### Quarterly Tasks

- [ ] Review and update monitoring and alerting configurations
- [ ] Performance tuning
- [ ] Update documentation
- [ ] Test scaling procedures