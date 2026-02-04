# 🚀 Hướng dẫn Deploy Nhanh - Alkana Dashboard

## Tóm tắt Nhanh

Triển khai dự án lên Ubuntu server qua GitHub với database từ máy phát triển.

---

## Cách 1: Deploy Tự động (Khuyến nghị) ⚡

### Bước 1: Setup Server (5 phút)

```bash
# SSH vào server
ssh root@YOUR_SERVER_IP

# Clone repo và chạy setup
git clone https://github.com/your-org/alkana-dashboard.git
cd alkana-dashboard
chmod +x deployment/*.sh
sudo ./deployment/setup-server.sh
```

### Bước 2: Cấu hình GitHub (3 phút)

**Tạo SSH key trên server:**
```bash
su - deploy
ssh-keygen -t ed25519 -C "deploy@alkana"
cat ~/.ssh/id_ed25519.pub
```

**Thêm vào GitHub:**
- Repo → Settings → Deploy keys → Add deploy key (paste public key)

**Thêm GitHub Secrets:**
Settings → Secrets → Actions → New secret

```
SERVER_HOST=165.232.123.45
SERVER_USER=deploy
SSH_PRIVATE_KEY=<nội dung file ~/.ssh/id_ed25519>
DB_PASSWORD=SecurePassword123
DB_NAME=alkana_dashboard
DB_USER=alkana_user
```

### Bước 3: Setup SSL (5 phút)

```bash
sudo ./deployment/setup-ssl.sh dashboard.alkana.com your@email.com
```

Cập nhật domain trong `nginx/nginx.prod.conf`:
```nginx
server_name dashboard.alkana.com;
```

### Bước 4: Deploy Code (2 phút)

```bash
# Từ máy local
git add .
git commit -m "Setup production deployment"
git push origin main
```

GitHub Actions sẽ tự động deploy!

### Bước 5: Migrate Database (5 phút)

**Trên Windows:**
```powershell
.\deployment\migrate-database.ps1 -Server YOUR_SERVER_IP -SshUser deploy
```

**Trên Linux/Mac:**
```bash
chmod +x deployment/migrate-database.sh
./deployment/migrate-database.sh YOUR_SERVER_IP deploy
```

### ✅ Hoàn thành!

Truy cập: `https://dashboard.alkana.com`

---

## Cách 2: Deploy Thủ công (Backup plan) 🔧

### Bước 1-3: Giống như trên

### Bước 4: Deploy Manual

```bash
# SSH vào server
ssh deploy@YOUR_SERVER_IP
cd ~/alkana-dashboard

# Tạo file environment
cp .env.production.example .env.production
nano .env.production
# Cập nhật: DB_PASSWORD, ALLOWED_ORIGINS, DOMAIN

# Deploy
./deployment/deploy.sh
```

### Bước 5: Export & Import Database

**Export từ local:**
```bash
./deployment/export-local-database.sh
```

**Upload lên server:**
```bash
scp database-exports/*.sql.gz deploy@SERVER:/home/deploy/alkana-dashboard/database-exports/
```

**Import trên server:**
```bash
ssh deploy@SERVER
cd ~/alkana-dashboard
./deployment/import-database.sh database-exports/alkana-db-export-*.sql.gz
```

---

## Kiểm tra Deployment

```bash
# Health check
curl https://dashboard.alkana.com/health
curl https://dashboard.alkana.com/api/health

# Xem logs
docker compose -f docker-compose.prod.yml logs -f

# Check services
docker compose -f docker-compose.prod.yml ps
```

---

## Troubleshooting Nhanh

### Service không start
```bash
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml restart
```

### SSL lỗi
```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

### Database lỗi
```bash
docker compose -f docker-compose.prod.yml exec postgres psql -U alkana_user -d alkana_dashboard
```

### Rollback
```bash
cd ~/alkana-dashboard
git reset --hard HEAD~1
docker compose -f docker-compose.prod.yml up -d --build
```

---

## Scripts Chính

| Script | Công dụng |
|--------|-----------|
| `setup-server.sh` | Cài đặt server lần đầu |
| `setup-ssl.sh` | Cấu hình SSL/HTTPS |
| `deploy.sh` | Deploy manual |
| `migrate-database.sh/ps1` | Migrate database tự động |
| `export-local-database.sh` | Export DB từ local |
| `import-database.sh` | Import DB vào server |
| `backup-database.sh` | Backup database |
| `health-check.sh` | Kiểm tra health |

---

## Files Quan trọng

```
deployment/           # Scripts triển khai
  ├── setup-server.sh       # Setup server
  ├── setup-ssl.sh          # Setup SSL
  ├── deploy.sh             # Deploy manual
  ├── migrate-database.ps1  # Migrate DB (Windows)
  ├── migrate-database.sh   # Migrate DB (Linux)
  ├── export-local-database.sh
  ├── import-database.sh
  ├── backup-database.sh
  └── health-check.sh

.github/workflows/
  └── deploy.yml      # CI/CD pipeline

docker-compose.prod.yml  # Production config
Dockerfile.backend       # Backend container
Dockerfile.frontend      # Frontend container
nginx/nginx.prod.conf    # Nginx config
.env.production.example  # Environment template
```

---

## Tài liệu Chi tiết

- [QUICKSTART.md](docs/QUICKSTART.md) - Quick start 30 phút
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Hướng dẫn đầy đủ
- [DATABASE-MIGRATION.md](docs/DATABASE-MIGRATION.md) - Chi tiết migrate DB
- [Deployment Plan](plans/2026-02-04-ubuntu-deployment/plan.md) - Kế hoạch triển khai

---

## Checklist Hoàn chỉnh

**Server Setup:**
- [ ] Chạy `setup-server.sh`
- [ ] Tạo SSH keys
- [ ] Add deploy key vào GitHub
- [ ] Cấu hình firewall

**GitHub:**
- [ ] Thêm GitHub Secrets
- [ ] Test SSH connection
- [ ] Clone repository

**SSL:**
- [ ] Chạy `setup-ssl.sh`
- [ ] Cập nhật nginx config
- [ ] Verify certificate

**Deploy:**
- [ ] Push code hoặc chạy `deploy.sh`
- [ ] Verify services running
- [ ] Check logs

**Database:**
- [ ] Export local database
- [ ] Upload to server
- [ ] Import to production
- [ ] Verify data

**Verification:**
- [ ] Test frontend: https://dashboard.alkana.com
- [ ] Test API: https://dashboard.alkana.com/api/health
- [ ] Login and test dashboards
- [ ] Check all modules

**Monitoring:**
- [ ] Setup automated backups (cron)
- [ ] Setup health checks (cron)
- [ ] Configure alerts
- [ ] Monitor logs

---

## Support

Nếu gặp vấn đề:
1. Check logs: `docker compose -f docker-compose.prod.yml logs`
2. Verify services: `docker compose ps`
3. Check firewall: `sudo ufw status`
4. Review docs ở trên

---

**Total Time:** ~30-45 phút
**Difficulty:** Trung bình
**Risk:** Thấp (có backup tự động)

🎉 **Happy Deploying!**
