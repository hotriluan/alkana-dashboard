# Triển Khai Tự Động Lên Production Ubuntu Server

## 📋 Tổng Quan

Hướng dẫn triển khai hoàn toàn tự động dự án **Alkana Dashboard** lên máy chủ Ubuntu production qua GitHub Actions.

**Thông tin server:**
- IP: 192.168.18.35
- Username: it
- Password: it123
- OS: Ubuntu

**Tự động hóa:** 95% | **Thời gian:** ~15 phút

## 🚀 Các Bước Triển Khai

### Bước 1: Chuẩn Bị SSH Key

Tạo SSH key pair để GitHub Actions có thể kết nối tới server:

```powershell
# Trong PowerShell trên máy Windows
ssh-keygen -t ed25519 -C "github-actions@alkana-dashboard" -f "$env:USERPROFILE\.ssh\alkana_deploy"
```

Khi được hỏi passphrase, nhấn Enter để bỏ qua.

### Bước 2: Cấu Hình Server

Chạy script tự động cài đặt server:

```powershell
# Chạy từ thư mục gốc dự án
.\deployment\setup-production-server.ps1
```

Script sẽ tự động:
- Kết nối SSH tới server
- Cài đặt Docker, Docker Compose
- Cài đặt Git và các dependencies
- Cấu hình firewall (ports 22, 80, 443)
- Copy SSH public key lên server
- Tạo thư mục dự án

### Bước 3: Cấu Hình GitHub Repository

1. **Push code lên GitHub** (nếu chưa có):
   ```powershell
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/alkana-dashboard.git
   git push -u origin main
   ```

2. **Thêm GitHub Secrets:**
   - Vào GitHub repository > Settings > Secrets and variables > Actions
   - Thêm các secrets sau:

   | Secret Name | Value |
   |------------|-------|
   | `SERVER_HOST` | `192.168.18.35` |
   | `SERVER_USER` | `it` |
   | `SSH_PRIVATE_KEY` | Nội dung file `~\.ssh\alkana_deploy` |
   | `DB_NAME` | `alkana_dashboard` |
   | `DB_USER` | `alkana_user` |
   | `DB_PASSWORD` | Mật khẩu database (tạo mới, ví dụ: `Alk@na2026!`) |

### Bước 4: Triển Khai Tự Động

Push code lên GitHub để kích hoạt deployment:

```powershell
git add .
git commit -m "Configure automated deployment"
git push origin main
```

GitHub Actions sẽ tự động:
1. ✅ Chạy tests (backend + frontend)
2. ✅ Build Docker images
3. ✅ SSH vào server
4. ✅ Pull code mới nhất
5. ✅ Backup database
6. ✅ Deploy với Docker Compose
7. ✅ Health checks
8. ✅ Rollback nếu có lỗi

### Bước 5: Kiểm Tra Deployment

Sau khi deployment hoàn tất (2-3 phút):

```powershell
# Kiểm tra frontend
curl http://192.168.18.35

# Kiểm tra API
curl http://192.168.18.35/api/health

# Kiểm tra logs trên server
ssh it@192.168.18.35 "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml logs -f --tail=50"
```

## 📦 Triển Khai Thủ Công (Fallback)

Nếu cần triển khai thủ công:

```powershell
# 1. SSH vào server
ssh it@192.168.18.35

# 2. Clone hoặc pull code
cd ~/alkana-dashboard
git pull origin main

# 3. Tạo .env.production
cat > .env.production << 'EOF'
DATABASE_URL=postgresql://alkana_user:YOUR_PASSWORD@postgres:5432/alkana_dashboard
DB_HOST=postgres
DB_PORT=5432
DB_NAME=alkana_dashboard
DB_USER=alkana_user
DB_PASSWORD=YOUR_PASSWORD
ENVIRONMENT=production
DEBUG=false
ALLOWED_ORIGINS=http://192.168.18.35
DEMODATA_PATH=/app/demodata
STUCK_IN_TRANSIT_HOURS=48
LOW_YIELD_THRESHOLD=85
EOF

# 4. Deploy
docker compose -f docker-compose.prod.yml up -d --build

# 5. Kiểm tra
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f
```

## 🔄 Workflow Triển Khai Liên Tục

Sau khi cấu hình xong, mỗi lần push code:

```powershell
git add .
git commit -m "feature: your feature description"
git push origin main
```

→ GitHub Actions tự động deploy (~3-5 phút)
→ Nhận thông báo success/failure qua GitHub
→ Tự động rollback nếu có lỗi

## 🛠️ Các Lệnh Hữu Ích

### Xem logs
```bash
ssh it@192.168.18.35 "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml logs -f backend"
```

### Restart services
```bash
ssh it@192.168.18.35 "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml restart"
```

### Backup database
```bash
ssh it@192.168.18.35 "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U alkana_user alkana_dashboard | gzip > backups/manual-backup-\$(date +%Y%m%d-%H%M%S).sql.gz"
```

### Restore database
```bash
ssh it@192.168.18.35 "cd ~/alkana-dashboard && gunzip -c backups/backup-file.sql.gz | docker compose -f docker-compose.prod.yml exec -T postgres psql -U alkana_user alkana_dashboard"
```

### Health check
```powershell
# Frontend
curl http://192.168.18.35

# API
curl http://192.168.18.35/api/health

# API Docs
Start-Process "http://192.168.18.35/api/docs"
```

## 🔒 Bảo Mật

### Các điểm đã được bảo vệ:
- ✅ SSH key authentication (không dùng password trong CI/CD)
- ✅ GitHub Secrets để lưu credentials
- ✅ Firewall cấu hình (UFW)
- ✅ Docker container isolation
- ✅ Non-root user trong containers
- ✅ Database password mạnh
- ✅ CORS configuration

### Khuyến nghị thêm:
- [ ] Cấu hình SSL/TLS nếu có domain
- [ ] Setup fail2ban
- [ ] Monitoring và alerting
- [ ] Regular backups tự động

## 📊 Monitoring

### Docker stats
```bash
ssh it@192.168.18.35 "docker stats --no-stream"
```

### Disk usage
```bash
ssh it@192.168.18.35 "df -h"
```

### Container logs
```bash
ssh it@192.168.18.35 "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml logs --tail=100 -f"
```

## 🆘 Troubleshooting

### Container không start
```bash
ssh it@192.168.18.35 "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml logs backend"
```

### Database connection issues
```bash
ssh it@192.168.18.35 "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml exec postgres psql -U alkana_user -d alkana_dashboard -c 'SELECT version();'"
```

### Port conflicts
```bash
ssh it@192.168.18.35 "sudo netstat -tlnp | grep :80"
```

### Rollback thủ công
```bash
ssh it@192.168.18.35 "cd ~/alkana-dashboard && git reset --hard HEAD~1 && docker compose -f docker-compose.prod.yml up -d --build"
```

## 📝 Checklist Triển Khai

- [ ] SSH key đã tạo và copy lên server
- [ ] GitHub repository đã setup
- [ ] GitHub Secrets đã thêm đầy đủ
- [ ] Server đã cài Docker và Git
- [ ] Firewall đã cấu hình
- [ ] .env.production đã tạo trên server
- [ ] Database password mạnh
- [ ] GitHub Actions workflow đã chạy thành công
- [ ] Health checks pass
- [ ] Frontend accessible tại http://192.168.18.35
- [ ] API accessible tại http://192.168.18.35/api/docs

## 🎯 Kết Quả Mong Đợi

Sau khi hoàn tất:
- ✅ Mỗi git push tự động deploy
- ✅ Tests tự động chạy trước khi deploy
- ✅ Database tự động backup
- ✅ Health checks đảm bảo service hoạt động
- ✅ Rollback tự động nếu deploy fail
- ✅ Zero-downtime deployment với Docker
- ✅ Logs tập trung dễ debug

## 📚 Tài Liệu Liên Quan

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [React Production Build](https://react.dev/learn/start-a-new-react-project#deploying-to-production)

---

**Tạo bởi:** ClaudeKit Engineer
**Ngày:** 2026-02-06
**Version:** 1.0.0
