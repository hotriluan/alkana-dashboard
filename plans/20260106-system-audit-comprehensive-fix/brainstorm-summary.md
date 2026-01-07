# COMPREHENSIVE SYSTEM AUDIT - BRAINSTORM & PLAN SUMMARY

**Date:** January 6, 2026  
**Plan Directory:** `plans/20260106-system-audit-comprehensive-fix/`

---

## 🎯 MISSION

Perform comprehensive system audit and fix 4 critical issues affecting Alkana Dashboard:

1. **Date Filters Not Working** (4 of 7 dashboards)
2. **AR Collection Empty Display**
3. **Data Inflated ~2x** (inventory and other metrics)
4. **ZRSD004 Headers Fail** (24,856 rows loaded as NULL)

---

## 🔍 RESEARCH COMPLETED

### ✅ Researcher #1: Date Filter Investigation

**Report:** `research/researcher-01-date-filters-report.md`

**Findings:**
- Backend APIs missing `start_date`/`end_date` parameters in 4 endpoints
- Frontend already correct (DateRangePicker implemented)
- Simple fix: Add Query params + WHERE clauses

**Affected Endpoints:**
- `/api/sales/summary` ❌
- `/api/production/yield` ❌
- `/api/inventory/summary` ❌
- `/api/ar/aging` ❌ (needs `snapshot_date` instead)

---

### ⚠️ Researcher #2: AR Collection Investigation

**Status:** PENDING - Subagent returned no output

**Action Required:** Re-run investigation before Phase 2 implementation

---

### ✅ Researcher #3: Data Inflation Investigation

**Report:** `research/researcher-03-data-inflation-report.md`

**Findings:**
- **fact_inventory:** 5,889 duplicate rows (57.7% of table!)
- **view_inventory_current:** GROUP BY includes uom+description → creates duplicates
- **Transform logic:** Inserts raw movements instead of aggregating

**Impact:**
- Inventory totals inflated ~50%
- Total weight: 4,152,005 kg (should be ~2,076,000 kg)

---

### ✅ Researcher #4: ZRSD004 Header Investigation

**Report:** `research/researcher-04-zrsd004-headers-report.md`

**Findings:**
- Excel has merged/formatted cells in Row 1
- Pandas reads as `['Unnamed: 0', 'Unnamed: 1', ...]`
- **Result:** ALL 24,856 rows loaded with NULL values (100% data loss!)

**Solution:** Use same fix as Mb51Loader (proven, already in production)

---

## 📋 IMPLEMENTATION PLAN

### Phase 1: Date Filters (4 hours)
- Add `start_date`/`end_date` to 4 backend APIs
- Add SQL `WHERE date BETWEEN` clauses
- Update AR Aging to use single `snapshot_date`

**Files:** 4 files in `src/api/routers/`

---

### Phase 2: AR Collection (2 hours + investigation)
- **BLOCKED:** Awaiting investigation results
- Likely frontend mapping or backend query issue
- Fix display logic

**Files:** TBD

---

### Phase 3: Data Inflation (6 hours) 🔴 CRITICAL
1. Clean 5,889 duplicate rows from fact_inventory
2. Update view_inventory_current GROUP BY
3. Add UNIQUE constraint (prevent future dupes)
4. Fix transform to aggregate movements

**Files:**
- `src/db/views.py` or migration
- `src/etl/transform.py`
- Migration scripts

**Risk:** HIGH - Database schema changes

---

### Phase 4: ZRSD004 Headers (2 hours) 🔴 CRITICAL
1. Change `pd.read_excel(header=0)` → `header=None, skiprows=1`
2. Manually assign 34 column names
3. Fix 5 column name mappings
4. Re-load zrsd004 data

**Files:** `src/etl/loaders.py`

**Risk:** LOW - Proven fix

---

### Phase 5: Performance (4 hours)
- Add database indexes for date columns
- Optimize transform (bulk operations)
- Add TRUNCATE to prevent accumulation

**Files:**
- Migration scripts
- `src/etl/transform.py`

---

## 📊 TOTAL EFFORT

| Phase | Hours | Priority | Risk |
|-------|-------|----------|------|
| Phase 1 | 4h | HIGH | LOW |
| Phase 2 | 2h | HIGH | MEDIUM |
| Phase 3 | 6h | CRITICAL | HIGH |
| Phase 4 | 2h | CRITICAL | LOW |
| Phase 5 | 4h | MEDIUM | LOW |
| **TOTAL** | **18h** | | |

**Estimated Duration:** 3 working days (6h/day)

---

## ⚠️ CRITICAL RISKS

1. **Data Inflation Fix (Phase 3):**
   - Requires database backup
   - Schema changes (UNIQUE constraint)
   - Potential data loss if aggregation wrong

2. **AR Collection (Phase 2):**
   - Investigation incomplete
   - May require additional research time

3. **Performance (Phase 5):**
   - Transform might still be slow without indexes
   - Need testing with production data volumes

---

## ✅ SUCCESS CRITERIA

**System is Fixed When:**

- [ ] All 7 dashboards support date filtering
- [ ] AR Collection displays all 93 records
- [ ] Inventory totals drop ~50% (correct de-inflation)
- [ ] fact_inventory has 0 duplicates
- [ ] ZRSD004 loads 24,856 rows with populated data
- [ ] Transform completes in <5 minutes
- [ ] No duplicate accumulation on re-run

---

## 📁 PLAN STRUCTURE

```
plans/20260106-system-audit-comprehensive-fix/
├── plan.md                          # Master plan (this file)
├── brainstorm-summary.md           # This brainstorm summary
├── phase-01-date-filters.md        # ✅ Created
├── phase-02-ar-collection.md       # ⏳ Pending investigation
├── phase-03-data-inflation.md      # ✅ Created
├── phase-04-zrsd004-headers.md     # ✅ Created
├── phase-05-performance.md         # 📝 To create
└── research/
    ├── researcher-01-date-filters-report.md    # ✅ Complete
    ├── researcher-02-ar-collection-report.md   # ❌ Failed (no output)
    ├── researcher-03-data-inflation-report.md  # ✅ Complete
    └── researcher-04-zrsd004-headers-report.md # ✅ Complete
```

---

## 🚀 RECOMMENDED EXECUTION ORDER

1. **Phase 4 First** (ZRSD004 headers)
   - Lowest risk, high impact
   - Recovers 24,856 rows of lost data
   - No dependencies

2. **Phase 1 Second** (Date filters)
   - Low risk, high user impact
   - No dependencies
   - Quick wins

3. **Complete AR Investigation** (Phase 2 prep)
   - Unblock Phase 2
   - Parallel with Phase 1

4. **Database Backup** ⚠️
   - Before Phase 3!

5. **Phase 3 Third** (Data inflation)
   - High risk, critical impact
   - Requires backup
   - Main blocker resolved

6. **Phase 5 Last** (Performance)
   - Low risk, medium impact
   - Builds on all previous phases

---

## 📞 NEXT ACTIONS

1. ✅ **Review & approve this plan**
2. ⚠️ **Re-run AR Collection investigation** (subagent failed)
3. ✅ **Start Phase 4** (ZRSD004 - quick win)
4. ✅ **Start Phase 1** (Date filters - parallel)
5. ⚠️ **Backup database** (before Phase 3)
6. ✅ **Execute remaining phases** (sequential validation)

---

**Plan Created By:** Claude Code (Copilot)  
**Research Method:** 4 parallel researcher subagents  
**Validation:** Cross-referenced with database audit reports  
**Status:** ✅ READY FOR APPROVAL & EXECUTION
