# Production Settings Guide

This document provides information about configuring the Social Cube application for production environments.

## Environment Variables

Social Cube uses environment variables for configuration. The following table outlines the available settings:

| Variable | Purpose | Default | Required |
|----------|---------|---------|----------|
| `DJANGO_ENV` | Sets the environment type | `development` | Yes |
| `SECRET_KEY` | Django's secret key for cryptographic signing | None | Yes |
| `DEBUG` | Enable debug mode (should be False in production) | `False` | No |
| `ALLOWED_HOSTS` | List of hosts allowed to serve the application | `localhost,127.0.0.1` | Yes |
| `CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF protection | None | Yes |
| `DATABASE_URL` | Database connection string | None | No* |
| `DB_ENGINE` | Database engine to use | `django.db.backends.postgresql` | No* |
| `DB_NAME` | Database name | `social_cube` | No* |
| `DB_USER` | Database user | `postgres` | No* |
| `DB_PASSWORD` | Database password | None | Yes |
| `DB_HOST` | Database host | `db` | No* |
| `DB_PORT` | Database port | `5432` | No* |
| `REDIS_HOST` | Redis host | `redis` | No |
| `REDIS_PORT` | Redis port | `6379` | No |
| `REDIS_URL` | Redis connection URL | Constructed from host/port | No |
| `EMAIL_BACKEND` | Email backend class | `django.core.mail.backends.smtp.EmailBackend` | No |
| `EMAIL_HOST` | SMTP server host | None | Yes (for email) |
| `EMAIL_PORT` | SMTP server port | `587` | No |
| `EMAIL_USE_TLS` | Use TLS for email | `True` | No |
| `EMAIL_HOST_USER` | SMTP username | None | Yes (for email) |
| `EMAIL_HOST_PASSWORD` | SMTP password | None | Yes (for email) |
| `DEFAULT_FROM_EMAIL` | Default sender address | Same as `EMAIL_HOST_USER` | No |
| `DISCORD_CLIENT_ID` | Discord OAuth2 client ID | None | Yes |
| `DISCORD_CLIENT_SECRET` | Discord OAuth2 client secret | None | Yes |
| `DISCORD_REDIRECT_URI` | Discord OAuth2 redirect URI | None | Yes |
| `SECURE_SSL_REDIRECT` | Redirect HTTP to HTTPS | `True` | No |
| `STATIC_ROOT` | Directory for collected static files | `/app/staticfiles` | No |
| `MEDIA_ROOT` | Directory for user-uploaded files | `/app/media` | No |
| `LOG_LEVEL` | Logging level | `ERROR` | No |
| `LOG_FILE` | Log file path | `/app/logs/django-errors.log` | No |
| `DJANGO_AUTO_MIGRATE` | Run migrations on startup (Docker) | `true` | No |
| `DJANGO_COLLECTSTATIC` | Collect static files on startup (Docker) | `true` | No |
| `DJANGO_CREATE_SUPERUSER` | Create superuser on startup (Docker) | `false` | No |
| `DJANGO_SUPERUSER_USERNAME` | Initial superuser username | None | No |
| `DJANGO_SUPERUSER_EMAIL` | Initial superuser email | None | No |
| `DJANGO_SUPERUSER_PASSWORD` | Initial superuser password | None | No |

\* Either `DATABASE_URL` or the individual database settings (`DB_*`) must be provided.

## Environment File Example

See the `.env.example` file for a template that can be copied to `.env` and customized.

## Docker Environment Configuration

When running with Docker Compose, environment variables can be set in several ways:

1. In the `.env` file (recommended)
2. In the `docker-compose.yml` file under the `environment` key
3. In the `docker-compose.override.yml` file for environment-specific overrides

Example docker-compose.override.yml for production:

```yaml
version: '3.8'

services:
  web:
    environment:
      - DJANGO_ENV=production
      - VIRTUAL_HOST=yourdomain.com
      - LETSENCRYPT_HOST=yourdomain.com
      - LETSENCRYPT_EMAIL=your@email.com
    
  db:
    volumes:
      - ./backups:/backups
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      
  nginx:
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
```

## Security Settings

In production, the following security settings are enabled:

- HTTPS redirection (`SECURE_SSL_REDIRECT=True`)
- HTTP Strict Transport Security (`SECURE_HSTS_*` settings)
- Secure cookies (HTTPS only)
- XSS protection headers
- Content-Type sniffing protection
- X-Frame-Options to prevent clickjacking

## Scaling Considerations

When scaling the application:

1. **Database Connection Pooling**: The production settings include connection pooling with `CONN_MAX_AGE` to maintain persistent connections.

2. **Redis for Caching and Channels**: Redis is configured for both caching and WebSocket channels, with optimized connection settings.

3. **Gunicorn Workers**: The number of Gunicorn workers can be adjusted using the `WEB_CONCURRENCY` environment variable.

4. **Nginx Configuration**: The Nginx configuration includes optimized settings for handling WebSockets and static files.

## Logging and Monitoring

Production settings include comprehensive logging to both console and file, with different log levels for various components:

- Django core (`django`)
- Request handling (`django.request`)
- Security issues (`django.security`)
- Database operations (`django.db.backends`)
- Application-specific modules (`dashboard`, `bot_management`, `api`, `realtime`)

## Health Checks

Docker Compose includes health checks for all services:

- Web: Checks the `/health/` endpoint
- Database: Uses `pg_isready` to verify database availability
- Redis: Uses `redis-cli ping` to check Redis availability
- Nginx: Checks for a successful HTTP response

The `/health/` endpoint provides detailed information about the status of the application and its dependencies.

## Maintenance Tasks

The production environment includes several maintenance tasks:

1. **Database Backups**: Use the `scripts/backup.sh` script to create regular backups.

2. **Log Rotation**: Configure log rotation to prevent logs from growing too large.

3. **Certificate Renewal**: The `certbot` service automatically renews SSL certificates.

4. **Monitoring**: Consider setting up external monitoring for the `/health/` endpoint.