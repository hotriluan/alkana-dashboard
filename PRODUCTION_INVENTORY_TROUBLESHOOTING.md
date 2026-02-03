# 🔧 Production Troubleshooting Guide: Inventory Top Movers & Dead Stock

**Issue:** Dashboard shows data on development but not on production (alkanadashboard.com)

## Root Cause Analysis

Based on the screenshots, production shows:
- Empty "Top 10 High Velocity Items" (green panel)
- Empty "Top 10 Dead Stock Risks" (red panel)

While development shows proper data with movement counts.

## Possible Causes

### 1. **Production Database is Empty** (MOST LIKELY)
   - Production database has no `fact_inventory` data loaded
   - The inventory pipeline hasn't run on production

### 2. **Production Database Has Wrong Movement Types**
   - Data exists but uses different movement type codes
   - Query filters for (999, 601, 261) but production has different types

### 3. **Date Range Mismatch**
   - Production data exists but outside the 90-day default range
   - Old data that's been archived or purged

### 4. **API Connection Issues**
   - Frontend can't reach backend API
   - CORS or authentication errors

---

## Diagnostic Steps

### Step 1: Run Production Database Diagnostic

SSH into production server and run:

```bash
# Copy diagnostic script to production
scp diagnose_production_inventory.py user@alkanadashboard.com:/app/

# SSH into production
ssh user@alkanadashboard.com

# Run diagnostic
cd /app
python diagnose_production_inventory.py
```

**What to look for:**
- Total records in `fact_inventory` table
- Available movement types (999, 601, 261)
- Date range coverage
- Material code distribution

### Step 2: Check Backend Logs

```bash
# On production server
docker logs alkana-backend --tail=100 | grep "Top Movers"
```

**Look for:**
- Query parameters received
- Results count (e.g., "Results: 0 top movers, 0 dead stock items")
- Warning messages about missing data
- Error stack traces

### Step 3: Check Browser Console

On alkanadashboard.com:
1. Open Developer Tools (F12)
2. Go to Console tab
3. Look for: `🔍 Top Movers API Response:`
4. Check if API returns empty arrays: `{ top_movers: [], dead_stock: [] }`

### Step 4: Test API Endpoint Directly

```bash
# Get auth token first
curl -X POST https://alkanadashboard.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'

# Test inventory endpoint (replace TOKEN)
curl -X GET "https://alkanadashboard.com/api/v1/dashboards/inventory/top-movers-and-dead-stock?limit=10" \
  -H "Authorization: Bearer TOKEN" | jq
```

**Expected response if working:**
```json
{
  "top_movers": [
    {
      "material_code": "150000472",
      "material_description": "Material Name",
      "velocity_score": 3560,
      "material_type": "RM"
    },
    ...
  ],
  "dead_stock": [ ... ]
}
```

**Response if no data:**
```json
{
  "top_movers": [],
  "dead_stock": [],
  "warning": "No inventory data available. Please upload data first."
}
```

---

## Solutions

### Solution 1: Load Data into Production Database

If database is empty:

```bash
# On production server
cd /app

# Option A: Upload via API (recommended)
# 1. Go to https://alkanadashboard.com/upload
# 2. Upload MB51 Excel files
# 3. Wait for processing

# Option B: Manual ETL pipeline
python -m src.main load       # Load source data
python -m src.main transform  # Transform to warehouse
```

### Solution 2: Update Movement Type Configuration

If production uses different movement types:

```bash
# Check actual movement types
psql $DATABASE_URL -c "SELECT DISTINCT mvt_type, COUNT(*) FROM fact_inventory GROUP BY mvt_type;"

# Edit configuration
# File: src/core/inventory_analytics.py
# Line 43: Update OUTBOUND_MVT_TYPES to match production data
```

Example fix:
```python
# OLD
OUTBOUND_MVT_TYPES = [999, 601, 261]

# NEW (if production uses different codes)
OUTBOUND_MVT_TYPES = [101, 102, 201]  # Update based on psql query
```

### Solution 3: Adjust Date Range

If data is old:

```python
# In src/core/inventory_analytics.py, line 207
# Change default from 90 to 180 or 365 days

# OLD
if start_date is None:
    start_date = end_date - timedelta(days=90)

# NEW
if start_date is None:
    start_date = end_date - timedelta(days=180)  # 6 months
```

### Solution 4: Fix Frontend API Connection

Check [web/.env](web/.env) or nginx config:

```bash
# Development
VITE_API_URL=http://localhost:8000

# Production (should auto-detect or set explicitly)
VITE_API_URL=https://alkanadashboard.com
```

Rebuild frontend if needed:
```bash
cd web
npm run build
```

---

## Verification

After applying fixes:

1. **Check backend logs:**
   ```bash
   docker logs alkana-backend --tail=50 | grep "Top Movers"
   # Should show: "Results: 10 top movers, 10 dead stock items"
   ```

2. **Check browser console:**
   - Refresh https://alkanadashboard.com/inventory
   - Console should show non-empty API response
   
3. **Visual check:**
   - Green panel should show materials with movement counts > 0
   - Red panel should show materials with stock > 0

---

## Quick Reference

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| Both panels empty | No database data | Load data (Solution 1) |
| Console shows `warning: "No inventory data available"` | Empty fact_inventory table | Run ETL pipeline |
| API returns `[]` arrays | Wrong movement types | Update OUTBOUND_MVT_TYPES (Solution 2) |
| Old data only | Date range too narrow | Adjust timedelta (Solution 3) |
| API 404/500 error | Backend connection issue | Check nginx/docker config |

---

## Development vs Production Comparison

### Development (Working) ✅
```
Database: localhost:5432/alkana_dashboard
Records: 1,098,392
Movement types: 261 (507K), 601 (170K)
Date range: 2024-12-31 to 2026-02-03
Result: 10 top movers, 10 dead stock
```

### Production (Not Working) ❓
```
Database: postgres:5432/alkana_dashboard (Docker)
Records: UNKNOWN - need to check
Movement types: UNKNOWN - need to check
Date range: UNKNOWN - need to check
Result: 0 top movers, 0 dead stock
```

**Action:** Run diagnostic script to fill in the unknowns.

---

## Prevention

To avoid this in the future:

1. **Automated data sync:** Set up cron job to sync data from dev to production
2. **Health checks:** Add monitoring for inventory data freshness
3. **CI/CD validation:** Test data availability before deploying
4. **Documentation:** Document production data load process

---

## Support

If issue persists after following this guide:

1. Share diagnostic script output
2. Share backend logs (last 100 lines)
3. Share browser console output
4. Share API response from curl test

**Created:** 2026-02-03  
**Last Updated:** 2026-02-03
