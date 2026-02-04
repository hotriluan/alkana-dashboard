# Deployment Scripts

Automated deployment tools for Alkana Dashboard to production server.

## Quick Start

### One-Click Automated Deployment

**Windows:**
```powershell
.\deployment\one-click-deploy.ps1
```

**Linux/Mac/Git Bash:**
```bash
chmod +x deployment/one-click-deploy.sh
bash deployment/one-click-deploy.sh
```

This will automatically:
- Setup server (Docker, dependencies)
- Configure environment
- Export & import database
- Deploy application
- Setup monitoring

**Time:** ~10-15 minutes

## Configuration

Edit `server-config.env` before deployment:

```bash
SERVER_IP=192.168.68.166       # Your server IP
SERVER_USER=alkana              # SSH username
SERVER_PASSWORD=alkana123       # SSH password
PROD_DB_PASSWORD=<secure-pass> # Database password
```

## Scripts Overview

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `one-click-deploy.sh` | Full automated deployment | First deployment |
| `one-click-deploy.ps1` | Windows version | First deployment (Windows) |
| `setup-server.sh` | Initialize server | Run on fresh server |
| `deploy.sh` | Manual deployment | Code updates |
| `migrate-database.sh` | Database migration | Migrate local DB |
| `export-local-database.sh` | Export local DB | Before migration |
| `import-database.sh` | Import DB to server | On server |
| `backup-database.sh` | Backup database | Manual backups |
| `health-check.sh` | Check services | Monitoring |
| `setup-ssl.sh` | Configure SSL | If you have domain |

## Manual Deployment Steps

If you prefer manual control:

### 1. Server Setup
```bash
scp deployment/setup-server.sh user@server:/tmp/
ssh user@server "sudo bash /tmp/setup-server.sh"
```

### 2. Deploy Code
```bash
ssh user@server
cd ~/alkana-dashboard
git clone <your-repo>
bash deployment/deploy.sh
```

### 3. Migrate Database
```bash
# Local machine
bash deployment/migrate-database.sh SERVER_IP
```

## GitHub Actions

Automated deployment on push to `main` branch.

### Setup:
1. Add secrets to GitHub repo:
   - `SERVER_PASSWORD`: SSH password
   - `DB_PASSWORD`: Database password

2. Push code:
```bash
git push origin main
```

GitHub Actions will automatically deploy.

## Access

After deployment:
- **Frontend:** http://192.168.68.166
- **API Docs:** http://192.168.68.166/api/docs
- **Health:** http://192.168.68.166/health

Default login:
- Username: `admin`
- Password: `admin123` (change immediately!)

## Monitoring

Automated tasks:
- **Backups:** Daily at 2 AM
- **Health Checks:** Every 5 minutes

View logs:
```bash
ssh alkana@192.168.68.166
cd ~/alkana-dashboard
docker compose -f docker-compose.prod.yml logs -f
```

## Troubleshooting

### Connection Issues
```bash
# Test SSH
ssh alkana@192.168.68.166

# Check if server is accessible
ping 192.168.68.166
```

### Services Not Running
```bash
ssh alkana@192.168.68.166
cd ~/alkana-dashboard
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs
docker compose -f docker-compose.prod.yml restart
```

### Database Issues
```bash
# Check database logs
docker compose -f docker-compose.prod.yml logs postgres

# Access database
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U alkana_user -d alkana_dashboard
```

## Documentation

- [DEPLOY-AUTO.md](../DEPLOY-AUTO.md) - Quick deployment guide
- [DEPLOYMENT.md](../docs/DEPLOYMENT.md) - Full deployment guide
- [DATABASE-MIGRATION.md](../docs/DATABASE-MIGRATION.md) - Database migration details

## Requirements

- SSH access to server
- Docker installed (auto-installed by setup script)
- Git installed
- sshpass (Linux/Mac) or PuTTY (Windows)

## Support

For issues, check:
1. Script output for error messages
2. Server logs: `docker compose logs`
3. Documentation in `docs/`
