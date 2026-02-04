#!/bin/bash

# Automated One-Click Deployment Script
# Deploys Alkana Dashboard to production server with full automation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load server configuration
if [ -f "$SCRIPT_DIR/server-config.env" ]; then
    source "$SCRIPT_DIR/server-config.env"
else
    echo -e "${RED}Error: server-config.env not found${NC}"
    exit 1
fi

# Progress indicator
show_progress() {
    echo -e "${BLUE}▶ $1${NC}"
}

show_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

show_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

show_error() {
    echo -e "${RED}✗ $1${NC}"
}

echo ""
echo "=========================================="
echo "  Alkana Dashboard - One-Click Deployment"
echo "=========================================="
echo ""
echo "Target Server: $SERVER_IP"
echo "User: $SERVER_USER"
echo "Domain/IP: $APP_DOMAIN"
echo ""
read -p "Continue with deployment? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo "=========================================="
echo "Phase 1: Pre-deployment Checks"
echo "=========================================="

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    show_progress "Installing sshpass..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install hudochenkov/sshpass/sshpass
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y sshpass
    else
        show_error "Please install sshpass manually"
        exit 1
    fi
fi

# Test SSH connection
show_progress "Testing SSH connection..."
if sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
    "$SERVER_USER@$SERVER_IP" "echo 'Connection successful'" &> /dev/null; then
    show_success "SSH connection successful"
else
    show_error "Cannot connect to server. Please check credentials."
    exit 1
fi

echo ""
echo "=========================================="
echo "Phase 2: Server Initialization"
echo "=========================================="

show_progress "Uploading setup scripts to server..."
sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no \
    "$SCRIPT_DIR"/{setup-server.sh,setup-ssl.sh} \
    "$SERVER_USER@$SERVER_IP:/tmp/"

show_progress "Running server setup..."
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no \
    "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
    set -e
    
    # Make scripts executable
    chmod +x /tmp/setup-server.sh
    
    # Run setup as root
    echo "alkana123" | sudo -S bash /tmp/setup-server.sh
    
    # Create project directory
    mkdir -p ~/alkana-dashboard
    
    echo "Server setup completed"
ENDSSH

show_success "Server initialized"

echo ""
echo "=========================================="
echo "Phase 3: SSH Key Setup"
echo "=========================================="

show_progress "Generating SSH key pair on server..."
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no \
    "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
    if [ ! -f ~/.ssh/id_ed25519 ]; then
        ssh-keygen -t ed25519 -C "alkana@deployment" -f ~/.ssh/id_ed25519 -N ""
        echo "SSH key generated"
    else
        echo "SSH key already exists"
    fi
ENDSSH

# Get the public key
SERVER_PUBLIC_KEY=$(sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no \
    "$SERVER_USER@$SERVER_IP" "cat ~/.ssh/id_ed25519.pub")

show_success "SSH key generated"
echo ""
echo "📋 Server SSH Public Key (add this to GitHub Deploy Keys):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$SERVER_PUBLIC_KEY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Please add this key to GitHub:"
echo "1. Go to: https://github.com/$GITHUB_REPO/settings/keys"
echo "2. Click 'Add deploy key'"
echo "3. Paste the key above"
echo "4. Check 'Allow write access' if needed"
echo ""
read -p "Press Enter when you have added the key to GitHub..."

echo ""
echo "=========================================="
echo "Phase 4: Repository Setup"
echo "=========================================="

show_progress "Cloning repository on server..."
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no \
    "$SERVER_USER@$SERVER_IP" << ENDSSH
    set -e
    
    # Add GitHub to known hosts
    ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null
    
    # Clone repository
    cd ~
    if [ -d "alkana-dashboard/.git" ]; then
        echo "Repository already exists, pulling latest..."
        cd alkana-dashboard
        git pull origin $GITHUB_BRANCH
    else
        git clone git@github.com:$GITHUB_REPO.git alkana-dashboard || \
        git clone https://github.com/$GITHUB_REPO.git alkana-dashboard
        cd alkana-dashboard
    fi
    
    echo "Repository cloned/updated"
ENDSSH

show_success "Repository ready"

echo ""
echo "=========================================="
echo "Phase 5: Database Migration"
echo "=========================================="

if [ "$AUTO_MIGRATE_DB" = "true" ]; then
    show_progress "Exporting local database..."
    cd "$PROJECT_ROOT"
    bash "$SCRIPT_DIR/export-local-database.sh"
    
    # Get latest export
    LATEST_EXPORT=$(ls -t database-exports/*.sql.gz 2>/dev/null | head -1)
    
    if [ -f "$LATEST_EXPORT" ]; then
        show_success "Database exported: $(basename $LATEST_EXPORT)"
        
        show_progress "Uploading database to server..."
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no \
            "$SERVER_USER@$SERVER_IP" "mkdir -p ~/alkana-dashboard/database-exports"
        
        sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no \
            "$LATEST_EXPORT" \
            "$SERVER_USER@$SERVER_IP:~/alkana-dashboard/database-exports/"
        
        show_success "Database uploaded"
    else
        show_warning "No database export found, skipping migration"
    fi
else
    show_warning "Auto database migration disabled"
fi

echo ""
echo "=========================================="
echo "Phase 6: Environment Configuration"
echo "=========================================="

show_progress "Creating production environment file..."
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no \
    "$SERVER_USER@$SERVER_IP" << ENDSSH
    cd ~/alkana-dashboard
    
    cat > .env.production << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://$PROD_DB_USER:$PROD_DB_PASSWORD@postgres:5432/$PROD_DB_NAME
DB_HOST=postgres
DB_PORT=5432
DB_NAME=$PROD_DB_NAME
DB_USER=$PROD_DB_USER
DB_PASSWORD=$PROD_DB_PASSWORD

# Application Settings
ENVIRONMENT=production
DEBUG=false
API_BASE_URL=http://$APP_DOMAIN/api
ALLOWED_ORIGINS=http://$APP_DOMAIN,https://$APP_DOMAIN

# Data Paths
DEMODATA_PATH=/app/demodata

# Alert Thresholds
STUCK_IN_TRANSIT_HOURS=48
LOW_YIELD_THRESHOLD=85
EOF
    
    echo "Environment configured"
ENDSSH

show_success "Environment configured"

echo ""
echo "=========================================="
echo "Phase 7: Application Deployment"
echo "=========================================="

show_progress "Building and starting services..."
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no \
    "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
    cd ~/alkana-dashboard
    
    # Make scripts executable
    chmod +x deployment/*.sh
    
    # Build and start services
    docker compose -f docker-compose.prod.yml build
    docker compose -f docker-compose.prod.yml up -d
    
    echo "Services started"
ENDSSH

show_success "Services deployed"

# Wait for services to start
show_progress "Waiting for services to initialize (30 seconds)..."
sleep 30

echo ""
echo "=========================================="
echo "Phase 8: Database Import (if needed)"
echo "=========================================="

if [ "$AUTO_MIGRATE_DB" = "true" ] && [ -f "$LATEST_EXPORT" ]; then
    show_progress "Importing database..."
    
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no \
        "$SERVER_USER@$SERVER_IP" << ENDSSH
        cd ~/alkana-dashboard
        echo "yes" | bash deployment/import-database.sh database-exports/$(basename $LATEST_EXPORT)
ENDSSH
    
    show_success "Database imported"
else
    show_warning "Skipping database import"
    show_progress "Initializing empty database..."
    
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no \
        "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
        cd ~/alkana-dashboard
        docker compose -f docker-compose.prod.yml exec -T backend \
            python -m src.main init
ENDSSH
    
    show_success "Database initialized"
fi

echo ""
echo "=========================================="
echo "Phase 9: Setup Automated Tasks"
echo "=========================================="

if [ "$AUTO_BACKUP" = "true" ]; then
    show_progress "Setting up automated backups..."
    
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no \
        "$SERVER_USER@$SERVER_IP" << ENDSSH
        # Add backup cron job
        (crontab -l 2>/dev/null | grep -v "backup-database.sh"; \
         echo "$BACKUP_SCHEDULE cd ~/alkana-dashboard && bash deployment/backup-database.sh >> ~/alkana-dashboard/logs/backup.log 2>&1") | crontab -
        
        echo "Backup cron job added"
ENDSSH
    
    show_success "Automated backups configured"
fi

if [ "$HEALTH_CHECK_ENABLED" = "true" ]; then
    show_progress "Setting up health checks..."
    
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no \
        "$SERVER_USER@$SERVER_IP" << ENDSSH
        # Add health check cron job
        (crontab -l 2>/dev/null | grep -v "health-check.sh"; \
         echo "*/5 * * * * cd ~/alkana-dashboard && bash deployment/health-check.sh >> ~/alkana-dashboard/logs/health.log 2>&1") | crontab -
        
        echo "Health check cron job added"
ENDSSH
    
    show_success "Health checks configured"
fi

echo ""
echo "=========================================="
echo "Phase 10: Verification"
echo "=========================================="

show_progress "Running health checks..."

# Check frontend
if curl -sf "http://$APP_DOMAIN/health" > /dev/null 2>&1; then
    show_success "Frontend is healthy"
else
    show_warning "Frontend health check failed"
fi

# Check API
if curl -sf "http://$APP_DOMAIN/api/health" > /dev/null 2>&1; then
    show_success "API is healthy"
else
    show_warning "API health check failed (may need more time to start)"
fi

# Check services on server
sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no \
    "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
    echo ""
    echo "Docker Services Status:"
    cd ~/alkana-dashboard
    docker compose -f docker-compose.prod.yml ps
ENDSSH

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
echo "🔧 Manage Services:"
echo "   SSH:       ssh $SERVER_USER@$SERVER_IP"
echo "   Logs:      cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml logs -f"
echo "   Restart:   cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml restart"
echo "   Stop:      cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml down"
echo ""
echo "📚 Documentation:"
echo "   Full Guide:     docs/DEPLOYMENT.md"
echo "   Quick Start:    DEPLOY-GUIDE-VI.md"
echo "   DB Migration:   docs/DATABASE-MIGRATION.md"
echo ""
echo "🎉 Happy using Alkana Dashboard!"
echo ""
