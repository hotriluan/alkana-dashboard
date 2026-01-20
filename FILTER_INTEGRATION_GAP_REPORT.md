# 🕵️ FILTER INTEGRATION GAP ANALYSIS REPORT

**Generated:** January 16, 2026  
**Auditor:** AI Development Agent  
**Scope:** Global Date Filter Integration for Visual Intelligence Charts  

---

## 📊 EXECUTIVE SUMMARY

**Status:** ❌ **CRITICAL GAP IDENTIFIED**

All 4 newly added Visual Intelligence charts are **NOT** connected to the Global Date Range Picker. Charts display static/hardcoded timeframes, creating disconnect between user expectations and actual data shown.

**Root Cause:** Analytics layer designed without date parameters; API endpoints accept but ignore date params; Frontend integration incomplete.

---

## 🔍 DETAILED AUDIT FINDINGS

| Module | Chart Component | API Endpoint | API Accepts Dates? | Analytics Uses Dates? | Frontend Passes Dates? | Remediation Effort |
|--------|----------------|--------------|-------------------|----------------------|----------------------|-------------------|
| **Inventory** | `InventoryTreemap` | `/dashboards/inventory/abc-analysis` | ❌ NO | ❌ NO (Hardcoded 90d) | ❌ NO | **HIGH** |
| **Production** | `ProductionFunnel` | `/dashboards/mto-orders/funnel` | ❌ NO | ❌ NO (All-time) | ❌ NO | **HIGH** |
| **Sales** | `SegmentationScatter` | `/dashboards/sales-performance/segmentation` | ❌ NO | ❌ NO (All-time) | ❌ NO | **HIGH** |
| **LeadTime** | `LeadTimeBreakdownChart` | `/leadtime/stage-breakdown` | ✅ YES | ❌ **NOT USED** | ✅ YES | **MEDIUM** |

---

## 🔬 LAYER-BY-LAYER ANALYSIS

### 1️⃣ INVENTORY MODULE

**Component:** `InventoryTreemap.tsx`  
**API Endpoint:** `GET /api/v1/dashboards/inventory/abc-analysis`  
**Analytics Class:** `InventoryAnalytics.get_abc_analysis()`

#### Backend Layer (API)
```python
# src/api/routers/inventory.py:153
@router.get("/abc-analysis")
async def get_abc_analysis(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # ❌ NO start_date/end_date parameters
```

#### Analytics Layer
```python
# src/core/inventory_analytics.py:45
cutoff_date = datetime.utcnow().date() - timedelta(days=90)  # ❌ HARDCODED 90 days

# Query uses hardcoded cutoff
velocity_data = self.db.query(...).filter(
    FactInventory.posting_date >= cutoff_date  # ❌ Fixed window
)
```

#### Frontend Integration
```tsx
// web/src/pages/Inventory.tsx:28
const { data: abcData, isLoading: abcLoading } = useQuery({
  queryKey: ['inventory-abc-analysis'],  // ❌ No date dependency
  queryFn: async () => (await api.get('/api/v1/dashboards/inventory/abc-analysis')).data
  // ❌ No params passed
});

// Line 91: InventoryTreemap component
<InventoryTreemap data={abcData || []} loading={abcLoading} />
// ❌ No dateRange prop
```

**Gap Summary:**
- ❌ API does NOT accept date params
- ❌ Analytics hardcodes 90-day window
- ❌ Frontend does NOT pass dates
- ❌ Component does NOT accept date props

**Impact:** Chart always shows last 90 days regardless of user selection

---

### 2️⃣ PRODUCTION MODULE

**Component:** `ProductionFunnel.tsx`  
**API Endpoint:** `GET /api/v1/dashboards/mto-orders/funnel`  
**Analytics Class:** `ProductionAnalytics.get_production_funnel()`

#### Backend Layer (API)
```python
# src/api/routers/mto_orders.py:173
@router.get("/funnel")
async def get_production_funnel(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # ❌ NO start_date/end_date parameters
```

#### Analytics Layer
```python
# src/core/production_analytics.py:46
def get_production_funnel(self) -> List[FunnelStage]:
    # ❌ NO date filtering - queries entire table
    # Counts all production orders regardless of date
```

**Gap Summary:**
- ❌ API does NOT accept date params
- ❌ Analytics queries entire history (all-time data)
- ❌ Frontend integration unknown (component file exists but not wired)

**Impact:** Funnel shows all-time production data, not filtered by selected date range

---

### 3️⃣ SALES MODULE

**Component:** `SegmentationScatter.tsx` (assumed name)  
**API Endpoint:** `GET /api/v1/dashboards/sales-performance/segmentation`  
**Analytics Class:** `SalesAnalytics.get_customer_segmentation()`

#### Backend Layer (API)
```python
# src/api/routers/sales_performance.py:254
@router.get("/segmentation")
async def get_customer_segmentation(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # ❌ NO start_date/end_date parameters
```

#### Analytics Layer
```python
# src/core/sales_analytics.py:41
results = self.db.query(
    FactBilling.customer_name,
    func.count(func.distinct(FactBilling.billing_document)).label('order_count'),
    func.sum(FactBilling.net_value).label('total_revenue')
).group_by(
    FactBilling.customer_name
).all()
# ❌ NO date filter - aggregates all billing history
```

**Gap Summary:**
- ❌ API does NOT accept date params
- ❌ Analytics aggregates entire billing history
- ❌ Frontend integration unknown

**Impact:** Scatter plot shows lifetime customer metrics, not period-specific

---

### 4️⃣ LEADTIME MODULE

**Component:** `LeadTimeBreakdownChart.tsx`  
**API Endpoint:** `GET /api/v1/leadtime/stage-breakdown`  
**Analytics Class:** `LeadTimeAnalytics.get_stage_breakdown()`

#### Backend Layer (API)
```python
# src/api/routers/lead_time.py:490
@router.get("/stage-breakdown")
async def get_stage_breakdown(
    limit: int = Query(20, ge=10, le=50, description="Number of recent orders"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),  # ✅ Defined
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),      # ✅ Defined
    db: Session = Depends(get_db)
):
    analytics = LeadTimeAnalytics(db)
    result = analytics.get_stage_breakdown(order_limit=limit)
    # ❌ API ACCEPTS params but DOES NOT PASS to analytics!
```

#### Analytics Layer
```python
# src/core/leadtime_analytics.py:51
orders = self.db.query(FactLeadTime).filter(
    FactLeadTime.lead_time_days.isnot(None)
).order_by(
    FactLeadTime.created_at.desc()  # ❌ Orders by creation, no date range filter
).limit(order_limit).all()
```

#### Frontend Integration
```tsx
// web/src/pages/LeadTimeDashboard.tsx:146
const { data: stageBreakdown, isLoading: stageBreakdownLoading } = useQuery({
  queryKey: ['leadtime-stage-breakdown', startDate, endDate],  // ✅ Has date dependency
  queryFn: async () => {
    const response = await api.get<StageBreakdown[]>(
      `/api/v1/leadtime/stage-breakdown?limit=20&start_date=${startDate}&end_date=${endDate}`
    );  // ✅ Passes dates
    return response.data;
  },
});
```

**Gap Summary:**
- ✅ API ACCEPTS date params
- ❌ API endpoint IGNORES params (doesn't pass to analytics)
- ❌ Analytics method signature does NOT accept dates
- ✅ Frontend PASSES dates correctly

**Impact:** Chart shows last 20 orders by creation date, ignoring user-selected range

---

## 🎯 REMEDIATION STRATEGY

### Priority 1: ARCHITECTURE FIX (All Modules)

**Pattern to Follow:**
```python
# BEFORE (Current - Broken)
def get_abc_analysis(self) -> List[ABCAnalysisItem]:
    cutoff_date = datetime.utcnow().date() - timedelta(days=90)  # ❌ Hardcoded
    ...

# AFTER (Target - Working)
def get_abc_analysis(
    self,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[ABCAnalysisItem]:
    if not start_date:
        start_date = datetime.utcnow().date() - timedelta(days=90)
    if not end_date:
        end_date = datetime.utcnow().date()
    
    # Use start_date/end_date in query filters
```

### Remediation Steps by Module

#### 🔧 INVENTORY (HIGH Effort)

1. **Analytics Layer** (`src/core/inventory_analytics.py`)
   - Add `start_date`, `end_date` params to `get_abc_analysis()`
   - Replace hardcoded `cutoff_date` with `start_date`
   - Filter velocity query: `FactInventory.posting_date.between(start_date, end_date)`

2. **API Layer** (`src/api/routers/inventory.py`)
   ```python
   @router.get("/abc-analysis")
   async def get_abc_analysis(
       start_date: Optional[str] = Query(None),
       end_date: Optional[str] = Query(None),
       db: Session = Depends(get_db),
       current_user = Depends(get_current_user)
   ):
       analytics = InventoryAnalytics(db)
       result = analytics.get_abc_analysis(
           start_date=datetime.fromisoformat(start_date) if start_date else None,
           end_date=datetime.fromisoformat(end_date) if end_date else None
       )
   ```

3. **Frontend Integration** (`web/src/pages/Inventory.tsx`)
   ```tsx
   const { data: abcData } = useQuery({
     queryKey: ['inventory-abc-analysis', startDate, endDate],  // Add date dependency
     queryFn: async () => (await api.get('/api/v1/dashboards/inventory/abc-analysis', {
       params: { start_date: startDate, end_date: endDate }
     })).data
   });
   ```

**Estimated Effort:** 2-3 hours (query logic modification + testing)

---

#### 🔧 PRODUCTION (HIGH Effort)

1. **Analytics Layer** (`src/core/production_analytics.py`)
   - Add `start_date`, `end_date` params to `get_production_funnel()`
   - Filter: `FactProduction.created_at.between(start_date, end_date)` or similar

2. **API Layer** (`src/api/routers/mto_orders.py`)
   - Add `start_date`, `end_date` query params
   - Pass to analytics

3. **Frontend Integration** (unknown component)
   - Wire up date range to query

**Estimated Effort:** 2-3 hours

---

#### 🔧 SALES (HIGH Effort)

1. **Analytics Layer** (`src/core/sales_analytics.py`)
   - Add `start_date`, `end_date` params to `get_customer_segmentation()`
   - Filter: `FactBilling.billing_date.between(start_date, end_date)`

2. **API Layer** (`src/api/routers/sales_performance.py`)
   - Add query params
   - Pass to analytics

3. **Frontend Integration** (unknown component)
   - Wire up date range

**Estimated Effort:** 2-3 hours

---

#### 🔧 LEADTIME (MEDIUM Effort)

**This module is CLOSEST to working** - only needs analytics fix:

1. **Analytics Layer** (`src/core/leadtime_analytics.py`)
   ```python
   def get_stage_breakdown(
       self,
       order_limit: int = 20,
       start_date: Optional[date] = None,  # ✅ ADD
       end_date: Optional[date] = None      # ✅ ADD
   ) -> List[StageBreakdownItem]:
       query = self.db.query(FactLeadTime).filter(
           FactLeadTime.lead_time_days.isnot(None)
       )
       
       if start_date:
           query = query.filter(FactLeadTime.start_date >= start_date)
       if end_date:
           query = query.filter(FactLeadTime.end_date <= end_date)
       
       orders = query.order_by(FactLeadTime.created_at.desc()).limit(order_limit).all()
   ```

2. **API Layer** (`src/api/routers/lead_time.py`)
   ```python
   # Line 504: Pass params to analytics
   result = analytics.get_stage_breakdown(
       order_limit=limit,
       start_date=datetime.fromisoformat(start_date) if start_date else None,
       end_date=datetime.fromisoformat(end_date) if end_date else None
   )
   ```

**Estimated Effort:** 1 hour (API already wired, just analytics fix)

---

## 📋 IMPLEMENTATION CHECKLIST

**Before Starting:**
- [ ] Read `.claude/rules/development-rules.md`
- [ ] Follow KISS principle - simple date filters, no complex logic
- [ ] Test each module independently

**Per Module:**
1. [ ] Update analytics class method signature
2. [ ] Add date filtering to database queries
3. [ ] Update API endpoint to accept and pass params
4. [ ] Update frontend query to include dates in params
5. [ ] Update queryKey to include dates for cache invalidation
6. [ ] Test with different date ranges
7. [ ] Verify chart updates when date picker changes

**Validation:**
- [ ] Change date range → Chart re-queries API
- [ ] Verify Network tab shows correct params
- [ ] Verify chart data changes (not cached)

---

## 🚨 RISK ASSESSMENT

**Deployment Risk:** MEDIUM
- Changes affect data layer (analytics) and API contracts
- Existing non-date-filtered queries may break if not handled carefully
- Frontend cache invalidation critical for UX

**Testing Requirements:**
- Unit tests for analytics with/without dates
- Integration tests for API endpoints
- Manual UAT for each dashboard

**Rollback Plan:**
- Analytics changes are backward compatible (default params)
- API changes are additive (optional params)
- Frontend changes can be reverted independently

---

## 📌 RECOMMENDATIONS

1. **Fix LeadTime First** (Quick Win)
   - Already 80% wired, only analytics layer needs fix
   - Demonstrates pattern for other modules

2. **Standardize Date Parameter Handling**
   - Create shared utility: `parse_date_params(start_date, end_date)`
   - Default to current month if not provided
   - Consistent across all analytics classes

3. **Add Telemetry**
   - Log when date filters are used vs defaults
   - Track query performance with date ranges

4. **Documentation Update**
   - Update API docs to reflect new params
   - Add date filtering to user guide

---

## ✅ CONCLUSION

**Current State:** Visual Intelligence charts are **NOT** integrated with Global Date Filter

**Root Cause:** Analytics layer designed without date awareness; API/Frontend partially prepared but not connected

**Fix Complexity:**
- LeadTime: **MEDIUM** (1 hour)
- Inventory: **HIGH** (2-3 hours)
- Production: **HIGH** (2-3 hours)
- Sales: **HIGH** (2-3 hours)

**Total Effort:** ~8-10 hours for full remediation

**Next Action:** Implement LeadTime fix first as proof-of-concept, then replicate pattern to other modules.

---

*Report Generated: January 16, 2026*  
*Compliance: Claude Kit Engineering Standards*  
*Principles Applied: KISS, DRY, Sequential Thinking*
