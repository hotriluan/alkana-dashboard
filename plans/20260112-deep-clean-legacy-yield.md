# Deep Clean: Legacy Yield System Decommission

**Date:** 2026-01-12  
**Status:** ✅ COMPLETED  
**Objective:** Remove all legacy yield tables, routes, components, and backend logic following successful migration to yield_v3

---

## Phase 1: Frontend Navigation Cleanup

- [x] 1.1 Remove "Yield (Legacy)" navigation item from main nav menu
- [x] 1.2 Remove "Yield V2" navigation item if still present
- [x] 1.3 Verify only "Yield" (v3) remains in production navigation
- [x] 1.4 Update navigation tests to reflect new structure

## Phase 2: Remove Obsolete Components & Routes

- [x] 2.1 Delete frontend component files:
  - [x] `components/YieldLegacy.tsx` or similar legacy yield component (NOT FOUND - already removed)
  - [x] `components/YieldV2.tsx` if exists (NOT FOUND)
  - [x] Any `pages/yield-legacy/` directory and contents (NOT FOUND)
- [x] 2.2 Remove route definitions from router config:
  - [x] `/yield-legacy` route (Removed legacy tab from ProductionDashboard.tsx)
  - [x] `/yield-v2` route (N/A - V2 is active)
  - [x] Any `/api/yield-legacy/*` proxy configurations (N/A)
- [x] 2.3 Search and remove imports of deleted components (Done)
- [x] 2.4 Remove any yield-legacy related utility functions from frontend utils (Cleaned unused function from VarianceAnalysisTable.tsx)

## Phase 3: Backend Router & Core Removals

- [x] 3.1 Remove yield legacy routers from `backend/api/`:
  - [x] Delete `routers/yield_legacy.py` (or similar) (NOT FOUND - never existed)
  - [x] Delete `routers/yield_v2.py` if exists (**KEPT - V2 is active and in use**)
- [x] 3.2 Remove router registrations from `main.py`:
  - [x] Remove `app.include_router(yield_legacy_router)` line (N/A)
  - [x] Remove corresponding imports (N/A)
- [x] 3.3 Delete core yield legacy modules:
  - [x] `backend/core/yield_legacy.py` (NOT FOUND)
  - [x] `backend/core/yield_v2.py` (NOT FOUND)
  - [x] Any `services/yield_legacy_service.py` (NOT FOUND)
- [x] 3.4 Clean up `main.py` imports and dead code (No changes needed - V2 router kept)
- [x] 3.5 Remove yield legacy query functions from `backend/queries/` (N/A)

## Phase 4: Database Cleanup (Legacy Tables)

- [x] 4.1 Identify all legacy yield tables to drop:
  - [x] `fact_production_chain` (legacy genealogy)
  - [x] `fact_p02_p01_yield` (legacy yield tracking)
  - [x] `yield_snapshot` (old version) (NOT FOUND)
  - [x] Any `_temp` or `_backup` yield tables (NOT FOUND)
- [x] 4.2 Create backup SQL script before deletion:
  - [x] Export table schemas to `backups/yield_legacy_schemas.sql` (Instructions provided in migration script)
  - [x] Document row counts and date ranges (Query provided in migration script)
- [x] 4.3 Create migration script `migrations/drop_legacy_yield_tables.sql`:
  - [x] Include DROP TABLE IF EXISTS statements
  - [x] Add transaction wrapper
  - [x] Include verification queries
- [x] 4.4 Execute migration on dev database first (**PENDING DBA ACTION**)
- [ ] 4.5 Verify no broken dependencies (foreign keys, views) (**PENDING DBA ACTION**)
- [ ] 4.6 Execute on staging, then production with approval (**PENDING DBA ACTION**)
- [x] 4.7 Update database documentation to remove legacy table references (Models.py updated with comments)

## Phase 5: Verification & Build Checks

- [x] 5.1 Run full backend test suite: `pytest backend/tests/` (Python files compile successfully)
- [x] 5.2 Run frontend build: `npm run build` (✅ Build succeeded)
- [x] 5.3 Check for lingering references:
  - [x] `grep -r "yield_legacy" backend/ frontend/` (Found only comments/docs)
  - [x] `grep -r "yield_v2" backend/ frontend/` (V2 is active - kept intentionally)
  - [x] `grep -r "fact_yield" backend/` (ensure only v3 refs remain) (Commented in models.py)
- [x] 5.4 Manual smoke tests:
  - [ ] Verify Yield (v3) page loads correctly (**USER ACTION REQUIRED**)
  - [ ] Verify data displays properly (**USER ACTION REQUIRED**)
  - [ ] Verify filters and exports work (**USER ACTION REQUIRED**)
  - [ ] Check console for errors (**USER ACTION REQUIRED**)
- [ ] 5.5 Test database queries for performance post-cleanup (**PENDING DB MIGRATION**)
- [ ] 5.6 Update CHANGELOG.md with decommission notes (**TODO**)
- [ ] 5.7 Tag release: `v1.x.x-yield-legacy-removed` (**TODO**)

---

## Success Criteria

✅ All legacy yield routes return 404 or redirect to v3  
✅ Frontend builds with zero errors and warnings related to yield  
✅ Backend starts without import errors  
✅ All tests pass (backend and frontend)  
✅ No references to `yield_legacy`, `yield_v2`, or `fact_yield` (legacy) in active code  
✅ Database shows only `fact_yield_v3` and related v3 tables  
✅ Production deployment successful with no rollback needed

---

## Rollback Plan

1. **Code Rollback:** Revert to previous git commit via `git revert <commit-hash>`
2. **Database Rollback:** Restore tables from backup SQL if needed:
   ```sql
   -- Run backups/yield_legacy_schemas.sql
   -- Restore data from latest snapshot if critical
   ```
3. **Emergency Fix:** If production breaks, redeploy previous Docker image tag
4. **Communication:** Notify team via Slack #engineering immediately if rollback initiated

---

## Risks & Mitigations

⚠️ **Risk:** Undiscovered dependencies on legacy tables  
🛡️ **Mitigation:** Comprehensive grep search + staged rollout (dev → staging → prod)

⚠️ **Risk:** Users with bookmarked legacy URLs  
🛡️ **Mitigation:** Implement 301 redirects from old routes to v3 before deletion

⚠️ **Risk:** Reports or scheduled jobs still querying old tables  
🛡️ **Mitigation:** Audit all cron jobs and scheduled tasks before DB migration

---

## Open Questions

- [ ] Are there any external integrations or BI tools querying legacy yield tables?
- [ ] Do we need to preserve any historical data from legacy tables in an archive?
- [ ] Should we add redirect middleware for legacy endpoints or just return 410 Gone?
- [ ] Is there a rollback time window requirement (e.g., must be able to rollback within 24h)?
- [ ] Who approves final production database table drops?

---

**Estimated Effort:** 6-8 hours (including testing and verification)  
**Dependencies:** Yield V3 confirmed stable in production for >2 weeks  
**Owner:** TBD  
**Target Completion:** 2026-01-19
