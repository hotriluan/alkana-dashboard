# Performance Monitoring Guide

Guide for monitoring ETL performance and detecting regressions in production.

## Table of Contents

- [Overview](#overview)
- [ETL Performance Metrics](#etl-performance-metrics)
- [Log Query Examples](#log-query-examples)
- [Performance Regression Detection](#performance-regression-detection)
- [Alerting Thresholds](#alerting-thresholds)
- [Troubleshooting Slow Queries](#troubleshooting-slow-queries)

## Overview

**Purpose:** Track ETL transform execution times to detect performance regressions early.

**Target Metrics (Feb 2026 baseline):**
- `transform_cooispi`: < 10s (baseline: 5.43s)
- `transform_lead_time`: < 15s (baseline: 8.97s)
- Total ETL: < 30s (baseline: 14.40s)

**Alert Thresholds:**
- ⚠️ Warning: >150% of baseline (e.g., `transform_cooispi` > 8.15s)
- 🚨 Critical: >200% of baseline (e.g., `transform_cooispi` > 10.86s)

## ETL Performance Metrics

### Key Performance Indicators

1. **Transform Execution Time**: Duration of each transform function
2. **Database Query Time**: Time spent in database operations
3. **Record Processing Rate**: Records processed per second
4. **Memory Usage**: Peak memory during ETL
5. **Database Connection Pool**: Active/idle connections

### Logging Performance Metrics

**File:** `src/etl/transform.py`

**Current Implementation:**
```python
import time
import logging

logger = logging.getLogger(__name__)

def transform_cooispi(db: Session):
    """Transform COOISPI data with performance logging"""
    start_time = time.time()
    
    try:
        # ... transformation logic ...
        
        duration = time.time() - start_time
        logger.info(f"transform_cooispi completed in {duration:.2f}s")
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"transform_cooispi failed after {duration:.2f}s: {e}")
        raise
```

**Enhanced Logging (Recommended):**
```python
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def log_performance(func):
    """Decorator to log function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        func_name = func.__name__
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start
            
            # Structured logging for easy parsing
            logger.info(
                f"PERF: {func_name} | duration={duration:.2f}s | status=success"
            )
            return result
            
        except Exception as e:
            duration = time.time() - start
            logger.error(
                f"PERF: {func_name} | duration={duration:.2f}s | status=error | error={str(e)}"
            )
            raise
    
    return wrapper

@log_performance
def transform_cooispi(db: Session):
    """Transform COOISPI data"""
    # ... implementation ...
    pass

@log_performance
def transform_lead_time(db: Session):
    """Transform lead time data"""
    # ... implementation ...
    pass
```

## Log Query Examples

### View Recent ETL Performance

**Docker Logs (production):**
```bash
# SSH to production server
ssh alkana@192.168.18.35

# View last 100 PERF logs
docker logs alkana-backend 2>&1 | grep "PERF:" | tail -100

# Extract transform_cooispi times from last 24 hours
docker logs --since 24h alkana-backend 2>&1 | \
  grep "PERF: transform_cooispi" | \
  grep -oP 'duration=\K[0-9.]+' | \
  awk '{sum+=$1; count++} END {print "Avg:", sum/count, "Count:", count}'

# Find slow executions (>10s)
docker logs --since 24h alkana-backend 2>&1 | \
  grep "PERF:" | \
  awk -F'duration=' '{if ($2 > 10) print $0}'
```

### Parse Structured Logs

```python
# scripts/analyze_perf_logs.py
import re
from collections import defaultdict
from datetime import datetime

def parse_perf_logs(log_file: str):
    """Parse performance logs and calculate statistics"""
    
    perf_pattern = re.compile(
        r'PERF: (?P<func>\w+) \| duration=(?P<duration>[0-9.]+)s \| status=(?P<status>\w+)'
    )
    
    metrics = defaultdict(list)
    
    with open(log_file, 'r') as f:
        for line in f:
            match = perf_pattern.search(line)
            if match:
                func = match.group('func')
                duration = float(match.group('duration'))
                status = match.group('status')
                
                if status == 'success':
                    metrics[func].append(duration)
    
    # Calculate statistics
    for func, durations in metrics.items():
        avg = sum(durations) / len(durations)
        min_dur = min(durations)
        max_dur = max(durations)
        p95 = sorted(durations)[int(len(durations) * 0.95)]
        
        print(f"{func}:")
        print(f"  Count: {len(durations)}")
        print(f"  Avg: {avg:.2f}s")
        print(f"  Min: {min_dur:.2f}s")
        print(f"  Max: {max_dur:.2f}s")
        print(f"  P95: {p95:.2f}s")
        print()

if __name__ == '__main__':
    # Get logs from Docker
    import subprocess
    subprocess.run(
        ["ssh", "alkana@192.168.18.35", 
         "docker logs --since 24h alkana-backend > /tmp/backend.log"],
        shell=True
    )
    parse_perf_logs("/tmp/backend.log")
```

## Performance Regression Detection

### Baseline Performance (Feb 2026)

| Transform | P50 (median) | P95 | P99 | Max |
|-----------|--------------|-----|-----|-----|
| `transform_cooispi` | 5.43s | 6.50s | 7.20s | 8.00s |
| `transform_lead_time` | 8.97s | 10.50s | 11.80s | 13.00s |
| **Total ETL** | 14.40s | 17.00s | 19.00s | 21.00s |

**Environment:** PostgreSQL on 192.168.18.35, 14,938 production records

### Regression Detection Script

```python
# scripts/check_perf_regression.py
import subprocess
import re
from datetime import datetime, timedelta

BASELINE = {
    'transform_cooispi': 5.43,
    'transform_lead_time': 8.97,
}

WARNING_THRESHOLD = 1.5  # 150% of baseline
CRITICAL_THRESHOLD = 2.0  # 200% of baseline

def get_recent_perf(func_name: str, hours: int = 24):
    """Get recent performance metrics from Docker logs"""
    
    # SSH and get logs
    cmd = f"ssh alkana@192.168.18.35 \
           'docker logs --since {hours}h alkana-backend 2>&1 | \
           grep \"PERF: {func_name}\" | \
           grep -oP \"duration=\\K[0-9.]+\"'"
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    durations = [float(x) for x in result.stdout.strip().split('\n') if x]
    
    if not durations:
        return None
    
    avg = sum(durations) / len(durations)
    max_dur = max(durations)
    
    return {'avg': avg, 'max': max_dur, 'count': len(durations)}

def check_regression():
    """Check for performance regressions"""
    
    print(f"Performance Regression Check - {datetime.now()}\n")
    print(f"{'Transform':<25} {'Baseline':<10} {'Current Avg':<12} {'Status'}")
    print("-" * 70)
    
    alerts = []
    
    for func, baseline in BASELINE.items():
        metrics = get_recent_perf(func)
        
        if not metrics:
            print(f"{func:<25} {baseline:.2f}s     {'N/A':<12} No data")
            continue
        
        avg = metrics['avg']
        max_dur = metrics['max']
        ratio = avg / baseline
        
        if ratio >= CRITICAL_THRESHOLD:
            status = f"🚨 CRITICAL ({ratio:.0%})"
            alerts.append(f"CRITICAL: {func} is {ratio:.0%} slower (baseline: {baseline:.2f}s, current: {avg:.2f}s)")
        elif ratio >= WARNING_THRESHOLD:
            status = f"⚠️  WARNING ({ratio:.0%})"
            alerts.append(f"WARNING: {func} is {ratio:.0%} slower (baseline: {baseline:.2f}s, current: {avg:.2f}s)")
        else:
            status = f"✅ OK ({ratio:.0%})"
        
        print(f"{func:<25} {baseline:.2f}s     {avg:.2f}s      {status}")
        print(f"{'':25} {'':10} Max: {max_dur:.2f}s, Runs: {metrics['count']}")
    
    if alerts:
        print("\n🚨 ALERTS:")
        for alert in alerts:
            print(f"  - {alert}")
    else:
        print("\n✅ All transforms within normal range")

if __name__ == '__main__':
    check_regression()
```

**Run Daily via Cron:**
```bash
# Add to crontab on production server
# Run regression check daily at 6 AM
0 6 * * * /usr/bin/python3 /app/scripts/check_perf_regression.py >> /var/log/perf_check.log
```

## Alerting Thresholds

### Warning Level (150% of baseline)

**Triggers:**
- `transform_cooispi` > 8.15s
- `transform_lead_time` > 13.46s
- Total ETL > 21.60s

**Action:**
1. Check database connection pool usage
2. Review recent code changes
3. Verify database indexes are still present
4. Check for data volume increase

### Critical Level (200% of baseline)

**Triggers:**
- `transform_cooispi` > 10.86s
- `transform_lead_time` > 17.94s
- Total ETL > 28.80s

**Action:**
1. Immediately investigate root cause
2. Check for missing indexes: `SELECT * FROM pg_indexes WHERE tablename LIKE 'raw_%';`
3. Run `EXPLAIN ANALYZE` on slow queries
4. Check database disk space and memory
5. Consider rolling back recent changes

## Troubleshooting Slow Queries

### Step 1: Identify Slow Transform

```bash
# Get performance logs from last 24h
ssh alkana@192.168.18.35
docker logs --since 24h alkana-backend 2>&1 | grep "PERF:" | sort -t'=' -k2 -n -r | head -20
```

### Step 2: Check Database Indexes

```sql
-- Connect to production database
psql -U alkana_user -d alkana_dashboard

-- Verify critical indexes exist
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('raw_mb51', 'fact_lead_time', 'fact_production_record')
ORDER BY tablename, indexname;

-- Expected indexes:
-- idx_mb51_batch_mvt_date
-- idx_mb51_material_date
-- idx_leadtime_batch_date
-- idx_production_batch_date
```

### Step 3: Analyze Query Execution Plan

```sql
-- Example: Analyze production chain query
EXPLAIN ANALYZE
SELECT 
    batch_number,
    movement_type,
    posting_date,
    quantity
FROM raw_mb51
WHERE movement_type IN ('101', '261', '311', '301')
    AND batch_number IN (SELECT DISTINCT batch_number FROM fact_lead_time)
ORDER BY batch_number, posting_date;

-- Look for:
-- ✅ "Index Scan" (good)
-- ❌ "Seq Scan" on large tables (bad - missing index)
-- ✅ Execution time < 100ms
```

### Step 4: Check Database Stats

```sql
-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Unused indexes (idx_scan = 0)
SELECT indexname
FROM pg_stat_user_indexes
WHERE schemaname = 'public' AND idx_scan = 0;
```

### Step 5: Database Vacuum and Analyze

```sql
-- Vacuum and analyze all tables
VACUUM ANALYZE;

-- Or specific tables
VACUUM ANALYZE raw_mb51;
VACUUM ANALYZE fact_lead_time;
VACUUM ANALYZE fact_production_record;

-- Check last vacuum time
SELECT 
    schemaname,
    tablename,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY last_analyze;
```

## Best Practices

1. **Log All Transform Execution Times**: Use `@log_performance` decorator consistently
2. **Run Regression Checks Daily**: Automated cron job to detect slowdowns early
3. **Monitor Database Size**: Track table/index sizes for capacity planning
4. **Verify Indexes Monthly**: Check `pg_indexes` to ensure critical indexes exist
5. **Vacuum Weekly**: Schedule `VACUUM ANALYZE` to maintain database performance
6. **Baseline After Changes**: Re-establish baselines after major optimizations
7. **Document Alerts**: Log all performance alerts with root cause analysis

---

**Last Updated:** February 9, 2026  
**Baseline Established:** February 9, 2026 (commit: 709b86f)  
**Next Review:** March 9, 2026
