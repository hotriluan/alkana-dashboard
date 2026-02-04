# -*- mode: powershell; coding: utf-8 -*-
#
# Alkana Dashboard - Deployment Guide (PowerShell)
# For Windows users
# 
# RECOMMENDATION: Use Git Bash for full automation instead:
#   bash deployment/one-click-deploy.sh
#
# This script provides guided manual deployment steps
#
# Usage:
#   .\deployment\one-click-deploy.ps1
#   .\deployment\one-click-deploy.ps1 -SkipConfirm

param(
    [switch]$SkipConfirm
)

# Load configuration
$configFile = Join-Path $PSScriptRoot "server-config.env"
if (-not (Test-Path $configFile)) {
    Write-Host "Error: $configFile not found" -ForegroundColor Red
    Write-Host "Please create it from server-config.env.example" -ForegroundColor Yellow
    exit 1
}

Get-Content $configFile | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        Set-Variable -Name $name -Value $value -Scope Script
    }
}

# Helper functions
function Show-Progress { 
    param([string]$msg) 
    Write-Host "⏳ $msg" -ForegroundColor Yellow 
}

function Show-Success { 
    param([string]$msg) 
    Write-Host "✓ $msg" -ForegroundColor Green 
}

function Show-Warning { 
    param([string]$msg) 
    Write-Host "⚠ $msg" -ForegroundColor Yellow 
}

function Show-Error { 
    param([string]$msg) 
    Write-Host "✗ $msg" -ForegroundColor Red 
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Alkana Dashboard - Deployment Guide" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Target Server: $SERVER_IP"
Write-Host "User: $SERVER_USER"
Write-Host "Domain/IP: $APP_DOMAIN"
Write-Host ""

if (-not $SkipConfirm) {
    $confirm = Read-Host "Continue with deployment? (yes/no)"
    if ($confirm -ne "yes") {
        Write-Host "Deployment cancelled."
        exit 0
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Important Note" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Show-Warning "For fully automated deployment, use Git Bash instead:"
Write-Host ""
Write-Host "  bash deployment/one-click-deploy.sh" -ForegroundColor Green
Write-Host ""
Write-Host "This PowerShell script provides manual step-by-step guidance." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to cancel and use Git Bash, or" -ForegroundColor Yellow
Write-Host ""
$choice = Read-Host "Continue with manual steps? (yes/no)"
if ($choice -ne "yes") {
    Write-Host ""
    Write-Host "Please run: bash deployment/one-click-deploy.sh" -ForegroundColor Green
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Step 1: Test SSH Connection" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open a new PowerShell window and run:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  ssh $SERVER_USER@$SERVER_IP" -ForegroundColor Green
Write-Host ""
Write-Host "Password: $SERVER_PASSWORD" -ForegroundColor Cyan
Write-Host ""
Write-Host "If ssh command not found, install OpenSSH or use PuTTY" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter after testing SSH connection"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Step 2: Setup Server" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Connect to server:" -ForegroundColor Yellow
Write-Host "  ssh $SERVER_USER@$SERVER_IP" -ForegroundColor Green
Write-Host ""
Write-Host "Then run these commands on the server:" -ForegroundColor Yellow
Write-Host ""
Write-Host "# Update system" -ForegroundColor Cyan
Write-Host 'sudo apt update && sudo apt upgrade -y' -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "# Install Docker" -ForegroundColor Cyan
Write-Host 'curl -fsSL https://get.docker.com -o get-docker.sh' -ForegroundColor Cyan
Write-Host 'sudo sh get-docker.sh' -ForegroundColor Cyan
Write-Host "sudo usermod -aG docker $SERVER_USER" -ForegroundColor Cyan
Write-Host 'newgrp docker' -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "# Install tools" -ForegroundColor Cyan
Write-Host 'sudo apt install -y git curl wget ufw fail2ban' -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "# Configure firewall" -ForegroundColor Cyan
Write-Host 'sudo ufw allow 22' -ForegroundColor Cyan
Write-Host 'sudo ufw allow 80' -ForegroundColor Cyan
Write-Host 'sudo ufw allow 443' -ForegroundColor Cyan
Write-Host 'sudo ufw --force enable' -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "# Create project directory" -ForegroundColor Cyan
Write-Host 'mkdir -p ~/alkana-dashboard' -ForegroundColor Cyan
Write-Host 'cd ~/alkana-dashboard' -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "# Clone repository (replace YOUR_ORG with actual GitHub organization)" -ForegroundColor Cyan
Write-Host "git clone https://github.com/$GITHUB_REPO.git ." -ForegroundColor Cyan
Write-Host "# Or if private repo, you'll need to setup SSH keys first" -ForegroundColor Cyan
Write-Host ""
Write-Host "Copy and paste above commands in SSH session" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter after server setup is complete"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Step 3: Create Environment File" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "On the server, create .env.production file:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  cd ~/alkana-dashboard" -ForegroundColor Green
Write-Host "  nano .env.production" -ForegroundColor Green
Write-Host ""
Write-Host "Paste this content (press Ctrl+O to save, Ctrl+X to exit):" -ForegroundColor Yellow
Write-Host ""
Write-Host "DATABASE_URL=postgresql://$PROD_DB_USER`:$PROD_DB_PASSWORD@postgres:5432/$PROD_DB_NAME" -ForegroundColor Cyan
Write-Host "DB_HOST=postgres" -ForegroundColor Cyan
Write-Host "DB_PORT=5432" -ForegroundColor Cyan
Write-Host "DB_NAME=$PROD_DB_NAME" -ForegroundColor Cyan
Write-Host "DB_USER=$PROD_DB_USER" -ForegroundColor Cyan
Write-Host "DB_PASSWORD=$PROD_DB_PASSWORD" -ForegroundColor Cyan
Write-Host "ENVIRONMENT=production" -ForegroundColor Cyan
Write-Host "DEBUG=false" -ForegroundColor Cyan
Write-Host "API_BASE_URL=http://$APP_DOMAIN/api" -ForegroundColor Cyan
Write-Host "ALLOWED_ORIGINS=http://$APP_DOMAIN" -ForegroundColor Cyan
Write-Host "DEMODATA_PATH=/app/demodata" -ForegroundColor Cyan
Write-Host "STUCK_IN_TRANSIT_HOURS=48" -ForegroundColor Cyan
Write-Host "LOW_YIELD_THRESHOLD=85" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter after creating .env.production"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Step 4: Export Local Database (Optional)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "If you want to migrate your local database:" -ForegroundColor Yellow
Write-Host ""
Write-Host "On your LOCAL machine, open Git Bash and run:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  cd c:/dev/alkana-dashboard" -ForegroundColor Green
Write-Host "  bash deployment/export-local-database.sh" -ForegroundColor Green
Write-Host ""
Write-Host "This creates database-exports/*.sql.gz file" -ForegroundColor Cyan
Write-Host ""
$skipDB = Read-Host "Skip database migration? (yes/no)"

if ($skipDB -ne "yes") {
    Write-Host ""
    Write-Host "Upload database to server using WinSCP or scp:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  scp database-exports/*.sql.gz $SERVER_USER@$SERVER_IP`:~/alkana-dashboard/database-exports/" -ForegroundColor Green
    Write-Host ""
    Write-Host "Then on server, import:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host 'cd ~/alkana-dashboard' -ForegroundColor Cyan
    Write-Host 'chmod +x deployment/import-database.sh' -ForegroundColor Cyan
    Write-Host 'bash deployment/import-database.sh database-exports/YOUR_FILE.sql.gz' -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter after database upload and import"
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Step 5: Build and Deploy" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "On the server, run:" -ForegroundColor Yellow
Write-Host ""
Write-Host 'cd ~/alkana-dashboard' -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "# Build containers" -ForegroundColor Cyan
Write-Host 'docker compose -f docker-compose.prod.yml build' -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "# Start services" -ForegroundColor Cyan
Write-Host 'docker compose -f docker-compose.prod.yml up -d' -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "# Check status" -ForegroundColor Cyan
Write-Host 'docker compose -f docker-compose.prod.yml ps' -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "# View logs" -ForegroundColor Cyan
Write-Host 'docker compose -f docker-compose.prod.yml logs -f' -ForegroundColor Cyan
Write-Host ""
Write-Host "Services will start. Wait 30-60 seconds for initialization" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter after deployment"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Step 6: Setup Automated Backups" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "On the server, setup cron jobs:" -ForegroundColor Yellow
Write-Host ""
Write-Host "# Make scripts executable" -ForegroundColor Cyan
Write-Host 'chmod +x ~/alkana-dashboard/deployment/*.sh' -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "# Add backup job (daily at 2 AM)" -ForegroundColor Cyan
Write-Host '(crontab -l 2>/dev/null | grep -v backup-database; echo "0 2 * * * cd ~/alkana-dashboard && bash deployment/backup-database.sh") | crontab -' -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "# Add health check (every 5 minutes)" -ForegroundColor Cyan
Write-Host '(crontab -l 2>/dev/null | grep -v health-check; echo "*/5 * * * * cd ~/alkana-dashboard && bash deployment/health-check.sh") | crontab -' -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "# Verify cron jobs" -ForegroundColor Cyan
Write-Host 'crontab -l' -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter after setting up cron jobs"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Step 7: Verification" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Show-Progress "Checking if services are accessible..."
Write-Host ""

# Check frontend
try {
    $response = Invoke-WebRequest -Uri "http://$APP_DOMAIN/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Show-Success "Frontend is responding!"
    }
} catch {
    Show-Warning "Frontend not responding yet. May need more time."
}

# Check API
try {
    $response = Invoke-WebRequest -Uri "http://$APP_DOMAIN/api/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Show-Success "API is responding!"
    }
} catch {
    Show-Warning "API not responding yet. May need more time."
}

Write-Host ""
Write-Host "Manual verification URLs:" -ForegroundColor Yellow
Write-Host "  http://$APP_DOMAIN/health" -ForegroundColor Cyan
Write-Host "  http://$APP_DOMAIN/api/health" -ForegroundColor Cyan
Write-Host "  http://$APP_DOMAIN/api/docs" -ForegroundColor Cyan
Write-Host ""

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Deployment Guide Completed!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Access Points:" -ForegroundColor Yellow
Write-Host "   Frontend:  http://$APP_DOMAIN" -ForegroundColor Cyan
Write-Host "   API Docs:  http://$APP_DOMAIN/api/docs" -ForegroundColor Cyan
Write-Host "   Health:    http://$APP_DOMAIN/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Default Login:" -ForegroundColor Yellow
Write-Host "   Username: admin" -ForegroundColor Cyan
Write-Host "   Password: admin123" -ForegroundColor Cyan
Write-Host "   ⚠️  CHANGE THIS IMMEDIATELY!" -ForegroundColor Red
Write-Host ""
Write-Host "🔧 Server Commands:" -ForegroundColor Yellow
Write-Host "   View logs:     docker compose -f docker-compose.prod.yml logs -f" -ForegroundColor Cyan
Write-Host "   Restart:       docker compose -f docker-compose.prod.yml restart" -ForegroundColor Cyan
Write-Host "   Stop:          docker compose -f docker-compose.prod.yml down" -ForegroundColor Cyan
Write-Host "   Start:         docker compose -f docker-compose.prod.yml up -d" -ForegroundColor Cyan
Write-Host "   Check status:  docker compose -f docker-compose.prod.yml ps" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔐 SSL Setup (Optional):" -ForegroundColor Yellow
Write-Host "   If you have a domain name, run on server:" -ForegroundColor Cyan
Write-Host "   bash deployment/setup-ssl.sh your-domain.com" -ForegroundColor Green
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Yellow
Write-Host "   DEPLOY-AUTO.md      - Full automation guide" -ForegroundColor Cyan
Write-Host "   START-HERE.md       - Getting started" -ForegroundColor Cyan
Write-Host "   DEPLOYMENT-SUMMARY.md - Technical details" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 For fully automated deployment next time:" -ForegroundColor Yellow
Write-Host "   bash deployment/one-click-deploy.sh" -ForegroundColor Green
Write-Host ""
