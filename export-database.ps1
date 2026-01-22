# Export Database from Development Machine (PowerShell)
# Usage: .\export-database.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================"  -ForegroundColor Green
Write-Host "Export Database from Development"  -ForegroundColor Green
Write-Host "========================================`n"  -ForegroundColor Green

# Configuration
$BackupDir = ".\database-exports"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "alkana_db_$Timestamp.sql.gz"
$BackupPath = Join-Path $BackupDir $BackupFile

# Create backup directory
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

Write-Host "Checking database connection method..." -ForegroundColor Yellow

# Check if using Docker Compose
$dockerRunning = $false
try {
    $containerStatus = docker compose ps postgres 2>$null
    if ($LASTEXITCODE -eq 0) {
        $dockerRunning = $true
        Write-Host "✓ Using Docker Compose" -ForegroundColor Green
    }
} catch {
    # Docker not available
}

if ($dockerRunning) {
    Write-Host "`nExporting database from Docker container..." -ForegroundColor Yellow
    
    # Export from Docker and compress
    docker compose exec -T postgres pg_dump -U postgres alkana_dashboard | gzip > $BackupPath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Export failed!" -ForegroundColor Red
        exit 1
    }
    
} else {
    Write-Host "✓ Using local PostgreSQL" -ForegroundColor Green
    
    # Check if pg_dump is available
    $pgDump = Get-Command pg_dump -ErrorAction SilentlyContinue
    if (!$pgDump) {
        Write-Host "`n✗ pg_dump not found!" -ForegroundColor Red
        Write-Host "Please install PostgreSQL client tools or use Docker" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "`nExporting database from local PostgreSQL..." -ForegroundColor Yellow
    
    # Set password environment variable
    $env:PGPASSWORD = "password123"
    
    # Export from local PostgreSQL
    pg_dump -h localhost -U postgres -d alkana_dashboard | gzip > $BackupPath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Export failed!" -ForegroundColor Red
        exit 1
    }
    
    # Clear password
    Remove-Item env:PGPASSWORD
}

# Get file size
$FileSize = (Get-Item $BackupPath).Length
$FileSizeMB = [math]::Round($FileSize / 1MB, 2)

Write-Host "`n✓ Database exported successfully!" -ForegroundColor Green
Write-Host "  File: $BackupPath" -ForegroundColor White
Write-Host "  Size: $FileSizeMB MB" -ForegroundColor White

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Transfer to production server:" -ForegroundColor White
Write-Host "     scp $BackupPath user@production-server:/tmp/" -ForegroundColor Cyan
Write-Host ""
Write-Host "     Or use WinSCP/FileZilla to upload to server:/tmp/" -ForegroundColor Cyan
Write-Host "`n  2. On production server, run:" -ForegroundColor White
Write-Host "     cd /opt/alkana-dashboard" -ForegroundColor Cyan
Write-Host "     sudo ./import-database.sh /tmp/$BackupFile" -ForegroundColor Cyan

Write-Host "`n✓ Export completed!" -ForegroundColor Green
Write-Host ""
