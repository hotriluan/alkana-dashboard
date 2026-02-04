#!/bin/bash

# Import Database Script
# Imports SQL dump into production database

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <dump-file.sql.gz>"
    echo "Example: $0 database-exports/alkana-db-export-20260204-120000.sql.gz"
    exit 1
fi

DUMP_FILE=$1

if [ ! -f "$DUMP_FILE" ]; then
    echo "❌ Error: File not found: $DUMP_FILE"
    exit 1
fi

# Load environment
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
else
    echo "❌ Error: .env.production not found"
    exit 1
fi

DB_NAME="${DB_NAME:-alkana_dashboard}"
DB_USER="${DB_USER:-alkana_user}"

echo "=========================================="
echo "Database Import"
echo "=========================================="
echo "⚠️  WARNING: This will replace the current database!"
echo "Database: $DB_NAME"
echo "File: $DUMP_FILE"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Import cancelled"
    exit 0
fi

# Create backup of current database
echo ""
echo "💾 Creating backup of current database..."
BACKUP_FILE="backups/pre-import-backup-$(date +%Y%m%d-%H%M%S).sql.gz"
mkdir -p backups

docker compose -f docker-compose.prod.yml exec -T postgres \
    pg_dump -U "$DB_USER" "$DB_NAME" 2>/dev/null | gzip > "$BACKUP_FILE" || echo "⚠️  No existing database to backup"

if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Backup created: $BACKUP_FILE ($BACKUP_SIZE)"
fi

# Stop backend to prevent connections
echo ""
echo "🛑 Stopping backend service..."
docker compose -f docker-compose.prod.yml stop backend

# Drop and recreate database
echo "🗑️  Dropping existing database..."
docker compose -f docker-compose.prod.yml exec -T postgres \
    psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" || true

echo "🏗️  Creating fresh database..."
docker compose -f docker-compose.prod.yml exec -T postgres \
    psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# Import dump
echo "📥 Importing database dump..."
if [[ "$DUMP_FILE" == *.gz ]]; then
    gunzip -c "$DUMP_FILE" | docker compose -f docker-compose.prod.yml exec -T postgres \
        psql -U "$DB_USER" -d "$DB_NAME"
else
    cat "$DUMP_FILE" | docker compose -f docker-compose.prod.yml exec -T postgres \
        psql -U "$DB_USER" -d "$DB_NAME"
fi

# Restart backend
echo ""
echo "🚀 Restarting backend service..."
docker compose -f docker-compose.prod.yml start backend

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 10

# Verify import
echo "🔍 Verifying database..."
TABLE_COUNT=$(docker compose -f docker-compose.prod.yml exec -T postgres \
    psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema');")

echo ""
echo "=========================================="
echo "✅ Import completed successfully!"
echo "=========================================="
echo "Tables imported: $(echo $TABLE_COUNT | xargs)"
echo "Backup location: $BACKUP_FILE"
echo ""
echo "Verify the application:"
echo "  docker compose -f docker-compose.prod.yml logs backend"
echo "  curl https://dashboard.alkana.com/api/health"
echo ""
