# 🚀 Hướng Dẫn Triển Khai Nhanh - Alkana Dashboard

## Tóm Tắt Nhanh

**Server:** 192.168.18.35 | **User:** it | **Pass:** it123

**3 bước chính:**
1. Chuẩn bị SSH key
2. Setup server
3. Cấu hình GitHub và deploy

⏱️ **Thời gian:** 15-20 phút | 🤖 **Tự động:** 95%

---

## 📋 Bước 1: Chuẩn Bị SSH Key (2 phút)

### Tạo SSH Key

```powershell
# Mở PowerShell
ssh-keygen -t ed25519 -C "alkana-deploy" -f "$env:USERPROFILE\.ssh\alkana_deploy"
```

> Nhấn Enter khi hỏi passphrase (để trống)

### Kiểm tra key đã tạo

```powershell
ls $env:USERPROFILE\.ssh\alkana_deploy*
```

Phải thấy 2 files:
- `alkana_deploy` (private key)
- `alkana_deploy.pub` (public key)

---

## 🖥️ Bước 2: Setup Production Server (5-10 phút)

### Chạy script tự động

```powershell
# Từ thư mục gốc dự án
.\deployment\setup-production-server.ps1
```

Script sẽ:
- ✅ Upload SSH key lên server
- ✅ Cài Docker và Docker Compose
- ✅ Cài Git và tools cần thiết
- ✅ Cấu hình firewall (ports 22, 80, 443)
- ✅ Tạo thư mục dự án

### Nếu script lỗi - Cách thủ công:

```powershell
# 1. Copy SSH key lên server
ssh it@192.168.18.35
# Nhập password: it123

# 2. Cài đặt trên server
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker it
sudo apt install -y git curl wget ufw
sudo ufw allow 22 && sudo ufw allow 80 && sudo ufw allow 443
sudo ufw --force enable
mkdir -p ~/alkana-dashboard
exit

# 3. Copy SSH public key
type $env:USERPROFILE\.ssh\alkana_deploy.pub | ssh it@192.168.18.35 "cat >> ~/.ssh/authorized_keys"
```

### Kiểm tra SSH key hoạt động

```powershell
ssh -i $env:USERPROFILE\.ssh\alkana_deploy it@192.168.18.35 "echo 'SSH OK'"
```

Phải thấy "SSH OK" mà không cần nhập password.

---

## 🔧 Bước 3: Cấu Hình GitHub (3-5 phút)

### 3.1. Push code lên GitHub (nếu chưa có)

```powershell
git init
git add .
git commit -m "Initial commit - Alkana Dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/alkana-dashboard.git
git push -u origin main
```

### 3.2. Thêm GitHub Secrets

1. Vào repository trên GitHub
2. **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Thêm các secrets sau:

| Tên Secret | Giá Trị |
|-----------|---------|
| `SERVER_HOST` | `192.168.18.35` |
| `SERVER_USER` | `it` |
| `SSH_PRIVATE_KEY` | Nội dung file private key (xem bên dưới) |
| `DB_NAME` | `alkana_dashboard` |
| `DB_USER` | `alkana_user` |
| `DB_PASSWORD` | `Alkana2026SecureDB!` |

### Lấy nội dung SSH Private Key:

```powershell
# Copy vào clipboard
Get-Content $env:USERPROFILE\.ssh\alkana_deploy | Set-Clipboard

# Hoặc xem trực tiếp
Get-Content $env:USERPROFILE\.ssh\alkana_deploy
```

> **QUAN TRỌNG:** Copy toàn bộ nội dung từ `-----BEGIN` đến `-----END`

### 3.3. Deploy

Push code để trigger deployment:

```powershell
git add .
git commit -m "Configure production deployment"
git push origin main
```

---

## ✅ Bước 4: Kiểm Tra Deployment

### Xem quá trình deploy trên GitHub

1. Vào repository trên GitHub
2. Click tab **Actions**
3. Xem workflow đang chạy
4. Đợi 2-3 phút cho đến khi thấy ✅

### Kiểm tra ứng dụng

```powershell
# Frontend
Start-Process http://192.168.18.35

# API Documentation
Start-Process http://192.168.18.35/api/docs

# Health check
curl http://192.168.18.35/api/health
```

### Xem logs trên server

```powershell
ssh -i $env:USERPROFILE\.ssh\alkana_deploy it@192.168.18.35 "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml logs -f --tail=50"
```

---

## 🔄 Deployment Tiếp Theo

Sau khi setup xong, mỗi lần cần deploy:

```powershell
git add .
git commit -m "feature: description"
git push origin main
```

GitHub Actions sẽ tự động:
1. Chạy tests
2. Build Docker images
3. Deploy lên server
4. Kiểm tra health
5. Rollback nếu có lỗi

---

## 🛠️ Các Lệnh Hữu Ích

### Deploy thủ công (không qua GitHub)

```powershell
.\deployment\quick-deploy.ps1
```

### Xem logs

```powershell
ssh it@192.168.18.35 "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml logs -f backend"
```

### Restart services

```powershell
ssh it@192.168.18.35 "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml restart"
```

### Backup database

```powershell
ssh it@192.168.18.35 "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U alkana_user alkana_dashboard | gzip > backups/manual-backup-$(date +%Y%m%d).sql.gz"
```

### Xem trạng thái containers

```powershell
ssh it@192.168.18.35 "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml ps"
```

### SSH vào server

```powershell
ssh -i $env:USERPROFILE\.ssh\alkana_deploy it@192.168.18.35
```

---

## ❌ Xử Lý Lỗi Thường Gặp

### 1. SSH connection refused

```powershell
# Kiểm tra SSH service trên server
ssh it@192.168.18.35 "sudo systemctl status sshd"

# Kiểm tra firewall
ssh it@192.168.18.35 "sudo ufw status"
```

### 2. Docker containers không start

```powershell
# Xem logs chi tiết
ssh it@192.168.18.35 "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml logs"

# Restart
ssh it@192.168.18.35 "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml restart"
```

### 3. Database connection error

```powershell
# Kiểm tra postgres container
ssh it@192.168.18.35 "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml ps postgres"

# Test database connection
ssh it@192.168.18.35 "cd ~/alkana-dashboard && docker compose -f docker-compose.prod.yml exec postgres psql -U alkana_user -d alkana_dashboard -c 'SELECT version();'"
```

### 4. GitHub Actions fail

- Kiểm tra GitHub Secrets đã thêm đúng chưa
- Xem logs chi tiết trong Actions tab
- Đảm bảo SSH key đã copy lên server

### 5. Port 80 bị chiếm

```powershell
# Kiểm tra process nào đang dùng port 80
ssh it@192.168.18.35 "sudo netstat -tlnp | grep :80"

# Stop service nếu cần
ssh it@192.168.18.35 "sudo systemctl stop apache2"  # hoặc nginx
```

---

## 📊 Checklist Hoàn Thành

- [ ] SSH key đã tạo ✅
- [ ] SSH key đã copy lên server ✅
- [ ] Server đã cài Docker ✅
- [ ] Firewall đã cấu hình ✅
- [ ] Code đã push lên GitHub ✅
- [ ] GitHub Secrets đã thêm ✅
- [ ] GitHub Actions chạy thành công ✅
- [ ] Frontend truy cập được ✅
- [ ] API health check pass ✅
- [ ] Logs không có error ✅

---

## 📞 Hỗ Trợ

### Files quan trọng

- `deployment/PRODUCTION_DEPLOYMENT_GUIDE.md` - Hướng dẫn chi tiết
- `deployment/GITHUB_SECRETS.md` - Cấu hình GitHub Secrets
- `.github/workflows/deploy.yml` - CI/CD workflow
- `docker-compose.prod.yml` - Docker production config

### Xem thêm

- [README.md](../README.md) - Tổng quan dự án
- [START-HERE.md](../START-HERE.md) - Getting started

---

**Chúc bạn deploy thành công! 🎉**

*Tạo bởi: ClaudeKit Engineer*
*Ngày: 2026-02-06*
