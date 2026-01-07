# Deployment Guide

This guide covers deploying the Alkana Dashboard to production environments.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Deployment Methods](#deployment-methods)
- [Database Setup](#database-setup)
- [Post-Deployment Tasks](#post-deployment-tasks)
- [Monitoring & Health Checks](#monitoring--health-checks)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **Server**: Linux (Ubuntu 20.04+ recommended) or Windows Server
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: 20GB+ for application and data
- **Network**: HTTPS (443), HTTP (80) for web traffic

### Software Dependencies
- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **PostgreSQL**: 15 or higher
- **Docker** (optional): 24.0+ with Docker Compose v2

### Access Requirements
- PostgreSQL admin credentials
- SAP data export files (Excel format)
- SSL certificate (for HTTPS in production)

## Environment Configuration

### 1. Backend Environment Variables

Create `.env` file in project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@host:5432/alkana_dashboard
DB_HOST=your-db-host.example.com
DB_PORT=5432
DB_NAME=alkana_dashboard
DB_USER=alkana_user
DB_PASSWORD=<strong-password-here>

# Data Paths
DEMODATA_PATH=/var/lib/alkana/demodata

# Alert Thresholds
STUCK_IN_TRANSIT_HOURS=48
LOW_YIELD_THRESHOLD=85

# Security
SECRET_KEY=<generate-with: openssl rand -hex 32>
JWT_SECRET_KEY=<generate-with: openssl rand -hex 32>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# CORS Origins (comma-separated)
CORS_ORIGINS=https://dashboard.yourcompany.com,https://www.yourcompany.com

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### 2. Frontend Environment Variables

Create `web/.env.production`:

```bash
VITE_API_URL=https://api.dashboard.yourcompany.com
VITE_APP_TITLE=Alkana Dashboard
VITE_ENVIRONMENT=production
```

### 3. Security Checklist

- [ ] Generate unique `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Use strong database passwords (16+ characters, mixed case, special chars)
- [ ] Never commit `.env` files to version control
- [ ] Restrict database access to application server IP only
- [ ] Enable SSL/TLS for database connections
- [ ] Configure CORS to allow only trusted domains
- [ ] Set up firewall rules (allow only 80/443)

## Deployment Methods

### Method 1: Docker Deployment (Recommended)

#### Step 1: Build Docker Images

```bash
# Build backend image
docker build -t alkana-backend:latest -f Dockerfile.backend .

# Build frontend image
docker build -t alkana-frontend:latest -f Dockerfile.frontend ./web
```

#### Step 2: Configure Docker Compose

Update `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: alkana-postgres
    environment:
      POSTGRES_DB: alkana_dashboard
      POSTGRES_USER: alkana_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  backend:
    image: alkana-backend:latest
    container_name: alkana-backend
    env_file: .env
    depends_on:
      - postgres
    volumes:
      - ./demodata:/app/demodata
      - backend_logs:/app/logs
    ports:
      - "8000:8000"
    restart: unless-stopped
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000

  frontend:
    image: alkana-frontend:latest
    container_name: alkana-frontend
    depends_on:
      - backend
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    restart: unless-stopped

volumes:
  postgres_data:
  backend_logs:
```

#### Step 3: Deploy

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### Method 2: Manual Deployment

#### Backend Deployment

```bash
# 1. Clone repository
git clone <repository-url> /opt/alkana-dashboard
cd /opt/alkana-dashboard

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env  # Edit with production values

# 5. Initialize database (see Database Setup section)
python -m src.main init

# 6. Start with systemd (recommended)
sudo cp deployment/alkana-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable alkana-backend
sudo systemctl start alkana-backend
```

**Create `deployment/alkana-backend.service`:**

```ini
[Unit]
Description=Alkana Dashboard Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=alkana
Group=alkana
WorkingDirectory=/opt/alkana-dashboard
Environment="PATH=/opt/alkana-dashboard/venv/bin"
ExecStart=/opt/alkana-dashboard/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Frontend Deployment

```bash
# 1. Navigate to frontend
cd /opt/alkana-dashboard/web

# 2. Install dependencies
npm ci --production

# 3. Build for production
npm run build

# 4. Deploy build artifacts
# Option A: Nginx
sudo cp -r dist/* /var/www/alkana-dashboard/
sudo chown -R www-data:www-data /var/www/alkana-dashboard

# Option B: Serve with Node.js
npm install -g serve
serve -s dist -l 3000
```

**Nginx Configuration (`/etc/nginx/sites-available/alkana`):**

```nginx
server {
    listen 80;
    server_name dashboard.yourcompany.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dashboard.yourcompany.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    root /var/www/alkana-dashboard;
    index index.html;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/alkana /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Database Setup

### 1. Create Production Database

```sql
-- Connect as postgres superuser
psql -U postgres

-- Create database and user
CREATE DATABASE alkana_dashboard;
CREATE USER alkana_user WITH ENCRYPTED PASSWORD 'your-secure-password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE alkana_dashboard TO alkana_user;

-- Connect to database
\c alkana_dashboard

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO alkana_user;
```

### 2. Initialize Schema

```bash
# Run migrations
python -m src.main init

# Verify tables created
psql -U alkana_user -d alkana_dashboard -c "\dt"
```

### 3. Load Initial Data

```bash
# Place SAP Excel exports in demodata/ folder
mkdir -p /var/lib/alkana/demodata
cp /path/to/sap-exports/*.xlsx /var/lib/alkana/demodata/

# Load raw data
python -m src.main load

# Transform to warehouse
python -m src.main transform

# Verify data loaded
python -m src.main verify
```

### 4. Database Backup Configuration

Create automated backup script (`/opt/alkana/backup-db.sh`):

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/alkana"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="alkana_dashboard_${DATE}.sql.gz"

mkdir -p $BACKUP_DIR
pg_dump -U alkana_user alkana_dashboard | gzip > "$BACKUP_DIR/$FILENAME"

# Keep last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /opt/alkana/backup-db.sh
```

## Post-Deployment Tasks

### 1. Create Admin User

```bash
# Access Python shell
cd /opt/alkana-dashboard
source venv/bin/activate
python

# Create admin user
from src.db.database import SessionLocal
from src.db.auth_models import User
from src.core.auth import get_password_hash

db = SessionLocal()
admin = User(
    username="admin",
    email="admin@yourcompany.com",
    hashed_password=get_password_hash("change-this-password"),
    role="admin",
    is_active=True
)
db.add(admin)
db.commit()
print(f"Admin user created: {admin.username}")
db.close()
```

### 2. Verify API Health

```bash
# Check backend health
curl http://localhost:8000/api/health

# Expected response:
# {"status":"healthy","database":"connected","version":"1.0.0"}
```

### 3. Test End-to-End Flow

1. **Login**: Navigate to `https://dashboard.yourcompany.com`
2. **Authenticate**: Login with admin credentials
3. **Check Dashboards**: Verify all 9 dashboard modules load
4. **Test Data**: Verify KPIs display correctly
5. **Check Alerts**: Navigate to Alert Monitor

### 4. Configure Data Refresh Schedule

Set up cron job for daily data refresh:

```bash
# Add to crontab
crontab -e

# Daily ETL at 6 AM
0 6 * * * cd /opt/alkana-dashboard && /opt/alkana-dashboard/venv/bin/python -m src.main load && /opt/alkana-dashboard/venv/bin/python -m src.main transform
```

## Monitoring & Health Checks

### Health Endpoints

- **API Health**: `GET /api/health`
- **Database Status**: `GET /api/health/db`
- **ETL Status**: `GET /api/health/etl`

### Log Locations

- **Backend**: `/opt/alkana-dashboard/logs/app.log`
- **Nginx**: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- **PostgreSQL**: `/var/log/postgresql/postgresql-15-main.log`
- **Docker**: `docker-compose logs <service>`

### Monitoring Checklist

```bash
# Check service status
sudo systemctl status alkana-backend
sudo systemctl status nginx
sudo systemctl status postgresql

# Check disk space
df -h

# Check memory usage
free -m

# Check database connections
psql -U alkana_user -d alkana_dashboard -c "SELECT count(*) FROM pg_stat_activity;"

# Check API response time
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/health
```

**Create `curl-format.txt`:**
```
time_namelookup:  %{time_namelookup}\n
time_connect:  %{time_connect}\n
time_starttransfer:  %{time_starttransfer}\n
time_total:  %{time_total}\n
```

### Performance Metrics

Monitor these key metrics:
- **API Response Time**: < 200ms for most endpoints
- **Database Connections**: < 80% of max_connections
- **Memory Usage**: < 70% of available RAM
- **Disk I/O**: Monitor for sustained high writes
- **Error Rate**: < 1% of total requests

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u alkana-backend -n 50

# Common issues:
# 1. Database not accessible
psql -U alkana_user -d alkana_dashboard -h localhost

# 2. Port already in use
sudo lsof -i :8000

# 3. Permission issues
sudo chown -R alkana:alkana /opt/alkana-dashboard
```

### Database Connection Failed

```bash
# Test connection
psql postgresql://alkana_user:password@localhost:5432/alkana_dashboard

# Check PostgreSQL status
sudo systemctl status postgresql

# Review pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf
# Add: host alkana_dashboard alkana_user 127.0.0.1/32 md5
sudo systemctl reload postgresql
```

### Frontend 404 Errors

```bash
# Check Nginx configuration
sudo nginx -t

# Ensure SPA routing configured
# In nginx.conf: try_files $uri $uri/ /index.html;

# Check build artifacts
ls -la /var/www/alkana-dashboard/
# Should contain index.html, assets/, etc.
```

### High Memory Usage

```bash
# Check PostgreSQL memory
# Edit postgresql.conf
sudo nano /etc/postgresql/15/main/postgresql.conf

# Adjust:
shared_buffers = 256MB  # 25% of RAM
work_mem = 4MB
maintenance_work_mem = 64MB

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### ETL Job Failures

```bash
# Check ETL logs
tail -f /opt/alkana-dashboard/logs/etl.log

# Manual ETL run
cd /opt/alkana-dashboard
source venv/bin/activate
python -m src.main load --verbose
python -m src.main transform --verbose

# Verify data files
ls -lh demodata/
# Should contain: MB51.xlsx, ZRSD002.xlsx, etc.
```

## Rollback Procedure

If deployment fails:

```bash
# 1. Stop services
docker-compose down
# OR
sudo systemctl stop alkana-backend nginx

# 2. Restore database backup
gunzip < /var/backups/alkana/alkana_dashboard_20251229_020000.sql.gz | psql -U alkana_user alkana_dashboard

# 3. Revert to previous version
cd /opt/alkana-dashboard
git checkout <previous-version-tag>

# 4. Rebuild and restart
pip install -r requirements.txt
cd web && npm ci && npm run build
sudo systemctl start alkana-backend nginx
```

## Production Checklist

Before going live:

- [ ] All environment variables configured
- [ ] Strong passwords and secrets generated
- [ ] Database backups configured and tested
- [ ] SSL certificate installed and valid
- [ ] CORS origins restricted to production domains
- [ ] Admin user created
- [ ] All health checks passing
- [ ] Data loaded and verified
- [ ] Monitoring alerts configured
- [ ] Firewall rules applied
- [ ] DNS records pointing to server
- [ ] Documentation updated with production URLs
- [ ] Team trained on accessing dashboards
- [ ] Rollback procedure tested

## Support

For deployment issues:
1. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
2. Review application logs
3. Contact DevOps team: devops@yourcompany.com
