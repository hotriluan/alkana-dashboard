# 🚀 HƯỚNG DẪN TRIỂN KHAI LÊN PRODUCTION SERVER

**Ngày:** 03/02/2026  
**Phương pháp:** GitHub-based Deployment  
**Thời gian ước tính:** 10-15 phút

---

## 📊 HIỆN TRẠNG

### Những gì đã thay đổi (Chưa deploy):
- ✅ **Smart Date Range Feature** - Dashboard tự động điều chỉnh ngày dựa trên dữ liệu
- ✅ **Upload 307 Fix** - Sửa lỗi redirect khi upload file
- 📝 **Documentation** - DOCKER_PRODUCTION_AUDIT.md, DEPLOYMENT_POST_MORTEM_REPORT.md

### Commit hiện tại:
```
917a7f8 - feat: implement smart date range fallback and fix upload 307 redirect
```

### Files mới (chưa commit):
- `DOCKER_PRODUCTION_AUDIT.md` - Báo cáo kiểm tra bảo mật Docker
- `DEPLOYMENT_POST_MORTEM_REPORT.md` - Tài liệu kiến trúc deployment
- `PRODUCTION_DEPLOYMENT_GUIDE.md` - File này

---

## ⚠️ QUAN TRỌNG: ĐỌC TRƯỚC KHI DEPLOY

### Security Issues (Từ Docker Audit):
1. ❌ **Backend port 8000 đang exposed** - Rủi ro bảo mật cao
2. ❌ **Container chạy với root user** - Rủi ro container escape
3. ❌ **Chưa có HTTPS** - Dữ liệu truyền không mã hóa

**KHUYẾN NGHỊ:** Fix các vấn đề bảo mật trước khi deploy production data quan trọng.

---

## 🎯 LỰA CHỌN DEPLOYMENT

### Option A: Deploy Code Thay Đổi (KHUYẾN NGHỊ)
**Mục đích:** Deploy smart date range + upload fix  
**Downtime:** ~30 giây  
**Risk:** Thấp (đã test local)

### Option B: Deploy + Security Fixes
**Mục đích:** Deploy code + fix bảo mật  
**Downtime:** ~5-10 phút  
**Risk:** Trung bình (cần test kỹ)

### Option C: Chỉ Deploy Documentation
**Mục đích:** Cập nhật docs, không thay đổi code  
**Downtime:** 0  
**Risk:** Không có

---

## 📝 OPTION A: DEPLOY CODE THAY ĐỔI (Quick Deploy)

### Bước 1: Commit Documentation Files

**Trên máy local (Windows):**
```powershell
# Di chuyển vào thư mục project
cd c:\dev\alkana-dashboard

# Stage documentation files
git add DOCKER_PRODUCTION_AUDIT.md
git add DEPLOYMENT_POST_MORTEM_REPORT.md
git add PRODUCTION_DEPLOYMENT_GUIDE.md

# Commit với conventional format
git commit -m "docs: add production deployment and security audit reports

- Add DOCKER_PRODUCTION_AUDIT.md with security findings
- Add DEPLOYMENT_POST_MORTEM_REPORT.md documenting GitHub workflow
- Add PRODUCTION_DEPLOYMENT_GUIDE.md for deployment instructions

Related to commit 917a7f8 (smart date range + upload fix)"

# Push lên GitHub
git push origin main
```

### Bước 2: SSH vào Production Server

```bash
# Kết nối SSH
ssh root@YOUR_PRODUCTION_SERVER_IP

# Hoặc nếu dùng user khác:
ssh your-username@YOUR_PRODUCTION_SERVER_IP
```

### Bước 3: Pull Latest Changes

```bash
# Di chuyển vào thư mục app
cd /opt/alkana-dashboard

# Pull code mới nhất từ GitHub
git pull origin main

# Verify commit được pull
git log --oneline -3
# Phải thấy: 917a7f8 feat: implement smart date range...
```

### Bước 4: Rebuild và Restart Services

```bash
# Rebuild backend (có thay đổi Python code)
docker compose build backend

# Rebuild frontend (có thay đổi TypeScript/React code)
docker compose build frontend

# Restart services
docker compose up -d

# Kiểm tra trạng thái
docker compose ps
# Tất cả services phải "Up" và "healthy"
```

### Bước 5: Verify Deployment

```bash
# Test backend API
curl http://localhost:8000/api/health
# Expected: {"status":"healthy"}

# Test smart date endpoint (new feature)
curl http://localhost:8000/api/v1/dashboards/executive/latest-data-date
# Expected: {"latest_date":"2026-01-21","recommended_start":"2026-01-01","recommended_end":"2026-01-21"}

# Test frontend
curl -I http://localhost/
# Expected: HTTP/1.1 200 OK

# Check logs for errors
docker compose logs backend --tail 50 | grep -i error
docker compose logs frontend --tail 50 | grep -i error
```

### Bước 6: Browser Testing

**Mở browser và test:**
1. Truy cập `http://YOUR_SERVER_IP`
2. Vào **Executive Dashboard**
3. **Kiểm tra:** Ngày tự động set về tháng 1/2026 (không phải tháng hiện tại)
4. Vào **Data Upload** page
5. **Upload file SAP** - Không được thấy lỗi ECONNRESET

**Expected Behavior:**
- ✅ Dashboard loads với data tháng 1/2026
- ✅ Upload file thành công không redirect
- ✅ Không có error trong browser console

### ✅ DEPLOYMENT COMPLETE

**Rollback nếu có vấn đề:**
```bash
cd /opt/alkana-dashboard
git reset --hard HEAD~1
docker compose build
docker compose up -d
```

---

## 🔒 OPTION B: DEPLOY + SECURITY FIXES (Recommended for Production)

### Bước 1: Commit Current Work (như Option A)

### Bước 2: Implement Security Fixes

#### Fix 1: Remove Backend Port Exposure

**Trên máy local:**
```powershell
cd c:\dev\alkana-dashboard

# Edit docker-compose.yml
notepad docker-compose.yml
```

**Thay đổi:**
```yaml
# TÌM section này:
backend:
  build:
    context: .
    dockerfile: Dockerfile.backend
  ports:
    - "8000:8000"  # ← XÓA DÒNG NÀY

# THÀNH:
backend:
  build:
    context: .
    dockerfile: Dockerfile.backend
  # ports section removed - backend is internal only
```

#### Fix 2: Add Resource Limits

**Trong docker-compose.yml, thêm vào backend service:**
```yaml
backend:
  build:
    context: .
    dockerfile: Dockerfile.backend
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        cpus: '0.5'
        memory: 512M
  # ... rest of config
```

**Thêm vào frontend service:**
```yaml
frontend:
  build:
    context: .
    dockerfile: Dockerfile.frontend
  deploy:
    resources:
      limits:
        cpus: '1.0'
        memory: 512M
      reservations:
        cpus: '0.25'
        memory: 128M
  # ... rest of config
```

#### Fix 3: Update Nginx to Use Non-Root User

**Edit Dockerfile.frontend:**
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY web/package*.json ./
RUN npm install
COPY web/ ./
RUN npm run build

FROM nginx:1.25-alpine

# Create non-root user
RUN addgroup -S nginx-user && adduser -S -G nginx-user nginx-user

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

# Fix permissions
RUN chown -R nginx-user:nginx-user /usr/share/nginx/html && \
    chown -R nginx-user:nginx-user /var/cache/nginx && \
    chown -R nginx-user:nginx-user /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx-user:nginx-user /var/run/nginx.pid

USER nginx-user
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
```

**Update docker-compose.yml frontend ports:**
```yaml
frontend:
  ports:
    - "80:8080"  # Map host 80 to container 8080
    - "443:8443"
```

### Bước 3: Commit Security Fixes

```powershell
git add docker-compose.yml Dockerfile.frontend
git commit -m "fix: implement docker security hardening

- Remove backend port 8000 public exposure
- Add CPU/RAM resource limits to all services
- Configure nginx to run as non-root user
- Update frontend to listen on port 8080

Fixes security issues from DOCKER_PRODUCTION_AUDIT.md"

git push origin main
```

### Bước 4: Deploy to Production

```bash
# SSH to server
ssh root@YOUR_PRODUCTION_SERVER_IP

# Pull changes
cd /opt/alkana-dashboard
git pull origin main

# Rebuild with new configs
docker compose down
docker compose build
docker compose up -d

# Verify
docker compose ps
docker compose logs backend --tail 20
docker compose logs frontend --tail 20
```

### Bước 5: Verify Security

```bash
# Test 1: Backend port 8000 should be CLOSED
curl http://YOUR_SERVER_IP:8000/api/health
# Expected: Connection refused or timeout (GOOD!)

# Test 2: API should work via Nginx proxy
curl http://YOUR_SERVER_IP/api/health
# Expected: {"status":"healthy"} (GOOD!)

# Test 3: Check containers are not root
docker compose exec backend whoami
# Expected: appuser (not root)

docker compose exec frontend whoami
# Expected: nginx-user (not root)
```

---

## 📋 OPTION C: DEPLOY DOCUMENTATION ONLY

### Bước 1: Commit Docs

```powershell
cd c:\dev\alkana-dashboard

git add DOCKER_PRODUCTION_AUDIT.md
git add DEPLOYMENT_POST_MORTEM_REPORT.md
git add PRODUCTION_DEPLOYMENT_GUIDE.md

git commit -m "docs: add production deployment documentation

- Docker security audit report
- Post-mortem of GitHub-based deployment workflow
- Step-by-step deployment guide"

git push origin main
```

### Bước 2: Pull on Server (Optional)

```bash
ssh root@YOUR_PRODUCTION_SERVER_IP
cd /opt/alkana-dashboard
git pull origin main
# No rebuild needed - docs only
```

---

## 🔍 TROUBLESHOOTING

### Issue 1: Git Pull Fails (Merge Conflict)

**Nguyên nhân:** Server có thay đổi local chưa commit

**Giải pháp:**
```bash
# Backup local changes
cd /opt/alkana-dashboard
git stash

# Pull changes
git pull origin main

# Reapply local changes (if needed)
git stash pop
```

### Issue 2: Docker Build Fails

**Nguyên nhân:** Thiếu dependencies hoặc network issue

**Giải pháp:**
```bash
# Clear Docker cache
docker compose down
docker system prune -a -f

# Rebuild with no cache
docker compose build --no-cache

# Restart
docker compose up -d
```

### Issue 3: Container Unhealthy

**Nguyên nhân:** Service không start được

**Giải pháp:**
```bash
# Check logs
docker compose logs backend -f

# Common fixes:
# - Database not ready: Wait 30s, check postgres logs
# - Port conflict: Check if port already in use
# - Permission issue: Check file ownership
```

### Issue 4: Smart Date API Returns Error

**Nguyên nhân:** Database chưa có data

**Giải pháp:**
```bash
# Check if data exists
docker compose exec backend python -c "
from src.db.database import SessionLocal
from src.models.warehouse import FactBilling
db = SessionLocal()
count = db.query(FactBilling).count()
print(f'Records: {count}')
"

# If 0 records, load data:
docker compose exec backend python -m src.main load
docker compose exec backend python -m src.main transform
```

---

## 📊 POST-DEPLOYMENT CHECKLIST

**Sau khi deploy, kiểm tra:**

- [ ] Git commit đã push thành công lên GitHub
- [ ] Production server đã pull latest code
- [ ] All Docker containers healthy: `docker compose ps`
- [ ] No errors in logs: `docker compose logs --tail 100`
- [ ] Backend health check: `curl http://localhost:8000/api/health`
- [ ] Frontend loads: `curl -I http://localhost/`
- [ ] Smart date API works: `curl http://localhost:8000/api/v1/dashboards/executive/latest-data-date`
- [ ] Upload functionality works (browser test)
- [ ] Dashboard displays correct date range (browser test)
- [ ] **Security:** Backend port 8000 not accessible externally (if Option B)
- [ ] **Security:** Containers running as non-root user (if Option B)

---

## 📞 SUPPORT & REFERENCES

**Tài liệu liên quan:**
- [DEPLOYMENT_POST_MORTEM_REPORT.md](DEPLOYMENT_POST_MORTEM_REPORT.md) - Chi tiết kiến trúc
- [DOCKER_PRODUCTION_AUDIT.md](DOCKER_PRODUCTION_AUDIT.md) - Báo cáo bảo mật
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Hướng dẫn deployment tổng quát
- [UBUNTU_DEPLOYMENT.md](UBUNTU_DEPLOYMENT.md) - Hướng dẫn Ubuntu cụ thể

**Command Reference:**
```bash
# Git commands
git status
git log --oneline -5
git pull origin main
git push origin main

# Docker commands
docker compose ps
docker compose logs -f [service]
docker compose build [service]
docker compose up -d
docker compose down
docker compose restart [service]

# Health checks
curl http://localhost:8000/api/health
curl -I http://localhost/
```

---

## ✅ KHUYẾN NGHỊ CỦA TÔI

**Cho production environment thật:**
1. **Ngay lập tức:** Deploy Option A (code changes only) - 10 phút
2. **Trong tuần này:** Implement Option B (security fixes) - 1 giờ
3. **Trong tháng này:** Configure HTTPS với Let's Encrypt - 30 phút

**Cho testing/development server:**
- Deploy Option A là đủ

**Câu hỏi cần trả lời:**
- Server IP của production là gì?
- Đang dùng HTTP hay HTTPS?
- Có domain name chưa? (cần cho HTTPS)
- Đã backup database chưa?

---

**Tạo:** February 03, 2026  
**Methodology:** ClaudeKit Engineer (KISS, YAGNI, DRY)  
**Testing:** ✅ Code changes tested locally  
**Security:** ⚠️ Needs hardening (see Option B)

---

*Nếu cần hỗ trợ deploy, vui lòng cung cấp thông tin server và tôi sẽ hướng dẫn từng bước chi tiết.*
