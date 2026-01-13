# Legacy/V2 Yield Module Decommission Plan
**Date:** 2026-01-12  
**Status:** Draft  
**Owner:** Engineering Team  
**Objective:** Remove legacy/V2 yield modules while protecting V3 Efficiency Hub assets

---

## DO NOT TOUCH - Protected Assets
**Database Tables:**
- `fact_production_performance_v2` (V3 data source)
- `dim_product_hierarchy` (V3 dependency)

**Backend Files:**
- `src/api/routers/yield_v3.py` (Efficiency Hub API)
- `src/etl/loaders/loader_zrpp062.py` (V3 data loader)
- `src/etl/loaders/loader_zrsd006.py` (V3 dependency)

**Frontend Components:**
- `EfficiencyHub` (V3 dashboard)
- `PerformanceMatrix` (V3 visualization)
- `SmartUpload` (V3 upload interface)
- `YieldV3Dashboard.tsx` (primary V3 component)

---

## Phase 1: Frontend Navigation Cleanup

### 1.1 Update Production Dashboard Page
- [ ] Remove "legacy" tab from [web/src/pages/ProductionDashboard.tsx](web/src/pages/ProductionDashboard.tsx#L21)
- [ ] Remove "variance" tab (V2) from [web/src/pages/ProductionDashboard.tsx](web/src/pages/ProductionDashboard.tsx#L22)
- [ ] Set "efficiency" (V3) as default and only tab
- [ ] Clean up TabType declarations (remove 'legacy' | 'variance')
- [ ] Remove VarianceAnalysisTable import and conditional render

### 1.2 Update Dashboard Layout Navigation
- [ ] Review [web/src/components/DashboardLayout.tsx](web/src/components/DashboardLayout.tsx#L36)
- [ ] Rename "Production Yield" to "Efficiency Hub" or keep as-is
- [ ] Ensure nav icon points to /production route (V3 only)

---

## Phase 2: Remove Obsolete Frontend Components

### 2.1 Delete V2 Components
- [ ] Delete `web/src/components/dashboard/production/VarianceAnalysisTable.tsx`
- [ ] Delete `web/src/components/dashboard/production/InsightSummary.tsx` (if V2-only)
- [ ] Verify `PeriodRangeSelector.tsx` usage - keep if used by V3

### 2.2 Update Alert Monitor (Low Yield Alerts)
- [ ] Review [web/src/pages/AlertMonitor.tsx](web/src/pages/AlertMonitor.tsx#L10)
- [ ] Verify alert source: if legacy yield tables → remove section
- [ ] If sourced from V3 tables → keep and update comments
- [ ] Update API endpoint references from V2 to V3 if applicable

### 2.3 Update Data Upload Page
- [ ] Review [web/src/pages/DataUpload.tsx](web/src/pages/DataUpload.tsx#L99-L101)
- [ ] Update query invalidation to V3 only: `queryClient.invalidateQueries({ queryKey: ['yield', 'v3'] })`
- [ ] Remove legacy yield references from upload descriptions

---

## Phase 3: Backend Router & API Cleanup

### 3.1 Remove V2 Router
- [ ] Delete file: `src/api/routers/yield_v2.py` (353 lines)
- [ ] Update `src/api/routers/__init__.py`:
  - Remove `yield_v2` import
  - Remove from `__all__` list

### 3.2 Update Main Application
- [ ] Edit [src/api/main.py](src/api/main.py#L60):
  - Remove `app.include_router(yield_v2.router, ...)` line
  - Remove V2 comment block
  - Keep only V3 router registration

### 3.3 Audit API Dependencies
- [ ] Search codebase for `/api/v2/yield` endpoint references
- [ ] Update or remove integration tests referencing V2 endpoints
- [ ] Check `check_duplicates_api.py` and similar scripts

---

## Phase 4: Database Schema Cleanup

### 4.1 Legacy Yield Tables (DROP ONLY IF NO DEPENDENCIES)
**CAUTION:** Verify no external tools/scripts use these tables before dropping.

Tables to drop:
- [ ] `fact_p02_p01_yield` (P02→P01 yield tracking)
- [ ] `view_yield_dashboard` (materialized view)
- [ ] `fact_production_chain` (if exists and not used by V3)

**Script template:**
```sql
-- Backup first: pg_dump -t fact_p02_p01_yield alkana_db > backup_$(date +%Y%m%d).sql

BEGIN;
DROP VIEW IF EXISTS view_yield_dashboard CASCADE;
DROP TABLE IF EXISTS fact_p02_p01_yield CASCADE;
DROP TABLE IF EXISTS fact_production_chain CASCADE; -- verify first
COMMIT;
```

### 4.2 Model Cleanup
- [ ] Remove `FactP02P01Yield` class from [src/db/models.py](src/db/models.py#L772-L807)
- [ ] Remove view definitions from [src/db/views.py](src/db/views.py#L55-L82)
- [ ] Update `__all__` exports in models.py

### 4.3 Migration Scripts (Archive, Don't Delete)
- [ ] Move to `backups/legacy-yield-scripts/`:
  - `add_p02_p01_yield_table.py`
  - `check_yield_view.py`
  - `check_yield_data_structure.py`
  - `migrate_yield_v3.py`
  - `truncate_yield_data.py`

---

## Phase 5: ETL & Data Processing Cleanup

### 5.1 Loader Validation
- [ ] Verify `src/etl/loaders.py` does NOT contain legacy yield loaders
- [ ] Confirm `loader_zrpp062.py` is standalone (protected)
- [ ] Check for orphaned yield loader functions

### 5.2 Analysis Scripts Cleanup
Archive to `backups/legacy-yield-scripts/`:
- [ ] `analyze_p02_to_multiple_p01.py`
- [ ] `BRAINSTORM_YIELD_DECOMMISSION.md`
- [ ] `BRAINSTORM_YIELD_V3.md`
- [ ] Any scripts with "yield" in filename (review first)

---

## Phase 6: Verification & Health Checks

### 6.1 Build Verification
- [ ] Frontend build: `cd web && npm run build`
- [ ] Check for TypeScript errors
- [ ] Check for missing imports or unused variables
- [ ] Backend startup: `python -m uvicorn src.api.main:app`

### 6.2 API Health Checks
- [ ] Test V3 endpoints:
  - `GET /api/v3/yield/kpi`
  - `GET /api/v3/yield/trend`
  - `GET /api/v3/yield/distribution`
  - `POST /api/v3/yield/upload`
- [ ] Confirm V2 endpoints return 404: `GET /api/v2/yield/variance`
- [ ] Check `/docs` (Swagger) - V2 routes should be absent

### 6.3 Database Integrity
- [ ] Verify V3 tables intact:
  ```sql
  SELECT COUNT(*) FROM fact_production_performance_v2;
  SELECT COUNT(*) FROM dim_product_hierarchy;
  ```
- [ ] Confirm legacy tables dropped (if Phase 4 executed)
- [ ] Check foreign key constraints still valid

### 6.4 Frontend E2E Testing
- [ ] Navigate to /production route
- [ ] Verify only "Efficiency Hub" tab visible
- [ ] Test KPI cards load correctly
- [ ] Test trend charts render
- [ ] Test performance matrix interactions
- [ ] Upload ZRPP062 file via SmartUpload component

---

## Risks & Open Questions

### High Risks
1. **Alert Monitor Dependency:** Low yield alerts may reference legacy tables. Needs audit before table drop.
2. **External Integrations:** Unknown if external BI tools query `fact_p02_p01_yield` or `view_yield_dashboard`.
3. **Data Loss:** Dropping tables is irreversible. Ensure complete backup exists.

### Medium Risks
1. **TypeScript Build Errors:** Removing components may reveal circular dependencies.
2. **Query Invalidation:** DataUpload page invalidates both V2 and V3 queries - needs cleanup.
3. **Navigation UX:** Single-tab production page may confuse users expecting multi-view dashboard.

### Open Questions
1. Should we keep `raw_zrpp062` table or is it V2-specific? (Answer: KEEP - used by V3)
2. Are there scheduled jobs/cron tasks loading legacy yield data?
3. Do we need to preserve historical V2 variance analysis data for audits?
4. Should `/production` route redirect to a renamed route like `/efficiency-hub`?
5. Who has permission to execute DROP TABLE commands in production?

---

## Rollback Plan
If critical issues arise:
1. Restore database from backup: `psql alkana_db < backups/yield-decommission-2026-01-08/yield_tables_backup.sql`
2. Revert git commits for backend/frontend changes
3. Restart API server and rebuild frontend
4. Expected downtime: <15 minutes

---

## Success Criteria
- [ ] Production build succeeds with zero errors
- [ ] All V3 API endpoints return 200 status
- [ ] Database size reduced by removal of legacy tables
- [ ] No references to `yield_v2`, `VarianceAnalysisTable`, or legacy yield in codebase
- [ ] Documentation updated (README, API docs, changelog)

**Estimated Effort:** 6-8 hours (2 hours frontend, 2 hours backend, 2 hours DB, 2 hours testing)
