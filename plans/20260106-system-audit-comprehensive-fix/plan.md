# COMPREHENSIVE SYSTEM AUDIT & FIX PLAN

**Created:** January 6, 2026  
**Status:** Ready for Implementation  
**Priority:** 🔴 CRITICAL

---

## 📋 EXECUTIVE SUMMARY

Comprehensive audit revealed **4 critical system issues** affecting data integrity, user experience, and performance:

1. **Date Filters Not Working** - 4 of 7 dashboards ignore date range filters
2. **AR Collection Empty Display** - Shows nothing despite having 93 rows
3. **Data Still Inflated** - Inventory data inflated ~2x despite duplicate cleanup
4. **ZRSD004 Header Detection Failure** - ALL 24,856 rows loaded with NULL values

---

## 🎯 ISSUES IDENTIFIED

### Issue #1: Date Filters Only Work in 3/7 Dashboards ❌

**Impact:** HIGH - Users cannot filter data by date in most dashboards

**Affected Dashboards:**
- ❌ Sales Performance Dashboard
- ❌ Production Yield Dashboard  
- ❌ Inventory Dashboard
- ❌ AR Aging Dashboard (uses snapshot_date)
- ✅ Lead Time Analysis (works)
- ✅ Alert Monitor (works)
- ✅ Executive Dashboard (works)

**Root Cause:**
Backend API endpoints for broken dashboards **don't accept `start_date` and `end_date` query parameters**, even though frontend includes DateRangePicker components.

**Files Affected:**
- Backend: `src/api/routers/*.py` (4 files)
- Frontend: Already correct (no changes needed)

---

### Issue #2: AR Collection Shows Nothing ❌

**Impact:** HIGH - Users cannot view AR aging data

**Root Cause:** [Research pending - subagent returned no output]

**Status:** NEEDS INVESTIGATION

---

### Issue #3: Data Inflated in Multiple Sections ❌

**Impact:** CRITICAL - Inventory and other metrics show ~2x actual values

**Confirmed Issues:**

1. **fact_inventory has 5,889 duplicate rows (57.7%)**
   - Total rows: 10,201
   - Unique combinations: 4,312
   - Duplicates: 5,889 rows

2. **view_inventory_current creates duplicates**
   - Groups by `material_code + plant_code + uom + description`
   - Should group by `material_code + plant_code` only
   - Causes same material to appear multiple times

3. **Transform logic doesn't aggregate movements**
   - Inserts each transaction from raw_mb51
   - Should aggregate to current stock levels

**Impact:**
- Inventory totals inflated ~50%
- Total weight: 4,152,005 kg (should be ~2,076,000 kg)

---

### Issue #4: ZRSD004 Header Detection Fails ❌

**Impact:** CRITICAL - ALL 24,856 rows loaded with NULL values

**Root Cause:**
Excel file has merged cells/special formatting in header row. Pandas reads headers as `['Unnamed: 0', 'Unnamed: 1', ...]` instead of actual column names.

**Result:**
```python
row.get('Delivery')  # Returns None ❌
```

All 24,856 rows have NULL in every column - complete data loss!

---

## 🛠️ IMPLEMENTATION PHASES

### **Phase 1: Fix Date Filters (4 Backend Files)**
**Priority:** HIGH  
**Effort:** 4 hours  
**Risk:** LOW

Add date filter parameters to 4 API endpoints:
1. Sales Performance (`/api/sales/summary`)
2. Production Yield (`/api/production/yield`)
3. Inventory (`/api/inventory/summary`)
4. AR Aging (use `snapshot_date` instead)

See: `phase-01-date-filters.md`

---

### **Phase 2: Fix AR Collection Display**
**Priority:** HIGH  
**Effort:** 2 hours (after investigation)  
**Risk:** MEDIUM

1. Complete investigation (AR Collection subagent had no output)
2. Fix backend API or frontend mapping
3. Add error handling

See: `phase-02-ar-collection.md`

---

### **Phase 3: Fix Data Inflation (3 Changes)**
**Priority:** CRITICAL  
**Effort:** 6 hours  
**Risk:** HIGH - Requires database migration

1. Update `view_inventory_current` GROUP BY clause
2. Add UNIQUE constraint to `fact_inventory`
3. Fix `transform_mb51()` to aggregate movements

See: `phase-03-data-inflation.md`

---

### **Phase 4: Fix ZRSD004 Header Detection**
**Priority:** CRITICAL  
**Effort:** 2 hours  
**Risk:** LOW - Proven fix already exists (Mb51Loader)

1. Change `pd.read_excel()` to skip header row
2. Manually assign 34 column names
3. Update column name mappings (5 fields)
4. Re-load zrsd004 data

See: `phase-04-zrsd004-headers.md`

---

### **Phase 5: Performance Optimization**
**Priority:** MEDIUM  
**Effort:** 4 hours  
**Risk:** LOW

1. Add database indexes for date filters
2. Optimize transform pipeline (bulk operations)
3. Add TRUNCATE before fact table inserts

See: `phase-05-performance.md`

---

## 📊 EFFORT ESTIMATION

| Phase | Effort | Priority | Dependencies |
|-------|--------|----------|--------------|
| Phase 1: Date Filters | 4h | HIGH | None |
| Phase 2: AR Collection | 2h | HIGH | Investigation complete |
| Phase 3: Data Inflation | 6h | CRITICAL | Database backup |
| Phase 4: ZRSD004 Headers | 2h | CRITICAL | None |
| Phase 5: Performance | 4h | MEDIUM | Phases 1-4 complete |
| **TOTAL** | **18h** | | |

---

## ⚠️ RISKS & MITIGATION

### Risk #1: Data Loss from View/Transform Changes
**Mitigation:** 
- Backup database before Phase 3
- Test in dev environment first
- Keep migration rollback scripts

### Risk #2: AR Collection Issue Still Unknown
**Mitigation:**
- Complete investigation before Phase 2
- May need additional research time

### Risk #3: Transform Performance Still Slow
**Mitigation:**
- Phase 5 addresses root cause (no bulk operations)
- Add indexes incrementally

---

## ✅ SUCCESS CRITERIA

### Phase 1 Complete When:
- [ ] All 7 dashboards accept date range filters
- [ ] SQL queries include WHERE date BETWEEN clauses
- [ ] Frontend correctly passes dates to backend

### Phase 2 Complete When:
- [ ] AR Collection displays all 93 records
- [ ] No console errors
- [ ] Data maps correctly to UI components

### Phase 3 Complete When:
- [ ] `fact_inventory` has 0 duplicates
- [ ] `view_inventory_current` shows 1 row per material+plant
- [ ] Total inventory weight drops to ~2M kg (from 4.15M)
- [ ] UNIQUE constraint prevents future duplicates

### Phase 4 Complete When:
- [ ] ZRSD004 loads with actual column names
- [ ] All 24,856 rows have populated values
- [ ] No more `'Unnamed: X'` column names

### Phase 5 Complete When:
- [ ] Transform completes in <5 minutes (from current >10min)
- [ ] Database has indexes on date columns
- [ ] No duplicate accumulation from multiple transform runs

---

## 📂 PLAN STRUCTURE

```
plans/20260106-system-audit-comprehensive-fix/
├── plan.md (this file)
├── phase-01-date-filters.md
├── phase-02-ar-collection.md
├── phase-03-data-inflation.md
├── phase-04-zrsd004-headers.md
├── phase-05-performance.md
└── research/
    ├── researcher-01-date-filters-report.md
    ├── researcher-02-ar-collection-report.md (pending)
    ├── researcher-03-data-inflation-report.md
    └── researcher-04-zrsd004-headers-report.md
```

---

## 🚀 NEXT STEPS

1. **Review this plan** - Confirm priorities and scope
2. **Start Phase 1** - Date filters (lowest risk, high impact)
3. **Parallel: Complete AR Collection investigation** (Phase 2 prep)
4. **Database backup** - Before Phase 3 (data changes)
5. **Execute phases sequentially** - Validate after each
6. **Final system test** - All issues resolved

---

## 📞 SUPPORT RESOURCES

- **Database Audit Reports:**
  - `FINAL_DATABASE_AUDIT_REPORT.md`
  - `DUPLICATE_PREVENTION_STRATEGY.md`
  
- **Research Reports:**
  - `research/researcher-01-date-filters-report.md`
  - `research/researcher-03-data-inflation-report.md`
  - `research/researcher-04-zrsd004-headers-report.md`

- **Diagnostic Scripts:**
  - `final_comprehensive_audit.py`
  - `fix_duplicates_safe.py`

---

**Plan Status:** ✅ READY FOR IMPLEMENTATION  
**Approval Required:** Team Lead / Product Owner  
**Start Date:** [TBD]  
**Target Completion:** [Start Date + 3 days]
