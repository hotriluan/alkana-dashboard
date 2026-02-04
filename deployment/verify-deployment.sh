#!/bin/bash

# Post-Deployment Verification Script
# Verifies all services are running correctly

set -e

# Load config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/server-config.env" ]; then
    source "$SCRIPT_DIR/server-config.env"
else
    echo "Warning: server-config.env not found, using defaults"
    SERVER_IP="${1:-192.168.68.166}"
    APP_DOMAIN="${SERVER_IP}"
fi

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "  Deployment Verification"
echo "=========================================="
echo "Target: $APP_DOMAIN"
echo ""

FAILED=0
PASSED=0

check_service() {
    local name=$1
    local url=$2
    
    echo -n "Checking $name... "
    
    if curl -sf "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "Frontend Checks:"
echo "----------------"
check_service "Frontend Health" "http://$APP_DOMAIN/health"
check_service "Frontend Root" "http://$APP_DOMAIN/"

echo ""
echo "Backend Checks:"
echo "---------------"
check_service "API Health" "http://$APP_DOMAIN/api/health"
check_service "API Docs" "http://$APP_DOMAIN/api/docs"

echo ""
echo "Service Status on Server:"
echo "-------------------------"

if command -v sshpass &> /dev/null && [ -n "$SERVER_PASSWORD" ]; then
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no \
        "$SERVER_USER@$SERVER_IP" << 'ENDSSH'
        cd ~/alkana-dashboard 2>/dev/null || cd /home/deploy/alkana-dashboard
        docker compose -f docker-compose.prod.yml ps
ENDSSH
else
    echo "Note: Install sshpass to check remote services"
    echo "Or run manually: ssh $SERVER_USER@$SERVER_IP 'cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml ps'"
fi

echo ""
echo "Database Connection:"
echo "--------------------"

if command -v sshpass &> /dev/null && [ -n "$SERVER_PASSWORD" ]; then
    if sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no \
        "$SERVER_USER@$SERVER_IP" \
        "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml exec -T postgres psql -U alkana_user -d alkana_dashboard -c 'SELECT version();'" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database accessible${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ Database not accessible${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo "Skipping database check (no sshpass)"
fi

echo ""
echo "Disk Space:"
echo "-----------"

if command -v sshpass &> /dev/null && [ -n "$SERVER_PASSWORD" ]; then
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no \
        "$SERVER_USER@$SERVER_IP" "df -h /"
else
    echo "Skipping disk space check"
fi

echo ""
echo "Memory Usage:"
echo "-------------"

if command -v sshpass &> /dev/null && [ -n "$SERVER_PASSWORD" ]; then
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no \
        "$SERVER_USER@$SERVER_IP" "free -h"
else
    echo "Skipping memory check"
fi

echo ""
echo "=========================================="
echo "  Verification Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "🎉 Deployment is healthy!"
    echo ""
    echo "Access your application:"
    echo "  Frontend: http://$APP_DOMAIN"
    echo "  API Docs: http://$APP_DOMAIN/api/docs"
    echo ""
    echo "Default login:"
    echo "  Username: admin"
    echo "  Password: admin123"
    echo "  ⚠️  Change password immediately!"
    exit 0
else
    echo -e "${RED}✗ Some checks failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check logs: ssh $SERVER_USER@$SERVER_IP 'cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml logs'"
    echo "2. Verify services: ssh $SERVER_USER@$SERVER_IP 'cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml ps'"
    echo "3. Restart if needed: ssh $SERVER_USER@$SERVER_IP 'cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml restart'"
    exit 1
fi
