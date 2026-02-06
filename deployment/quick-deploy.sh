#!/bin/bash
#
# Quick deployment script for Alkana Dashboard
# Usage: ./deployment/quick-deploy.sh [environment]
# Example: ./deployment/quick-deploy.sh production

set -e

ENVIRONMENT=${1:-production}
SERVER_IP=${SERVER_IP:-192.168.18.35}
SERVER_USER=${SERVER_USER:-it}
PROJECT_DIR="~/alkana-dashboard"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo_success() { echo -e "${GREEN}✓ $1${NC}"; }
echo_info() { echo -e "${YELLOW}ℹ $1${NC}"; }
echo_error() { echo -e "${RED}✗ $1${NC}"; }

echo ""
echo "========================================"
echo "  Alkana Dashboard - Quick Deploy"
echo "========================================"
echo ""
echo "Environment: $ENVIRONMENT"
echo "Server: $SERVER_USER@$SERVER_IP"
echo ""

# Check if SSH connection works
echo_info "Testing SSH connection..."
if ssh -o BatchMode=yes -o ConnectTimeout=5 "$SERVER_USER@$SERVER_IP" "echo 'Connected'" &>/dev/null; then
    echo_success "SSH connection OK"
else
    echo_error "Cannot connect to server via SSH"
    echo_info "Please ensure SSH key is configured or use:"
    echo "  ssh-copy-id $SERVER_USER@$SERVER_IP"
    exit 1
fi

# Deploy
echo ""
echo_info "Deploying to production server..."
echo ""

ssh "$SERVER_USER@$SERVER_IP" bash << 'ENDSSH'
set -e

cd ~/alkana-dashboard || { echo "Project directory not found. Run setup first."; exit 1; }

echo "📥 Pulling latest code..."
git pull origin main

echo "🏗️  Building Docker images..."
docker compose -f docker-compose.prod.yml build

echo "📦 Backing up database..."
mkdir -p backups
if docker compose -f docker-compose.prod.yml ps postgres | grep -q "Up"; then
    docker compose -f docker-compose.prod.yml exec -T postgres \
        pg_dump -U alkana_user alkana_dashboard 2>/dev/null | \
        gzip > backups/backup-$(date +%Y%m%d-%H%M%S).sql.gz || echo "Backup skipped"
fi

echo "🚀 Starting services..."
docker compose -f docker-compose.prod.yml up -d

echo "⏳ Waiting for services to be healthy..."
sleep 20

echo "🔍 Checking service status..."
docker compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Service URLs:"
echo "  - Frontend: http://$(hostname -I | awk '{print $1}')"
echo "  - API Docs: http://$(hostname -I | awk '{print $1}')/api/docs"
echo "  - Health: http://$(hostname -I | awk '{print $1}')/api/health"
echo ""

ENDSSH

echo_success "Deployment completed successfully!"
echo ""
echo_info "View logs with:"
echo "  ssh $SERVER_USER@$SERVER_IP 'cd $PROJECT_DIR && docker compose -f docker-compose.prod.yml logs -f'"
echo ""
