# Backup and Restore Guide

This guide provides detailed instructions for backing up and restoring the Social Cube application data and configuration.

## What to Backup

The Social Cube application has several components that need to be backed up:

1. **Database**: Contains all application data (users, bots, guilds, logs, etc.)
2. **Media Files**: User-uploaded files (images, etc.)
3. **Environment Configuration**: Environment variables and settings
4. **Custom Configuration Files**: Any customized configuration files (Nginx, etc.)

## Automated Backup

Social Cube includes an automated backup script that handles the most critical components.

### Using the Backup Script

The `scripts/backup.sh` script creates backups of the database and media files:

```bash
# Run from the project root
./scripts/backup.sh
```

This script creates timestamped backups in the `backups` directory:
- Database backups: `backups/db_backup_YYYYMMDD_HHMMSS.sql.gz`
- Media backups: `backups/media_backup_YYYYMMDD_HHMMSS.tar.gz`

### Setting Up Scheduled Backups

To run backups automatically, set up a cron job:

```bash
# Example: Run backup daily at 2:00 AM
0 2 * * * cd /path/to/social_cube && ./scripts/backup.sh
```

On a Docker Compose setup, you can use the backup service defined in the `docker-compose.override.example.yml` file:

```yaml
backup:
  image: alpine:latest
  volumes:
    - ./scripts:/scripts
    - ./backups:/backups
    - postgres_data:/var/lib/postgresql/data:ro
    - media_volume:/app/media:ro
  depends_on:
    - db
  environment:
    - DB_USER=${DB_USER:-postgres}
    - DB_NAME=${DB_NAME:-social_cube}
    - BACKUP_RETENTION_DAYS=7
  entrypoint: >
    /bin/sh -c "apk add --no-cache postgresql-client &&
                chmod +x /scripts/backup.sh &&
                while :; do /scripts/backup.sh; sleep 24h; done"
  restart: unless-stopped
```

## Manual Backup

In addition to the automated backup script, you can perform manual backups of each component.

### Database Backup

```bash
# With Docker Compose
docker-compose exec db pg_dump -U postgres social_cube > backups/manual_db_backup_$(date +'%Y%m%d_%H%M%S').sql

# Compress the backup
gzip backups/manual_db_backup_*.sql

# Without Docker Compose
pg_dump -U postgres -h localhost -p 5432 social_cube > backups/manual_db_backup_$(date +'%Y%m%d_%H%M%S').sql
```

For a more complete backup including roles and permissions:

```bash
docker-compose exec db pg_dumpall -U postgres > backups/full_db_backup_$(date +'%Y%m%d_%H%M%S').sql
```

### Media Files Backup

```bash
# With Docker Compose
docker-compose exec web tar -czf - -C /app media > backups/manual_media_backup_$(date +'%Y%m%d_%H%M%S').tar.gz

# Without Docker Compose
tar -czf backups/manual_media_backup_$(date +'%Y%m%d_%H%M%S').tar.gz -C /path/to/social_cube media
```

### Environment Configuration Backup

```bash
# Simple copy
cp .env backups/env_backup_$(date +'%Y%m%d_%H%M%S')
```

### Configuration Files Backup

```bash
# Create a tar archive of configuration files
tar -czf backups/config_backup_$(date +'%Y%m%d_%H%M%S').tar.gz nginx/ docker-compose.yml docker-compose.override.yml
```

### Full Application Backup

For a complete backup of the application, including code and configuration:

```bash
# Create a tar archive of the entire application
tar -czf backups/full_app_backup_$(date +'%Y%m%d_%H%M%S').tar.gz --exclude='backups/*.tar.gz' --exclude='backups/*.sql' --exclude='backups/*.sql.gz' --exclude='.git' .
```

## Backup Storage Recommendations

1. **Local Storage**: Keep backups on the local system for quick recovery
2. **Off-site Storage**: Copy backups to a remote location for disaster recovery
3. **Multiple Backup Sets**: Maintain multiple backup sets with different retention periods
4. **Encryption**: Encrypt sensitive backups, especially those stored off-site

### Setting Up Off-site Backup Storage

Example script to copy backups to an S3 bucket:

```bash
#!/bin/bash
# s3_backup.sh - Upload backups to S3

# Configuration
S3_BUCKET="your-backup-bucket"
BACKUP_DIR="./backups"

# Install AWS CLI if not already installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI not found, installing..."
    pip install awscli
fi

# Upload latest backups to S3
echo "Uploading backups to S3..."
aws s3 cp ${BACKUP_DIR}/db_backup_$(ls -t ${BACKUP_DIR}/db_backup_* | head -n 1 | xargs basename) s3://${S3_BUCKET}/
aws s3 cp ${BACKUP_DIR}/media_backup_$(ls -t ${BACKUP_DIR}/media_backup_* | head -n 1 | xargs basename) s3://${S3_BUCKET}/

echo "Backup upload complete."
```

Save this as `scripts/s3_backup.sh` and make it executable:

```bash
chmod +x scripts/s3_backup.sh
```

Run after your regular backup:

```bash
# Run regular backup and then upload to S3
./scripts/backup.sh && ./scripts/s3_backup.sh
```

## Backup Verification

It's essential to verify that backups are complete and can be restored. Periodically test the restore process to ensure backups are working correctly.

### Database Backup Verification

```bash
# Create a temporary database for verification
docker-compose exec db psql -U postgres -c "CREATE DATABASE backup_test;"

# Restore the backup to the test database
cat backups/db_backup_YYYYMMDD_HHMMSS.sql | docker-compose exec -T db psql -U postgres backup_test

# Verify the restore
docker-compose exec db psql -U postgres -d backup_test -c "SELECT COUNT(*) FROM auth_user;"

# Clean up
docker-compose exec db psql -U postgres -c "DROP DATABASE backup_test;"
```

### Media Backup Verification

```bash
# Create a temporary directory
mkdir -p /tmp/backup_test

# Extract the backup
tar -xzf backups/media_backup_YYYYMMDD_HHMMSS.tar.gz -C /tmp/backup_test

# Verify the extraction
ls -la /tmp/backup_test/media

# Clean up
rm -rf /tmp/backup_test
```

## Restoration Procedures

### Database Restoration

#### Complete Database Restoration

```bash
# Stop the web service to prevent write operations during restore
docker-compose stop web

# Restore the database
cat backups/db_backup_YYYYMMDD_HHMMSS.sql | docker-compose exec -T db psql -U postgres social_cube

# Start the web service
docker-compose start web
```

#### Selective Table Restoration

To restore specific tables:

1. Create a temporary database
2. Restore the backup to the temporary database
3. Copy the specific table to the main database
4. Drop the temporary database

```bash
# Create a temporary database
docker-compose exec db psql -U postgres -c "CREATE DATABASE temp_restore;"

# Restore the backup to the temporary database
cat backups/db_backup_YYYYMMDD_HHMMSS.sql | docker-compose exec -T db psql -U postgres temp_restore

# Copy specific table(s) to the main database
docker-compose exec db psql -U postgres -c "INSERT INTO social_cube.public.bot_management_bot SELECT * FROM temp_restore.public.bot_management_bot WHERE id = 123;"

# Drop the temporary database
docker-compose exec db psql -U postgres -c "DROP DATABASE temp_restore;"
```

### Media Files Restoration

```bash
# Extract media files
docker-compose exec -T web bash -c "rm -rf /app/media/*"
cat backups/media_backup_YYYYMMDD_HHMMSS.tar.gz | docker-compose exec -T web tar -xzf - -C /app
```

### Environment Configuration Restoration

```bash
# Restore environment configuration
cp backups/env_backup_YYYYMMDD_HHMMSS .env
```

### Configuration Files Restoration

```bash
# Extract configuration files
tar -xzf backups/config_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Full Application Restoration

For a complete application restore:

```bash
# Extract the full application backup
tar -xzf backups/full_app_backup_YYYYMMDD_HHMMSS.tar.gz -C /path/to/restore

# Change to the restored directory
cd /path/to/restore

# Rebuild and restart services
docker-compose build
docker-compose down
docker-compose up -d
```

## Disaster Recovery

### Complete System Failure

In case of a complete system failure, follow these steps to restore the application:

1. **Set up a new server** with Docker and Docker Compose installed
2. **Copy the backup files** to the new server
3. **Clone the repository** or extract the full application backup
4. **Restore environment configuration** from backup
5. **Restore configuration files** from backup
6. **Build and start the services**:
   ```bash
   docker-compose build
   docker-compose up -d db redis
   ```
7. **Restore the database**:
   ```bash
   cat backups/db_backup_YYYYMMDD_HHMMSS.sql | docker-compose exec -T db psql -U postgres social_cube
   ```
8. **Restore media files**:
   ```bash
   cat backups/media_backup_YYYYMMDD_HHMMSS.tar.gz | docker-compose exec -T web tar -xzf - -C /app
   ```
9. **Start the remaining services**:
   ```bash
   docker-compose up -d
   ```

### Database Corruption

In case of database corruption:

1. **Stop the web service** to prevent further writes:
   ```bash
   docker-compose stop web
   ```
2. **Backup the corrupt database** for analysis:
   ```bash
   docker-compose exec db pg_dump -U postgres social_cube > backups/corrupt_db_$(date +'%Y%m%d_%H%M%S').sql
   ```
3. **Drop and recreate the database**:
   ```bash
   docker-compose exec db psql -U postgres -c "DROP DATABASE social_cube;"
   docker-compose exec db psql -U postgres -c "CREATE DATABASE social_cube;"
   ```
4. **Restore from the last good backup**:
   ```bash
   cat backups/db_backup_YYYYMMDD_HHMMSS.sql | docker-compose exec -T db psql -U postgres social_cube
   ```
5. **Start the web service**:
   ```bash
   docker-compose start web
   ```

### Data Loss Recovery

If specific data is lost but the system is still operational:

1. **Identify the lost data** and when it was last known to exist
2. **Find a backup** from before the data loss but after the data was created
3. **Create a temporary database** for recovery:
   ```bash
   docker-compose exec db psql -U postgres -c "CREATE DATABASE recovery;"
   ```
4. **Restore the backup** to the temporary database:
   ```bash
   cat backups/db_backup_YYYYMMDD_HHMMSS.sql | docker-compose exec -T db psql -U postgres recovery
   ```
5. **Extract the lost data** from the temporary database:
   ```bash
   docker-compose exec db psql -U postgres -c "COPY (SELECT * FROM recovery.public.bot_management_bot WHERE id = 123) TO STDOUT" > recovered_data.sql
   ```
6. **Import the recovered data** to the main database:
   ```bash
   cat recovered_data.sql | docker-compose exec -T db psql -U postgres -c "COPY social_cube.public.bot_management_bot FROM STDIN;"
   ```
7. **Drop the temporary database**:
   ```bash
   docker-compose exec db psql -U postgres -c "DROP DATABASE recovery;"
   ```

## Backup Retention Policy

Implement a backup retention policy to manage backup storage efficiently:

1. **Daily Backups**: Keep for 7 days
2. **Weekly Backups**: Keep for 4 weeks
3. **Monthly Backups**: Keep for 12 months
4. **Annual Backups**: Keep indefinitely

The backup script automatically manages retention for daily backups:

```bash
# Clean up old backups (older than BACKUP_RETENTION_DAYS)
find $BACKUP_DIR -name "db_backup_*.gz" -type f -mtime +$BACKUP_RETENTION_DAYS -delete
find $BACKUP_DIR -name "media_backup_*.tar.gz" -type f -mtime +$BACKUP_RETENTION_DAYS -delete
```

## Security Considerations

### Encryption

Encrypt sensitive backups, especially those stored off-site:

```bash
# Encrypt a backup file
gpg --encrypt --recipient your@email.com backups/db_backup_YYYYMMDD_HHMMSS.sql.gz
```

### Access Control

Restrict access to backup files:

```bash
# Set restrictive permissions on backup directory
chmod 700 backups
```

### Secure Transport

Use secure methods to transfer backups:

```bash
# Example: Secure copy to remote server
scp -r backups user@remote-server:/path/to/backup/storage/
```

## Recovery Testing Procedures

Regularly test the recovery process to ensure backups are working correctly:

1. **Schedule regular recovery tests** (e.g., quarterly)
2. **Document the test procedure and results**
3. **Address any issues identified during testing**

Example recovery test procedure:

1. **Set up a test environment** (separate from production)
2. **Restore the latest backups** to the test environment
3. **Verify application functionality**
4. **Document any issues encountered**
5. **Update recovery procedures as needed**

## Conclusion

Regular backups and tested recovery procedures are essential for data safety. Implement automated backups, verify backup integrity regularly, and practice recovery procedures to ensure you can quickly restore the application in case of failure.