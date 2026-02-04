#!/bin/bash

# Automated Database Migration Script
# Exports local database and imports to production server

set -e

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <server-ip-or-domain> [ssh-user]"
    echo "Example: $0 165.232.123.45"
    echo "Example: $0 dashboard.alkana.com deploy"
    exit 1
fi

SERVER=$1
SSH_USER="${2:-deploy}"
EXPORT_DIR="./database-exports"

echo "=========================================="
echo "Automated Database Migration"
echo "=========================================="
echo "Source: Local development database"
echo "Target: $SSH_USER@$SERVER"
echo ""
read -p "This will replace the production database. Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Migration cancelled"
    exit 0
fi

# Step 1: Export local database
echo ""
echo "Step 1/4: Exporting local database..."
./deployment/export-local-database.sh

# Get the latest export file
LATEST_EXPORT=$(ls -t $EXPORT_DIR/*.sql.gz | head -1)

if [ ! -f "$LATEST_EXPORT" ]; then
    echo "❌ Export file not found"
    exit 1
fi

echo "✅ Export created: $LATEST_EXPORT"

# Step 2: Transfer to server
echo ""
echo "Step 2/4: Transferring to server..."
echo "Uploading $(basename $LATEST_EXPORT)..."

ssh $SSH_USER@$SERVER "mkdir -p ~/alkana-dashboard/database-exports"

scp "$LATEST_EXPORT" "$SSH_USER@$SERVER:~/alkana-dashboard/database-exports/"

echo "✅ Transfer completed"

# Step 3: Import on server
echo ""
echo "Step 3/4: Importing on server..."

ssh $SSH_USER@$SERVER << EOF
    cd ~/alkana-dashboard
    chmod +x deployment/import-database.sh
    echo "yes" | ./deployment/import-database.sh database-exports/$(basename $LATEST_EXPORT)
EOF

echo "✅ Import completed"

# Step 4: Verify
echo ""
echo "Step 4/4: Verifying deployment..."

if curl -sf "https://$SERVER/api/health" > /dev/null 2>&1; then
    echo "✅ API is healthy"
else
    echo "⚠️  API health check failed, checking HTTP..."
    if curl -sf "http://$SERVER/api/health" > /dev/null 2>&1; then
        echo "✅ API is responding on HTTP (HTTPS may not be configured yet)"
    else
        echo "⚠️  Warning: API is not responding"
        echo "Check logs: ssh $SSH_USER@$SERVER 'cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml logs backend'"
    fi
fi

echo ""
echo "=========================================="
echo "✅ Migration completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify application: https://$SERVER"
echo "2. Check logs: ssh $SSH_USER@$SERVER 'cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml logs -f'"
echo "3. Test functionality"
echo ""
echo "Rollback if needed:"
echo "  ssh $SSH_USER@$SERVER"
echo "  cd ~/alkana-dashboard"
echo "  ls -lh backups/pre-import-backup-*.sql.gz"
echo "  ./deployment/import-database.sh backups/pre-import-backup-XXXXXX.sql.gz"
echo ""
