# 🚀 BẮT ĐẦU NGAY - Triển khai lên 192.168.68.166

## ⚡ Lệnh Duy Nhất (Khuyến nghị)

### Windows (PowerShell - Chạy as Administrator)

```powershell
cd c:\dev\alkana-dashboard
.\deployment\one-click-deploy.ps1
```

### Git Bash (Windows) / Linux / Mac

```bash
cd /c/dev/alkana-dashboard  # Windows Git Bash
# hoặc
cd ~/dev/alkana-dashboard   # Linux/Mac

chmod +x deployment/*.sh
bash deployment/one-click-deploy.sh
```

---

## 📝 Những gì script sẽ làm

1. ✅ **Kiểm tra kết nối** đến 192.168.68.166
2. ✅ **Cài đặt server** (Docker, tools)
3. ✅ **Generate SSH keys** và hiện public key
4. ✅ **Clone repository** từ GitHub
5. ✅ **Export database** từ máy này
6. ✅ **Upload database** lên server
7. ✅ **Deploy containers** (backend, frontend, postgres)
8. ✅ **Import database**
9. ✅ **Setup monitoring** (backups, health checks)
10. ✅ **Verify** tất cả services

---

## 🎯 Trong quá trình chạy

### Bước quan trọng cần làm:

Khi script hiển thị SSH public key:

```
📋 Server SSH Public Key (add this to GitHub Deploy Keys):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ssh-ed25519 AAAAC3... alkana@deployment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please add this key to GitHub:
1. Go to: https://github.com/your-org/alkana-dashboard/settings/keys
2. Click 'Add deploy key'
3. Paste the key above
4. Check 'Allow write access' if needed

Press Enter when you have added the key to GitHub...
```

**Làm theo hướng dẫn:**
1. Copy SSH key được hiển thị
2. Mở link GitHub
3. Add deploy key
4. Quay lại terminal và nhấn Enter

Script sẽ tiếp tục tự động!

---

## ⏱️ Thời gian dự kiến

- **Chuẩn bị:** 2 phút
- **Server setup:** 3 phút
- **Database export/upload:** 3-5 phút (tùy kích thước DB)
- **Deploy & verify:** 5 phút

**Tổng:** ~15 phút

---

## ✅ Sau khi hoàn thành

Bạn sẽ thấy:

```
==========================================
✅ DEPLOYMENT COMPLETED!
==========================================

🌐 Access Points:
   Frontend:  http://192.168.68.166
   API Docs:  http://192.168.68.166/api/docs
   Health:    http://192.168.68.166/health

📊 Default Login:
   Username: admin
   Password: admin123
   ⚠️  CHANGE THIS IMMEDIATELY!
```

### Truy cập ngay:

1. Mở trình duyệt: **http://192.168.68.166**
2. Login: `admin` / `admin123`
3. Đổi password ngay!
4. Kiểm tra các dashboards

---

## 🔄 Để deploy lại hoặc update

### Cách 1: Tự động qua GitHub (sau khi setup lần đầu)

```bash
# Chỉ cần commit và push
git add .
git commit -m "Update feature"
git push origin main

# GitHub Actions sẽ tự động deploy!
```

**Yêu cầu:** Thêm GitHub Secret `SERVER_PASSWORD=alkana123`

### Cách 2: Manual update

```bash
ssh alkana@192.168.68.166
# Password: alkana123

cd ~/alkana-dashboard
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
```

---

## 🔍 Kiểm tra deployment

```bash
# Verify tất cả services
bash deployment/verify-deployment.sh
```

Hoặc truy cập trực tiếp:
- Frontend: http://192.168.68.166
- API Health: http://192.168.68.166/api/health
- API Docs: http://192.168.68.166/api/docs

---

## 🐛 Nếu có lỗi

### Lỗi kết nối SSH
```bash
# Test connection
ssh alkana@192.168.68.166
# Password: alkana123

# Nếu không connect được:
# - Kiểm tra server có bật không
# - Ping 192.168.68.166
# - Kiểm tra firewall
```

### Script dừng giữa chừng
```bash
# Chạy lại, script có thể resume
bash deployment/one-click-deploy.sh
```

### Services không chạy
```bash
ssh alkana@192.168.68.166
cd ~/alkana-dashboard

# Check status
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart
docker compose -f docker-compose.prod.yml restart
```

---

## 📚 Tài liệu chi tiết

- [DEPLOY-AUTO.md](DEPLOY-AUTO.md) - Hướng dẫn tự động hóa
- [deployment/README.md](deployment/README.md) - Scripts overview
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Full deployment guide
- [docs/DATABASE-MIGRATION.md](docs/DATABASE-MIGRATION.md) - Database details

---

## 💡 Tips

### Xem logs khi đang deploy
```bash
# Mở terminal khác
ssh alkana@192.168.68.166
cd ~/alkana-dashboard
docker compose -f docker-compose.prod.yml logs -f
```

### Backup manual trước khi deploy
```bash
# Nếu muốn backup thêm
bash deployment/export-local-database.sh
# File sẽ lưu trong database-exports/
```

### Reset hoàn toàn (nếu cần)
```bash
ssh alkana@192.168.68.166
cd ~/alkana-dashboard
docker compose -f docker-compose.prod.yml down -v
docker system prune -a
# Sau đó chạy lại one-click-deploy
```

---

## 🎯 Checklist Nhanh

Trước khi chạy:
- [ ] Có kết nối internet
- [ ] Server 192.168.68.166 đang bật
- [ ] Git đã commit hết changes
- [ ] Database local đang chạy (để export)

Trong quá trình:
- [ ] Thêm SSH key vào GitHub khi được yêu cầu
- [ ] Đợi script chạy xong (~15 phút)

Sau khi xong:
- [ ] Truy cập http://192.168.68.166
- [ ] Login thành công
- [ ] Đổi password admin
- [ ] Test các dashboards
- [ ] Add SERVER_PASSWORD vào GitHub Secrets

---

## 🚀 SẴN SÀNG? BẮT ĐẦU NGAY!

```powershell
# Windows PowerShell
.\deployment\one-click-deploy.ps1
```

Hoặc

```bash
# Git Bash / Linux / Mac
bash deployment/one-click-deploy.sh
```

**Thời gian:** 15 phút  
**Độ khó:** Dễ  
**Tự động:** 95%  

🎉 **Chúc bạn deploy thành công!**

---

**Hỗ trợ:**  
Nếu gặp vấn đề, check logs và tài liệu ở trên.  
Hoặc xem troubleshooting trong [DEPLOY-AUTO.md](DEPLOY-AUTO.md)
