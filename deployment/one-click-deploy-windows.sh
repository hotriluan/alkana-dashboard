#!/bin/bash
#
# Alkana Dashboard - Windows Git Bash Deployment
# Simplified version for Windows (no sshpass required)
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Helper functions
show_progress() { echo -e "${YELLOW}⏳ $1${NC}"; }
show_success() { echo -e "${GREEN}✓ $1${NC}"; }
show_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
show_error() { echo -e "${RED}✗ $1${NC}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Load configuration
if [ ! -f "$SCRIPT_DIR/server-config.env" ]; then
    show_error "server-config.env not found"
    exit 1
fi

source "$SCRIPT_DIR/server-config.env"

echo ""
echo "=========================================="
echo "  Alkana Dashboard - Windows Deployment"
echo "=========================================="
echo ""
echo "Target Server: $SERVER_IP"
echo "User: $SERVER_USER"
echo "Domain/IP: $APP_DOMAIN"
echo ""

read -p "Continue with deployment? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo "=========================================="
echo "Step 1: SSH Connection Test"
echo "=========================================="
show_progress "Testing SSH connection..."
echo ""
echo "You'll be prompted for password: $SERVER_PASSWORD"
echo ""

if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no \
    "$SERVER_USER@$SERVER_IP" "echo 'Connection successful'" 2>/dev/null; then
    show_success "SSH connection successful"
else
    show_error "Cannot connect to server"
    echo ""
    echo "Please test manually:"
    echo "  ssh $SERVER_USER@$SERVER_IP"
    echo "  Password: $SERVER_PASSWORD"
    exit 1
fi

echo ""
echo "=========================================="
echo "Step 2: Server Setup"
echo "=========================================="
show_progress "Uploading setup scripts..."

scp -o StrictHostKeyChecking=no \
    "$SCRIPT_DIR/setup-server.sh" \
    "$SCRIPT_DIR/setup-ssl.sh" \
    "$SERVER_USER@$SERVER_IP:/tmp/" || {
    show_error "Failed to upload files"
    echo "Password: $SERVER_PASSWORD"
    exit 1
}

show_progress "Running server setup..."
ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << ENDSSH
chmod +x /tmp/setup-server.sh
echo '$SERVER_PASSWORD' | sudo -S bash /tmp/setup-server.sh
mkdir -p ~/alkana-dashboard
ENDSSH

show_success "Server initialized"

echo ""
echo "=========================================="
echo "Step 3: Deploy Application"
echo "=========================================="

show_progress "Creating deployment package..."
tar -czf /tmp/alkana-deploy.tar.gz \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='database-exports' \
    .

show_progress "Uploading application..."
scp -o StrictHostKeyChecking=no /tmp/alkana-deploy.tar.gz \
    "$SERVER_USER@$SERVER_IP:~/alkana-dashboard/"

rm /tmp/alkana-deploy.tar.gz

show_progress "Extracting and configuring..."
ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << ENDSSH
cd ~/alkana-dashboard
tar -xzf alkana-deploy.tar.gz
rm alkana-deploy.tar.gz

# Create environment file
cat > .env.production << 'EOF'
DATABASE_URL=postgresql://$PROD_DB_USER:$PROD_DB_PASSWORD@postgres:5432/$PROD_DB_NAME
DB_HOST=postgres
DB_PORT=5432
DB_NAME=$PROD_DB_NAME
DB_USER=$PROD_DB_USER
DB_PASSWORD=$PROD_DB_PASSWORD
ENVIRONMENT=production
DEBUG=false
API_BASE_URL=http://$APP_DOMAIN/api
ALLOWED_ORIGINS=http://$APP_DOMAIN
DEMODATA_PATH=/app/demodata
STUCK_IN_TRANSIT_HOURS=48
LOW_YIELD_THRESHOLD=85
EOF

# Build and start
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Wait for services
sleep 30

# Initialize database
docker compose -f docker-compose.prod.yml exec -T backend python -m src.main init || true
ENDSSH

show_success "Application deployed"

echo ""
echo "=========================================="
echo "Step 4: Database Migration (Optional)"
echo "=========================================="
echo ""
read -p "Migrate local database? (yes/no): " migrate_db

if [ "$migrate_db" = "yes" ]; then
    show_progress "Exporting local database..."
    bash "$SCRIPT_DIR/export-local-database.sh" || {
        show_warning "Database export failed. Skipping migration."
    }
    
    LATEST_EXPORT=$(ls -t database-exports/*.sql.gz 2>/dev/null | head -1)
    if [ -n "$LATEST_EXPORT" ]; then
        show_progress "Uploading database..."
        ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "mkdir -p ~/alkana-dashboard/database-exports"
        scp -o StrictHostKeyChecking=no "$LATEST_EXPORT" \
            "$SERVER_USER@$SERVER_IP:~/alkana-dashboard/database-exports/"
        
        show_progress "Importing database..."
        ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << ENDSSH
cd ~/alkana-dashboard
chmod +x deployment/import-database.sh
echo 'yes' | bash deployment/import-database.sh "database-exports/$(basename $LATEST_EXPORT)"
ENDSSH
        show_success "Database migrated"
    fi
fi

echo ""
echo "=========================================="
echo "Step 5: Setup Automation"
echo "=========================================="

show_progress "Configuring backups and health checks..."
ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
cd ~/alkana-dashboard
chmod +x deployment/*.sh

# Add cron jobs
(crontab -l 2>/dev/null | grep -v backup-database; echo "0 2 * * * cd ~/alkana-dashboard && bash deployment/backup-database.sh") | crontab -
(crontab -l 2>/dev/null | grep -v health-check; echo "*/5 * * * * cd ~/alkana-dashboard && bash deployment/health-check.sh") | crontab -
ENDSSH

show_success "Automation configured"

echo ""
echo "=========================================="
echo "Step 6: Verification"
echo "=========================================="

show_progress "Checking services..."
sleep 5

if curl -s -o /dev/null -w "%{http_code}" "http://$APP_DOMAIN/health" | grep -q "200"; then
    show_success "Frontend is healthy"
else
    show_warning "Frontend not responding yet"
fi

if curl -s -o /dev/null -w "%{http_code}" "http://$APP_DOMAIN/api/health" | grep -q "200"; then
    show_success "API is healthy"
else
    show_warning "API not responding yet (may need more time)"
fi

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETED!"
echo "=========================================="
echo ""
echo "🌐 Access Points:"
echo "   Frontend:  http://$APP_DOMAIN"
echo "   API Docs:  http://$APP_DOMAIN/api/docs"
echo "   Health:    http://$APP_DOMAIN/health"
echo ""
echo "📊 Default Login:"
echo "   Username: admin"
echo "   Password: admin123"
echo "   ⚠️  CHANGE THIS IMMEDIATELY!"
echo ""
echo "🔧 Server Commands (SSH to server and run):"
echo "   ssh $SERVER_USER@$SERVER_IP"
echo "   cd ~/alkana-dashboard"
echo "   docker compose -f docker-compose.prod.yml ps"
echo "   docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo "📚 For help, see: deployment/WINDOWS-USERS.md"
echo ""
