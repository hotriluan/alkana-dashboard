# PowerShell Script for Database Migration (Windows)
# Exports local database and imports to production server

param(
    [Parameter(Mandatory=$true)]
    [string]$Server,
    
    [Parameter(Mandatory=$false)]
    [string]$SshUser = "deploy"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Automated Database Migration" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Source: Local development database"
Write-Host "Target: $SshUser@$Server"
Write-Host ""

$confirm = Read-Host "This will replace the production database. Continue? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "❌ Migration cancelled" -ForegroundColor Red
    exit 0
}

# Step 1: Export local database
Write-Host ""
Write-Host "Step 1/4: Exporting local database..." -ForegroundColor Yellow

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

Write-Host "Database: $DbName"
Write-Host "Host: ${DbHost}:${DbPort}"
Write-Host "User: $DbUser"
Write-Host ""

# Check if Docker is being used
$dockerRunning = docker compose ps 2>$null | Select-String "postgres"

if ($dockerRunning) {
    Write-Host "✅ Found PostgreSQL in Docker" -ForegroundColor Green
    docker compose exec -T postgres pg_dump -U $DbUser $DbName > $ExportFile
} else {
    Write-Host "📦 Exporting database using pg_dump..." -ForegroundColor Yellow
    
    # Set password environment variable
    $env:PGPASSWORD = $DbPassword
    
    # Export database
    & pg_dump -h $DbHost -U $DbUser -d $DbName --clean --if-exists --no-owner --no-acl > $ExportFile
    
    # Clear password from environment
    Remove-Item Env:\PGPASSWORD
}

# Compress the export
Write-Host "🗜️  Compressing export..." -ForegroundColor Yellow
if (Get-Command "7z" -ErrorAction SilentlyContinue) {
    & 7z a -tgzip "$ExportFile.gz" $ExportFile -sdel | Out-Null
    $ExportFile = "$ExportFile.gz"
} else {
    Write-Host "⚠️  7-Zip not found, using PowerShell compression..." -ForegroundColor Yellow
    Compress-Archive -Path $ExportFile -DestinationPath "$ExportFile.zip" -Force
    Remove-Item $ExportFile
    $ExportFile = "$ExportFile.zip"
}

$ExportSize = (Get-Item $ExportFile).Length / 1MB
Write-Host "✅ Export created: $ExportFile ($([math]::Round($ExportSize, 2)) MB)" -ForegroundColor Green

# Step 2: Transfer to server
Write-Host ""
Write-Host "Step 2/4: Transferring to server..." -ForegroundColor Yellow

# Create remote directory
ssh "$SshUser@$Server" "mkdir -p ~/alkana-dashboard/database-exports"

# Transfer file
Write-Host "Uploading $(Split-Path $ExportFile -Leaf)..."
scp $ExportFile "${SshUser}@${Server}:~/alkana-dashboard/database-exports/"

Write-Host "✅ Transfer completed" -ForegroundColor Green

# Step 3: Import on server
Write-Host ""
Write-Host "Step 3/4: Importing on server..." -ForegroundColor Yellow

$RemoteFile = "database-exports/$(Split-Path $ExportFile -Leaf)"
$RemoteFile = $RemoteFile -replace '\\', '/'

# Handle .zip vs .gz
if ($ExportFile -like "*.zip") {
    # For zip files, decompress on server first
    ssh "$SshUser@$Server" @"
        cd ~/alkana-dashboard
        unzip -o $RemoteFile -d database-exports/
        SQLFILE=`$(echo $RemoteFile | sed 's/.zip//')
        chmod +x deployment/import-database.sh
        echo 'yes' | ./deployment/import-database.sh `$SQLFILE
        rm `$SQLFILE
"@
} else {
    ssh "$SshUser@$Server" @"
        cd ~/alkana-dashboard
        chmod +x deployment/import-database.sh
        echo 'yes' | ./deployment/import-database.sh $RemoteFile
"@
}

Write-Host "✅ Import completed" -ForegroundColor Green

# Step 4: Verify
Write-Host ""
Write-Host "Step 4/4: Verifying deployment..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "https://$Server/api/health" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ API is healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  HTTPS health check failed, trying HTTP..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://$Server/api/health" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ API is responding on HTTP (HTTPS may not be configured yet)" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️  Warning: API is not responding" -ForegroundColor Yellow
        Write-Host "Check logs: ssh $SshUser@$Server 'cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml logs backend'"
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Migration completed!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Verify application: https://$Server"
Write-Host "2. Check logs: ssh $SshUser@$Server 'cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml logs -f'"
Write-Host "3. Test functionality"
Write-Host ""
Write-Host "Rollback if needed:" -ForegroundColor Yellow
Write-Host "  ssh $SshUser@$Server"
Write-Host "  cd ~/alkana-dashboard"
Write-Host "  ls -lh backups/pre-import-backup-*.sql.gz"
Write-Host "  ./deployment/import-database.sh backups/pre-import-backup-XXXXXX.sql.gz"
Write-Host ""
