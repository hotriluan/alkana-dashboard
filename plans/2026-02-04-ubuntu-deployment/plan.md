# Ubuntu Server Deployment Plan - Alkana Dashboard
**Date:** 2026-02-04  
**Status:** Planning  
**Type:** Production Deployment  

## Executive Summary

Deploy Alkana Dashboard (FastAPI + React) to Ubuntu server with Docker, Nginx reverse proxy, SSL/HTTPS, and GitHub Actions CI/CD. Strategy: containerized deployment with automated pipelines, monitoring, and rollback capabilities.

**Deployment Approach:** Docker Compose orchestration with Nginx reverse proxy

**Timeline:** 5-7 business days  
**Risk Level:** Medium  
**Dependencies:** GitHub repo access, Ubuntu 20.04/22.04 server, domain name

---

## Phase 1: Server Preparation & Dependencies

### 1.1 Server Requirements
**Minimum Specifications:**
- Ubuntu 20.04 LTS or 22.04 LTS
- 4 CPU cores (8 recommended)
- 8GB RAM minimum (16GB recommended)
- 50GB SSD storage (100GB recommended)
- Public IPv4 address
- Domain name (e.g., `dashboard.alkana.com`)

### 1.2 Initial Server Setup

**Connect to server:**
```bash
ssh root@your-server-ip
```

**Update system packages:**
```bash
apt update && apt upgrade -y
apt install -y curl wget git vim ufw fail2ban
```

**Create non-root user:**
```bash
adduser deploy
usermod -aG sudo deploy
su - deploy
```

### 1.3 Install Docker & Docker Compose

**Install Docker:**
```bash
# Remove old versions
sudo apt-get remove docker docker-engine docker.io containerd runc

# Install dependencies
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker deploy
newgrp docker

# Verify installation
docker --version
docker compose version
```

**Configure Docker daemon:**
```bash
sudo nano /etc/docker/daemon.json
```

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
```

```bash
sudo systemctl restart docker
sudo systemctl enable docker
```

### 1.4 Firewall Configuration

```bash
# Enable UFW
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

### 1.5 Install Additional Tools

```bash
# PostgreSQL client (for backups/debugging)
sudo apt install -y postgresql-client

# Monitoring tools
sudo apt install -y htop ncdu

# SSL certificate tool
sudo apt install -y certbot python3-certbot-nginx
```

**Validation Checklist:**
- [ ] Docker running: `docker ps`
- [ ] Docker Compose available: `docker compose version`
- [ ] Firewall configured: `sudo ufw status`
- [ ] User in docker group: `groups deploy`

---

## Phase 2: GitHub Repository Setup & Secrets

### 2.1 Repository Configuration

**Add server SSH key to GitHub:**
```bash
# On server, generate SSH key
ssh-keygen -t ed25519 -C "deploy@alkana-server"
cat ~/.ssh/id_ed25519.pub
# Copy and add to GitHub: Settings → Deploy keys
```

**Clone repository:**
```bash
cd /home/deploy
git clone git@github.com:your-org/alkana-dashboard.git
cd alkana-dashboard
```

### 2.2 GitHub Secrets Setup

Navigate to GitHub repo → Settings → Secrets and variables → Actions

**Add the following secrets:**

| Secret Name | Description | Example |
|------------|-------------|---------|
| `SERVER_HOST` | Server IP or domain | `165.232.123.45` |
| `SERVER_USER` | SSH user | `deploy` |
| `SSH_PRIVATE_KEY` | Deploy user's private key | `-----BEGIN OPENSSH...` |
| `DB_PASSWORD` | PostgreSQL password | `securePass123!` |
| `DB_NAME` | Database name | `alkana_dashboard` |
| `DB_USER` | Database user | `alkana_user` |
| `DOCKER_HUB_USERNAME` | (Optional) For image cache | `youruser` |
| `DOCKER_HUB_TOKEN` | (Optional) For image cache | `dckr_pat_...` |

**Get SSH private key:**
```bash
cat ~/.ssh/id_ed25519
# Copy entire output including BEGIN/END lines
```

### 2.3 Environment Variables Template

Create `.env.production` template (don't commit):
```bash
# Database Configuration
DATABASE_URL=postgresql://alkana_user:${DB_PASSWORD}@postgres:5432/alkana_dashboard
DB_HOST=postgres
DB_PORT=5432
DB_NAME=alkana_dashboard
DB_USER=alkana_user
DB_PASSWORD=${DB_PASSWORD}

# Application Settings
ENVIRONMENT=production
DEBUG=false
API_BASE_URL=https://dashboard.alkana.com/api

# Data Paths
DEMODATA_PATH=/app/demodata

# Alert Thresholds
STUCK_IN_TRANSIT_HOURS=48
LOW_YIELD_THRESHOLD=85

# CORS Origins
ALLOWED_ORIGINS=https://dashboard.alkana.com
```

**Validation Checklist:**
- [ ] Repository cloned successfully
- [ ] All GitHub secrets configured
- [ ] SSH deploy key added to GitHub
- [ ] `.env.production` template created

---

## Phase 3: Docker Containerization

### 3.1 Review Current Dockerfiles

**Current setup is production-ready:**
- ✅ `Dockerfile.backend` - Python/FastAPI with health checks
- ✅ `Dockerfile.frontend` - Multi-stage build with Nginx
- ✅ `docker-compose.yml` - Orchestrates all services
- ✅ `nginx.conf` - Reverse proxy configured

### 3.2 Production Docker Compose Enhancements

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: alkana-postgres
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_INITDB_ARGS: "-E UTF8 --locale=C"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - alkana-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: alkana-backend
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DEMODATA_PATH=/app/demodata
      - ENVIRONMENT=production
      - DEBUG=false
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./demodata:/app/demodata:ro
      - backend_logs:/app/logs
      - ./backups:/app/backups
    restart: unless-stopped
    networks:
      - alkana-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/api/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
      args:
        - VITE_API_URL=/api
    container_name: alkana-frontend
    depends_on:
      backend:
        condition: service_healthy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
    restart: unless-stopped
    networks:
      - alkana-network
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://127.0.0.1/ || exit 1"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  alkana-network:
    driver: bridge

volumes:
  postgres_data:
    driver: local
  backend_logs:
    driver: local
```

### 3.3 Dockerfile Optimization

**Update `Dockerfile.backend` for production:**
```dockerfile
# Multi-stage build for smaller image
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy system dependencies from base
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser src/ ./src/

# Create directories
RUN mkdir -p logs demodata backups && \
    chown -R appuser:appuser logs demodata backups

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Use gunicorn for production
CMD ["gunicorn", "src.api.main:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

**Update `requirements.txt`:**
```txt
# Add gunicorn for production
gunicorn==21.2.0
```

**Update `Dockerfile.frontend`:**
```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

COPY web/package*.json ./
RUN npm ci --only=production

COPY web/ ./

# Build with production env
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Stage 2: Production
FROM nginx:1.25-alpine

# Install security updates
RUN apk --no-cache upgrade

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

EXPOSE 80 443

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

**Validation Checklist:**
- [ ] `docker-compose.prod.yml` created
- [ ] Dockerfiles optimized for production
- [ ] Health checks configured
- [ ] Logging configured
- [ ] Non-root users in containers

---

## Phase 4: Nginx Reverse Proxy Configuration

### 4.1 Production Nginx Configuration

Create `nginx/nginx.prod.conf`:
```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 2048;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;
    client_body_timeout 60s;
    client_header_timeout 60s;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_comp_level 6;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_types 
        text/plain 
        text/css 
        text/xml 
        text/javascript 
        application/x-javascript 
        application/xml+rss 
        application/javascript 
        application/json
        image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload_limit:10m rate=2r/s;

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name dashboard.alkana.com;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$server_name$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name dashboard.alkana.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:50m;
        ssl_session_tickets off;

        # Modern SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
        ssl_prefer_server_ciphers off;

        # OCSP stapling
        ssl_stapling on;
        ssl_stapling_verify on;

        root /usr/share/nginx/html;
        index index.html;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;" always;

        # Frontend routes (SPA)
        location / {
            try_files $uri $uri/ /index.html;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires "0";
        }

        # Static assets with long cache
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # API proxy to backend
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://backend:8000/api/;
            proxy_http_version 1.1;
            
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
            proxy_send_timeout 300s;
            
            # Don't cache API responses
            add_header Cache-Control "no-store, no-cache, must-revalidate";
        }

        # Upload endpoint with stricter rate limiting
        location /api/upload {
            limit_req zone=upload_limit burst=5 nodelay;
            
            client_max_body_size 100M;
            
            proxy_pass http://backend:8000/api/upload;
            proxy_http_version 1.1;
            
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_read_timeout 600s;
            proxy_connect_timeout 75s;
            proxy_send_timeout 600s;
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

**Validation Checklist:**
- [ ] Production nginx config created
- [ ] SSL placeholders configured
- [ ] Rate limiting configured
- [ ] Security headers configured
- [ ] Gzip compression enabled

---

## Phase 5: SSL/HTTPS with Let's Encrypt

### 5.1 DNS Configuration

**Point domain to server:**
```
A Record: dashboard.alkana.com → YOUR_SERVER_IP
```

**Verify DNS propagation:**
```bash
dig dashboard.alkana.com +short
nslookup dashboard.alkana.com
```

### 5.2 Initial SSL Certificate (Manual Method)

**Install Certbot:**
```bash
sudo apt install -y certbot
```

**Create directories:**
```bash
mkdir -p /home/deploy/alkana-dashboard/nginx/ssl
```

**Obtain certificate (standalone mode):**
```bash
sudo certbot certonly --standalone \
    --preferred-challenges http \
    -d dashboard.alkana.com \
    --agree-tos \
    --email admin@alkana.com \
    --non-interactive

# Copy certificates
sudo cp /etc/letsencrypt/live/dashboard.alkana.com/fullchain.pem \
    /home/deploy/alkana-dashboard/nginx/ssl/
sudo cp /etc/letsencrypt/live/dashboard.alkana.com/privkey.pem \
    /home/deploy/alkana-dashboard/nginx/ssl/
sudo chown -R deploy:deploy /home/deploy/alkana-dashboard/nginx/ssl/
sudo chmod 600 /home/deploy/alkana-dashboard/nginx/ssl/privkey.pem
```

### 5.3 Automated Renewal with Certbot

**Create renewal script:**
```bash
sudo nano /home/deploy/renew-cert.sh
```

```bash
#!/bin/bash
# SSL Certificate Renewal Script

set -e

DOMAIN="dashboard.alkana.com"
APP_DIR="/home/deploy/alkana-dashboard"

echo "Renewing SSL certificate for $DOMAIN..."

# Renew certificate
certbot renew --quiet

# Copy renewed certificates
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $APP_DIR/nginx/ssl/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $APP_DIR/nginx/ssl/
chown -R deploy:deploy $APP_DIR/nginx/ssl/
chmod 600 $APP_DIR/nginx/ssl/privkey.pem

# Reload Nginx
cd $APP_DIR
docker compose -f docker-compose.prod.yml exec frontend nginx -s reload

echo "SSL certificate renewed and Nginx reloaded successfully!"
```

```bash
sudo chmod +x /home/deploy/renew-cert.sh
```

**Setup cron job for auto-renewal:**
```bash
sudo crontab -e
```

Add:
```cron
# Renew SSL certificate every 60 days at 3 AM
0 3 1 */2 * /home/deploy/renew-cert.sh >> /var/log/certbot-renewal.log 2>&1
```

### 5.4 Alternative: Docker-based Certbot (Recommended)

**Update `docker-compose.prod.yml`:**
```yaml
services:
  # ... existing services ...

  certbot:
    image: certbot/certbot:latest
    container_name: alkana-certbot
    volumes:
      - ./nginx/ssl:/etc/letsencrypt
      - ./nginx/certbot-webroot:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew --webroot -w /var/www/certbot; sleep 12h & wait $${!}; done;'"
    networks:
      - alkana-network
```

**Validation Checklist:**
- [ ] DNS points to server
- [ ] SSL certificate obtained
- [ ] Certificates copied to project
- [ ] Auto-renewal configured
- [ ] HTTPS accessible

---

## Phase 6: GitHub Actions CI/CD Pipeline

### 6.1 Workflow File

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main
  workflow_dispatch:

env:
  DEPLOY_PATH: /home/deploy/alkana-dashboard

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run backend tests
        run: |
          cd src
          pytest tests/ -v --cov --cov-report=term-missing

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install frontend dependencies
        run: |
          cd web
          npm ci

      - name: Run frontend tests
        run: |
          cd web
          npm run test -- --run

      - name: Build frontend
        run: |
          cd web
          npm run build

  deploy:
    name: Deploy to Ubuntu Server
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.9.0
        with:
          ssh-private-key: ${{ secrets.SSH_PRIVATE_KEY }}

      - name: Add server to known hosts
        run: |
          mkdir -p ~/.ssh
          ssh-keyscan -H ${{ secrets.SERVER_HOST }} >> ~/.ssh/known_hosts

      - name: Deploy to server
        env:
          SERVER_HOST: ${{ secrets.SERVER_HOST }}
          SERVER_USER: ${{ secrets.SERVER_USER }}
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
          DB_NAME: ${{ secrets.DB_NAME }}
          DB_USER: ${{ secrets.DB_USER }}
        run: |
          ssh $SERVER_USER@$SERVER_HOST << 'ENDSSH'
            set -e
            
            # Navigate to app directory
            cd ${{ env.DEPLOY_PATH }}
            
            # Pull latest code
            echo "Pulling latest code..."
            git pull origin main
            
            # Create .env file
            echo "Creating environment file..."
            cat > .env.production << EOF
          DATABASE_URL=postgresql://${{ secrets.DB_USER }}:${{ secrets.DB_PASSWORD }}@postgres:5432/${{ secrets.DB_NAME }}
          DB_HOST=postgres
          DB_PORT=5432
          DB_NAME=${{ secrets.DB_NAME }}
          DB_USER=${{ secrets.DB_USER }}
          DB_PASSWORD=${{ secrets.DB_PASSWORD }}
          ENVIRONMENT=production
          DEBUG=false
          DEMODATA_PATH=/app/demodata
          STUCK_IN_TRANSIT_HOURS=48
          LOW_YIELD_THRESHOLD=85
          ALLOWED_ORIGINS=https://dashboard.alkana.com
          EOF
            
            # Backup database
            echo "Creating database backup..."
            docker compose -f docker-compose.prod.yml exec -T postgres \
              pg_dump -U ${{ secrets.DB_USER }} ${{ secrets.DB_NAME }} | \
              gzip > ./backups/backup-$(date +%Y%m%d-%H%M%S).sql.gz
            
            # Pull latest images (if using registry)
            echo "Pulling Docker images..."
            docker compose -f docker-compose.prod.yml pull || true
            
            # Rebuild and restart services
            echo "Rebuilding services..."
            docker compose -f docker-compose.prod.yml build --no-cache
            
            echo "Restarting services..."
            docker compose -f docker-compose.prod.yml up -d --force-recreate
            
            # Wait for health checks
            echo "Waiting for services to be healthy..."
            sleep 30
            
            # Verify services
            docker compose -f docker-compose.prod.yml ps
            
            # Clean up old images
            echo "Cleaning up old Docker images..."
            docker image prune -f
            
            echo "Deployment completed successfully!"
          ENDSSH

      - name: Health check
        run: |
          sleep 10
          curl -f https://dashboard.alkana.com/health || exit 1
          curl -f https://dashboard.alkana.com/api/health || exit 1

      - name: Notify deployment status
        if: always()
        run: |
          if [ ${{ job.status }} == 'success' ]; then
            echo "✅ Deployment successful!"
          else
            echo "❌ Deployment failed!"
          fi

  rollback:
    name: Rollback on Failure
    runs-on: ubuntu-latest
    needs: deploy
    if: failure()

    steps:
      - name: Setup SSH
        uses: webfactory/ssh-agent@v0.9.0
        with:
          ssh-private-key: ${{ secrets.SSH_PRIVATE_KEY }}

      - name: Rollback deployment
        env:
          SERVER_HOST: ${{ secrets.SERVER_HOST }}
          SERVER_USER: ${{ secrets.SERVER_USER }}
        run: |
          ssh $SERVER_USER@$SERVER_HOST << 'ENDSSH'
            cd ${{ env.DEPLOY_PATH }}
            
            echo "Rolling back to previous version..."
            git reset --hard HEAD~1
            docker compose -f docker-compose.prod.yml up -d --force-recreate
            
            echo "Rollback completed"
          ENDSSH
```

### 6.2 Alternative: Simple Deployment Script

Create `scripts/deploy.sh`:
```bash
#!/bin/bash
# Simple deployment script for manual deployments

set -e

DEPLOY_USER="deploy"
SERVER_HOST="dashboard.alkana.com"
APP_DIR="/home/deploy/alkana-dashboard"

echo "🚀 Deploying Alkana Dashboard to production..."

# Test connection
echo "Testing SSH connection..."
ssh -o ConnectTimeout=10 $DEPLOY_USER@$SERVER_HOST "echo 'Connection successful'"

# Deploy
ssh $DEPLOY_USER@$SERVER_HOST << 'ENDSSH'
    set -e
    
    cd /home/deploy/alkana-dashboard
    
    # Pull latest
    echo "📥 Pulling latest code..."
    git pull origin main
    
    # Backup database
    echo "💾 Backing up database..."
    BACKUP_FILE="backup-$(date +%Y%m%d-%H%M%S).sql.gz"
    docker compose -f docker-compose.prod.yml exec -T postgres \
        pg_dump -U alkana_user alkana_dashboard | gzip > ./backups/$BACKUP_FILE
    echo "Database backed up to: $BACKUP_FILE"
    
    # Rebuild and restart
    echo "🔨 Rebuilding containers..."
    docker compose -f docker-compose.prod.yml build
    
    echo "🔄 Restarting services..."
    docker compose -f docker-compose.prod.yml up -d --force-recreate
    
    # Wait for health
    echo "⏳ Waiting for services..."
    sleep 30
    
    # Check status
    echo "📊 Service status:"
    docker compose -f docker-compose.prod.yml ps
    
    echo "✅ Deployment complete!"
ENDSSH

# Verify
echo "🔍 Running health checks..."
curl -f https://dashboard.alkana.com/health
curl -f https://dashboard.alkana.com/api/health

echo "🎉 Deployment successful!"
```

```bash
chmod +x scripts/deploy.sh
```

**Validation Checklist:**
- [ ] GitHub Actions workflow created
- [ ] All secrets configured in GitHub
- [ ] Deployment script tested
- [ ] Health checks working
- [ ] Rollback mechanism tested

---

## Phase 7: Database Initialization & Migration

### 7.1 Initial Database Setup

**Create initialization script:**
```bash
# scripts/init-database.sh
#!/bin/bash

set -e

APP_DIR="/home/deploy/alkana-dashboard"

echo "Initializing database..."

# Run init via backend container
docker compose -f $APP_DIR/docker-compose.prod.yml exec backend \
    python -m src.main init

echo "Database initialized successfully!"
```

### 7.2 Database Migration Strategy

**Create migration script:**
```bash
# scripts/migrate-database.sh
#!/bin/bash

set -e

APP_DIR="/home/deploy/alkana-dashboard"
BACKUP_DIR="$APP_DIR/backups"

# Backup before migration
BACKUP_FILE="$BACKUP_DIR/pre-migration-$(date +%Y%m%d-%H%M%S).sql.gz"
echo "Creating backup: $BACKUP_FILE"

docker compose -f $APP_DIR/docker-compose.prod.yml exec -T postgres \
    pg_dump -U alkana_user alkana_dashboard | gzip > $BACKUP_FILE

# Run migrations
echo "Running migrations..."
docker compose -f $APP_DIR/docker-compose.prod.yml exec backend \
    python -m src.db.migrate

echo "Migration completed successfully!"
```

### 7.3 Database Backup Strategy

**Create backup script:**
```bash
# scripts/backup-database.sh
#!/bin/bash

set -e

APP_DIR="/home/deploy/alkana-dashboard"
BACKUP_DIR="$APP_DIR/backups"
RETENTION_DAYS=30

# Create backup
BACKUP_FILE="$BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S).sql.gz"
echo "Creating backup: $BACKUP_FILE"

docker compose -f $APP_DIR/docker-compose.prod.yml exec -T postgres \
    pg_dump -U alkana_user alkana_dashboard | gzip > $BACKUP_FILE

# Remove old backups
find $BACKUP_DIR -name "backup-*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $BACKUP_FILE"
```

**Setup cron job:**
```bash
sudo crontab -e -u deploy
```

Add:
```cron
# Daily database backup at 2 AM
0 2 * * * /home/deploy/alkana-dashboard/scripts/backup-database.sh >> /var/log/alkana-backup.log 2>&1
```

### 7.4 Database Restore Procedure

**Create restore script:**
```bash
# scripts/restore-database.sh
#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Usage: ./restore-database.sh <backup-file.sql.gz>"
    echo "Available backups:"
    ls -lh /home/deploy/alkana-dashboard/backups/*.sql.gz
    exit 1
fi

BACKUP_FILE="$1"
APP_DIR="/home/deploy/alkana-dashboard"

echo "⚠️  WARNING: This will replace the current database!"
echo "Backup file: $BACKUP_FILE"
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

echo "Restoring database from: $BACKUP_FILE"

# Stop backend to prevent connections
docker compose -f $APP_DIR/docker-compose.prod.yml stop backend

# Drop and recreate database
docker compose -f $APP_DIR/docker-compose.prod.yml exec -T postgres psql -U alkana_user << EOF
DROP DATABASE IF EXISTS alkana_dashboard;
CREATE DATABASE alkana_dashboard;
EOF

# Restore data
gunzip -c $BACKUP_FILE | docker compose -f $APP_DIR/docker-compose.prod.yml exec -T postgres \
    psql -U alkana_user alkana_dashboard

# Restart backend
docker compose -f $APP_DIR/docker-compose.prod.yml start backend

echo "✅ Database restored successfully!"
```

```bash
chmod +x scripts/*.sh
```

**Validation Checklist:**
- [ ] Database initialization script created
- [ ] Migration strategy documented
- [ ] Backup automation configured
- [ ] Restore procedure tested
- [ ] Backup retention policy set

---

## Phase 8: Environment Configuration

### 8.1 Environment File Management

**Create environment template generator:**
```bash
# scripts/generate-env.sh
#!/bin/bash

cat > .env.production << EOF
# Database Configuration
DATABASE_URL=postgresql://\${DB_USER}:\${DB_PASSWORD}@postgres:5432/\${DB_NAME}
DB_HOST=postgres
DB_PORT=5432
DB_NAME=${DB_NAME:-alkana_dashboard}
DB_USER=${DB_USER:-alkana_user}
DB_PASSWORD=${DB_PASSWORD}

# Application Settings
ENVIRONMENT=production
DEBUG=false
API_BASE_URL=https://dashboard.alkana.com/api

# Data Paths
DEMODATA_PATH=/app/demodata

# Alert Thresholds
STUCK_IN_TRANSIT_HOURS=48
LOW_YIELD_THRESHOLD=85

# CORS Origins (comma-separated)
ALLOWED_ORIGINS=https://dashboard.alkana.com

# Session & Security
SECRET_KEY=$(openssl rand -hex 32)
SESSION_TIMEOUT=3600

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Performance
WORKERS=4
MAX_CONNECTIONS=100
EOF

echo "Environment file created: .env.production"
```

### 8.2 Secret Management

**Using Docker secrets (recommended):**
```yaml
# In docker-compose.prod.yml
services:
  backend:
    secrets:
      - db_password
      - secret_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  secret_key:
    file: ./secrets/secret_key.txt
```

**Create secrets directory:**
```bash
mkdir -p /home/deploy/alkana-dashboard/secrets
echo "your-secure-password" > secrets/db_password.txt
chmod 600 secrets/*.txt
```

### 8.3 Configuration Validation

**Create validation script:**
```bash
# scripts/validate-config.sh
#!/bin/bash

set -e

echo "Validating configuration..."

# Check environment file
if [ ! -f .env.production ]; then
    echo "❌ .env.production not found"
    exit 1
fi

# Check required variables
REQUIRED_VARS=(
    "DATABASE_URL"
    "DB_PASSWORD"
    "ALLOWED_ORIGINS"
)

source .env.production

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing required variable: $var"
        exit 1
    fi
done

# Check SSL certificates
if [ ! -f nginx/ssl/fullchain.pem ] || [ ! -f nginx/ssl/privkey.pem ]; then
    echo "❌ SSL certificates not found"
    exit 1
fi

# Check Docker
if ! docker compose -f docker-compose.prod.yml config > /dev/null 2>&1; then
    echo "❌ Invalid docker-compose configuration"
    exit 1
fi

echo "✅ Configuration valid!"
```

**Validation Checklist:**
- [ ] Environment variables configured
- [ ] Secrets properly secured (600 permissions)
- [ ] Configuration validation script created
- [ ] SSL certificates in place
- [ ] Docker Compose config valid

---

## Phase 9: Deployment Automation Scripts

### 9.1 Complete Deployment Script

Create `scripts/deploy-production.sh`:
```bash
#!/bin/bash
# Complete Production Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

APP_DIR="/home/deploy/alkana-dashboard"
BACKUP_DIR="$APP_DIR/backups"
LOG_FILE="/var/log/alkana-deploy.log"

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a $LOG_FILE
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a $LOG_FILE
}

# Pre-deployment checks
log "Starting pre-deployment checks..."

# Check Docker
if ! docker --version &> /dev/null; then
    error "Docker not installed"
    exit 1
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    warn "Disk usage is at ${DISK_USAGE}%"
fi

# Pull latest code
log "Pulling latest code from Git..."
cd $APP_DIR
git fetch origin
git pull origin main

# Backup database
log "Creating database backup..."
BACKUP_FILE="$BACKUP_DIR/pre-deploy-$(date +%Y%m%d-%H%M%S).sql.gz"
docker compose -f docker-compose.prod.yml exec -T postgres \
    pg_dump -U alkana_user alkana_dashboard | gzip > $BACKUP_FILE
log "Backup created: $BACKUP_FILE"

# Build new images
log "Building Docker images..."
docker compose -f docker-compose.prod.yml build --no-cache

# Stop services gracefully
log "Stopping services..."
docker compose -f docker-compose.prod.yml down

# Start services
log "Starting services..."
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
log "Waiting for services to become healthy..."
MAX_WAIT=120
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if docker compose -f docker-compose.prod.yml ps | grep -q "healthy"; then
        log "Services are healthy!"
        break
    fi
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    error "Services did not become healthy within $MAX_WAIT seconds"
    log "Rolling back..."
    docker compose -f docker-compose.prod.yml down
    docker compose -f docker-compose.prod.yml up -d
    exit 1
fi

# Run smoke tests
log "Running smoke tests..."
curl -f https://dashboard.alkana.com/health || {
    error "Frontend health check failed"
    exit 1
}

curl -f https://dashboard.alkana.com/api/health || {
    error "Backend health check failed"
    exit 1
}

# Clean up
log "Cleaning up old Docker images..."
docker image prune -f

log "Deployment completed successfully! 🎉"
```

### 9.2 Rollback Script

Create `scripts/rollback.sh`:
```bash
#!/bin/bash
# Rollback Script

set -e

APP_DIR="/home/deploy/alkana-dashboard"

echo "Available Git commits:"
git -C $APP_DIR log --oneline -n 10

read -p "Enter commit hash to rollback to: " COMMIT_HASH

if [ -z "$COMMIT_HASH" ]; then
    echo "No commit hash provided"
    exit 1
fi

echo "Rolling back to commit: $COMMIT_HASH"
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Rollback cancelled"
    exit 0
fi

cd $APP_DIR

# Checkout commit
git checkout $COMMIT_HASH

# Rebuild and restart
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

echo "Rollback completed"
```

### 9.3 Monitoring Script

Create `scripts/monitor.sh`:
```bash
#!/bin/bash
# Monitoring Script

APP_DIR="/home/deploy/alkana-dashboard"

echo "========================================="
echo "Alkana Dashboard System Status"
echo "========================================="
echo ""

# Docker containers status
echo "📦 Docker Containers:"
docker compose -f $APP_DIR/docker-compose.prod.yml ps
echo ""

# Resource usage
echo "💻 Resource Usage:"
echo "CPU:" $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)"%"
echo "Memory:" $(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2}')
echo "Disk:" $(df -h / | awk 'NR==2 {print $5}')
echo ""

# Database size
echo "🗄️  Database:"
docker compose -f $APP_DIR/docker-compose.prod.yml exec -T postgres \
    psql -U alkana_user alkana_dashboard -c "\l+" | grep alkana_dashboard
echo ""

# Recent logs
echo "📋 Recent Backend Logs (last 10 lines):"
docker compose -f $APP_DIR/docker-compose.prod.yml logs --tail=10 backend
echo ""

# Health checks
echo "🏥 Health Checks:"
curl -s https://dashboard.alkana.com/health && echo " ✅ Frontend OK" || echo " ❌ Frontend FAIL"
curl -s https://dashboard.alkana.com/api/health && echo " ✅ Backend OK" || echo " ❌ Backend FAIL"
```

```bash
chmod +x scripts/*.sh
```

**Validation Checklist:**
- [ ] Deployment script created and tested
- [ ] Rollback script created and tested
- [ ] Monitoring script created
- [ ] All scripts have execute permissions
- [ ] Scripts tested in staging environment

---

## Phase 10: Monitoring & Maintenance

### 10.1 Application Monitoring

**Install Prometheus & Grafana (Optional):**
```yaml
# Add to docker-compose.prod.yml
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: alkana-prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped
    networks:
      - alkana-network

  grafana:
    image: grafana/grafana:latest
    container_name: alkana-grafana
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=secure_password
    restart: unless-stopped
    networks:
      - alkana-network
    ports:
      - "3000:3000"

volumes:
  prometheus_data:
  grafana_data:
```

**Create `monitoring/prometheus.yml`:**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
```

### 10.2 Log Management

**Configure log rotation:**
```bash
sudo nano /etc/logrotate.d/alkana-dashboard
```

```
/home/deploy/alkana-dashboard/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 deploy deploy
    sharedscripts
}
```

**Centralized logging with Loki (Optional):**
```yaml
# Add to docker-compose.prod.yml
services:
  loki:
    image: grafana/loki:latest
    container_name: alkana-loki
    volumes:
      - ./monitoring/loki-config.yml:/etc/loki/local-config.yaml
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    restart: unless-stopped
    networks:
      - alkana-network

volumes:
  loki_data:
```

### 10.3 Alerts & Notifications

**Create alert script:**
```bash
# scripts/check-health.sh
#!/bin/bash

WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Check services
if ! curl -sf https://dashboard.alkana.com/health > /dev/null; then
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"🚨 Alkana Dashboard frontend is DOWN!"}' \
        $WEBHOOK_URL
fi

if ! curl -sf https://dashboard.alkana.com/api/health > /dev/null; then
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"🚨 Alkana Dashboard API is DOWN!"}' \
        $WEBHOOK_URL
fi
```

**Setup cron for health checks:**
```cron
# Check health every 5 minutes
*/5 * * * * /home/deploy/alkana-dashboard/scripts/check-health.sh
```

### 10.4 Maintenance Tasks

**Create maintenance checklist:**
```markdown
## Weekly Maintenance
- [ ] Review logs for errors
- [ ] Check disk usage
- [ ] Review database performance
- [ ] Check backup success

## Monthly Maintenance
- [ ] Update system packages: `sudo apt update && sudo apt upgrade`
- [ ] Update Docker images
- [ ] Review and clean old backups
- [ ] Security audit

## Quarterly Maintenance
- [ ] SSL certificate renewal check
- [ ] Performance optimization review
- [ ] Disaster recovery test
- [ ] Update documentation
```

**System update script:**
```bash
# scripts/system-update.sh
#!/bin/bash

set -e

echo "Updating system packages..."
sudo apt update
sudo apt upgrade -y

echo "Updating Docker images..."
cd /home/deploy/alkana-dashboard
docker compose -f docker-compose.prod.yml pull

echo "Restarting services with new images..."
docker compose -f docker-compose.prod.yml up -d

echo "Cleaning up..."
docker image prune -f
docker volume prune -f

echo "System update completed!"
```

**Validation Checklist:**
- [ ] Monitoring tools configured
- [ ] Log rotation setup
- [ ] Health check alerts configured
- [ ] Maintenance schedule created
- [ ] Update procedures documented

---

## Security Considerations

### 1. Server Hardening
```bash
# Disable root login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
# Set: PasswordAuthentication no
sudo systemctl restart sshd

# Configure fail2ban
sudo apt install fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 2. Database Security
- Use strong passwords (16+ characters)
- Database not exposed to external network
- Regular backups encrypted
- Connection pooling limits
- Query timeout limits

### 3. Application Security
- HTTPS only (HSTS enabled)
- Security headers configured
- Rate limiting enabled
- CORS properly configured
- File upload validation
- SQL injection protection (SQLAlchemy ORM)
- XSS protection headers

### 4. Container Security
- Non-root users in containers
- Read-only filesystem where possible
- Resource limits configured
- Regular image updates
- Vulnerability scanning

### 5. Access Control
- SSH key-based authentication only
- Separate deploy user with limited permissions
- GitHub deploy keys (read-only)
- Environment secrets not in Git
- Principle of least privilege

---

## Rollback Strategy

### Immediate Rollback (< 5 minutes)
```bash
# Method 1: Git-based rollback
cd /home/deploy/alkana-dashboard
git log --oneline -n 5  # Find last working commit
git checkout <commit-hash>
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Database Rollback
```bash
# List available backups
ls -lh /home/deploy/alkana-dashboard/backups/

# Restore from backup
./scripts/restore-database.sh backups/backup-YYYYMMDD-HHMMSS.sql.gz
```

### Full System Rollback
```bash
# Stop all services
docker compose -f docker-compose.prod.yml down

# Checkout last stable version
git checkout <stable-commit>

# Restore database
./scripts/restore-database.sh <backup-file>

# Rebuild and restart
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

---

## Troubleshooting Guide

### Issue: Containers won't start
```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Check resources
docker stats
df -h
free -m

# Restart Docker daemon
sudo systemctl restart docker
```

### Issue: Database connection failed
```bash
# Check database container
docker compose -f docker-compose.prod.yml exec postgres pg_isready

# Check credentials
docker compose -f docker-compose.prod.yml exec backend env | grep DB_

# Check network
docker network ls
docker network inspect alkana-network
```

### Issue: SSL certificate issues
```bash
# Check certificate validity
openssl x509 -in nginx/ssl/fullchain.pem -text -noout

# Renew certificate manually
sudo certbot renew --force-renewal

# Check Nginx config
docker compose -f docker-compose.prod.yml exec frontend nginx -t
```

### Issue: High memory usage
```bash
# Check container usage
docker stats

# Adjust worker count in docker-compose.prod.yml
# Restart specific service
docker compose -f docker-compose.prod.yml restart backend
```

### Issue: Deployment fails
```bash
# Check GitHub Actions logs
# Verify SSH connection
ssh deploy@dashboard.alkana.com "whoami"

# Check server disk space
ssh deploy@dashboard.alkana.com "df -h"

# Manual deployment
./scripts/deploy-production.sh
```

---

## Testing Checklist

### Pre-Deployment Testing
- [ ] Backend tests pass: `pytest src/tests/`
- [ ] Frontend tests pass: `npm run test`
- [ ] Build succeeds locally: `docker compose build`
- [ ] Environment variables validated
- [ ] Database migrations tested

### Post-Deployment Testing
- [ ] Frontend accessible: `https://dashboard.alkana.com`
- [ ] API responding: `https://dashboard.alkana.com/api/health`
- [ ] Database connected
- [ ] File upload working
- [ ] All dashboards loading
- [ ] SSL certificate valid
- [ ] Performance acceptable (< 2s page load)

### Security Testing
- [ ] HTTPS enforced (HTTP redirects)
- [ ] Security headers present
- [ ] Rate limiting working
- [ ] CORS configured correctly
- [ ] SQL injection prevention verified
- [ ] XSS protection verified

---

## Documentation & Knowledge Transfer

### Required Documentation
1. **Architecture Diagram**
   - System components
   - Network topology
   - Data flow

2. **Deployment Runbook**
   - Step-by-step deployment
   - Rollback procedures
   - Emergency contacts

3. **Monitoring Guide**
   - Key metrics
   - Alert thresholds
   - Incident response

4. **Maintenance Schedule**
   - Daily tasks
   - Weekly tasks
   - Monthly tasks

### Team Training
- Deploy procedure walkthrough
- Monitoring dashboard review
- Incident response drill
- Backup/restore practice

---

## Success Criteria

- [ ] Application accessible at `https://dashboard.alkana.com`
- [ ] HTTPS with valid SSL certificate
- [ ] All services healthy and running
- [ ] Database persistent across restarts
- [ ] Automated deployments via GitHub Actions
- [ ] Monitoring and alerting configured
- [ ] Backup automation working
- [ ] Rollback tested and working
- [ ] Documentation complete
- [ ] Team trained on deployment procedures

---

## Timeline & Milestones

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1: Server Setup | 0.5 days | Server configured, Docker installed |
| Phase 2: GitHub Setup | 0.5 days | Repository configured, secrets added |
| Phase 3: Containerization | 1 day | Production Dockerfiles ready |
| Phase 4: Nginx Config | 0.5 days | Reverse proxy configured |
| Phase 5: SSL Setup | 0.5 days | HTTPS working with Let's Encrypt |
| Phase 6: CI/CD Pipeline | 1 day | GitHub Actions working |
| Phase 7: Database Setup | 0.5 days | DB initialized, backups working |
| Phase 8: Environment Config | 0.5 days | All configs validated |
| Phase 9: Automation | 1 day | All scripts created and tested |
| Phase 10: Monitoring | 1 day | Monitoring and alerts configured |
| **Total** | **7 days** | **Full production deployment** |

---

## Next Steps

1. **Immediate (Day 1)**
   - Provision Ubuntu server
   - Configure DNS
   - Install Docker & dependencies

2. **Short-term (Days 2-3)**
   - Setup GitHub repository and secrets
   - Configure SSL certificates
   - Deploy initial version

3. **Mid-term (Days 4-5)**
   - Implement CI/CD pipeline
   - Configure monitoring
   - Setup backup automation

4. **Long-term (Days 6-7)**
   - Performance optimization
   - Security hardening
   - Documentation completion
   - Team training

---

## Appendix

### A. Useful Commands
```bash
# View all logs
docker compose -f docker-compose.prod.yml logs -f

# Restart specific service
docker compose -f docker-compose.prod.yml restart backend

# Access database
docker compose -f docker-compose.prod.yml exec postgres psql -U alkana_user alkana_dashboard

# View resource usage
docker stats

# Clean up system
docker system prune -a
```

### B. Important Files
- `/home/deploy/alkana-dashboard/` - Application root
- `/home/deploy/alkana-dashboard/.env.production` - Environment variables
- `/home/deploy/alkana-dashboard/backups/` - Database backups
- `/var/log/alkana-*.log` - Application logs
- `/etc/nginx/sites-available/` - Nginx configs

### C. Support Contacts
- Server provider support
- Domain registrar support
- Database administrator
- DevOps team lead

---

**Plan Status:** Ready for Implementation  
**Last Updated:** 2026-02-04  
**Review Date:** 2026-03-04
