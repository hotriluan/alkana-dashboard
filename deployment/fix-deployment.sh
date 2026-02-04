#!/bin/bash
#
# Fix deployment on server
#

set -e

SERVER_IP="192.168.68.166"
SERVER_USER="alkana"
REPO_URL="https://github.com/hotriluan/alkana-dashboard.git"

echo "=========================================="
echo "Fix Deployment on Server"
echo "=========================================="
echo ""
echo "Connecting to $SERVER_IP..."
echo "Password: alkana123"
echo ""

ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP << 'ENDSSH'
set -e

echo "Step 1: Remove old deployment and clone fresh"
cd ~
rm -rf alkana-dashboard
git clone https://github.com/hotriluan/alkana-dashboard.git
cd alkana-dashboard

echo "Step 2: Create environment file"
cat > .env.production << 'EOF'
DATABASE_URL=postgresql://alkana_user:alkana_secure_pass_2026@postgres:5432/alkana_dashboard
DB_HOST=postgres
DB_PORT=5432
DB_NAME=alkana_dashboard
DB_USER=alkana_user
DB_PASSWORD=alkana_secure_pass_2026
ENVIRONMENT=production
DEBUG=false
API_BASE_URL=http://192.168.68.166/api
ALLOWED_ORIGINS=http://192.168.68.166
DEMODATA_PATH=/app/demodata
STUCK_IN_TRANSIT_HOURS=48
LOW_YIELD_THRESHOLD=85
EOF

echo "Step 3: Add user to docker group"
echo 'alkana123' | sudo -S usermod -aG docker alkana

echo "Step 4: Build and start (with sudo for now)"
echo 'alkana123' | sudo -S docker compose -f docker-compose.prod.yml build
echo 'alkana123' | sudo -S docker compose -f docker-compose.prod.yml up -d

echo "Step 5: Check status"
echo 'alkana123' | sudo -S docker compose -f docker-compose.prod.yml ps

echo ""
echo "=========================================="
echo "✅ Deployment fixed!"
echo "=========================================="
echo ""
echo "You need to LOGOUT and LOGIN again for docker group to take effect:"
echo "  exit"
echo "  ssh alkana@192.168.68.166"
echo "  cd ~/alkana-dashboard"
echo "  docker compose -f docker-compose.prod.yml ps"
echo ""
ENDSSH

echo ""
echo "Deployment fixed! Services should be starting now."
echo ""
