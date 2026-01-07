# Performance Optimization Guide

Comprehensive guide to optimizing the Alkana Dashboard for production performance.

## Table of Contents

- [Overview](#overview)
- [Database Optimization](#database-optimization)
- [API Performance](#api-performance)
- [Frontend Optimization](#frontend-optimization)
- [Caching Strategies](#caching-strategies)
- [ETL Performance](#etl-performance)
- [Query Optimization](#query-optimization)
- [Connection Pooling](#connection-pooling)
- [Monitoring Performance](#monitoring-performance)
- [Load Testing](#load-testing)

## Overview

### Performance Targets

**Backend API:**
- Response time (p95): < 500ms
- Response time (p99): < 1000ms
- Throughput: > 100 requests/second
- Database connection pool: 80% utilization max

**Frontend:**
- First Contentful Paint (FCP): < 1.5s
- Time to Interactive (TTI): < 3.5s
- Largest Contentful Paint (LCP): < 2.5s

**Database:**
- Query execution (p95): < 200ms
- Connection acquisition: < 50ms
- Active connections: < 80

**ETL:**
- Full refresh: < 30 minutes
- Incremental update: < 5 minutes

### Performance Monitoring

```python
import time
import functools

def measure_time(func):
    """Decorator to measure function execution time"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        
        logger.info(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper
```

## Database Optimization

### Indexing Strategy

**Critical indexes:**

```sql
-- Material dimension (frequently joined)
CREATE INDEX idx_dim_material_id ON dim_material(material_id);
CREATE INDEX idx_dim_material_type ON dim_material(material_type);

-- Date dimension (date range queries)
CREATE INDEX idx_dim_date_date ON dim_date(date);
CREATE INDEX idx_dim_date_year_month ON dim_date(year, month);

-- Inventory fact (high-volume queries)
CREATE INDEX idx_fact_inventory_material ON fact_inventory(material_id);
CREATE INDEX idx_fact_inventory_date ON fact_inventory(date_id);
CREATE INDEX idx_fact_inventory_location ON fact_inventory(location_id);

-- Composite index for common query pattern
CREATE INDEX idx_fact_inventory_lookup 
ON fact_inventory(material_id, date_id, location_id);

-- Production chain (genealogy queries)
CREATE INDEX idx_production_chain_batch ON production_chain(batch_id);
CREATE INDEX idx_production_chain_parent ON production_chain(parent_batch_id);
CREATE INDEX idx_production_chain_date ON production_chain(production_date);

-- Alerts (recent alerts query)
CREATE INDEX idx_fact_alerts_date ON fact_alerts(alert_date DESC);
CREATE INDEX idx_fact_alerts_status ON fact_alerts(status) WHERE status = 'active';
```

**Check index usage:**

```sql
-- Find unused indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
    AND schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Find missing indexes (sequential scans on large tables)
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    seq_tup_read / seq_scan as avg_seq_tup_read,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size
FROM pg_stat_user_tables
WHERE seq_scan > 0
    AND schemaname = 'public'
    AND pg_relation_size(schemaname||'.'||tablename) > 1048576  -- > 1MB
ORDER BY seq_tup_read DESC
LIMIT 10;
```

### Table Partitioning

**Partition large tables by date:**

```sql
-- Partition fact_inventory by month
CREATE TABLE fact_inventory_partitioned (
    id SERIAL,
    material_id INTEGER,
    date_id INTEGER,
    location_id INTEGER,
    quantity DECIMAL(15,3),
    value DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (date_id);

-- Create monthly partitions
CREATE TABLE fact_inventory_2024_01 PARTITION OF fact_inventory_partitioned
    FOR VALUES FROM (20240101) TO (20240201);

CREATE TABLE fact_inventory_2024_02 PARTITION OF fact_inventory_partitioned
    FOR VALUES FROM (20240201) TO (20240301);

-- Indexes on each partition
CREATE INDEX idx_fact_inventory_2024_01_material 
ON fact_inventory_2024_01(material_id);
```

### Materialized View Optimization

**Refresh strategies:**

```sql
-- Full refresh (heavy operation)
REFRESH MATERIALIZED VIEW mv_inventory_summary;

-- Concurrent refresh (allows reads during refresh)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_inventory_summary;

-- Partial refresh (refresh only changed data)
CREATE OR REPLACE FUNCTION refresh_inventory_incremental()
RETURNS void AS $$
BEGIN
    -- Delete stale data
    DELETE FROM mv_inventory_summary
    WHERE last_updated < CURRENT_DATE - INTERVAL '7 days';
    
    -- Insert new data
    INSERT INTO mv_inventory_summary
    SELECT ...
    FROM fact_inventory
    WHERE created_at > CURRENT_DATE - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;
```

**Scheduled refresh** (see [MONITORING.md](MONITORING.md)):

```bash
# crontab
# Refresh every 6 hours
0 */6 * * * psql -d alkana_dashboard -c "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_inventory_summary;"
```

### VACUUM and ANALYZE

**Regular maintenance:**

```sql
-- Analyze tables to update statistics
ANALYZE fact_inventory;
ANALYZE production_chain;

-- Vacuum to reclaim space
VACUUM ANALYZE fact_inventory;

-- Full vacuum (requires table lock)
VACUUM FULL fact_inventory;
```

**Autovacuum configuration** (`postgresql.conf`):

```conf
autovacuum = on
autovacuum_naptime = 1min
autovacuum_vacuum_threshold = 50
autovacuum_analyze_threshold = 50
autovacuum_vacuum_scale_factor = 0.1
autovacuum_analyze_scale_factor = 0.05
```

## API Performance

### Query Optimization

**Use pagination for large datasets:**

```python
from fastapi import Query

@router.get("/inventory")
async def get_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Paginated inventory query"""
    
    total = db.query(func.count(FactInventory.id)).scalar()
    
    items = (
        db.query(FactInventory)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return {
        "total": total,
        "items": items,
        "skip": skip,
        "limit": limit
    }
```

**Optimize joins:**

```python
# ❌ BAD: N+1 query problem
batches = db.query(ProductionChain).all()
for batch in batches:
    material = db.query(DimMaterial).filter(
        DimMaterial.id == batch.material_id
    ).first()  # Separate query for each batch!

# ✅ GOOD: Single query with join
batches = (
    db.query(ProductionChain)
    .join(DimMaterial)
    .options(joinedload(ProductionChain.material))
    .all()
)
```

**Use select specific columns:**

```python
# ❌ BAD: Select all columns
inventory = db.query(FactInventory).all()

# ✅ GOOD: Select only needed columns
inventory = db.query(
    FactInventory.material_id,
    FactInventory.quantity,
    FactInventory.value
).all()
```

### Response Compression

**Enable gzip compression:**

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**nginx compression:**

```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
gzip_min_length 1000;
gzip_comp_level 6;
```

### Async Processing

**Use async for I/O operations:**

```python
from fastapi import BackgroundTasks

@router.post("/export")
async def export_data(
    background_tasks: BackgroundTasks,
    query: ExportQuery
):
    """Export data in background"""
    
    # Validate request
    if not query.email:
        raise HTTPException(400, "Email required")
    
    # Queue background task
    background_tasks.add_task(generate_export, query)
    
    return {"message": "Export started, will email when complete"}

async def generate_export(query: ExportQuery):
    """Background task to generate export"""
    
    # Generate export
    data = await fetch_data(query)
    file_path = create_excel(data)
    
    # Send email
    await send_email(query.email, file_path)
```

## Frontend Optimization

### Code Splitting

**Lazy load routes:**

```typescript
// App.tsx
import { lazy, Suspense } from 'react';

const ExecutiveDashboard = lazy(() => import('./pages/ExecutiveDashboard'));
const Inventory = lazy(() => import('./pages/Inventory'));
const LeadTime = lazy(() => import('./pages/LeadTimeDashboard'));

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div>Loading...</div>}>
        <Routes>
          <Route path="/" element={<ExecutiveDashboard />} />
          <Route path="/inventory" element={<Inventory />} />
          <Route path="/lead-time" element={<LeadTime />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
```

### Data Fetching Optimization

**Use TanStack Query for caching:**

```typescript
import { useQuery } from '@tanstack/react-query';

function InventoryPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['inventory'],
    queryFn: () => api.getInventory(),
    staleTime: 5 * 60 * 1000,  // 5 minutes
    cacheTime: 10 * 60 * 1000,  // 10 minutes
    refetchOnWindowFocus: false
  });
  
  if (isLoading) return <Spinner />;
  
  return <InventoryTable data={data} />;
}
```

**Prefetch data:**

```typescript
import { useQueryClient } from '@tanstack/react-query';

function DashboardLayout() {
  const queryClient = useQueryClient();
  
  // Prefetch likely next page
  const handleHoverInventory = () => {
    queryClient.prefetchQuery({
      queryKey: ['inventory'],
      queryFn: () => api.getInventory()
    });
  };
  
  return (
    <nav>
      <Link to="/inventory" onMouseEnter={handleHoverInventory}>
        Inventory
      </Link>
    </nav>
  );
}
```

### Chart Performance

**Optimize large datasets:**

```typescript
import { useMemo } from 'react';

function InventoryChart({ data }: { data: InventoryItem[] }) {
  // Downsample data for chart
  const chartData = useMemo(() => {
    if (data.length <= 100) return data;
    
    // Sample every Nth item
    const step = Math.ceil(data.length / 100);
    return data.filter((_, i) => i % step === 0);
  }, [data]);
  
  return (
    <LineChart data={chartData}>
      <Line dataKey="quantity" />
    </LineChart>
  );
}
```

**Virtual scrolling for large tables:**

```bash
npm install react-window
```

```typescript
import { FixedSizeList } from 'react-window';

function LargeTable({ items }: { items: any[] }) {
  const Row = ({ index, style }: any) => (
    <div style={style}>
      {items[index].name} - {items[index].quantity}
    </div>
  );
  
  return (
    <FixedSizeList
      height={600}
      itemCount={items.length}
      itemSize={50}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
}
```

### Build Optimization

**Vite configuration** (`vite.config.ts`):

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'chart-vendor': ['recharts'],
          'query-vendor': ['@tanstack/react-query']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  }
});
```

## Caching Strategies

### Application-Level Caching

**Redis cache for expensive queries:**

```bash
pip install redis
```

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

@router.get("/executive-summary")
async def get_executive_summary(db: Session = Depends(get_db)):
    """Cached executive summary"""
    
    # Check cache
    cache_key = "executive_summary"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Compute if not cached
    summary = compute_executive_summary(db)
    
    # Cache for 5 minutes
    redis_client.setex(
        cache_key,
        300,  # 5 minutes
        json.dumps(summary)
    )
    
    return summary
```

**Decorator for caching:**

```python
from functools import wraps

def cache_result(ttl: int = 300):
    """Cache decorator with TTL"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name + args
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Check cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            redis_client.setex(cache_key, ttl, json.dumps(result))
            
            return result
        return wrapper
    return decorator

@router.get("/inventory-summary")
@cache_result(ttl=600)  # 10 minutes
async def get_inventory_summary(db: Session = Depends(get_db)):
    return compute_inventory_summary(db)
```

### HTTP Caching

**Cache-Control headers:**

```python
from fastapi import Response

@router.get("/static-data")
async def get_static_data():
    """Data that rarely changes"""
    
    response = Response(content=json.dumps(data))
    response.headers["Cache-Control"] = "public, max-age=3600"  # 1 hour
    
    return response
```

**ETag support:**

```python
import hashlib

@router.get("/inventory")
async def get_inventory(
    request: Request,
    db: Session = Depends(get_db)
):
    """Inventory with ETag caching"""
    
    # Get data
    data = fetch_inventory(db)
    
    # Generate ETag
    etag = hashlib.md5(json.dumps(data).encode()).hexdigest()
    
    # Check If-None-Match header
    if request.headers.get("If-None-Match") == etag:
        return Response(status_code=304)  # Not Modified
    
    # Return with ETag
    response = Response(content=json.dumps(data))
    response.headers["ETag"] = etag
    
    return response
```

## ETL Performance

### Batch Processing

**Process in chunks:**

```python
def process_mb51_data(file_path: str, db: Session):
    """Process MB51 file in batches"""
    
    chunk_size = 1000
    
    # Read Excel in chunks
    for chunk in pd.read_excel(file_path, chunksize=chunk_size):
        # Transform
        transformed = transform_mb51(chunk)
        
        # Bulk insert
        db.bulk_insert_mappings(RawMB51, transformed.to_dict('records'))
        db.commit()
        
        logger.info(f"Processed {len(chunk)} rows")
```

### Parallel Processing

**Use multiprocessing for CPU-intensive tasks:**

```python
from multiprocessing import Pool
import pandas as pd

def process_batch(batch_data):
    """Process single batch"""
    # Heavy computation
    return transform_data(batch_data)

def parallel_etl(data: pd.DataFrame, num_workers: int = 4):
    """Process ETL in parallel"""
    
    # Split into batches
    batch_size = len(data) // num_workers
    batches = [
        data[i:i + batch_size] 
        for i in range(0, len(data), batch_size)
    ]
    
    # Process in parallel
    with Pool(num_workers) as pool:
        results = pool.map(process_batch, batches)
    
    # Combine results
    return pd.concat(results)
```

### Database Bulk Operations

**Use COPY for fastest inserts:**

```python
from io import StringIO

def bulk_insert_csv(data: pd.DataFrame, table_name: str, db: Session):
    """Fast bulk insert using COPY"""
    
    # Convert to CSV
    csv_buffer = StringIO()
    data.to_csv(csv_buffer, index=False, header=False)
    csv_buffer.seek(0)
    
    # Use raw connection for COPY
    conn = db.connection()
    cursor = conn.cursor()
    
    cursor.copy_from(
        csv_buffer,
        table_name,
        sep=',',
        columns=data.columns.tolist()
    )
    
    conn.commit()
```

## Query Optimization

### EXPLAIN ANALYZE

**Analyze query performance:**

```sql
EXPLAIN ANALYZE
SELECT 
    m.material_name,
    SUM(i.quantity) as total_qty
FROM fact_inventory i
JOIN dim_material m ON i.material_id = m.id
WHERE i.date_id >= 20240101
GROUP BY m.material_name
ORDER BY total_qty DESC
LIMIT 100;
```

**Look for:**
- Sequential Scans (bad on large tables)
- High cost estimates
- Long execution times
- Missing indexes

### Common Query Patterns

**Date range queries:**

```python
# ✅ GOOD: Use indexed date_id
inventory = db.query(FactInventory).filter(
    FactInventory.date_id >= 20240101,
    FactInventory.date_id <= 20240131
).all()

# ❌ BAD: String comparison
inventory = db.query(FactInventory).filter(
    func.to_char(FactInventory.date_id, 'YYYYMMDD') >= '20240101'
).all()
```

**Aggregations:**

```python
# ✅ GOOD: Database-side aggregation
summary = db.query(
    FactInventory.material_id,
    func.sum(FactInventory.quantity).label('total_qty')
).group_by(FactInventory.material_id).all()

# ❌ BAD: Application-side aggregation
inventory = db.query(FactInventory).all()
summary = {}
for item in inventory:
    summary[item.material_id] = summary.get(item.material_id, 0) + item.quantity
```

## Connection Pooling

### SQLAlchemy Pool Configuration

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,              # Base connection pool size
    max_overflow=20,           # Max additional connections
    pool_timeout=30,           # Connection timeout (seconds)
    pool_recycle=3600,         # Recycle connections after 1 hour
    pool_pre_ping=True,        # Verify connection before use
    echo_pool=False            # Log pool events (debug only)
)
```

### Monitor Pool Usage

```python
from prometheus_client import Gauge

pool_size = Gauge('db_pool_size', 'Database connection pool size')
pool_checked_out = Gauge('db_pool_checked_out', 'Checked out connections')

@app.middleware("http")
async def track_pool_metrics(request: Request, call_next):
    pool = engine.pool
    
    pool_size.set(pool.size())
    pool_checked_out.set(pool.checkedout())
    
    response = await call_next(request)
    return response
```

## Monitoring Performance

### Application Performance Monitoring (APM)

**New Relic integration:**

```bash
pip install newrelic
```

```bash
# Run with New Relic
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program uvicorn app.main:app
```

**Sentry for error tracking:**

```bash
pip install sentry-sdk
```

```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://your-sentry-dsn",
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1
)
```

### Custom Performance Metrics

```python
from prometheus_client import Histogram

query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

@query_duration.labels('inventory_summary').time()
def get_inventory_summary(db: Session):
    # Query execution
    return db.query(FactInventory).all()
```

## Load Testing

### Using Locust

**Install:**

```bash
pip install locust
```

**Test script** (`locustfile.py`):

```python
from locust import HttpUser, task, between

class DashboardUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before tests"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "password"
        })
        self.token = response.json()["access_token"]
        self.client.headers["Authorization"] = f"Bearer {self.token}"
    
    @task(3)
    def view_executive_dashboard(self):
        self.client.get("/api/v1/executive/summary")
    
    @task(2)
    def view_inventory(self):
        self.client.get("/api/v1/inventory")
    
    @task(1)
    def view_lead_time(self):
        self.client.get("/api/v1/lead-time")
```

**Run test:**

```bash
# Web UI
locust -f locustfile.py --host=http://localhost:8000

# Headless
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless
```

### Performance Baselines

**Establish baselines:**

```bash
# Run baseline test
locust -f locustfile.py --users 50 --spawn-rate 5 --run-time 5m --headless --csv=baseline

# Compare after optimization
locust -f locustfile.py --users 50 --spawn-rate 5 --run-time 5m --headless --csv=optimized
```

## Related Documentation

- [Database Documentation](DATABASE.md) - Schema and queries
- [Monitoring Guide](MONITORING.md) - Performance monitoring
- [Deployment Guide](DEPLOYMENT.md) - Production setup
- [API Reference](API_REFERENCE.md) - API endpoints

---

**Optimize for the 95th percentile, not the average. Performance is a feature.**
