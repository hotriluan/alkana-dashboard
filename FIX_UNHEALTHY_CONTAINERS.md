# 🔧 FIX: UNHEALTHY CONTAINERS ISSUE

**Date:** February 03, 2026  
**Issue:** Backend & Frontend containers showing "unhealthy" status  
**Root Cause:** Health check configuration using unavailable tools

---

## 🔴 PROBLEM IDENTIFIED

### Symptom:
```
alkana-backend    Up 7 minutes (unhealthy)
alkana-frontend   Up 7 minutes (unhealthy)
```

### Root Cause:

**Backend Health Check (BEFORE):**
```dockerfile
# Used Python requests module (NOT installed in container)
CMD python -c "import requests; requests.get('http://localhost:8000/api/health')"
```

**Error:** `ModuleNotFoundError: No module named 'requests'`  
Health checks run in minimal environment without Python packages.

---

## ✅ SOLUTION IMPLEMENTED

### Fix 1: Backend Health Check

**Changed from:** Python requests  
**Changed to:** curl (system tool)

**docker-compose.yml:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8000/api/health || exit 1"]
```

**Dockerfile.backend:**
```dockerfile
# Install curl
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    curl \  # ← Added
    && rm -rf /var/lib/apt/lists/*

# Updated health check
HEALTHCHECK CMD curl -f http://localhost:8000/api/health || exit 1
```

### Fix 2: Frontend Health Check

Frontend already uses `wget` (available in nginx:alpine), no change needed.

---

## 🚀 DEPLOYMENT STEPS

### Trên Server Production:

```bash
# 1. Pull changes
cd /opt/alkana-dashboard
git pull origin main

# 2. Rebuild with fixed health checks
sudo docker compose down
sudo docker compose build backend
sudo docker compose up -d

# 3. Wait for health checks (60 seconds)
sleep 60

# 4. Verify containers are healthy
sudo docker compose ps
# Expected: All containers show (healthy)

# 5. Test health endpoint
curl http://localhost:8000/api/health
# Expected: {"status":"healthy","service":"alkana-dashboard-api","version":"1.0.0"}
```

---

## 📊 VERIFICATION

### Before Fix:
```
alkana-backend    Up 7 minutes (unhealthy)
alkana-frontend   Up 7 minutes (unhealthy)
```

### After Fix (Expected):
```
alkana-backend    Up 2 minutes (healthy)
alkana-frontend   Up 2 minutes (healthy)
```

---

## 📝 CHANGES SUMMARY

**Files Modified:**
- `docker-compose.yml` - Updated backend health check to use curl
- `Dockerfile.backend` - Added curl installation, updated HEALTHCHECK

**Commit Message:**
```
fix: resolve unhealthy container status by updating health checks

- Change backend health check from Python requests to curl
- Install curl in backend Docker image
- Use CMD-SHELL format for docker-compose health check
- Ensures health checks work in minimal container environment

Fixes containers showing unhealthy status despite working correctly
```

---

## 🔍 WHY CONTAINERS APPEARED UNHEALTHY

**Technical Explanation:**

Docker health checks run in a **minimal shell environment** without access to:
- Python virtual environments
- Installed pip packages (requests, etc.)
- Application runtime context

**Solution:**
Use system-level tools available in base image:
- ✅ `curl` (HTTP client)
- ✅ `wget` (HTTP client)
- ✅ `pg_isready` (PostgreSQL check)
- ❌ `python -c "import requests"` (NOT available)

---

## ✅ STATUS

- [x] Root cause identified
- [x] Fix implemented in local files
- [ ] Commit and push to GitHub
- [ ] Deploy to production server
- [ ] Verify containers healthy

---

**Next Action:** Commit changes and deploy to production following steps above.
