# PowerShell Script: Database-Only Sync to Production Server
# Target: Configure server connection via parameters or environment variables
# 
# This script will:
# 1. Export local database
# 2. Transfer to server
# 3. Truncate (drop/recreate) database on server
# 4. Import database dump

param(
    [Parameter(Mandatory=$false)]
    [string]$ServerIP = $env:SERVER_HOST,
    
    [Parameter(Mandatory=$false)]
    [string]$SshUser = $env:SERVER_USER,
    
    [Parameter(Mandatory=$false)]
    [string]$SshPassword = $env:SERVER_PASSWORD,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipConfirm
)

$ErrorActionPreference = "Stop"

# Colors
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

Write-Step "Database-Only Sync to Production"
Write-Host "Source: Local development database"
Write-Host "Target: $SshUser@$ServerIP"
Write-Host ""

if (-not $SkipConfirm) {
    $confirm = Read-Host "This will REPLACE the production database. Continue? (yes/no)"
    if ($confirm -ne "yes") {
        Write-Error "Operation cancelled"
        exit 0
    }
}

# ======================================
# STEP 1: Export Local Database
# ======================================
Write-Step "Step 1/3: Exporting Local Database"

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
    if ($LASTEXITCODE -ne 0) { 
        Write-Error "Docker pg_dump failed"
        exit 1
    }
} else {
    Write-Warning "Using local pg_dump (not Docker)"
    
    if (-not (Get-Command "pg_dump" -ErrorAction SilentlyContinue)) {
        Write-Error "pg_dump not found. Please install PostgreSQL client tools or use Docker."
        exit 1
    }
    
    $env:PGPASSWORD = $DbPassword
    & pg_dump -h $DbHost -U $DbUser -d $DbName --clean --if-exists --no-owner --no-acl > $ExportFile
    if ($LASTEXITCODE -ne 0) { 
        Write-Error "pg_dump failed"
        Remove-Item Env:\PGPASSWORD
        exit 1
    }
    Remove-Item Env:\PGPASSWORD
}

# Compress the export
Write-Host "🗜️  Compressing export..."
if (Get-Command "gzip" -ErrorAction SilentlyContinue) {
    & gzip -f $ExportFile
    $ExportFile = "$ExportFile.gz"
} else {
    Write-Warning "gzip not found, skipping compression (will transfer .sql file)"
    # Keep as .sql file for faster processing
}

$ExportSize = (Get-Item $ExportFile).Length / 1MB
Write-Success "Export created: $(Split-Path $ExportFile -Leaf) ($([math]::Round($ExportSize, 2)) MB)"

# ======================================
# STEP 2: Transfer Database to Server
# ======================================
Write-Step "Step 2/3: Transferring Database to Server"

# Check for SSH tools
$hasPlink = Get-Command "plink" -ErrorAction SilentlyContinue
$hasPscp = Get-Command "pscp" -ErrorAction SilentlyContinue
$hasSsh = Get-Command "ssh" -ErrorAction SilentlyContinue
$hasScp = Get-Command "scp" -ErrorAction SilentlyContinue

$createDirCmd = "mkdir -p /opt/alkana-dashboard/database-exports 2>/dev/null; echo 'OK'"

if ($hasSsh -and $hasScp) {
    # Using OpenSSH (preferred)
    Write-Host "Creating remote directory..."
    $result = ssh -o StrictHostKeyChecking=no ${SshUser}@${ServerIP} $createDirCmd 2>&1
    if ($result -match "OK") {
        Write-Success "Remote directory ready"
    }
    
    Write-Host "Uploading $(Split-Path $ExportFile -Leaf)... (this may take a few minutes)"
    scp -o StrictHostKeyChecking=no $ExportFile "${SshUser}@${ServerIP}:/opt/alkana-dashboard/database-exports/"
    
    if ($LASTEXITCODE -ne 0) { 
        Write-Error "File transfer failed"
        exit 1
    }
} elseif ($hasPlink -and $hasPscp) {
    # Using PuTTY tools
    Write-Host "Creating remote directory..."
    $result = echo $createDirCmd | plink -ssh -batch -pw $SshPassword ${SshUser}@${ServerIP} 2>&1
    if ($result -match "OK") {
        Write-Success "Remote directory ready"
    }
    
    Write-Host "Uploading $(Split-Path $ExportFile -Leaf)... (this may take a few minutes)"
    pscp -batch -pw $SshPassword $ExportFile "${SshUser}@${ServerIP}:/opt/alkana-dashboard/database-exports/"
    
    if ($LASTEXITCODE -ne 0) { 
        Write-Error "File transfer failed"
        exit 1
    }
} else {
    Write-Error "No SSH tools found. Please install OpenSSH or PuTTY."
    exit 1
}

Write-Success "Database dump transferred to server"

# ======================================
# STEP 3: Import Database on Server
# ======================================
Write-Step "Step 3/3: Truncating and Importing Database"

$remoteDbFile = "/opt/alkana-dashboard/database-exports/$(Split-Path $ExportFile -Leaf)"

# Create a temporary bash script locally
$bashScript = @'
#!/bin/bash
set -e
cd /opt/alkana-dashboard

# Load production environment
if [ -f .env ]; then
    source .env
    echo "✅ Loaded .env"
else
    echo "⚠️  .env not found, using defaults"
    export DB_NAME=alkana_dashboard
    export DB_USER=postgres
    export DB_PASSWORD=password
fi

echo "🛑 Stopping backend service..."
docker compose stop backend 2>/dev/null || echo "Backend not running"

echo "🗑️  Dropping existing database..."
docker compose exec -T postgres psql -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null || true

echo "🏗️  Creating fresh database..."
docker compose exec -T postgres psql -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

echo "📥 Importing database dump..."
REMOTE_FILE="##REMOTE_FILE##"
if [[ "$REMOTE_FILE" == *.gz ]]; then
    gunzip -c $REMOTE_FILE | docker compose exec -T postgres psql -U $DB_USER -d $DB_NAME
else
    cat $REMOTE_FILE | docker compose exec -T postgres psql -U $DB_USER -d $DB_NAME
fi

echo "🚀 Restarting backend service..."
docker compose start backend

echo "⏳ Waiting for backend..."
sleep 10

echo "🔍 Verifying database..."
TABLE_COUNT=$(docker compose exec -T postgres psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema');")
echo "✅ Database has $TABLE_COUNT tables"

echo "✅ Database import completed!"
'@

# Replace placeholder with actual remote file path
$bashScript = $bashScript -replace '##REMOTE_FILE##', $remoteDbFile

# Save to temp file with LF line endings
$tempScriptPath = "$env:TEMP\import-db-$(Get-Date -Format 'yyyyMMddHHmmss').sh"
$bashScript -replace "`r`n", "`n" | Out-File -FilePath $tempScriptPath -Encoding ascii -NoNewline

# Transfer script to server
Write-Host "Transferring import script to server..."
if ($hasScp) {
    scp -o StrictHostKeyChecking=no $tempScriptPath "${SshUser}@${ServerIP}:/tmp/import-db.sh"
} elseif ($hasPscp) {
    pscp -batch -pw $SshPassword $tempScriptPath "${SshUser}@${ServerIP}:/tmp/import-db.sh"
}

# Make it executable and run it
Write-Host "Running database import on server..."
$remoteCommands = "chmod +x /tmp/import-db.sh && echo '$SshPassword' | sudo -S bash /tmp/import-db.sh && rm /tmp/import-db.sh"

if ($hasSsh) {
    ssh -o StrictHostKeyChecking=no ${SshUser}@${ServerIP} $remoteCommands
} elseif ($hasPlink) {
    echo $remoteCommands | plink -ssh -batch -pw $SshPassword ${SshUser}@${ServerIP}
} else {
    Write-Error "No SSH client found"
    Remove-Item $tempScriptPath -Force
    exit 1
}

# Clean up temp file
Remove-Item $tempScriptPath -Force

if ($LASTEXITCODE -ne 0) { 
    Write-Error "Database import failed on server"
    exit 1
}

Write-Success "Database imported successfully"

# ======================================
# COMPLETION
# ======================================
Write-Step "🎉 Database Sync Completed!"

Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  ✅ Local database exported"
Write-Host "  ✅ Transferred to server"
Write-Host "  ✅ Production database replaced"
Write-Host "  ✅ Backend service restarted"
Write-Host ""
Write-Host "Access your application at:" -ForegroundColor Cyan
Write-Host "  🌐 Frontend: http://$ServerIP:3000"
Write-Host "  🔧 API Docs: http://$ServerIP:8000/docs"
Write-Host ""
Write-Host "To verify database:" -ForegroundColor Yellow
Write-Host "  ssh ${SshUser}@${ServerIP}"
Write-Host "  cd /opt/alkana-dashboard"
Write-Host "  docker compose exec postgres psql -U postgres -d alkana_dashboard"
Write-Host ""
