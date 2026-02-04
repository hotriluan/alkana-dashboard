#!/bin/bash

# Export Local Database Script
# Exports current development database to SQL dump file

set -e

# Load environment from .env
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  .env file not found, using default values"
fi

DB_NAME="${DB_NAME:-alkana_dashboard}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
EXPORT_DIR="./database-exports"
EXPORT_FILE="$EXPORT_DIR/alkana-db-export-$(date +%Y%m%d-%H%M%S).sql"

echo "=========================================="
echo "Exporting Local Database"
echo "=========================================="
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "User: $DB_USER"
echo ""

# Create export directory
mkdir -p "$EXPORT_DIR"

# Check if database is accessible
echo "🔍 Checking database connection..."
if ! PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" > /dev/null 2>&1; then
    echo "❌ Cannot connect to database. Please check your connection settings."
    echo ""
    echo "Trying Docker container..."
    
    # Try to export from Docker container
    if docker compose ps | grep -q "postgres"; then
        echo "✅ Found PostgreSQL in Docker"
        docker compose exec -T postgres pg_dump -U "$DB_USER" "$DB_NAME" > "$EXPORT_FILE"
    else
        echo "❌ Cannot find PostgreSQL. Please ensure database is running."
        exit 1
    fi
else
    # Export using pg_dump
    echo "📦 Exporting database..."
    PGPASSWORD=$DB_PASSWORD pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        --clean \
        --if-exists \
        --no-owner \
        --no-acl \
        > "$EXPORT_FILE"
fi

# Check if export was successful
if [ ! -f "$EXPORT_FILE" ]; then
    echo "❌ Export failed!"
    exit 1
fi

# Compress the export
echo "🗜️  Compressing export..."
gzip "$EXPORT_FILE"
EXPORT_FILE="${EXPORT_FILE}.gz"

# Display export info
EXPORT_SIZE=$(du -h "$EXPORT_FILE" | cut -f1)
echo ""
echo "=========================================="
echo "✅ Export completed successfully!"
echo "=========================================="
echo "File: $EXPORT_FILE"
echo "Size: $EXPORT_SIZE"
echo ""
echo "Next steps:"
echo "1. Transfer to server: scp $EXPORT_FILE deploy@YOUR_SERVER:/home/deploy/alkana-dashboard/database-exports/"
echo "2. On server, run: ./deployment/import-database.sh $(basename $EXPORT_FILE)"
echo ""
echo "Or use the automated migration script:"
echo "  ./deployment/migrate-database.sh YOUR_SERVER_IP"
echo ""
