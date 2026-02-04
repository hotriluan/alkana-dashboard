#!/bin/bash

# Manual Deployment Script
# For manual deployment without GitHub Actions

set -e

echo "=========================================="
echo "Alkana Dashboard - Manual Deployment"
echo "=========================================="

# Check if .env.production exists
if [ ! -f .env.production ]; then
    echo "❌ Error: .env.production not found!"
    echo "Please create .env.production from .env.example"
    exit 1
fi

# Source environment variables
export $(cat .env.production | grep -v '^#' | xargs)

echo "🔄 Pulling latest changes..."
git pull origin main

echo "💾 Creating database backup..."
./deployment/backup-database.sh || echo "⚠️  Backup failed or database not running"

echo "🏗️  Building Docker images..."
docker compose -f docker-compose.prod.yml build --no-cache

echo "🚀 Starting services..."
docker compose -f docker-compose.prod.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 30

echo "🔍 Checking service health..."
docker compose -f docker-compose.prod.yml ps

echo "🧹 Cleaning up old images..."
docker image prune -af --filter "until=72h"

echo ""
echo "=========================================="
echo "✅ Deployment completed!"
echo "=========================================="
echo ""
echo "Verify deployment:"
echo "  docker compose -f docker-compose.prod.yml ps"
echo "  docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo "Check health:"
echo "  curl https://dashboard.alkana.com/health"
echo "  curl https://dashboard.alkana.com/api/health"
echo ""
