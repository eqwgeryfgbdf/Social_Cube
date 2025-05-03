#!/bin/bash
# Backup script for Social Cube production environment
# This script creates backups of the database and important files

# Configuration
BACKUP_DIR="./backups"
DATE=$(date +"%Y%m%d_%H%M%S")
DB_BACKUP="$BACKUP_DIR/db_backup_$DATE.sql"
MEDIA_BACKUP="$BACKUP_DIR/media_backup_$DATE.tar.gz"
RETENTION_DAYS=7

# Ensure backup directory exists
mkdir -p $BACKUP_DIR

echo "Starting backup process at $(date)"

# Backup PostgreSQL database
echo "Creating database backup..."
docker-compose exec -T db pg_dump -U ${DB_USER:-postgres} ${DB_NAME:-social_cube} > $DB_BACKUP
if [ $? -eq 0 ]; then
    echo "Database backup created: $DB_BACKUP"
    gzip $DB_BACKUP
else
    echo "Error creating database backup"
    exit 1
fi

# Backup media files
echo "Creating media files backup..."
docker-compose exec -T web tar -czf - -C /app media > $MEDIA_BACKUP
if [ $? -eq 0 ]; then
    echo "Media backup created: $MEDIA_BACKUP"
else
    echo "Error creating media backup"
    exit 1
fi

# Optional: Backup static files if needed
# docker-compose exec -T web tar -czf - -C /app staticfiles > "$BACKUP_DIR/static_backup_$DATE.tar.gz"

# Clean up old backups
echo "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find $BACKUP_DIR -name "db_backup_*.gz" -type f -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "media_backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete

echo "Backup completed at $(date)"

# Optional: Copy backups to remote location
# rsync -avz $BACKUP_DIR/ user@remote-server:/path/to/backup/storage/