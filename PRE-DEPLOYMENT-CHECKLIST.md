# ✅ PRE-DEPLOYMENT CHECKLIST

Kiểm tra trước khi chạy deployment script.

## 🖥️ Máy Local (Development)

### Môi trường
- [ ] Git installed và configured
- [ ] Database đang chạy (để export)
- [ ] Docker đang chạy (nếu dùng Docker local)
- [ ] Internet connection stable

### Code
- [ ] Tất cả changes đã commit
- [ ] Code tested locally
- [ ] No syntax errors
- [ ] `.env` file configured correctly

### Database  
- [ ] Database có data
- [ ] Database accessible
- [ ] Backup local database (optional)

## 🌐 Server (192.168.68.166)

### Network
- [ ] Server accessible: `ping 192.168.68.166`
- [ ] Port 22 (SSH) open
- [ ] Port 80 (HTTP) open
- [ ] Firewall configured correctly

### Access
- [ ] Username: `alkana` ✅
- [ ] Password: `alkana123` ✅
- [ ] Can SSH: `ssh alkana@192.168.68.166`

### Resources
- [ ] Minimum 8GB RAM available
- [ ] Minimum 20GB disk space available
- [ ] CPU sufficient (4+ cores recommended)

## 📦 GitHub

### Repository
- [ ] Repository exists and accessible
- [ ] SSH key will be added during deployment
- [ ] Or use HTTPS (public repo)

### Secrets (for CI/CD)
- [ ] `SERVER_PASSWORD` = `alkana123`
- [ ] `DB_PASSWORD` = `alkana_secure_pass_2026`

## 🔧 Tools

### Windows
- [ ] PowerShell (for .ps1 script)
- [ ] Git Bash (for .sh script)
- [ ] Or PuTTY/plink installed

### Linux/Mac
- [ ] Bash available
- [ ] sshpass will be auto-installed
- [ ] curl available

## 📄 Files Check

### Cần có
- [x] `deployment/one-click-deploy.sh`
- [x] `deployment/one-click-deploy.ps1`
- [x] `deployment/server-config.env`
- [x] `deployment/setup-server.sh`
- [x] `docker-compose.prod.yml`
- [x] `Dockerfile.backend`
- [x] `Dockerfile.frontend`
- [x] `nginx/nginx.prod.conf`

### Optional nhưng recommended
- [x] `.env.production.example`
- [x] `deployment/verify-deployment.sh`
- [x] Documentation files

## 🎯 Ready to Deploy?

Nếu tất cả checked ✅, bạn đã sẵn sàng!

### Run Deployment:

**Windows:**
```powershell
cd c:\dev\alkana-dashboard
.\deployment\one-click-deploy.ps1
```

**Git Bash / Linux / Mac:**
```bash
cd /c/dev/alkana-dashboard  # hoặc ~/dev/alkana-dashboard
bash deployment/one-click-deploy.sh
```

## 📝 During Deployment

Cần làm khi script yêu cầu:

1. **Add SSH key to GitHub** (script sẽ hiện key)
   - Copy key được hiển thị
   - Vào GitHub repo settings
   - Add deploy key
   - Quay lại nhấn Enter

2. **Xác nhận deployment** 
   - Type: `yes`
   - Enter

3. **Đợi script hoàn thành**
   - ~15 phút
   - Không tắt terminal

## 🎉 After Deployment

- [ ] Access http://192.168.68.166
- [ ] Login với admin/admin123
- [ ] Change password immediately
- [ ] Test all dashboards
- [ ] Add GitHub Secrets for auto-deploy
- [ ] Setup monitoring (already done by script)

## 📞 If Something Goes Wrong

1. Read error message carefully
2. Check [DEPLOY-AUTO.md](DEPLOY-AUTO.md) troubleshooting
3. Run `bash deployment/verify-deployment.sh`
4. Check logs: `ssh alkana@192.168.68.166 'cd ~/alkana-dashboard && docker compose logs'`
5. Re-run script (it's idempotent)

---

**All Set? → [START HERE](START-HERE.md)**
