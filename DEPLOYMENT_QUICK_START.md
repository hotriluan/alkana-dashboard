# DEPLOYMENT QUICK START

**Feature:** Smart Date Range Fallback  
**Date:** February 03, 2026  
**Priority:** HIGH

---

## 🚀 QUICK DEPLOY (5 Minutes)

### Step 1: Restart Backend (30 seconds)
```bash
cd c:\dev\alkana-dashboard
# Stop current backend (Ctrl+C if running)

cd src
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 2: Test Backend API (30 seconds)
Open new terminal:
```bash
cd c:\dev\alkana-dashboard
python verify_smart_date.py
```

**Expected Output:**
```
✅ API Response Successful
📊 Latest Data Dates:
   • Billing:    2026-01-21
   • Inventory:  2026-01-21
   • Production: 2026-01-XX

📅 Recommended Date Range:
   • Start: 2026-01-01
   • End:   2026-01-21

🎯 Current Month Data Available: NO ❌

✅ SMART FALLBACK ACTIVE
```

### Step 3: Start Frontend (1 minute)
```bash
cd c:\dev\alkana-dashboard\web
npm run dev
```

**Expected Output:**
```
VITE v7.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Step 4: Verify in Browser (2 minutes)

1. Open browser: http://localhost:5173
2. Login with credentials
3. Navigate to **Executive Dashboard**
4. **CHECK:** Date picker should show **Jan 1-21, 2026** (NOT Feb 2026)
5. **CHECK:** Charts should display data immediately
6. **CHECK:** No "Zero Data" issue

---

## ✅ SUCCESS CRITERIA

| Check | Expected | Status |
|-------|----------|--------|
| Backend starts | No errors | ⬜ |
| API returns data | `recommended_start_date: 2026-01-01` | ⬜ |
| Frontend builds | TypeScript compilation passes | ⬜ |
| Date picker shows | Jan 1-21, 2026 (not Feb 2026) | ⬜ |
| Charts load data | > 600K records displayed | ⬜ |
| Upload works | POST /upload/ → 200 OK | ⬜ |

---

## 🔧 TROUBLESHOOTING

### Issue: Backend won't start
**Error:** `ModuleNotFoundError: No module named 'src'`  
**Fix:** Make sure you're in project root:
```bash
cd c:\dev\alkana-dashboard
python -c "from src.api.main import app; print('✅ OK')"
```

### Issue: Smart date API returns 401
**Error:** `Unauthorized`  
**Fix:** Check credentials in `verify_smart_date.py` and ensure user exists in database

### Issue: Date picker still shows Feb 2026
**Possible Causes:**
1. Browser cache - Hard refresh (Ctrl+Shift+R)
2. Backend not restarted - Verify backend is running on port 8000
3. API error - Check browser DevTools Console for errors

**Debug:**
```javascript
// In browser DevTools Console
fetch('/api/v1/dashboards/executive/latest-data-date', {
  headers: { 'Authorization': 'Bearer ' + localStorage.getItem('access_token') }
}).then(r => r.json()).then(console.log)
```

### Issue: Charts still empty
**Cause:** Date range issue  
**Fix:**
1. Manually change date picker to Jan 2026
2. Check if data exists: 
```bash
psql -h localhost -U postgres -d alkana_dashboard -c "SELECT MAX(billing_date) FROM fact_billing;"
```

---

## 📋 ROLLBACK PLAN (If Needed)

If smart date feature causes issues:

### 1. Quick Disable (Frontend Only)
Comment out smart date in each dashboard:

```typescript
// useEffect(() => {
//   getSmartDateRange().then(range => {
//     setStartDate(range.startDate);
//     setEndDate(range.endDate);
//   }).catch(console.error);
// }, []);
```

### 2. Full Rollback (Git)
```bash
cd c:\dev\alkana-dashboard
git log --oneline -5  # Find commit before changes
git revert <commit-hash>
```

---

## 📞 SUPPORT

**Issues?** Check these files:
- [SYSTEM_HEALTH_AUDIT_REPORT.md](SYSTEM_HEALTH_AUDIT_REPORT.md) - Original audit findings
- [SMART_DATE_IMPLEMENTATION_SUMMARY.md](SMART_DATE_IMPLEMENTATION_SUMMARY.md) - Implementation details
- [verify_smart_date.py](verify_smart_date.py) - Verification script

**Still stuck?** Run diagnostic:
```bash
# Backend health
curl http://localhost:8000/health

# Database connection
psql -h localhost -U postgres -d alkana_dashboard -c "SELECT COUNT(*) FROM fact_billing;"

# Frontend build
cd web && npm run build
```

---

*Generated: 2026-02-03*  
*Following: ClaudeKit Engineer Methodology*
