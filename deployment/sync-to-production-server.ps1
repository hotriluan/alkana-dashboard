# PowerShell Script: Complete Database and Code Sync to Production Server
# Target: Ubuntu server at 192.168.18.35 (username: it, password: it123)
# 
# This script will:
# 1. Export local database
# 2. Push code to GitHub
# 3. SSH to server, truncate database
# 4. Import database dump
# 5. Pull latest code from GitHub
# 6. Restart services

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = "192.168.18.35",
    
    [Parameter(Mandatory=$false)]
    [string]$SshUser = "it",
    
    [Parameter(Mandatory=$false)]
    [string]$SshPassword = "it123",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipConfirm
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Step {
    param([string]$Message)
    Write-Host "`n==========================================`n$Message`n==========================================" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

Write-Step "Alkana Dashboard - Production Sync"
Write-Host "Source: Local development database"
Write-Host "Target: $SshUser@$ServerIP"
Write-Host ""

if (-not $SkipConfirm) {
    $confirm = Read-Host "This will replace the production database and sync code. Continue? (yes/no)"
    if ($confirm -ne "yes") {
        Write-Error "Operation cancelled"
        exit 0
    }
}

# ======================================
# STEP 1: Export Local Database
# ======================================
Write-Step "Step 1/6: Exporting Local Database"

# Load .env file
if (Test-Path ".env") {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}

$DbName = if ($env:DB_NAME) { $env:DB_NAME } else { "alkana_dashboard" }
$DbUser = if ($env:DB_USER) { $env:DB_USER } else { "postgres" }
$DbHost = if ($env:DB_HOST) { $env:DB_HOST } else { "localhost" }
$DbPort = if ($env:DB_PORT) { $env:DB_PORT } else { "5432" }
$DbPassword = $env:DB_PASSWORD

$ExportDir = ".\database-exports"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ExportFile = "$ExportDir\alkana-db-export-$Timestamp.sql"

# Create export directory
New-Item -ItemType Directory -Force -Path $ExportDir | Out-Null

Write-Host "Database: $DbName @ ${DbHost}:${DbPort}"

# Check if Docker is being used
$dockerRunning = docker compose ps 2>$null | Select-String "postgres"

if ($dockerRunning) {
    Write-Success "Found PostgreSQL in Docker"
    docker compose exec -T postgres pg_dump -U $DbUser $DbName > $ExportFile
    if ($LASTEXITCODE -ne 0) { throw "Docker pg_dump failed" }
} else {
    Write-Warning "Using local pg_dump (not Docker)"
    
    if (-not (Get-Command "pg_dump" -ErrorAction SilentlyContinue)) {
        Write-Error "pg_dump not found. Please install PostgreSQL client tools or use Docker."
        exit 1
    }
    
    $env:PGPASSWORD = $DbPassword
    & pg_dump -h $DbHost -U $DbUser -d $DbName --clean --if-exists --no-owner --no-acl > $ExportFile
    if ($LASTEXITCODE -ne 0) { throw "pg_dump failed" }
    Remove-Item Env:\PGPASSWORD
}

# Compress the export
Write-Host "🗜️  Compressing export..."
if (Get-Command "gzip" -ErrorAction SilentlyContinue) {
    & gzip -f $ExportFile
    $ExportFile = "$ExportFile.gz"
} elseif (Get-Command "7z" -ErrorAction SilentlyContinue) {
    & 7z a -tgzip "$ExportFile.gz" $ExportFile -sdel | Out-Null
    $ExportFile = "$ExportFile.gz"
} else {
    Write-Warning "Neither gzip nor 7-Zip found, using PowerShell compression"
    Compress-Archive -Path $ExportFile -DestinationPath "$ExportFile.zip" -Force
    Remove-Item $ExportFile
    $ExportFile = "$ExportFile.zip"
}

$ExportSize = (Get-Item $ExportFile).Length / 1MB
Write-Success "Export created: $(Split-Path $ExportFile -Leaf) ($([math]::Round($ExportSize, 2)) MB)"

# ======================================
# STEP 2: Push Code to GitHub
# ======================================
Write-Step "Step 2/6: Pushing Code to GitHub"

$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "Found uncommitted changes:"
    git status --short
    Write-Host ""
    
    if (-not $SkipConfirm) {
        $commitMsg = Read-Host "Enter commit message (or press Enter to skip commit)"
        if ($commitMsg) {
            git add -A
            git commit -m $commitMsg
            Write-Success "Changes committed"
        }
    }
}

Write-Host "Pushing to GitHub..."
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Git push failed or nothing to push"
} else {
    Write-Success "Code pushed to GitHub"
}

# ======================================
# STEP 3: Transfer Database to Server
# ======================================
Write-Step "Step 3/6: Transferring Database to Server"

# Check if plink/pscp is available for SSH (Windows)
$hasPlink = Get-Command "plink" -ErrorAction SilentlyContinue
$hasPscp = Get-Command "pscp" -ErrorAction SilentlyContinue

if (-not $hasPscp) {
    Write-Warning "PuTTY tools (pscp) not found. Trying scp..."
    $hasScp = Get-Command "scp" -ErrorAction SilentlyContinue
    
    if (-not $hasScp) {
        Write-Error "Neither pscp nor scp found. Please install PuTTY or OpenSSH."
        exit 1
    }
    
    # Using OpenSSH scp
    Write-Host "Creating remote directory..."
    $sshCmd = "mkdir -p ~/alkana-dashboard/database-exports && echo 'Directory created'"
    ssh ${SshUser}@${ServerIP} $sshCmd
    
    Write-Host "Uploading $(Split-Path $ExportFile -Leaf)..."
    scp $ExportFile "${SshUser}@${ServerIP}:~/alkana-dashboard/database-exports/"
    
} else {
    # Using PuTTY tools
    Write-Host "Creating remote directory..."
    echo "mkdir -p ~/alkana-dashboard/database-exports && echo 'Directory created'" | plink -ssh -pw $SshPassword ${SshUser}@${ServerIP}
    
    Write-Host "Uploading $(Split-Path $ExportFile -Leaf)..."
    pscp -pw $SshPassword $ExportFile "${SshUser}@${ServerIP}:~/alkana-dashboard/database-exports/"
}

if ($LASTEXITCODE -ne 0) { throw "File transfer failed" }
Write-Success "Database dump transferred to server"

# ======================================
# STEP 4: Truncate and Import Database
# ======================================
Write-Step "Step 4/6: Truncating and Importing Database on Server"

$remoteDbFile = "~/alkana-dashboard/database-exports/$(Split-Path $ExportFile -Leaf)"

# Multi-line SSH command to execute on server
$sshCommands = @"
set -e
cd ~/alkana-dashboard

# Load production environment
if [ -f .env.production ]; then
    export \$(cat .env.production | grep -v '^#' | xargs)
else
    echo '⚠️  .env.production not found, using defaults'
    export DB_NAME=alkana_dashboard
    export DB_USER=alkana_user
fi

echo '🛑 Stopping backend service...'
docker compose -f docker-compose.prod.yml stop backend || echo 'Backend not running'

echo '🗑️  Dropping existing database...'
docker compose -f docker-compose.prod.yml exec -T postgres psql -U \$DB_USER -d postgres -c "DROP DATABASE IF EXISTS \$DB_NAME;" || true

echo '🏗️  Creating fresh database...'
docker compose -f docker-compose.prod.yml exec -T postgres psql -U \$DB_USER -d postgres -c "CREATE DATABASE \$DB_NAME OWNER \$DB_USER;"

echo '📥 Importing database dump...'
if [[ "$remoteDbFile" == *.gz ]]; then
    gunzip -c $remoteDbFile | docker compose -f docker-compose.prod.yml exec -T postgres psql -U \$DB_USER -d \$DB_NAME
elif [[ "$remoteDbFile" == *.zip ]]; then
    unzip -p $remoteDbFile | docker compose -f docker-compose.prod.yml exec -T postgres psql -U \$DB_USER -d \$DB_NAME
else
    cat $remoteDbFile | docker compose -f docker-compose.prod.yml exec -T postgres psql -U \$DB_USER -d \$DB_NAME
fi

echo '✅ Database import completed!'
"@

if ($hasPlink) {
    $sshCommands | plink -ssh -pw $SshPassword ${SshUser}@${ServerIP}
} else {
    $sshCommands | ssh ${SshUser}@${ServerIP}
}

if ($LASTEXITCODE -ne 0) { throw "Database import failed" }
Write-Success "Database imported successfully"

# ======================================
# STEP 5: Pull Latest Code from GitHub
# ======================================
Write-Step "Step 5/6: Pulling Latest Code from GitHub"

$gitPullCommands = @"
set -e
cd ~/alkana-dashboard

echo '📥 Pulling latest code from GitHub...'
git fetch origin
git reset --hard origin/main

echo '✅ Code updated!'
"@

if ($hasPlink) {
    $gitPullCommands | plink -ssh -pw $SshPassword ${SshUser}@${ServerIP}
} else {
    $gitPullCommands | ssh ${SshUser}@${ServerIP}
}

if ($LASTEXITCODE -ne 0) { 
    Write-Warning "Git pull encountered issues, but continuing..."
}
Write-Success "Code synced from GitHub"

# ======================================
# STEP 6: Restart Services
# ======================================
Write-Step "Step 6/6: Restarting Services"

$restartCommands = @"
set -e
cd ~/alkana-dashboard

echo '🔄 Rebuilding and restarting services...'
docker compose -f docker-compose.prod.yml up -d --build

echo '⏳ Waiting for services to start...'
sleep 15

echo '🔍 Checking service status...'
docker compose -f docker-compose.prod.yml ps

echo '✅ Services restarted!'
"@

if ($hasPlink) {
    $restartCommands | plink -ssh -pw $SshPassword ${SshUser}@${ServerIP}
} else {
    $restartCommands | ssh ${SshUser}@${ServerIP}
}

if ($LASTEXITCODE -ne 0) { throw "Service restart failed" }
Write-Success "Services restarted successfully"

# ======================================
# COMPLETION
# ======================================
Write-Step "🎉 Deployment Completed Successfully!"

Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  ✅ Database exported and imported"
Write-Host "  ✅ Code synced via GitHub"
Write-Host "  ✅ Services restarted"
Write-Host ""
Write-Host "Access your application at:" -ForegroundColor Cyan
Write-Host "  🌐 http://$ServerIP:3000 (Frontend)"
Write-Host "  🔧 http://$ServerIP:8000/docs (API)"
Write-Host ""
Write-Host "To verify:" -ForegroundColor Yellow
Write-Host "  ssh ${SshUser}@${ServerIP}"
Write-Host "  cd ~/alkana-dashboard"
Write-Host "  docker compose -f docker-compose.prod.yml logs -f"
Write-Host ""
