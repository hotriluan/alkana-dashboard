# 📊 Database Migration Guide

> Hướng dẫn migrate database từ máy phát triển lên Ubuntu server

## Tổng quan

Guide này giúp bạn chuyển toàn bộ database hiện tại từ máy development lên production server một cách an toàn.

---

## Phương pháp 1: Tự động (Khuyến nghị) ⚡

### Trên Windows

```powershell
# Chạy script PowerShell
.\deployment\migrate-database.ps1 -Server YOUR_SERVER_IP -SshUser deploy
```

### Trên Linux/Mac

```bash
# Cấp quyền thực thi
chmod +x deployment/*.sh

# Chạy migration
./deployment/migrate-database.sh YOUR_SERVER_IP deploy
```

Script sẽ tự động:
1. ✅ Export database từ máy local
2. ✅ Nén và upload lên server
3. ✅ Backup database hiện tại trên server
4. ✅ Import database mới
5. ✅ Verify kết quả

**Thời gian:** ~5-10 phút (tùy kích thước database)

---

## Phương pháp 2: Thủ công 🔧

### Bước 1: Export Database từ Local

**Option A: Sử dụng script**

```bash
# Linux/Mac
./deployment/export-local-database.sh

# Windows (Git Bash)
bash deployment/export-local-database.sh
```

**Option B: Manual export**

Nếu database đang chạy trong Docker:

```bash
docker compose exec -T postgres pg_dump -U postgres alkana_dashboard > database-export.sql
gzip database-export.sql
```

Nếu PostgreSQL cài trực tiếp:

```bash
# Windows (có PostgreSQL installed)
pg_dump -h localhost -U postgres -d alkana_dashboard > database-export.sql

# Linux/Mac
pg_dump -h localhost -U postgres alkana_dashboard > database-export.sql

# Nén file
gzip database-export.sql
```

### Bước 2: Upload lên Server

```bash
# Tạo thư mục trên server
ssh deploy@YOUR_SERVER_IP "mkdir -p ~/alkana-dashboard/database-exports"

# Upload file
scp database-exports/alkana-db-export-*.sql.gz deploy@YOUR_SERVER_IP:~/alkana-dashboard/database-exports/
```

### Bước 3: Import trên Server

```bash
# SSH vào server
ssh deploy@YOUR_SERVER_IP

# Di chuyển vào project directory
cd ~/alkana-dashboard

# Cấp quyền execute
chmod +x deployment/import-database.sh

# Import database
./deployment/import-database.sh database-exports/alkana-db-export-XXXXXX.sql.gz
```

Script sẽ hỏi xác nhận trước khi import.

---

## Phương pháp 3: Chỉ Export (Để import sau)

Nếu bạn chỉ muốn export để lưu trữ hoặc import thủ công sau:

```bash
# Export database
./deployment/export-local-database.sh

# File sẽ được tạo trong thư mục database-exports/
```

Sau đó bạn có thể:
- Lưu trữ file backup
- Upload thủ công lên server
- Import bằng script hoặc manually

---

## Kiểm tra Database sau Migration

### 1. Kiểm tra Tables

```bash
# Trên server
docker compose -f docker-compose.prod.yml exec postgres psql -U alkana_user -d alkana_dashboard

# Trong PostgreSQL
\dt staging.*
\dt warehouse.*
SELECT COUNT(*) FROM staging.material_movements;
SELECT COUNT(*) FROM staging.sales;
\q
```

### 2. Kiểm tra API

```bash
curl https://dashboard.alkana.com/api/health
curl https://dashboard.alkana.com/api/executive/kpis
```

### 3. Kiểm tra Logs

```bash
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs postgres
```

---

## Troubleshooting

### Lỗi: Cannot connect to database

**Nguyên nhân:** Database không chạy hoặc credentials sai

**Giải pháp:**

```bash
# Kiểm tra database đang chạy
docker compose ps postgres

# Restart database
docker compose restart postgres

# Kiểm tra .env file
cat .env
```

### Lỗi: Permission denied

**Giải pháp:**

```bash
# Cấp quyền execute cho scripts
chmod +x deployment/*.sh
```

### Lỗi: pg_dump: command not found

**Windows:**
- Cài PostgreSQL hoặc dùng Git Bash
- Hoặc export từ Docker: `docker compose exec -T postgres pg_dump...`

**Linux/Mac:**
```bash
sudo apt install postgresql-client  # Ubuntu/Debian
brew install postgresql  # macOS
```

### Database quá lớn, upload lâu

**Giải pháp:**

```bash
# Kiểm tra kích thước export
ls -lh database-exports/*.gz

# Nếu > 1GB, có thể:
# 1. Upload trực tiếp vào server storage
# 2. Dùng rsync thay vì scp
rsync -avz --progress database-exports/*.gz deploy@SERVER:/home/deploy/alkana-dashboard/database-exports/

# 3. Hoặc chỉ export schema + recent data
pg_dump --schema-only ...  # Chỉ structure
pg_dump --data-only --where="created_at > '2026-01-01'" ...  # Recent data
```

### Import thất bại giữa chừng

**Giải pháp:** Rollback về backup

```bash
# Liệt kê backups
ls -lh backups/

# Restore backup gần nhất
./deployment/import-database.sh backups/pre-import-backup-XXXXXX.sql.gz
```

---

## Best Practices

### 1. Luôn Backup trước khi Import

Script tự động backup, nhưng nếu import manual:

```bash
# Backup production database
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U alkana_user alkana_dashboard | \
  gzip > backups/manual-backup-$(date +%Y%m%d-%H%M%S).sql.gz
```

### 2. Test trên Staging trước

Nếu có staging environment, test migration trước:

```bash
./deployment/migrate-database.sh staging.alkana.com
```

### 3. Schedule Maintenance Window

Thông báo users trước khi migrate:
- Database sẽ unavailable ~5-10 phút
- Schedule vào off-peak hours (đêm khuya/cuối tuần)

### 4. Verify Data Integrity

Sau migration:

```bash
# So sánh row counts
# Local
psql -d alkana_dashboard -c "SELECT 'material_movements', COUNT(*) FROM staging.material_movements;"

# Production
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U alkana_user -d alkana_dashboard \
  -c "SELECT 'material_movements', COUNT(*) FROM staging.material_movements;"
```

---

## Scripts Reference

| Script | Mô tả | Platform |
|--------|-------|----------|
| `export-local-database.sh` | Export database từ local | Linux/Mac/Windows (Git Bash) |
| `import-database.sh` | Import database vào server | Linux (on server) |
| `migrate-database.sh` | Full migration tự động | Linux/Mac |
| `migrate-database.ps1` | Full migration tự động | Windows PowerShell |

---

## Workflow Migration Hoàn chỉnh

```
┌─────────────────┐
│ Local Database  │
│ (Development)   │
└────────┬────────┘
         │
         │ export-local-database.sh
         ▼
┌─────────────────┐
│   Export File   │
│   (.sql.gz)     │
└────────┬────────┘
         │
         │ scp/rsync
         ▼
┌─────────────────┐
│  Server Upload  │
│  (/database-    │
│   exports/)     │
└────────┬────────┘
         │
         │ import-database.sh
         ▼
┌─────────────────┐
│   Production    │
│   Database      │
│   (Server)      │
└─────────────────┘
```

---

## Automated vs Manual Comparison

| Feature | Automated | Manual |
|---------|-----------|--------|
| Thời gian | ~5-10 phút | ~20-30 phút |
| Backup tự động | ✅ | ❌ Phải làm thủ công |
| Verify | ✅ | ❌ Phải check manually |
| Rollback | ✅ Tự động | 🔶 Manual |
| Error handling | ✅ | ❌ |
| Phù hợp cho | Production | Development/Testing |

---

## Ví dụ Thực tế

### Scenario 1: First-time Deployment

```bash
# 1. Export local database
./deployment/export-local-database.sh

# 2. Migrate to server
./deployment/migrate-database.sh 165.232.123.45 deploy

# 3. Verify
curl https://dashboard.alkana.com/api/health
```

### Scenario 2: Update Production Data

```bash
# 1. Thông báo maintenance
# 2. Run migration during off-peak
./deployment/migrate-database.sh dashboard.alkana.com

# 3. Verify và test
# 4. Announce completion
```

### Scenario 3: Rollback

```bash
# Nếu migration có vấn đề
ssh deploy@SERVER
cd ~/alkana-dashboard
ls -lh backups/pre-import-backup-*.sql.gz
./deployment/import-database.sh backups/pre-import-backup-20260204-120000.sql.gz
```

---

## Checklist Migration

- [ ] Backup database hiện tại (local)
- [ ] Test scripts locally
- [ ] Notify users về maintenance
- [ ] Run export script
- [ ] Verify export file size
- [ ] Upload to server
- [ ] Server backup sẽ được tạo tự động
- [ ] Run import script
- [ ] Verify table counts
- [ ] Test API endpoints
- [ ] Check application logs
- [ ] Verify data integrity
- [ ] Test user workflows
- [ ] Monitor for 24 hours
- [ ] Document any issues

---

## Support

Nếu gặp vấn đề:
1. Check logs: `docker compose -f docker-compose.prod.yml logs`
2. Verify connection: `docker compose ps`
3. Check disk space: `df -h`
4. Review backup: `ls -lh backups/`

---

**Lưu ý quan trọng:**
- ⚠️ Import sẽ **XÓA** toàn bộ database hiện tại trên server
- ⚠️ Backup tự động được tạo trước khi import
- ⚠️ Luôn test trên staging environment trước
- ⚠️ Schedule migration vào off-peak hours
