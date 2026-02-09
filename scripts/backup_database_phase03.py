"""
Database Backup Script for Phase 3 Data Inflation Fix
Must run BEFORE making any schema changes
"""
import os
import subprocess
from datetime import datetime
from pathlib import Path

# Create backups directory if not exists
backup_dir = Path("backups/phase-03-data-inflation")
backup_dir.mkdir(parents=True, exist_ok=True)

# Timestamp for backup file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = backup_dir / f"alkana_dashboard_phase03_{timestamp}.dump"

# Database connection from environment
db_host = os.getenv("DB_HOST", "192.168.18.35")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "alkana_dashboard")
db_user = os.getenv("DB_USER", "alkana_user")

print(f"🔒 Creating database backup...")
print(f"Database: {db_user}@{db_host}:{db_port}/{db_name}")
print(f"Backup file: {backup_file}")
print()

# pg_dump command
cmd = [
    "pg_dump",
    f"--host={db_host}",
    f"--port={db_port}",
    f"--username={db_user}",
    f"--dbname={db_name}",
    "--format=custom",
    "--verbose",
    f"--file={backup_file}"
]

try:
    # Run pg_dump
    result = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PGPASSWORD": os.getenv("DB_PASSWORD", "Alkana2026SecureDB!")}
    )
    
    # Check file size
    file_size_mb = backup_file.stat().st_size / (1024 * 1024)
    
    print(f"✅ Backup created successfully!")
    print(f"File: {backup_file}")
    print(f"Size: {file_size_mb:.2f} MB")
    print()
    print("📋 To restore if needed:")
    print(f"pg_restore --host={db_host} --port={db_port} --username={db_user} --dbname={db_name} --clean {backup_file}")
    print()
    print("🚀 Safe to proceed with Phase 3 implementation")
    
except subprocess.CalledProcessError as e:
    print(f"❌ Backup failed!")
    print(f"Error: {e.stderr}")
    print()
    print("⚠️  DO NOT PROCEED with Phase 3 without backup!")
    exit(1)
except FileNotFoundError:
    print("❌ pg_dump not found!")
    print("Install PostgreSQL client tools:")
    print("  Windows: Download from postgresql.org")
    print("  Linux: sudo apt-get install postgresql-client")
    print("  Mac: brew install postgresql")
    exit(1)
