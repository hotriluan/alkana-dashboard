# Troubleshooting Guide

**Last Updated:** January 13, 2026 | **Version:** v1.0+ | **Coverage:** Backend, Frontend, Database, ETL, Docker

Common issues and solutions for the Alkana Dashboard.

## Table of Contents
- [Quick Diagnostics](#quick-diagnostics)
- [Backend Issues](#backend-issues)
- [Frontend Issues](#frontend-issues)
- [Database Issues](#database-issues)
- [Authentication Issues](#authentication-issues)
- [ETL & Data Issues](#etl--data-issues)
- [Performance Issues](#performance-issues)
- [Docker Issues](#docker-issues)

---

## Quick Diagnostics

### Health Check Script

Run this diagnostic script to check all components:

```bash
#!/bin/bash
echo "=== Alkana Dashboard Health Check ==="

# Check backend
echo -n "Backend API: "
if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
    echo "✓ Running"
else
    echo "✗ Not responding"
fi

# Check frontend
echo -n "Frontend: "
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✓ Running"
else
    echo "✗ Not responding"
fi

# Check database
echo -n "PostgreSQL: "
if psql -U alkana_user -d alkana_dashboard -c "SELECT 1" > /dev/null 2>&1; then
    echo "✓ Connected"
else
    echo "✗ Cannot connect"
fi

# Check services (systemd)
echo -n "Backend service: "
systemctl is-active --quiet alkana-backend && echo "✓ Active" || echo "✗ Inactive"

echo -n "Nginx: "
systemctl is-active --quiet nginx && echo "✓ Active" || echo "✗ Inactive"
```

---

## Backend Issues

### Issue: Backend won't start

**Symptoms:**
- `uvicorn` command fails
- `systemctl start alkana-backend` fails
- Port 8000 already in use

**Solutions:**

1. **Check if port is in use:**
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Linux
   sudo lsof -i :8000
   ```
   
   Kill conflicting process:
   ```bash
   # Windows
   taskkill /PID <PID> /F
   
   # Linux
   kill -9 <PID>
   ```

2. **Check Python version:**
   ```bash
   python --version  # Should be 3.11+
   ```
   
   If wrong version, use virtual environment:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Check dependencies:**
   ```bash
   pip list | grep fastapi
   pip install -r requirements.txt --upgrade
   ```

4. **Check environment variables:**
   ```bash
   # Verify .env file exists
   cat .env | grep DATABASE_URL
   
   # Test database connection
   python -c "from src.db.database import engine; print(engine.connect())"
   ```

5. **Check logs:**
   ```bash
   # Systemd logs
   sudo journalctl -u alkana-backend -n 100 --no-pager
   
   # Application logs
   tail -f logs/app.log
   ```

**Common Error Messages:**

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'fastapi'` | Missing dependencies | Run `pip install -r requirements.txt` |
| `sqlalchemy.exc.OperationalError` | Database not accessible | Check DATABASE_URL in .env |
| `Address already in use` | Port 8000 occupied | Kill process or use different port |
| `Permission denied` | Wrong file ownership | Run `chown -R user:user /opt/alkana-dashboard` |

---

### Issue: API returns 500 errors

**Symptoms:**
- All endpoints return 500 Internal Server Error
- Specific endpoints fail

**Solutions:**

1. **Check backend logs:**
   ```bash
   tail -f logs/app.log
   # Look for stack traces
   ```

2. **Test database connection:**
   ```bash
   python -c "
   from src.db.database import SessionLocal
   db = SessionLocal()
   result = db.execute('SELECT 1').fetchone()
   print('DB OK' if result else 'DB Failed')
   db.close()
   "
   ```

3. **Check for missing tables:**
   ```bash
   psql -U alkana_user -d alkana_dashboard -c "\dt" | grep fact_
   # Should see: fact_production, fact_inventory, fact_billing, etc.
   ```
   
   If tables missing:
   ```bash
   python -m src.main init
   ```

4. **Verify data loaded:**
   ```bash
   psql -U alkana_user -d alkana_dashboard -c "SELECT COUNT(*) FROM raw_mb51;"
   # Should return > 0
   ```

5. **Check CORS configuration:**
   
   If errors in browser console about CORS:
   ```python
   # src/api/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:5173"],  # Add your frontend URL
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

---

### Issue: Slow API responses

**Symptoms:**
- Requests take >5 seconds
- Dashboard loads slowly

**Solutions:**

1. **Check database query performance:**
   ```sql
   -- Enable query logging
   ALTER DATABASE alkana_dashboard SET log_statement = 'all';
   ALTER DATABASE alkana_dashboard SET log_duration = on;
   
   -- Check slow queries
   SELECT query, mean_exec_time, calls
   FROM pg_stat_statements
   ORDER BY mean_exec_time DESC
   LIMIT 10;
   ```

2. **Refresh materialized views:**
   ```bash
   python -c "
   from src.db.database import SessionLocal
   db = SessionLocal()
   db.execute('REFRESH MATERIALIZED VIEW view_sales_performance')
   db.execute('REFRESH MATERIALIZED VIEW view_inventory_summary')
   db.commit()
   "
   ```

3. **Check database connection pool:**
   ```python
   # src/db/database.py
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,  # Increase if needed
       max_overflow=40
   )
   ```

4. **Add database indexes:**
   ```sql
   -- Common slow queries - add indexes
   CREATE INDEX IF NOT EXISTS idx_mb51_posting_date ON raw_mb51(posting_date);
   CREATE INDEX IF NOT EXISTS idx_mb51_material ON raw_mb51(material_code);
   CREATE INDEX IF NOT EXISTS idx_production_batch ON fact_production(batch_number);
   ```

See [PERFORMANCE.md](./PERFORMANCE.md) for detailed optimization guide.

---

## Frontend Issues

### Issue: Frontend won't start

**Symptoms:**
- `npm run dev` fails
- Port 5173 already in use

**Solutions:**

1. **Check Node.js version:**
   ```bash
   node --version  # Should be 18+
   npm --version   # Should be 9+
   ```

2. **Clear npm cache and reinstall:**
   ```bash
   cd web
   rm -rf node_modules package-lock.json
   npm cache clean --force
   npm install
   ```

3. **Check for port conflicts:**
   ```bash
   # Windows
   netstat -ano | findstr :5173
   
   # Linux
   lsof -i :5173
   ```
   
   Use different port:
   ```bash
   npm run dev -- --port 3000
   ```

4. **Check for TypeScript errors:**
   ```bash
   npm run type-check
   # Fix any type errors shown
   ```

---

### Issue: White screen / blank dashboard

**Symptoms:**
- Frontend loads but shows blank page
- Console errors in browser

**Solutions:**

1. **Check browser console (F12):**
   - Look for JavaScript errors
   - Check Network tab for failed requests

2. **Verify API connection:**
   ```javascript
   // Check web/.env or web/.env.development
   VITE_API_URL=http://localhost:8000
   ```
   
   Test in browser console:
   ```javascript
   fetch('http://localhost:8000/api/health')
     .then(r => r.json())
     .then(console.log)
   ```

3. **Check CORS errors:**
   
   If console shows CORS error, verify backend CORS settings:
   ```python
   # src/api/main.py
   allow_origins=["http://localhost:5173"]
   ```

4. **Clear browser cache:**
   - Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
   - Or clear cache in browser settings

5. **Rebuild frontend:**
   ```bash
   cd web
   rm -rf dist
   npm run build
   npm run dev
   ```

---

### Issue: Dashboard shows "No data"

**Symptoms:**
- Dashboard loads but charts/tables are empty
- KPIs show 0 or "N/A"

**Solutions:**

1. **Verify backend data:**
   ```bash
   curl http://localhost:8000/api/executive/summary \
     -H "Authorization: Bearer <your-token>"
   ```

2. **Check if ETL ran:**
   ```bash
   psql -U alkana_user -d alkana_dashboard -c "
   SELECT 'raw_mb51' as table_name, COUNT(*) FROM raw_mb51
   UNION ALL
   SELECT 'fact_production', COUNT(*) FROM fact_production
   UNION ALL
   SELECT 'fact_inventory', COUNT(*) FROM fact_inventory;
   "
   ```
   
   If counts are 0:
   ```bash
   python -m src.main load
   python -m src.main transform
   ```

3. **Check date filters:**
   - Ensure date range in dashboard includes data dates
   - Try removing date filters temporarily

4. **Check user permissions:**
   - Verify logged-in user has access to data
   - Try with admin account

---

## Database Issues

### Issue: Cannot connect to database

**Symptoms:**
- `psql: error: connection to server failed`
- Backend shows `OperationalError: could not connect`

**Solutions:**

1. **Check PostgreSQL is running:**
   ```bash
   # Windows
   Get-Service -Name postgresql*
   
   # Linux
   sudo systemctl status postgresql
   ```
   
   Start if stopped:
   ```bash
   # Windows
   Start-Service postgresql-x64-15
   
   # Linux
   sudo systemctl start postgresql
   ```

2. **Test connection:**
   ```bash
   psql -U alkana_user -d alkana_dashboard -h localhost
   # Enter password when prompted
   ```

3. **Check pg_hba.conf:**
   ```bash
   # Linux: /etc/postgresql/15/main/pg_hba.conf
   # Windows: C:\Program Files\PostgreSQL\15\data\pg_hba.conf
   
   # Should have:
   host    alkana_dashboard    alkana_user    127.0.0.1/32    md5
   ```
   
   Reload PostgreSQL:
   ```bash
   sudo systemctl reload postgresql
   ```

4. **Check postgresql.conf:**
   ```bash
   # Ensure PostgreSQL is listening
   listen_addresses = 'localhost'  # or '*' for remote
   port = 5432
   ```

5. **Verify credentials:**
   ```bash
   # Test credentials
   psql postgresql://alkana_user:password@localhost:5432/alkana_dashboard
   ```

---

### Issue: Database locked / deadlock errors

**Symptoms:**
- `ERROR:  deadlock detected`
- ETL hangs or times out

**Solutions:**

1. **Check for long-running queries:**
   ```sql
   SELECT pid, usename, query, state, query_start
   FROM pg_stat_activity
   WHERE state != 'idle'
   AND query_start < NOW() - INTERVAL '5 minutes'
   ORDER BY query_start;
   ```

2. **Kill blocking queries:**
   ```sql
   -- Find blocking PID
   SELECT pid FROM pg_stat_activity WHERE state = 'active';
   
   -- Kill it
   SELECT pg_terminate_backend(<pid>);
   ```

3. **Check for locks:**
   ```sql
   SELECT locktype, relation::regclass, mode, granted
   FROM pg_locks
   WHERE NOT granted;
   ```

4. **Restart PostgreSQL (last resort):**
   ```bash
   sudo systemctl restart postgresql
   ```

---

### Issue: Disk space full

**Symptoms:**
- `ERROR:  could not write to file: No space left on device`
- Database writes fail

**Solutions:**

1. **Check disk usage:**
   ```bash
   df -h
   # Look for 90%+ usage
   ```

2. **Clean PostgreSQL logs:**
   ```bash
   # Find large log files
   sudo du -sh /var/log/postgresql/*
   
   # Truncate old logs
   sudo truncate -s 0 /var/log/postgresql/postgresql-15-main.log.1
   ```

3. **Vacuum database:**
   ```sql
   VACUUM FULL ANALYZE;
   ```

4. **Check table sizes:**
   ```sql
   SELECT schemaname, tablename, 
          pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables
   WHERE schemaname = 'public'
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
   LIMIT 10;
   ```

5. **Archive old data:**
   ```sql
   -- Move old raw data to archive table
   CREATE TABLE raw_mb51_archive AS 
   SELECT * FROM raw_mb51 WHERE posting_date < '2024-01-01';
   
   DELETE FROM raw_mb51 WHERE posting_date < '2024-01-01';
   ```

---

## Authentication Issues

### Issue: Cannot login

**Symptoms:**
- Login shows "Invalid credentials"
- JWT token errors

**Solutions:**

1. **Verify user exists:**
   ```bash
   psql -U alkana_user -d alkana_dashboard -c "SELECT username, role, is_active FROM users;"
   ```

2. **Reset password:**
   ```bash
   python -c "
   from src.db.database import SessionLocal
   from src.db.auth_models import User
   from src.core.auth import get_password_hash
   
   db = SessionLocal()
   user = db.query(User).filter(User.username == 'admin').first()
   user.hashed_password = get_password_hash('new-password')
   db.commit()
   print('Password reset for admin')
   "
   ```

3. **Check user is active:**
   ```sql
   UPDATE users SET is_active = true WHERE username = 'admin';
   ```

4. **Verify JWT secret:**
   ```bash
   # Check .env has JWT_SECRET_KEY set
   grep JWT_SECRET_KEY .env
   ```

---

### Issue: Token expired / 401 errors

**Symptoms:**
- API returns "Could not validate credentials"
- Logged out unexpectedly

**Solutions:**

1. **Re-login to get new token**
   - Frontend should handle this automatically
   - Or manually login again

2. **Increase token expiration:**
   ```bash
   # .env
   JWT_EXPIRATION_MINUTES=1440  # 24 hours (default)
   # Increase to 10080 for 7 days
   ```

3. **Clear browser localStorage:**
   ```javascript
   // Browser console
   localStorage.clear();
   // Then re-login
   ```

---

## ETL & Data Issues

### Issue: ETL fails to load data

**Symptoms:**
- `python -m src.main load` fails
- "File not found" errors

**Solutions:**

1. **Verify data files exist:**
   ```bash
   ls -lh demodata/
   # Should see: MB51.xlsx, ZRSD002.xlsx, etc.
   ```

2. **Check file permissions:**
   ```bash
   chmod 644 demodata/*.xlsx
   ```

3. **Check file format:**
   ```bash
   # Files should be Excel format (.xlsx)
   file demodata/MB51.xlsx
   # Output: Microsoft Excel 2007+
   ```

4. **Run with verbose logging:**
   ```bash
   python -m src.main load --verbose
   # Check for specific error messages
   ```

5. **Check Excel file structure:**
   ```python
   import pandas as pd
   df = pd.read_excel('demodata/MB51.xlsx')
   print(df.columns)
   # Verify expected columns exist
   ```

---

### Issue: Data not updating

**Symptoms:**
- Dashboard shows old data
- New Excel files not reflected

**Solutions:**

1. **Check ETL last run:**
   ```sql
   SELECT MAX(created_at) FROM raw_mb51;
   -- Compare to current date
   ```

2. **Manual ETL run:**
   ```bash
   # Backup data first
   pg_dump alkana_dashboard > backup.sql
   
   # Clear and reload
   python -m src.main clear-raw
   python -m src.main load
   python -m src.main transform
   ```

3. **Check cron job:**
   ```bash
   crontab -l | grep alkana
   # Verify ETL scheduled
   ```

4. **Check ETL logs:**
   ```bash
   tail -f logs/etl.log
   # Look for errors during load/transform
   ```

---

### Issue: Incorrect calculations / metrics

**Symptoms:**
- KPIs don't match expectations
- Yield percentages seem wrong

**Solutions:**

1. **Verify raw data:**
   ```sql
   -- Check sample MB51 record
   SELECT * FROM raw_mb51 LIMIT 5;
   ```

2. **Check transformation logic:**
   ```bash
   # Review netting algorithm
   cat src/core/netting.py | grep -A 20 "def calculate_net_stock"
   ```

3. **Manual calculation verification:**
   ```sql
   -- Check inventory netting for specific material
   SELECT material_code, movement_type, quantity, posting_date
   FROM raw_mb51
   WHERE material_code = 'P01-12345'
   ORDER BY posting_date;
   
   -- Compare to fact table
   SELECT * FROM fact_inventory WHERE material_code = 'P01-12345';
   ```

4. **Check for duplicates:**
   ```sql
   SELECT document_number, COUNT(*)
   FROM raw_mb51
   GROUP BY document_number
   HAVING COUNT(*) > 1;
   ```

5. **Verify UOM conversions:**
   ```sql
   SELECT material_code, base_uom, sales_uom, conversion_factor
   FROM dim_material
   WHERE material_code = 'P01-12345';
   ```

---

## Performance Issues

### Issue: Dashboard loads slowly

**Symptoms:**
- Page takes >10 seconds to load
- Charts lag or freeze

**Solutions:**

1. **Check materialized view refresh:**
   ```sql
   -- Check view freshness
   SELECT schemaname, matviewname, 
          pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) AS size
   FROM pg_matviews;
   
   -- Refresh if stale
   REFRESH MATERIALIZED VIEW CONCURRENTLY view_sales_performance;
   ```

2. **Optimize queries:**
   ```sql
   -- Use EXPLAIN ANALYZE
   EXPLAIN ANALYZE SELECT * FROM fact_production LIMIT 100;
   ```

3. **Add indexes:**
   ```sql
   CREATE INDEX idx_fact_production_date ON fact_production(production_date);
   CREATE INDEX idx_fact_inventory_material ON fact_inventory(material_code);
   ```

4. **Limit data returned:**
   ```typescript
   // Add pagination to frontend
   const { data } = await api.get('/inventory/current?page=1&page_size=50');
   ```

5. **Enable caching:**
   ```python
   # Add Redis caching (future enhancement)
   ```

See [PERFORMANCE.md](./PERFORMANCE.md) for comprehensive optimization guide.

---

## Docker Issues

### Issue: Docker containers won't start

**Symptoms:**
- `docker-compose up` fails
- Containers restart repeatedly

**Solutions:**

1. **Check Docker daemon:**
   ```bash
   docker info
   # Verify Docker is running
   ```

2. **Check logs:**
   ```bash
   docker-compose logs backend
   docker-compose logs postgres
   ```

3. **Rebuild images:**
   ```bash
   docker-compose down -v
   docker-compose build --no-cache
   docker-compose up -d
   ```

4. **Check ports:**
   ```bash
   docker-compose ps
   # Ensure no port conflicts
   ```

5. **Check volumes:**
   ```bash
   docker volume ls
   docker volume inspect alkana_postgres_data
   ```

---

### Issue: Database data lost after restart

**Symptoms:**
- Data disappears after `docker-compose down`

**Solution:**

Don't use `-v` flag when stopping:
```bash
# WRONG: Deletes volumes
docker-compose down -v

# CORRECT: Preserves volumes
docker-compose down
```

---

## Getting Help

If issues persist:

1. **Collect diagnostics:**
   ```bash
   # System info
   uname -a
   python --version
   node --version
   psql --version
   
   # Service status
   systemctl status alkana-backend postgresql nginx
   
   # Logs
   tail -n 100 logs/app.log
   tail -n 100 /var/log/postgresql/postgresql-15-main.log
   ```

2. **Check GitHub Issues:**
   - Search existing issues
   - Create new issue with diagnostics

3. **Contact Support:**
   - Email: support@yourcompany.com
   - Include: OS, version, error messages, logs

4. **Documentation:**
   - [README.md](../README.md)
   - [DEPLOYMENT.md](./DEPLOYMENT.md)
   - [API_REFERENCE.md](./API_REFERENCE.md)

---

## Common Log Messages

| Log Message | Severity | Meaning | Action |
|-------------|----------|---------|--------|
| `Database connection pool exhausted` | ERROR | Too many concurrent connections | Increase pool_size in database.py |
| `Materialized view is stale` | WARNING | View needs refresh | Run REFRESH MATERIALIZED VIEW |
| `JWT token expired` | INFO | Normal token expiration | User needs to re-login |
| `File not found: demodata/MB51.xlsx` | ERROR | Missing data file | Place Excel file in demodata/ |
| `Deadlock detected` | ERROR | Concurrent transaction conflict | Retry operation |
| `Memory usage >80%` | WARNING | High memory pressure | Restart services or increase RAM |

---

## Debug Mode

Enable debug mode for detailed logging:

```bash
# .env
DEBUG=true
LOG_LEVEL=DEBUG
```

Restart backend:
```bash
sudo systemctl restart alkana-backend
```

**Warning:** Don't enable DEBUG in production - sensitive data may be logged.

---

## Performance Benchmarks

Expected performance metrics:

| Metric | Expected | Troubleshoot if |
|--------|----------|----------------|
| API response time | <200ms | >1 second |
| Dashboard load time | <3 seconds | >10 seconds |
| Database queries | <100ms | >500ms |
| ETL load time | <5 minutes | >30 minutes |
| Memory usage | <70% | >90% |
| CPU usage | <50% | >80% sustained |

---

**Last Updated:** January 13, 2026
