# Social Cube Deployment Guide

This document provides instructions for deploying Social Cube in a production environment using Docker.

## Prerequisites

- A server with Docker and Docker Compose installed
- Domain name pointed to your server
- Basic knowledge of Docker and Linux commands

## Deployment Steps

### 1. Clone the Repository

```bash
git clone <repository_url>
cd Social_Cube
```

### 2. Configure Environment Variables

1. Create a `.env` file for your environment variables:

```bash
cp docker.env.example .env
```

2. Edit the `.env` file and update:
   - `SECRET_KEY`: Generate a secure random string
   - `ALLOWED_HOSTS`: Add your domain name
   - `CSRF_TRUSTED_ORIGINS`: Add your domain with https:// prefix
   - `DB_PASSWORD`: Set a secure database password
   - Discord credentials and other API keys
   - Email settings
   - Initial superuser credentials

### 3. Basic Deployment (HTTP)

```bash
# Start all services
docker-compose up -d

# Check if services are running
docker-compose ps
```

### 4. Deployment with SSL (HTTPS)

1. Run the SSL setup script:

```bash
chmod +x scripts/setup_ssl.sh
./scripts/setup_ssl.sh yourdomain.com your@email.com
```

2. Follow the instructions printed by the script to obtain SSL certificates.

3. After certificates are generated, restart the services:

```bash
docker-compose down
docker-compose up -d
```

### 5. Database Backups

Backup the database:

```bash
docker-compose exec db pg_dump -U postgres social_cube > backups/social_cube_$(date +'%Y%m%d').sql
```

Restore from backup:

```bash
cat backups/social_cube_YYYYMMDD.sql | docker-compose exec -T db psql -U postgres social_cube
```

### 6. Maintenance

#### Updates

To update the application:

```bash
git pull
docker-compose build
docker-compose down
docker-compose up -d
```

#### Logs

View logs:

```bash
docker-compose logs -f web  # Web application logs
docker-compose logs -f asgi  # WebSocket logs
docker-compose logs -f nginx  # Nginx logs
docker-compose logs -f db  # Database logs
```

#### Monitoring

Check the health of services:

```bash
docker-compose ps
```

Visit the health check endpoint: `https://yourdomain.com/health/`

### 7. Scaling

To scale the web service:

```bash
docker-compose up -d --scale web=3
```

Note: When scaling, ensure your Nginx configuration is updated to balance load across instances.

## Troubleshooting

### Database Connection Issues

If the web service cannot connect to the database:

```bash
docker-compose logs db  # Check database logs
docker-compose restart db  # Restart the database
docker-compose restart web  # Restart the web service
```

### SSL Certificate Issues

If SSL certificates are not working:

```bash
docker-compose logs certbot  # Check Certbot logs
```

Manually renew certificates:

```bash
docker-compose run --rm certbot renew
```

### Static Files Not Loading

Check Nginx configuration and ensure volumes are mounted correctly:

```bash
docker-compose exec web python manage.py collectstatic --noinput
docker-compose restart nginx
```

## Security Considerations

- Regularly update the Docker images and dependencies
- Keep your `.env` file secure and never commit it to version control
- Set up regular database backups
- Configure firewall rules to only expose necessary ports (80 and 443)
- Use strong passwords for database and admin users
- Consider setting up monitoring and alerting