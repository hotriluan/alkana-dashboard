#!/bin/bash

# Database Backup Script
# Creates automated backups with retention policy

set -e

BACKUP_DIR="/home/deploy/alkana-dashboard/backups"
RETENTION_DAYS=30
DB_NAME="${DB_NAME:-alkana_dashboard}"
DB_USER="${DB_USER:-alkana_user}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
BACKUP_FILE="$BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S).sql.gz"

echo "Starting database backup..."
echo "Database: $DB_NAME"
echo "Backup file: $BACKUP_FILE"

# Create backup
docker compose -f /home/deploy/alkana-dashboard/docker-compose.prod.yml exec -T postgres \
    pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

# Check if backup was successful
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Backup completed successfully: $BACKUP_SIZE"
else
    echo "❌ Backup failed!"
    exit 1
fi

# Remove old backups
echo "Cleaning up old backups (retention: $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "backup-*.sql.gz" -mtime +$RETENTION_DAYS -delete

# List recent backups
echo ""
echo "Recent backups:"
ls -lh "$BACKUP_DIR" | tail -5

# Calculate total backup size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo ""
echo "Total backup size: $TOTAL_SIZE"
