# Quick Deployment Script for Windows
# Usage: .\deployment\quick-deploy.ps1

param(
    [string]$ServerIP = "192.168.18.35",
    [string]$ServerUser = "it",
    [string]$ProjectDir = "~/alkana-dashboard"
)

$ErrorActionPreference = "Stop"

function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Cyan }
function Write-Error { param($msg) Write-Host "✗ $msg" -ForegroundColor Red }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Alkana Dashboard - Quick Deploy" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Info "Server: $ServerUser@$ServerIP"
Write-Host ""

# Test SSH connection
Write-Info "Testing SSH connection..."
try {
    $testResult = ssh -o BatchMode=yes -o ConnectTimeout=5 "$ServerUser@$ServerIP" "echo 'Connected'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "SSH connection OK"
    } else {
        throw "SSH connection failed"
    }
} catch {
    Write-Error "Cannot connect to server via SSH"
    Write-Info "Please ensure SSH key is configured"
    exit 1
}

# Deploy
Write-Host ""
Write-Info "Deploying to production server..."
Write-Host ""

$deployScript = @'
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
'@

ssh "$ServerUser@$ServerIP" $deployScript

Write-Host ""
Write-Success "Deployment completed successfully!"
Write-Host ""
Write-Info "View logs with:"
Write-Host "  ssh $ServerUser@$ServerIP 'cd $ProjectDir && docker compose -f docker-compose.prod.yml logs -f'" -ForegroundColor White
Write-Host ""
Write-Info "Access application:"
Write-Host "  http://$ServerIP" -ForegroundColor White
Write-Host "  http://$ServerIP/api/docs" -ForegroundColor White
Write-Host ""
