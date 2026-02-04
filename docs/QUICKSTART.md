# 🚀 Quick Start - Ubuntu Deployment

> Get Alkana Dashboard running on Ubuntu server in under 30 minutes

## Prerequisites

- Ubuntu 20.04/22.04 server with root access
- Domain name pointed to your server IP
- GitHub repository access

---

## Step 1: Server Setup (5 minutes)

SSH into your server and run:

```bash
# Clone repository
git clone https://github.com/your-org/alkana-dashboard.git
cd alkana-dashboard

# Make scripts executable
chmod +x deployment/*.sh

# Run automated setup
sudo ./deployment/setup-server.sh
```

✅ This installs Docker, creates deploy user, configures firewall

---

## Step 2: SSH Keys (2 minutes)

```bash
# Switch to deploy user
su - deploy

# Generate SSH key
ssh-keygen -t ed25519 -C "deploy@alkana-server"

# Display public key
cat ~/.ssh/id_ed25519.pub
```

**Add this key to GitHub:**
- Go to GitHub repo → Settings → Deploy keys → Add deploy key
- Paste the public key

---

## Step 3: GitHub Secrets (5 minutes)

Add these secrets in GitHub:
**Settings → Secrets and variables → Actions**

```
SERVER_HOST=your.server.ip
SERVER_USER=deploy
SSH_PRIVATE_KEY=<content of ~/.ssh/id_ed25519>
DB_PASSWORD=SecurePassword123
DB_NAME=alkana_dashboard
DB_USER=alkana_user
```

To get private key:
```bash
cat ~/.ssh/id_ed25519
```

---

## Step 4: SSL Setup (5 minutes)

```bash
# Run SSL setup
sudo ./deployment/setup-ssl.sh dashboard.alkana.com your@email.com
```

Update domain in `nginx/nginx.prod.conf`:
```nginx
server_name dashboard.alkana.com;
```

---

## Step 5: Environment Configuration (3 minutes)

```bash
cd ~/alkana-dashboard

# Create production environment file
cp .env.production.example .env.production

# Edit with your values
nano .env.production
```

Update these values:
- `DB_PASSWORD` - Use a strong password
- `ALLOWED_ORIGINS` - Your domain URL
- `DOMAIN` - Your domain name

---

## Step 6: Deploy (10 minutes)

### Option A: Automatic (Recommended)

```bash
# Commit and push from local machine
git add .
git commit -m "Configure production deployment"
git push origin main
```

GitHub Actions will automatically deploy!

### Option B: Manual

```bash
# On server
./deployment/deploy.sh
```

---

## Step 7: Initialize Database (2 minutes)

```bash
# Enter backend container
docker compose -f docker-compose.prod.yml exec backend bash

# Initialize database schema
python -m src.main init

# Load sample data (optional)
python -m src.main load

# Transform data
python -m src.main transform

# Exit
exit
```

---

## Verify Deployment ✅

Check these URLs:

- Frontend: `https://dashboard.alkana.com`
- Health: `https://dashboard.alkana.com/health`
- API: `https://dashboard.alkana.com/api/health`
- API Docs: `https://dashboard.alkana.com/api/docs`

Check services:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
```

---

## Setup Automated Tasks

### Daily Backups

```bash
crontab -e
# Add:
0 2 * * * /home/deploy/alkana-dashboard/deployment/backup-database.sh
```

### Health Monitoring

```bash
crontab -e
# Add:
*/5 * * * * /home/deploy/alkana-dashboard/deployment/health-check.sh
```

---

## Common Commands

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart services
docker compose -f docker-compose.prod.yml restart

# Update application
cd ~/alkana-dashboard
git pull origin main
./deployment/deploy.sh

# Backup database
./deployment/backup-database.sh

# Check health
./deployment/health-check.sh
```

---

## Troubleshooting

**Service won't start:**
```bash
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml ps
```

**SSL issues:**
```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

**Port conflicts:**
```bash
sudo lsof -i :80
sudo lsof -i :443
```

---

## Next Steps

- [ ] Setup monitoring alerts
- [ ] Configure automated backups
- [ ] Review security settings
- [ ] Test disaster recovery
- [ ] Setup staging environment

---

For detailed documentation, see:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Complete deployment guide
- [README.md](../README.md) - Project overview
- [Deployment Plan](../plans/2026-02-04-ubuntu-deployment/plan.md)

---

**Need Help?**
- Check service logs
- Review nginx configuration
- Verify environment variables
- Test database connection

🎉 **You're all set!**
