"""
Remote Database Backup via SSH for Phase 3
Connects to production server and creates backup
Uses plink/pscp (PuTTY) for auto-password on Windows
"""
import subprocess
import os
from datetime import datetime
import shutil

# Production server details
PROD_SERVER = "192.168.18.35"
PROD_USER = "it"
PROD_PASSWORD = "it123"

# Database details
DB_NAME = "alkana_dashboard"
DB_USER = "alkana_user"
DB_PASSWORD = "Alkana2026SecureDB!"

# Timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_filename = f"alkana_dashboard_phase03_{timestamp}.dump"

# Use container's mounted backup volume: /backups (container) -> /home/it/alkana-dashboard/backups (host)
remote_backup_path_container = f"/backups/{backup_filename}"
remote_backup_path_host = f"/home/it/alkana-dashboard/backups/{backup_filename}"
local_backup_path = f"backups/phase-03-data-inflation/{backup_filename}"

print(f"🔒 Creating remote database backup...")
print(f"Server: {PROD_USER}@{PROD_SERVER}")
print(f"Database: {DB_NAME}")
print()

# Ensure local directory exists
os.makedirs("backups/phase-03-data-inflation", exist_ok=True)

# Check if plink is available
plink_path = shutil.which("plink")
pscp_path = shutil.which("pscp")

if not plink_path:
    print("⚠️  plink not found!")
    print("Install PuTTY for auto-password: winget install PuTTY.PuTTY")
    print("Or use SSH keys for better security")
    exit(1)

# Step 1: Create backup on remote server (using PostgreSQL in Docker container)
print("Step 1: Creating backup on production server...")
# PostgreSQL runs in Docker container 'alkana-postgres'
# Write to /backups (container) which is mounted to /home/it/alkana-dashboard/backups (host)
ssh_backup_cmd = f"docker exec -e PGPASSWORD='{DB_PASSWORD}' alkana-postgres pg_dump -h localhost -U {DB_USER} -d {DB_NAME} -F c -f {remote_backup_path_container} && echo 'Backup size:' && ls -lh {remote_backup_path_host}"

try:
    print("Using plink (PuTTY) for SSH with auto-password...")
    result = subprocess.run(
        ["plink", "-batch", "-pw", PROD_PASSWORD, f"{PROD_USER}@{PROD_SERVER}", ssh_backup_cmd],
        capture_output=True,
        text=True,
        timeout=180
    )
    
    if result.returncode != 0:
        print(f"❌ Remote backup failed!")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        print()
        print("⚠️  Possible issues:")
        print("  1. Wrong password/username")
        print("  2. pg_dump not installed on server")
        print("  3. Database not accessible")
        exit(1)
    
    print("Backup command output:")
    print(result.stdout)
    if result.stderr:
        print("Warnings:")
        print(result.stderr)
    print("✅ Remote backup created")
    print()
    
    # Step 2: Download backup to local
    print(f"Step 2: Downloading backup to {local_backup_path}...")
    
    if pscp_path:
        print("Using pscp (PuTTY) for download with auto-password...")
        scp_result = subprocess.run(
            ["pscp", "-batch", "-pw", PROD_PASSWORD, 
             f"{PROD_USER}@{PROD_SERVER}:{remote_backup_path_host}", 
             local_backup_path],
            capture_output=True,
            text=True,
            timeout=300
        )
    else:
        print("pscp not found, using scp (will prompt for password)...")
        scp_result = subprocess.run(
            ["scp", f"{PROD_USER}@{PROD_SERVER}:{remote_backup_path_host}", local_backup_path],
            capture_output=True,
            text=True,
            timeout=300
        )
    
    if scp_result.returncode != 0:
        print(f"❌ Download failed!")
        print(f"Error: {scp_result.stderr}")
        print()
        print(f"⚠️  Backup exists on server: {remote_backup_path_host}")
        print("   Download manually with:")
        print(f"   pscp -pw {PROD_PASSWORD} {PROD_USER}@{PROD_SERVER}:{remote_backup_path_host} {local_backup_path}")
        exit(1)
    
    # Check local file size
    file_size_mb = os.path.getsize(local_backup_path) / (1024 * 1024)
    
    print(f"✅ Backup downloaded successfully!")
    print(f"Local file: {local_backup_path}")
    print(f"Size: {file_size_mb:.2f} MB")
    print()
    
    # Step 3: Clean up remote backup
    print("Step 3: Cleaning up remote backup...")
    cleanup_result = subprocess.run(
        ["plink", "-batch", "-pw", PROD_PASSWORD, 
         f"{PROD_USER}@{PROD_SERVER}", 
         f"rm {remote_backup_path_host}"],
        capture_output=True,
        timeout=30
    )
    
    if cleanup_result.returncode == 0:
        print("✅ Remote backup cleaned up")
    else:
        print(f"⚠️  Could not clean remote backup: {cleanup_result.stderr}")
    
    print()
    print("📋 To restore if needed:")
    print(f"  pscp -pw {PROD_PASSWORD} {local_backup_path} {PROD_USER}@{PROD_SERVER}:/tmp/restore.dump")
    print(f"  plink -pw {PROD_PASSWORD} {PROD_USER}@{PROD_SERVER} 'pg_restore -U {DB_USER} -d {DB_NAME} --clean /tmp/restore.dump'")
    print()
    print("🚀 SAFE TO PROCEED with Phase 3 implementation")
    
except subprocess.TimeoutExpired:
    print("❌ Command timed out!")
    print("Database might be too large or network is slow")
    exit(1)
except FileNotFoundError as e:
    print(f"❌ Tool not found: {e}")
    print("Ensure plink and pscp are installed")
    exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
