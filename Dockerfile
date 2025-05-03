# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_ENV=production \
    PATH="/home/appuser/.local/bin:$PATH"

# Create and set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        postgresql-client \
        netcat-traditional \
        curl \
        gosu \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create user to run the app
RUN adduser --disabled-password --gecos '' appuser \
    && mkdir -p /app/media /app/staticfiles /app/logs \
    && chown -R appuser:appuser /app

# Set up directories
COPY --chown=appuser:appuser . /app/

# Switch to non-root user for pip operations
USER appuser

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Add gunicorn and psycopg2-binary if not in requirements
RUN pip install --no-cache-dir --user gunicorn psycopg2-binary daphne redis channels_redis

# Create wait-for script for container orchestration
USER root
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
host="$1"\n\
shift\n\
port="$1"\n\
shift\n\
cmd="$@"\n\
\n\
until nc -z "$host" "$port"; do\n\
  >&2 echo "Waiting for $host:$port..."\n\
  sleep 1\n\
done\n\
\n\
>&2 echo "$host:$port is available"\n\
exec $cmd' > /usr/local/bin/wait-for \
    && chmod +x /usr/local/bin/wait-for

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Run migrations if needed\n\
if [ "$DJANGO_AUTO_MIGRATE" = "true" ]; then\n\
  echo "Running migrations..."\n\
  gosu appuser python manage.py migrate --noinput\n\
fi\n\
\n\
# Collect static if needed\n\
if [ "$DJANGO_COLLECTSTATIC" = "true" ]; then\n\
  echo "Collecting static files..."\n\
  gosu appuser python manage.py collectstatic --noinput\n\
fi\n\
\n\
# Create superuser if needed (non-interactive)\n\
if [ "$DJANGO_CREATE_SUPERUSER" = "true" ] && [ -n "$DJANGO_SUPERUSER_USERNAME" ] \\\n\
    && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then\n\
  echo "Creating superuser..."\n\
  gosu appuser python manage.py createsuperuser --noinput || true\n\
fi\n\
\n\
# Execute the command as appuser\n\
exec gosu appuser "$@"' > /entrypoint.sh \
    && chmod +x /entrypoint.sh

# Expose port
EXPOSE 8000

# Set the entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "config.wsgi:application"]