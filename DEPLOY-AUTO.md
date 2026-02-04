# 🚀 Hướng dẫn Triển khai Tự động - Alkana Dashboard
## Cho Server: 192.168.68.166

> **Triển khai hoàn toàn tự động với một lệnh duy nhất!**

---

## ⚡ Triển khai Siêu Nhanh (One-Click)

### Trên Windows (PowerShell)

```powershell
# Chạy script tự động
.\deployment\one-click-deploy.ps1
```

### Trên Linux/Mac hoặc Git Bash

```bash
# Cấp quyền
chmod +x deployment/one-click-deploy.sh

# Chạy deployment
bash deployment/one-click-deploy.sh
```

**Thời gian:** ~10-15 phút (bao gồm cả database)

Script sẽ tự động:
1. ✅ Kiểm tra kết nối SSH
2. ✅ Cài đặt Docker & các dependencies trên server
3. ✅ Tạo SSH keys cho GitHub
4. ✅ Clone repository
5. ✅ Export database từ máy local
6. ✅ Upload và import database
7. ✅ Build và deploy containers
8. ✅ Setup automated backups & health checks
9. ✅ Verify deployment

---

## 📋 Thông tin Server

```
IP Address:     192.168.68.166
Username:       alkana
Password:       alkana123
App URL:        http://192.168.68.166
API Docs:       http://192.168.68.166/api/docs
```

---

## 🔧 Cấu hình (Đã được thiết lập sẵn)

File [deployment/server-config.env](deployment/server-config.env) đã chứa tất cả cấu hình:

```bash
SERVER_IP=192.168.68.166
SERVER_USER=alkana
SERVER_PASSWORD=alkana123
PROD_DB_PASSWORD=alkana_secure_pass_2026
AUTO_MIGRATE_DB=true
AUTO_BACKUP=true
HEALTH_CHECK_ENABLED=true
```

---

## 🎯 Quy trình One-Click Deployment

### Phase 1: Pre-deployment Checks
- Kiểm tra SSH connection
- Cài đặt sshpass (nếu cần)

### Phase 2: Server Initialization  
- Chạy setup-server.sh
- Cài Docker, Docker Compose
- Tạo user và directories

### Phase 3: SSH Key Setup
- Generate SSH keys trên server
- Hiển thị public key để add vào GitHub

### Phase 4: Repository Setup
- Clone repository từ GitHub
- Checkout branch chính

### Phase 5: Database Migration
- Export database từ máy local
- Upload lên server
- Backup database cũ (nếu có)
- Import database mới

### Phase 6: Environment Configuration
- Tạo .env.production
- Configure database credentials
- Set application settings

### Phase 7: Application Deployment
- Build Docker images
- Start containers
- Wait for services

### Phase 8: Database Import
- Import database dump
- Initialize schema (nếu cần)

### Phase 9: Automated Tasks
- Setup daily backups (2 AM)
- Setup health checks (every 5 min)

### Phase 10: Verification
- Check frontend health
- Check API health
- Display service status

---

## 🤖 GitHub Actions (Tự động khi push)

Sau khi deploy lần đầu, mỗi lần push code sẽ tự động deploy:

### Bước 1: Thêm GitHub Secret

Repository → Settings → Secrets → Actions → New secret:

```
Name: SERVER_PASSWORD
Value: alkana123
```

```
Name: DB_PASSWORD  
Value: alkana_secure_pass_2026
```

### Bước 2: Push code

```bash
git add .
git commit -m "Update feature"
git push origin main
```

GitHub Actions sẽ tự động:
- ✅ Run tests
- ✅ Build containers
- ✅ Deploy to server
- ✅ Backup database
- ✅ Health check
- ✅ Rollback nếu thất bại

---

## 📊 Sau khi Deploy

### Truy cập ứng dụng

```
Frontend:  http://192.168.68.166
API:       http://192.168.68.166/api/docs
Health:    http://192.168.68.166/health
```

### Login mặc định

```
Username: admin
Password: admin123
```

⚠️ **Đổi password ngay sau khi login lần đầu!**

### Quản lý Services

```bash
# SSH vào server
ssh alkana@192.168.68.166
# Password: alkana123

# Xem logs
cd ~/alkana-dashboard
docker compose -f docker-compose.prod.yml logs -f

# Restart services
docker compose -f docker-compose.prod.yml restart

# Stop services
docker compose -f docker-compose.prod.yml down

# Update code và redeploy
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
```

---

## 🔄 Update & Maintenance

### Update Code (tự động qua GitHub)

```bash
# Chỉ cần push
git push origin main
# GitHub Actions sẽ tự động deploy
```

### Update Code (manual)

```bash
ssh alkana@192.168.68.166
cd ~/alkana-dashboard
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
```

### Backup Database (tự động hàng ngày 2 AM)

Manual backup:
```bash
ssh alkana@192.168.68.166
cd ~/alkana-dashboard
bash deployment/backup-database.sh
```

### Restore Database

```bash
ssh alkana@192.168.68.166
cd ~/alkana-dashboard

# Xem backups
ls -lh backups/

# Restore
bash deployment/import-database.sh backups/backup-XXXXXX.sql.gz
```

### Health Check (tự động mỗi 5 phút)

Manual check:
```bash
ssh alkana@192.168.68.166
cd ~/alkana-dashboard
bash deployment/health-check.sh
```

---

## 🐛 Troubleshooting

### Script báo lỗi connection

```bash
# Test SSH manual
ssh alkana@192.168.68.166
# Nếu không kết nối được, kiểm tra:
# - IP có đúng không
# - Server có bật không
# - Firewall có block port 22 không
```

### Database import failed

```bash
# SSH vào server
ssh alkana@192.168.68.166
cd ~/alkana-dashboard

# Check database logs
docker compose -f docker-compose.prod.yml logs postgres

# Restart database
docker compose -f docker-compose.prod.yml restart postgres

# Try import again
bash deployment/import-database.sh database-exports/YOUR_FILE.sql.gz
```

### Services không start

```bash
ssh alkana@192.168.68.166
cd ~/alkana-dashboard

# Check status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs

# Restart all
docker compose -f docker-compose.prod.yml restart

# Rebuild if needed
docker compose -f docker-compose.prod.yml up -d --build
```

### Frontend không load

```bash
# Check nginx logs
docker compose -f docker-compose.prod.yml logs frontend

# Check if backend is running
curl http://192.168.68.166/api/health

# Restart frontend
docker compose -f docker-compose.prod.yml restart frontend
```

---

## 📁 Cấu trúc Files Deployment

```
deployment/
├── server-config.env           # Server configuration (đã setup)
├── one-click-deploy.sh         # One-click deploy script (Linux/Mac)
├── one-click-deploy.ps1        # One-click deploy script (Windows)
├── setup-server.sh             # Server initialization
├── setup-ssl.sh                # SSL setup (nếu có domain)
├── migrate-database.sh         # Database migration
├── export-local-database.sh    # Export local DB
├── import-database.sh          # Import DB to server
├── backup-database.sh          # Backup script
├── health-check.sh             # Health check script
└── deploy.sh                   # Manual deploy

.github/workflows/
└── auto-deploy.yml             # GitHub Actions workflow

docker-compose.prod.yml         # Production Docker config
Dockerfile.backend              # Backend container
Dockerfile.frontend             # Frontend container
nginx/nginx.prod.conf           # Nginx configuration
```

---

## ✅ Checklist Deployment

**Lần đầu tiên:**
- [ ] Chạy one-click-deploy script
- [ ] Thêm SSH public key vào GitHub
- [ ] Đợi script hoàn thành (~10-15 phút)
- [ ] Truy cập http://192.168.68.166
- [ ] Login và đổi password
- [ ] Test các dashboards
- [ ] Add SERVER_PASSWORD vào GitHub Secrets

**Các lần sau:**
- [ ] git add & commit changes
- [ ] git push origin main
- [ ] Chờ GitHub Actions deploy
- [ ] Verify application

---

## 🎉 Ưu điểm One-Click Deployment

✅ **Hoàn toàn tự động** - Không cần thao tác thủ công  
✅ **Bao gồm database** - Migrate data từ local  
✅ **Auto backup** - Backup trước khi deploy  
✅ **Auto rollback** - Tự động rollback nếu lỗi  
✅ **Health checks** - Tự động kiểm tra services  
✅ **Monitoring** - Setup cron jobs tự động  
✅ **Zero downtime** - Services restart smooth  
✅ **Idempotent** - Chạy nhiều lần không lỗi  

---

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Check logs: `docker compose logs`
2. Kiểm tra [DEPLOYMENT.md](docs/DEPLOYMENT.md)
3. Xem [DATABASE-MIGRATION.md](docs/DATABASE-MIGRATION.md)
4. Review deployment plan

---

**Thời gian deploy:** ~10-15 phút  
**Độ khó:** Rất dễ (chỉ cần 1 lệnh)  
**Tự động hóa:** 95%  
**Yêu cầu kiến thức:** Tối thiểu  

🚀 **Happy Deploying!**
