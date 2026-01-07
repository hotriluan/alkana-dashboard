# Phase 1: Fix Date Filters in 4 Dashboards

**Priority:** HIGH  
**Effort:** 4 hours  
**Risk:** LOW  
**Dependencies:** None

---

## 🎯 OBJECTIVE

Add `start_date` and `end_date` query parameters to 4 backend API endpoints so all dashboards can filter data by date range.

---

## 📋 SCOPE

### Dashboards to Fix:
1. ✅ **Sales Performance Dashboard** - `/api/sales/summary`
2. ✅ **Production Yield Dashboard** - `/api/production/yield`
3. ✅ **Inventory Dashboard** - `/api/inventory/summary`
4. ✅ **AR Aging Dashboard** - `/api/ar/aging` (special case: use `snapshot_date`)

### Dashboards Already Working (Reference):
- Lead Time Analysis - `/api/lead-time/summary`
- Alert Monitor - `/api/alerts`
- Executive Dashboard - `/api/executive/summary`

---

## 🔍 ROOT CAUSE

Frontend components include `<DateRangePicker>` and pass `startDate`/`endDate` to API calls, BUT backend endpoints don't accept these parameters.

**Evidence:**
```typescript
// Frontend (src/components/SalesPerformance.tsx)
const { data } = useQuery(['sales', startDate, endDate], () =>
  api.get('/sales/summary', { params: { startDate, endDate } })  // ✅ Passes dates
);
```

```python
# Backend (src/api/routers/sales.py)
@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):  # ❌ No date params!
    result = db.execute("SELECT * FROM fact_billing")  # ❌ No date filter
```

---

## 🛠️ IMPLEMENTATION

### Task 1.1: Fix Sales Performance API

**File:** `src/api/routers/sales.py`

**Current Code:**
```python
@router.get("/summary")
def get_sales_summary(db: Session = Depends(get_db)):
    query = """
        SELECT 
            billing_document,
            billing_date,
            customer_code,
            net_value,
            dist_channel
        FROM fact_billing
    """
    result = db.execute(text(query)).fetchall()
    return {"sales": result}
```

**Updated Code:**
```python
from typing import Optional
from fastapi import Query

@router.get("/summary")
def get_sales_summary(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    # Base query
    query = """
        SELECT 
            billing_document,
            billing_date,
            customer_code,
            net_value,
            dist_channel
        FROM fact_billing
    """
    
    # Add date filter if provided
    filters = []
    if start_date and end_date:
        filters.append(f"billing_date BETWEEN '{start_date}' AND '{end_date}'")
    
    if filters:
        query += " WHERE " + " AND ".join(filters)
    
    result = db.execute(text(query)).fetchall()
    return {"sales": result}
```

**Testing:**
```bash
# Test with date range
curl "http://localhost:8000/api/sales/summary?start_date=2025-01-01&end_date=2025-12-31"

# Test without dates (should return all)
curl "http://localhost:8000/api/sales/summary"
```

---

### Task 1.2: Fix Production Yield API

**File:** `src/api/routers/production.py`

**Find Endpoint:** `/yield` or `/production/yield`

**Pattern to Apply:**
```python
@router.get("/yield")
def get_yield_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = """
        SELECT 
            p02_batch,
            p01_batch,
            p02_qty,
            p01_qty,
            yield_percentage
        FROM fact_p02_p01_yield
    """
    
    # Add date filter on p02_date or production_date
    if start_date and end_date:
        query += f" WHERE production_date BETWEEN '{start_date}' AND '{end_date}'"
    
    result = db.execute(text(query)).fetchall()
    return {"yields": result}
```

**Date Column:** Check if `fact_p02_p01_yield` has `production_date` or similar. May need JOIN to `fact_production` for date.

---

### Task 1.3: Fix Inventory API

**File:** `src/api/routers/inventory.py`

**Pattern:**
```python
@router.get("/summary")
def get_inventory_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    # Use view_inventory_current or fact_inventory
    query = """
        SELECT 
            material_code,
            plant_code,
            total_qty,
            total_qty_kg
        FROM view_inventory_current
    """
    
    # Inventory snapshot - filter by posting_date if fact_inventory
    if start_date and end_date:
        # For view, might need WHERE in subquery
        # For fact_inventory direct:
        query = query.replace(
            "FROM view_inventory_current",
            "FROM fact_inventory WHERE posting_date BETWEEN '{start_date}' AND '{end_date}'"
        )
    
    result = db.execute(text(query)).fetchall()
    return {"inventory": result}
```

**Note:** Inventory is snapshot data. Decide if date filter means:
- "Show inventory movements between dates" OR
- "Show current inventory as of end_date"

---

### Task 1.4: Fix AR Aging API (Special Case)

**File:** `src/api/routers/ar_aging.py`

**Special Consideration:** AR Aging uses `snapshot_date` not date range.

**Pattern:**
```python
@router.get("/aging")
def get_ar_aging(
    snapshot_date: Optional[str] = Query(None, description="Snapshot date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    query = """
        SELECT 
            customer_code,
            customer_name,
            overdue_0_30,
            overdue_31_60,
            overdue_61_90,
            overdue_over_90,
            total_outstanding
        FROM fact_ar_aging
    """
    
    # Filter by snapshot_date if provided
    if snapshot_date:
        query += f" WHERE snapshot_date = '{snapshot_date}'"
    else:
        # Default to most recent snapshot
        query += " WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM fact_ar_aging)"
    
    result = db.execute(text(query)).fetchall()
    return {"ar_aging": result}
```

**Frontend Update Required:**
- Change `DateRangePicker` to `DatePicker` (single date)
- Pass `snapshotDate` instead of `startDate`/`endDate`

---

## ⚠️ SECURITY CONSIDERATIONS

**SQL Injection Risk:** Current implementation uses f-strings for SQL.

**Mitigation (Recommended):**
```python
# Instead of:
query += f" WHERE date BETWEEN '{start_date}' AND '{end_date}'"

# Use parameterized queries:
query += " WHERE date BETWEEN :start AND :end"
result = db.execute(text(query), {"start": start_date, "end": end_date})
```

**Date Validation:**
```python
from datetime import datetime

def validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
```

---

## 🧪 TESTING CHECKLIST

For each endpoint:

- [ ] **No dates:** Returns all records
- [ ] **With dates:** Returns only records in range
- [ ] **Invalid date format:** Returns 400 error
- [ ] **start_date > end_date:** Returns empty or error
- [ ] **Date outside data range:** Returns empty array (not error)
- [ ] **Frontend integration:** DatePicker values passed correctly

**Test Data:**
- Earliest billing_date: [check database]
- Latest billing_date: [check database]
- Record count in Jan 2025: [check database]

---

## 📊 SUCCESS CRITERIA

- [ ] All 4 endpoints accept `start_date`/`end_date` parameters
- [ ] SQL queries include `WHERE date BETWEEN` clauses
- [ ] Frontend DateRangePicker filters data correctly
- [ ] No SQL injection vulnerabilities
- [ ] Performance: <500ms response time with date filters
- [ ] Empty result when no data in range (not error)

---

## 🚀 DEPLOYMENT

1. **Code changes:** 4 files in `src/api/routers/`
2. **Database changes:** None
3. **Frontend changes:** AR Aging only (single date picker)
4. **Migration required:** No
5. **Restart required:** Yes (FastAPI backend)

**Rollback:** Previous code doesn't break if params added (backward compatible)

---

## 📈 PERFORMANCE NOTES

**Add Database Indexes (Phase 5):**
```sql
CREATE INDEX idx_fact_billing_date ON fact_billing(billing_date);
CREATE INDEX idx_fact_production_date ON fact_production(production_date);
CREATE INDEX idx_fact_inventory_date ON fact_inventory(posting_date);
CREATE INDEX idx_fact_ar_aging_snapshot ON fact_ar_aging(snapshot_date);
```

---

**Phase 1 Complete When:**
✅ All 7 dashboards support date filtering  
✅ Tests pass for all endpoints  
✅ No SQL injection risks  
✅ Performance acceptable (<500ms)
