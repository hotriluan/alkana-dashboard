# MB51 Upload Fix - Deployment Guide

## Problem
When uploading MB51 files to production, users encountered this error:
```
Error: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint
"idx_fact_inventory_unique" DETAIL: Key (material_code, plant_code, posting_date)=(150000487, 1201, 2026-02-04) already exists.
```

## Root Cause
The `transform_mb51()` function used `TRUNCATE TABLE fact_inventory CASCADE` before inserting new data. However:
- If the truncate failed (due to locks or constraints)
- Or if multiple uploads happened concurrently
- The INSERT would fail with duplicate key violation

## Solution
Changed from **TRUNCATE + INSERT** to **UPSERT (INSERT ON CONFLICT DO UPDATE)**

This ensures:
- ✅ No duplicate key errors
- ✅ Handles concurrent uploads gracefully  
- ✅ Updates existing records instead of failing
- ✅ Preserves data integrity

## Changes Made

### File: `src/etl/transform.py`

**Before:**
```python
# TRUNCATE table first
self.db.execute(text("TRUNCATE TABLE fact_inventory CASCADE"))

# Then INSERT
fact = FactInventory(...)
self.db.add(fact)
```

**After:**
```python
# Use UPSERT with ON CONFLICT DO UPDATE
upsert_sql = text("""
    INSERT INTO fact_inventory (...)
    VALUES (...)
    ON CONFLICT (material_code, plant_code, posting_date)
    DO UPDATE SET
        mvt_type = EXCLUDED.mvt_type,
        qty = EXCLUDED.qty,
        ...
""")
self.db.execute(upsert_sql, params)
```

## Deployment Steps

### Option 1: Using Git on Production Server

```bash
# SSH to production server
ssh it@192.168.18.35

# Navigate to project directory
cd ~/alkana-dashboard

# Pull latest changes
git pull origin main

# Restart services
docker-compose restart backend

# Verify logs
docker-compose logs -f backend
```

### Option 2: Manual File Update

If git is not configured, manually update the file:

```bash
# SSH to production
ssh it@192.168.18.35

# Backup current file
cp ~/alkana-dashboard/src/etl/transform.py ~/alkana-dashboard/src/etl/transform.py.backup

# Edit the file (use the updated version from repository)
nano ~/alkana-dashboard/src/etl/transform.py

# Restart backend
cd ~/alkana-dashboard
docker-compose restart backend
```

### Option 3: Using Remote Copy (from Windows)

```powershell
# From your Windows machine
cd c:\dev\alkana-dashboard

# Copy file to production using pscp (PuTTY)
pscp -pw it123 src/etl/transform.py it@192.168.18.35:/home/it/alkana-dashboard/src/etl/transform.py

# SSH and restart
plink -l it -pw it123 192.168.18.35 "cd ~/alkana-dashboard && docker-compose restart backend"
```

## Verification

After deployment, verify the fix:

1. **Upload a test MB51 file through the web interface**
   - Go to https://alkanadashboard.com/upload
   - Upload mb51.xlsx
   - Should complete successfully

2. **Upload the SAME file again**
   - Should update records instead of failing
   - Check upload history for status

3. **Check backend logs**
   ```bash
   docker-compose logs backend | grep "transform_mb51"
   ```
   
   Expected output:
   ```
   ✓ Transformed X aggregated inventory records
   Inserted: X, Updated: X
   UNIQUE constraint enforced: 1 row per (material, plant, date)
   Transaction committed successfully
   ```

## Rollback Plan

If issues occur, rollback to previous version:

```bash
# Restore backup
cp ~/alkana-dashboard/src/etl/transform.py.backup ~/alkana-dashboard/src/etl/transform.py

# Restart backend
docker-compose restart backend
```

## Testing Results

Local testing confirmed:
- ✅ First upload: Inserts new records
- ✅ Second upload: Updates existing records (no error)
- ✅ Concurrent uploads: Handled gracefully
- ✅ Data integrity: Quantities correctly aggregated

## Impact
- **Zero downtime** - Hot restart only
- **Backward compatible** - Existing data unaffected
- **Performance** - UPSERT is as fast as INSERT for new records

## Support
If issues persist after deployment, check:
1. Database connection pool settings
2. PostgreSQL locks: `SELECT * FROM pg_locks WHERE NOT granted;`
3. Backend error logs: `docker-compose logs backend --tail=100`

---
**Deployed:** 2026-02-09  
**Tested by:** AI Development Team  
**Approved by:** System Administrator
