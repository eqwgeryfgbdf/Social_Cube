# Social Cube Deployment Guide

This guide provides detailed instructions for deploying the Social Cube application in both development and production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Database Setup](#database-setup)
6. [Environment Configuration](#environment-configuration)
7. [HTTPS Configuration](#https-configuration)
8. [Deployment Checklist](#deployment-checklist)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying Social Cube, ensure you have the following:

- Python 3.9 or higher
- PostgreSQL 13 or higher (recommended for production)
- Redis (for caching and Celery tasks)
- Node.js and npm (for frontend assets)
- Docker and Docker Compose (for containerized deployment)
- A Discord application with bot token
- Domain name (for production deployment)
- SSL certificate (for production deployment)

## Development Deployment

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/social_cube.git
   cd social_cube
   ```

2. Create and activate a Conda environment:
   ```bash
   conda env create -f environment.yml
   conda activate Discord
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root using `.env.example` as a template:
   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file with your specific configuration values:
   ```
   DEBUG=True
   SECRET_KEY=your_secret_key
   DATABASE_URL=sqlite:///db.sqlite3
   DISCORD_CLIENT_ID=your_discord_client_id
   DISCORD_CLIENT_SECRET=your_discord_client_secret
   DISCORD_BOT_TOKEN=your_discord_bot_token
   DISCORD_REDIRECT_URI=http://localhost:8000/oauth2/callback
   ```

6. Run migrations:
   ```bash
   python manage.py migrate
   ```

7. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

8. Run the development server:
   ```bash
   python manage.py runserver
   ```

9. Access the application at `http://localhost:8000`

### Run Development Scripts

For Windows:
```bash
run_dev.bat
```

For Linux/Mac:
```bash
sh run_dev.sh
```

## Production Deployment

### Server Setup

1. Choose a suitable hosting provider (AWS, DigitalOcean, Heroku, etc.)
2. Provision a server with at least 2GB RAM and 1 CPU core
3. Install system dependencies:
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx redis-server
   ```

4. Set up a PostgreSQL database:
   ```bash
   sudo -u postgres psql
   CREATE DATABASE social_cube;
   CREATE USER social_cube_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE social_cube TO social_cube_user;
   \q
   ```

### Application Deployment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/social_cube.git
   cd social_cube
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file for production settings:
   ```
   DEBUG=False
   SECRET_KEY=your_secure_secret_key
   DATABASE_URL=postgres://social_cube_user:secure_password@localhost:5432/social_cube
   DISCORD_CLIENT_ID=your_discord_client_id
   DISCORD_CLIENT_SECRET=your_discord_client_secret
   DISCORD_BOT_TOKEN=your_discord_bot_token
   DISCORD_REDIRECT_URI=https://yourdomain.com/oauth2/callback
   ALLOWED_HOSTS=yourdomain.com
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Collect static files:
   ```bash
   python manage.py collectstatic --no-input
   ```

7. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

8. Set up Gunicorn as the application server:
   Create a systemd service file `/etc/systemd/system/social_cube.service`:
   ```
   [Unit]
   Description=Social Cube Gunicorn Service
   After=network.target

   [Service]
   User=your_username
   Group=your_username
   WorkingDirectory=/path/to/social_cube
   ExecStart=/path/to/social_cube/venv/bin/gunicorn social_cube.wsgi:application --workers 3 --bind unix:/path/to/social_cube/social_cube.sock
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

9. Enable and start the service:
   ```bash
   sudo systemctl enable social_cube
   sudo systemctl start social_cube
   ```

10. Configure Nginx as a reverse proxy:
    Create a file `/etc/nginx/sites-available/social_cube`:
    ```
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;

        location = /favicon.ico { access_log off; log_not_found off; }
        
        location /static/ {
            root /path/to/social_cube;
        }

        location /media/ {
            root /path/to/social_cube;
        }

        location / {
            include proxy_params;
            proxy_pass http://unix:/path/to/social_cube/social_cube.sock;
        }
    }
    ```

11. Enable the site:
    ```bash
    sudo ln -s /etc/nginx/sites-available/social_cube /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx
    ```

12. Set up SSL with Let's Encrypt:
    ```bash
    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
    ```

## Docker Deployment

### Using Docker Compose

1. Ensure Docker and Docker Compose are installed on your server

2. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/social_cube.git
   cd social_cube
   ```

3. Create a `docker.env` file based on the example:
   ```bash
   cp docker.env.example docker.env
   ```

4. Edit the `docker.env` file with your specific configuration values

5. For production, create `docker-compose.override.yml` for additional configuration:
   ```yaml
   version: '3.8'

   services:
     web:
       restart: always
       environment:
         - DEBUG=False
         - ALLOWED_HOSTS=yourdomain.com
       volumes:
         - ./static:/app/static
         - ./media:/app/media

     nginx:
       volumes:
         - ./ssl:/etc/nginx/ssl
   ```

6. Start the services:
   ```bash
   docker-compose up -d
   ```

7. Run migrations and create superuser:
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

8. Access the application at `https://yourdomain.com`

### Scaling with Docker Swarm

For larger deployments, consider using Docker Swarm:

1. Initialize Docker Swarm:
   ```bash
   docker swarm init
   ```

2. Deploy services with stack:
   ```bash
   docker stack deploy -c docker-compose.yml -c docker-compose.prod.yml social_cube
   ```

3. Scale services as needed:
   ```bash
   docker service scale social_cube_web=3
   ```

## Database Setup

### Backup and Restore

Regularly backup your database:

```bash
# Local backup
python manage.py dumpdata > backup.json

# PostgreSQL backup
pg_dump -U social_cube_user social_cube > social_cube_backup.sql
```

To restore from backup:

```bash
# Local restore
python manage.py loaddata backup.json

# PostgreSQL restore
psql -U social_cube_user social_cube < social_cube_backup.sql
```

### Database Migration

When upgrading to a new version:

```bash
# Make backup before migrating
python manage.py dumpdata > pre_migration_backup.json

# Apply migrations
python manage.py migrate

# If issues occur, you can restore
python manage.py loaddata pre_migration_backup.json
```

## Environment Configuration

### Critical Environment Variables

- `SECRET_KEY`: Django's secret key (use a strong random string)
- `DEBUG`: Set to False in production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DATABASE_URL`: Database connection string
- `DISCORD_CLIENT_ID`: Your Discord application client ID
- `DISCORD_CLIENT_SECRET`: Your Discord application client secret
- `DISCORD_BOT_TOKEN`: Your Discord bot token
- `DISCORD_REDIRECT_URI`: OAuth2 callback URL

### Optional Environment Variables

- `REDIS_URL`: Redis connection string
- `CELERY_BROKER_URL`: Celery broker URL (default: Redis)
- `CELERY_RESULT_BACKEND`: Celery result backend (default: Redis)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `SENTRY_DSN`: Sentry DSN for error tracking

## HTTPS Configuration

### Using Let's Encrypt with Nginx

1. Install Certbot:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   ```

2. Obtain SSL certificate:
   ```bash
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

3. Configure automatic renewal:
   ```bash
   sudo systemctl status certbot.timer
   ```

### Using Self-Signed Certificates (Development Only)

Generate self-signed certificate:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/social_cube.key -out /etc/nginx/ssl/social_cube.crt
```

Configure Nginx:

```
server {
    listen 443 ssl;
    server_name localhost;

    ssl_certificate /etc/nginx/ssl/social_cube.crt;
    ssl_certificate_key /etc/nginx/ssl/social_cube.key;

    # ... rest of configuration
}
```

## Deployment Checklist

Before going live, ensure:

1. ✅ Debug mode is disabled (`DEBUG=False`)
2. ✅ Secret key is secure and not shared
3. ✅ HTTPS is properly configured
4. ✅ Database migrations are applied
5. ✅ Static files are collected
6. ✅ Backups are configured
7. ✅ Discord application settings are correct
8. ✅ Error logging is set up
9. ✅ Required services (Postgres, Redis) are running
10. ✅ User permissions are set correctly

## Troubleshooting

### Common Issues

**Discord Authentication Errors**:
- Verify redirect URI matches exactly in Discord developer portal
- Check client ID and secret are correct
- Ensure proper scopes are enabled

**Static Files Not Loading**:
- Run `collectstatic` command
- Check STATIC_URL and STATIC_ROOT settings
- Verify web server is serving from correct location

**Database Connection Issues**:
- Check database credentials
- Ensure database server is running
- Verify network connectivity

**Application Errors**:
- Check application logs: `/var/log/social_cube/app.log`
- Check Nginx logs: `/var/log/nginx/error.log`
- Check system logs: `journalctl -u social_cube`

### Getting Help

If you encounter issues not covered in this guide:

1. Check the issue tracker on GitHub
2. Join our Discord community for support
3. Review the logs for specific error messages
4. For security issues, email security@yourdomain.com

---

This deployment guide provides the foundational steps for deploying Social Cube. Depending on your specific infrastructure and requirements, additional configuration may be necessary.