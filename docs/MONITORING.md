# Monitoring and Observability

Comprehensive guide to monitoring the Alkana Dashboard in production.

## Table of Contents

- [Overview](#overview)
- [Logging Strategy](#logging-strategy)
- [Metrics Collection](#metrics-collection)
- [Health Checks](#health-checks)
- [Alerting Setup](#alerting-setup)
- [Dashboard Monitoring](#dashboard-monitoring)
- [Database Monitoring](#database-monitoring)
- [Infrastructure Monitoring](#infrastructure-monitoring)
- [Log Aggregation](#log-aggregation)
- [Troubleshooting](#troubleshooting)

## Overview

### Monitoring Stack

**Recommended Tools:**
- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization and alerting
- **Loki** - Log aggregation (optional)
- **Alertmanager** - Alert routing and grouping
- **PostgreSQL** - Built-in monitoring views

**Minimal Setup:**
- Application logs (stdout/file)
- Health check endpoints
- Database monitoring queries
- Simple uptime monitoring (UptimeRobot, Pingdom)

## Logging Strategy

### Backend Logging

**Configuration** (`backend/app/core/config.py`):

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Console output
        RotatingFileHandler(
            LOG_FILE,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
    ]
)
```

**Log Levels:**
- **DEBUG** - Detailed diagnostic information
- **INFO** - General informational messages
- **WARNING** - Warning messages (non-critical)
- **ERROR** - Error messages (handled exceptions)
- **CRITICAL** - Critical errors (system failures)

**Best Practices:**

```python
import logging

logger = logging.getLogger(__name__)

# Good logging examples
logger.info(f"Processing ETL for table: {table_name}")
logger.warning(f"Missing data for batch: {batch_id}")
logger.error(f"Database connection failed: {str(e)}", exc_info=True)

# Include context
logger.info(
    "API request",
    extra={
        "endpoint": "/api/v1/inventory",
        "user": username,
        "duration_ms": duration,
        "status_code": 200
    }
)
```

### Log Rotation

**Using logrotate** (Linux):

```bash
# /etc/logrotate.d/alkana-dashboard
/var/log/alkana-dashboard/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload alkana-dashboard
    endscript
}
```

## Metrics Collection

### Prometheus Integration

**Install Prometheus client:**

```bash
pip install prometheus-client
```

**Backend metrics** (`backend/app/monitoring.py`):

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import APIRouter

router = APIRouter()

# Define metrics
api_requests = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"]
)

api_duration = Histogram(
    "api_duration_seconds",
    "API request duration",
    ["method", "endpoint"]
)

etl_duration = Histogram(
    "etl_duration_seconds",
    "ETL processing duration",
    ["table"]
)

db_connections = Gauge(
    "db_connections_active",
    "Active database connections"
)

# Metrics endpoint
@router.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

**Middleware for automatic tracking:**

```python
from fastapi import Request
import time

@app.middleware("http")
async def track_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    api_requests.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    api_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

### Key Metrics to Track

**Application Metrics:**
- API request rate (requests/second)
- API response time (p50, p95, p99)
- Error rate by endpoint
- Active database connections
- ETL processing duration
- Cache hit rate

**Business Metrics:**
- Daily data refresh status
- Alert count by type
- Dashboard active users
- Query execution time by dashboard

## Health Checks

### Endpoint Implementation

**Backend** (`backend/app/routers/health.py`):

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import redis

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Comprehensive health check"""
    
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Database check
    try:
        db.execute("SELECT 1")
        health["components"]["database"] = {
            "status": "healthy",
            "response_time_ms": 5
        }
    except Exception as e:
        health["status"] = "degraded"
        health["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check recent ETL runs
    try:
        last_etl = db.execute("""
            SELECT MAX(created_at) 
            FROM raw_mb51
        """).scalar()
        
        if last_etl:
            age_hours = (datetime.utcnow() - last_etl).total_seconds() / 3600
            health["components"]["etl"] = {
                "status": "healthy" if age_hours < 25 else "stale",
                "last_run": last_etl.isoformat(),
                "age_hours": round(age_hours, 1)
            }
    except Exception as e:
        health["components"]["etl"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    return health
```

### Monitoring Health Endpoints

**Docker Compose health check:**

```yaml
services:
  backend:
    image: alkana-dashboard-backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**External monitoring** (UptimeRobot, Pingdom):
- Monitor: `https://dashboard.yourcompany.com/api/v1/health`
- Interval: 5 minutes
- Alert on: HTTP != 200 or timeout

## Alerting Setup

### Alert Rules (Prometheus)

**Configuration** (`prometheus/alerts.yml`):

```yaml
groups:
  - name: alkana_dashboard
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          rate(api_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"
      
      # Slow API responses
      - alert: SlowAPIResponses
        expr: |
          histogram_quantile(0.95, api_duration_seconds_bucket) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "API responses are slow"
          description: "95th percentile is {{ $value }}s"
      
      # ETL not running
      - alert: ETLStale
        expr: |
          (time() - etl_last_run_timestamp) > 86400
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "ETL has not run in 24+ hours"
          description: "Last ETL run was {{ $value }}s ago"
      
      # Database connections exhausted
      - alert: DatabaseConnectionsHigh
        expr: |
          db_connections_active > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool near capacity"
          description: "Active connections: {{ $value }}"
```

### Alertmanager Configuration

**Setup** (`alertmanager/config.yml`):

```yaml
global:
  resolve_timeout: 5m
  
route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'team-email'
  
  routes:
    - match:
        severity: critical
      receiver: 'team-pagerduty'
      continue: true
    
    - match:
        severity: warning
      receiver: 'team-slack'

receivers:
  - name: 'team-email'
    email_configs:
      - to: 'team@yourcompany.com'
        from: 'alerts@yourcompany.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@yourcompany.com'
        auth_password: '${SMTP_PASSWORD}'
  
  - name: 'team-slack'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#dashboard-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
  
  - name: 'team-pagerduty'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_SERVICE_KEY}'
```

## Dashboard Monitoring

### Grafana Dashboards

**Key Panels:**

1. **API Performance**
   - Request rate (per endpoint)
   - Response time (p50, p95, p99)
   - Error rate
   - Active connections

2. **ETL Status**
   - Last run time by table
   - Processing duration
   - Row counts processed
   - Error count

3. **Database Metrics**
   - Connection pool usage
   - Query execution time
   - Table sizes
   - Index usage

4. **Business Metrics**
   - Dashboard page views
   - Active users
   - Alert counts by type
   - Data freshness

**Example Grafana query** (API request rate):

```promql
rate(api_requests_total[5m])
```

**Example Grafana query** (p95 response time):

```promql
histogram_quantile(0.95, 
  rate(api_duration_seconds_bucket[5m])
)
```

## Database Monitoring

### PostgreSQL Monitoring Queries

**Active connections:**

```sql
SELECT 
    count(*) as total_connections,
    count(*) FILTER (WHERE state = 'active') as active,
    count(*) FILTER (WHERE state = 'idle') as idle,
    count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
FROM pg_stat_activity
WHERE datname = 'alkana_dashboard';
```

**Slow queries:**

```sql
SELECT 
    pid,
    now() - query_start as duration,
    query,
    state
FROM pg_stat_activity
WHERE 
    state != 'idle' 
    AND now() - query_start > interval '30 seconds'
ORDER BY duration DESC;
```

**Table sizes:**

```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

**Materialized view freshness:**

```sql
SELECT 
    schemaname,
    matviewname,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as size,
    last_refresh
FROM pg_matviews
WHERE schemaname = 'public';
```

### Automated Monitoring Script

**Script** (`scripts/monitor_db.py`):

```python
#!/usr/bin/env python3
import psycopg2
from datetime import datetime

def check_database():
    conn = psycopg2.connect(
        dbname="alkana_dashboard",
        user="dashboard_user",
        password="password",
        host="localhost"
    )
    
    cur = conn.cursor()
    
    # Check connection count
    cur.execute("""
        SELECT count(*) 
        FROM pg_stat_activity 
        WHERE datname = 'alkana_dashboard'
    """)
    connections = cur.fetchone()[0]
    print(f"Active connections: {connections}")
    
    # Check last ETL run
    cur.execute("SELECT MAX(created_at) FROM raw_mb51")
    last_etl = cur.fetchone()[0]
    if last_etl:
        age = datetime.now() - last_etl
        print(f"Last ETL run: {age.total_seconds() / 3600:.1f} hours ago")
    
    # Check table sizes
    cur.execute("""
        SELECT 
            tablename,
            pg_size_pretty(pg_total_relation_size('public.'||tablename))
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size('public.'||tablename) DESC
        LIMIT 5
    """)
    print("\nLargest tables:")
    for table, size in cur.fetchall():
        print(f"  {table}: {size}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_database()
```

**Run daily via cron:**

```bash
0 8 * * * /usr/bin/python3 /opt/alkana-dashboard/scripts/monitor_db.py >> /var/log/alkana/db_monitor.log 2>&1
```

## Infrastructure Monitoring

### System Metrics

**Key metrics to track:**
- CPU usage
- Memory usage
- Disk space
- Network I/O
- Docker container status

**Using Prometheus Node Exporter:**

```bash
# Install node exporter
docker run -d \
  --name node-exporter \
  --restart=always \
  -p 9100:9100 \
  -v "/:/host:ro,rslave" \
  prom/node-exporter \
  --path.rootfs=/host
```

**Disk space alert:**

```yaml
- alert: DiskSpaceLow
  expr: |
    (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Disk space below 10%"
    description: "Only {{ $value | humanizePercentage }} remaining"
```

## Log Aggregation

### Loki Setup (Optional)

**Docker Compose** (`docker-compose.monitoring.yml`):

```yaml
version: '3.8'

services:
  loki:
    image: grafana/loki:2.9.0
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    volumes:
      - loki-data:/loki
  
  promtail:
    image: grafana/promtail:2.9.0
    volumes:
      - /var/log:/var/log
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml

volumes:
  loki-data:
```

**Promtail configuration** (`promtail-config.yml`):

```yaml
server:
  http_listen_port: 9080

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: alkana-dashboard
    static_configs:
      - targets:
          - localhost
        labels:
          job: alkana-dashboard
          __path__: /var/log/alkana-dashboard/*.log
```

## Troubleshooting

### Common Issues

**High memory usage:**
```bash
# Check top processes
docker stats alkana-dashboard-backend

# Check backend memory
ps aux | grep uvicorn
```

**Database connection leaks:**
```sql
-- Find idle connections
SELECT * FROM pg_stat_activity 
WHERE state = 'idle in transaction'
AND now() - state_change > interval '5 minutes';

-- Kill stuck connections
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle in transaction';
```

**ETL not running:**
```bash
# Check cron job
crontab -l

# Check ETL logs
tail -f /var/log/alkana-dashboard/etl.log

# Manually trigger ETL
python scripts/run_etl.py
```

## Related Documentation

- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues
- [Performance Guide](PERFORMANCE.md) - Optimization tips
- [Security Guide](SECURITY.md) - Security best practices

---

**Keep monitoring simple and actionable. Focus on metrics that matter.**
