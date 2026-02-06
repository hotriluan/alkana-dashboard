# Alkana Dashboard - Production Server Setup Script
# Automated server configuration for Ubuntu production server

param(
    [string]$ServerIP = "192.168.18.35",
    [string]$ServerUser = "it",
    [string]$ServerPassword = "it123",
    [string]$SSHKeyPath = "$env:USERPROFILE\.ssh\alkana_deploy",
    [switch]$SkipConfirm
)

$ErrorActionPreference = "Stop"

# Colors
function Write-Success { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Cyan }
function Write-Warning { Write-Host "⚠ $args" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "✗ $msg" -ForegroundColor Red }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Alkana Dashboard - Server Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Info "Target: $ServerUser@$ServerIP"
Write-Host ""

if (-not $SkipConfirm) {
    $confirm = Read-Host "Continue with server setup? (yes/no)"
    if ($confirm -ne "yes") {
        Write-Warning "Setup cancelled"
        exit 0
    }
}

# Step 1: Generate SSH key if not exists
Write-Host ""
Write-Info "Step 1: Checking SSH key..."
if (-not (Test-Path "$SSHKeyPath")) {
    Write-Info "Generating new SSH key pair..."
    ssh-keygen -t ed25519 -C "github-actions@alkana-dashboard" -f $SSHKeyPath -N '""'
    Write-Success "SSH key generated: $SSHKeyPath"
} else {
    Write-Success "SSH key already exists: $SSHKeyPath"
}

# Step 2: Check if sshpass is available
Write-Host ""
Write-Info "Step 2: Checking SSH connectivity..."
Write-Warning "Note: You may need to install 'sshpass' for password authentication"
Write-Info "Alternatively, use Git Bash or WSL for this script"

# Create temporary script for server setup
$setupScript = @"
#!/bin/bash
set -e

echo "========================================="
echo "  Server Setup Started"
echo "========================================="

# Update system
echo "📦 Updating system packages..."
sudo apt update -qq
sudo apt upgrade -y -qq

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sudo sh /tmp/get-docker.sh
    sudo usermod -aG docker $ServerUser
    echo "✓ Docker installed"
else
    echo "✓ Docker already installed"
fi

# Install Docker Compose v2
echo "🐙 Installing Docker Compose..."
if ! docker compose version &> /dev/null; then
    sudo apt install -y docker-compose-plugin
    echo "✓ Docker Compose installed"
else
    echo "✓ Docker Compose already installed"
fi

# Install essential tools
echo "🛠️  Installing essential tools..."
sudo apt install -y git curl wget ufw fail2ban htop net-tools

# Configure firewall
echo "🔥 Configuring firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'
sudo ufw --force enable
echo "✓ Firewall configured"

# Create project directory
echo "📁 Creating project directory..."
mkdir -p ~/alkana-dashboard
mkdir -p ~/alkana-dashboard/backups
mkdir -p ~/alkana-dashboard/logs
echo "✓ Project directory created"

# Configure Git
echo "🔧 Configuring Git..."
git config --global user.email "deploy@alkana-dashboard.local"
git config --global user.name "Alkana Deployment"

# Setup SSH for GitHub
echo "🔑 Setting up SSH..."
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

echo "========================================="
echo "  Server Setup Complete!"
echo "========================================="
echo ""
echo "✅ Docker: $(docker --version)"
echo "✅ Docker Compose: $(docker compose version)"
echo "✅ Git: $(git --version)"
echo "✅ Firewall: Active"
echo "✅ Project directory: ~/alkana-dashboard"
echo ""
"@

# Save script to temp file
$tempScriptPath = [System.IO.Path]::GetTempFileName()
$setupScript | Out-File -FilePath $tempScriptPath -Encoding UTF8 -NoNewline

Write-Host ""
Write-Info "Step 3: Uploading setup script to server..."
Write-Warning "Please enter password when prompted: $ServerPassword"

# Try using SCP (requires OpenSSH)
try {
    scp -o StrictHostKeyChecking=no $tempScriptPath "$ServerUser@$ServerIP:/tmp/setup-server.sh"
    Write-Success "Setup script uploaded"
} catch {
    Write-Error "Failed to upload script. Make sure OpenSSH is installed."
    Write-Info "Install OpenSSH: Settings > Apps > Optional Features > Add OpenSSH Client"
    exit 1
}

Write-Host ""
Write-Info "Step 4: Running setup script on server..."
Write-Info "This may take 5-10 minutes..."

ssh -o StrictHostKeyChecking=no "$ServerUser@$ServerIP" "bash /tmp/setup-server.sh"

Write-Host ""
Write-Info "Step 5: Copying SSH public key to server..."
$publicKey = Get-Content "$SSHKeyPath.pub"
ssh "$ServerUser@$ServerIP" "echo '$publicKey' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
Write-Success "SSH key copied to server"

Write-Host ""
Write-Info "Step 6: Testing SSH key authentication..."
ssh -i $SSHKeyPath -o BatchMode=yes "$ServerUser@$ServerIP" "echo 'SSH key authentication successful!'"
Write-Success "SSH key authentication working"

# Clean up
Remove-Item $tempScriptPath -Force

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ Server Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Add GitHub Secrets:" -ForegroundColor Yellow
Write-Host "   - SERVER_HOST: $ServerIP" -ForegroundColor White
Write-Host "   - SERVER_USER: $ServerUser" -ForegroundColor White
Write-Host "   - SSH_PRIVATE_KEY: Content of $SSHKeyPath" -ForegroundColor White
Write-Host ""
Write-Host "2. View private key:" -ForegroundColor Yellow
Write-Host "   Get-Content $SSHKeyPath" -ForegroundColor White
Write-Host ""
Write-Host "3. Push to GitHub to trigger deployment:" -ForegroundColor Yellow
Write-Host "   git add ." -ForegroundColor White
Write-Host "   git commit -m 'Configure production deployment'" -ForegroundColor White
Write-Host "   git push origin main" -ForegroundColor White
Write-Host ""
Write-Host "Server is ready for automated deployments! 🚀" -ForegroundColor Green
Write-Host ""
