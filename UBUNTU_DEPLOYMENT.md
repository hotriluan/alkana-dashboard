# Hướng Dẫn Triển Khai Alkana Dashboard trên Ubuntu 24

**Ngày cập nhật:** 22/01/2026 | **Phương pháp:** Docker + GitHub

Hướng dẫn này giúp bạn triển khai hoàn chỉnh Alkana Dashboard lên máy chủ Ubuntu 24 thông qua GitHub.

## 📋 Yêu Cầu

### Máy Chủ Ubuntu 24
- **RAM**: Tối thiểu 4GB, khuyến nghị 8GB+
- **Ổ cứng**: 20GB+ cho ứng dụng và dữ liệu
- **CPU**: 2 cores+
- **Network**: Port 80 (HTTP), 443 (HTTPS), 5432 (PostgreSQL)

### Phần Mềm
- Ubuntu 24.04 LTS
- Quyền truy cập root hoặc sudo
- Kết nối internet

## 🚀 Triển Khai Tự Động (Khuyến Nghị)

### Bước 1: Kết nối SSH vào Server

```bash
ssh user@your-server-ip
```

### Bước 2: Download và Chạy Script Tự Động

```bash
# Download deployment script
wget https://raw.githubusercontent.com/hotriluan/alkana-dashboard/main/deploy.sh

# Cấp quyền thực thi
chmod +x deploy.sh

# Chạy deployment script với quyền sudo
sudo ./deploy.sh
```

Script sẽ tự động:
1. ✅ Cài đặt Docker và Docker Compose
2. ✅ Cài đặt Git
3. ✅ Clone repository từ GitHub
4. ✅ Tạo file `.env` với secrets tự động
5. ✅ Build Docker images (backend + frontend)
6. ✅ Khởi động tất cả services
7. ✅ Khởi tạo database schema

### Bước 3: Upload Dữ Liệu SAP

```bash
# Copy file Excel vào server (từ máy local)
scp /path/to/excel-files/*.xlsx user@your-server-ip:/opt/alkana-dashboard/demodata/

# Hoặc upload trực tiếp trên server
cd /opt/alkana-dashboard/demodata
# Copy các file SAP Excel vào đây
```

### Bước 4: Load và Transform Dữ Liệu

```bash
cd /opt/alkana-dashboard

# Load dữ liệu từ Excel files
sudo docker compose exec backend python -m src.main load

# Transform sang data warehouse
sudo docker compose exec backend python -m src.main transform

# Verify dữ liệu đã load
sudo docker compose exec backend python -m src.main verify
```

### Bước 5: Truy Cập Dashboard

Mở trình duyệt và truy cập:
```
http://your-server-ip
```

API Documentation:
```
http://your-server-ip:8000/docs
```

---

## 🔧 Triển Khai Thủ Công (Chi Tiết)

### 1. Cài Đặt Docker

```bash
# Update package list
sudo apt-get update

# Install prerequisites
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
sudo docker --version
sudo docker compose version
```

### 2. Clone Repository

```bash
# Install Git
sudo apt-get install -y git

# Clone repository
sudo git clone https://github.com/hotriluan/alkana-dashboard.git /opt/alkana-dashboard

# Navigate to project
cd /opt/alkana-dashboard
```

### 3. Cấu Hình Environment

```bash
# Copy environment template
sudo cp .env.example .env

# Generate secure secrets
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -hex 16)

# Edit .env file
sudo nano .env
```

**Cập nhật các giá trị trong `.env`:**

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:YOUR_DB_PASSWORD@postgres:5432/alkana_dashboard
DB_HOST=postgres
DB_PORT=5432
DB_NAME=alkana_dashboard
DB_USER=postgres
DB_PASSWORD=YOUR_DB_PASSWORD  # Thay bằng password đã generate

# Security (sử dụng các giá trị đã generate ở trên)
SECRET_KEY=your_generated_secret_key
JWT_SECRET_KEY=your_generated_jwt_secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Data Path
DEMODATA_PATH=/app/demodata
```

### 4. Build và Start Services

```bash
# Build Docker images
sudo docker compose build

# Start all services
sudo docker compose up -d

# Check services status
sudo docker compose ps
```

Output mong đợi:
```
NAME                IMAGE                      STATUS         PORTS
alkana-backend      alkana-backend:latest      Up (healthy)   0.0.0.0:8000->8000/tcp
alkana-frontend     alkana-frontend:latest     Up             0.0.0.0:80->80/tcp
alkana-postgres     postgres:16-alpine         Up (healthy)   0.0.0.0:5432->5432/tcp
```

### 5. Khởi Tạo Database

```bash
# Initialize database schema
sudo docker compose exec backend python -m src.main init

# Verify tables created
sudo docker compose exec postgres psql -U postgres -d alkana_dashboard -c "\dt"
```

### 6. Load Dữ Liệu

```bash
# Upload SAP Excel files vào thư mục demodata/
# Các file cần thiết:
# - MB51.xlsx (Material movements)
# - ZRSD002.xlsx (Billing documents)
# - ZRSD004.xlsx (Sales orders)
# - COOISPI.xlsx (Production orders)
# - v.v.

# Load raw data
sudo docker compose exec backend python -m src.main load

# Transform to data warehouse
sudo docker compose exec backend python -m src.main transform

# Verify data
sudo docker compose exec backend python -m src.main verify
```

---

## 📊 Quản Lý Sau Triển Khai

### Xem Logs

```bash
# All services
sudo docker compose logs -f

# Specific service
sudo docker compose logs -f backend
sudo docker compose logs -f frontend
sudo docker compose logs -f postgres
```

### Restart Services

```bash
# Restart all
sudo docker compose restart

# Restart specific service
sudo docker compose restart backend
```

### Stop Services

```bash
sudo docker compose down
```

### Update Ứng Dụng

```bash
cd /opt/alkana-dashboard

# Pull latest changes from GitHub
sudo git pull origin main

# Rebuild and restart
sudo docker compose up -d --build
```

### Backup Database

```bash
# Create backup directory
sudo mkdir -p /var/backups/alkana

# Backup database
sudo docker compose exec postgres pg_dump -U postgres alkana_dashboard | gzip > /var/backups/alkana/backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Verify backup
ls -lh /var/backups/alkana/
```

### Restore Database

```bash
# Stop backend
sudo docker compose stop backend

# Restore from backup
gunzip < /var/backups/alkana/backup_YYYYMMDD_HHMMSS.sql.gz | \
  sudo docker compose exec -T postgres psql -U postgres alkana_dashboard

# Restart backend
sudo docker compose start backend
```

---

## 🔐 Bảo Mật

### Cấu Hình Firewall (UFW)

```bash
# Enable firewall
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

### Cài Đặt SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (already configured by certbot)
sudo certbot renew --dry-run
```

### Giới Hạn Truy Cập Database

Chỉ cho phép backend container kết nối đến PostgreSQL:

```bash
# Edit docker-compose.yml
# Remove external port mapping for postgres:
#   ports:
#     - "5432:5432"  # Comment this line
```

---

## 🔍 Kiểm Tra Hệ Thống

### Health Checks

```bash
# Backend API
curl http://localhost:8000/api/health

# Frontend
curl http://localhost/

# Database connection
sudo docker compose exec postgres pg_isready -U postgres
```

### Monitoring Resources

```bash
# Container stats
sudo docker stats

# Disk usage
df -h

# Memory usage
free -m

# Database size
sudo docker compose exec postgres psql -U postgres -d alkana_dashboard -c "SELECT pg_size_pretty(pg_database_size('alkana_dashboard'));"
```

---

## 🐛 Xử Lý Sự Cố

### Backend không start

```bash
# Check logs
sudo docker compose logs backend

# Common issues:
# 1. Database connection failed
sudo docker compose exec postgres psql -U postgres -c "\l"

# 2. Port already in use
sudo lsof -i :8000

# 3. Environment variables missing
sudo docker compose exec backend env | grep DB_
```

### Frontend 404 Error

```bash
# Check nginx config
sudo docker compose exec frontend nginx -t

# Rebuild frontend
sudo docker compose up -d --build frontend
```

### Database Connection Error

```bash
# Check PostgreSQL status
sudo docker compose ps postgres

# Test connection
sudo docker compose exec postgres psql -U postgres -d alkana_dashboard -c "SELECT version();"

# Reset database (⚠️ Mất dữ liệu)
sudo docker compose down -v
sudo docker compose up -d
```

---

## 📈 Tối Ưu Production

### Tăng Worker Processes

Sửa [Dockerfile.backend](Dockerfile.backend):
```dockerfile
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "8"]
```

### Tăng Database Performance

```bash
# Edit postgresql.conf
sudo docker compose exec postgres bash -c "echo 'shared_buffers = 512MB' >> /var/lib/postgresql/data/postgresql.conf"
sudo docker compose restart postgres
```

### Scheduled Data Refresh

```bash
# Add to crontab
sudo crontab -e

# Daily ETL at 6 AM
0 6 * * * cd /opt/alkana-dashboard && docker compose exec backend python -m src.main load && docker compose exec backend python -m src.main transform
```

---

## 📞 Hỗ Trợ

**Tài liệu:**
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Chi tiết deployment
- [README.md](README.md) - Tổng quan dự án
- [CLAUDE.md](CLAUDE.md) - Development guidelines

**GitHub:** https://github.com/hotriluan/alkana-dashboard

---

**Chúc bạn triển khai thành công! 🚀**
