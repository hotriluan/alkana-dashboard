# Date Filter Fix - Quick Summary

## Problem
Date filters only work in 3 dashboards (Lead Time, Alert Monitor, Executive) but not in others (Sales, Inventory, Yield, AR Aging).

## Root Cause
**Backend API endpoints don't accept date parameters** for non-working dashboards.

### Working Pattern ✅
```python
# Backend accepts dates
def get_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    # SQL filters by date
    if start_date and end_date:
        date_filter = f"WHERE date_col BETWEEN '{start_date}' AND '{end_date}'"
```

```typescript
// Frontend passes dates
api.get(`/summary?start_date=${startDate}&end_date=${endDate}`)
```

### Broken Pattern ❌
```python
# Backend MISSING date parameters
def get_summary():
    # SQL has NO date filter
    result = db.execute("SELECT * FROM table")
```

```typescript
// Frontend has DatePicker but doesn't pass dates
api.get('/summary')  // No params!
```

## Files to Fix

### 1. Sales Performance (Priority 1)
**Backend**: `src/api/routers/sales_performance.py`
- Lines 42-62: Add `start_date`, `end_date` params to `get_sales_summary()`
- Lines 65-95: Add params to `get_sales_by_customer()`
- Lines 98-125: Add params to `get_sales_by_division()`
- Lines 128-150: Add params to `get_top_customers()`

**Frontend**: `web/src/pages/SalesPerformance.tsx`
- Lines 42-48: Add `?start_date=${startDate}&end_date=${endDate}` to API call
- Lines 50-58: Add date params
- Lines 60-68: Add date params

### 2. Production Yield (Priority 2)
**Backend**: `src/api/routers/yield_dashboard.py`
- Lines 44-65: Add params + date filter

**Frontend**: `web/src/pages/ProductionYield.tsx`
- Add date params to all API calls

### 3. Inventory (Priority 3)
**Backend**: `src/api/routers/inventory.py`
- Consider if date filter is needed (shows current state)

**Frontend**: `web/src/pages/Inventory.tsx`
- Either use dates or remove DateRangePicker

### 4. AR Aging (Special Case)
Uses `snapshot_date` not date ranges - either:
- Remove DateRangePicker (it's unused), OR
- Add trend comparison feature

## Quick Fix Example

**Backend** (`sales_performance.py`):
```python
@router.get("/summary", response_model=SalesKPIs)
async def get_sales_summary(
    start_date: Optional[str] = Query(None),  # ADD
    end_date: Optional[str] = Query(None),    # ADD
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    date_filter = ""  # ADD
    if start_date and end_date:  # ADD
        date_filter = f"WHERE billing_date BETWEEN '{start_date}' AND '{end_date}'"  # ADD
    
    result = db.execute(text(f"""
        SELECT SUM(sales_amount) FROM view_sales_performance
        {date_filter}  /* ADD */
    """)).fetchone()
```

**Frontend** (`SalesPerformance.tsx`):
```typescript
const response = await api.get<SalesKPIs>(
    `/api/v1/dashboards/sales/summary?start_date=${startDate}&end_date=${endDate}`
    // ADD: --------------------------------^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
);
```

## Testing
1. Make changes
2. Restart backend: `uvicorn src.api.main:app --reload`
3. Open dashboard in browser
4. Change date range
5. Verify in DevTools Network tab that URLs include `?start_date=...&end_date=...`
6. Verify data changes

## See Full Report
`DATE_FILTER_ANALYSIS_REPORT.md` - Complete analysis with code locations, security notes, and implementation guide.
