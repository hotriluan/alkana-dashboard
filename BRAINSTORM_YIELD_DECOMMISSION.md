# 🗑️ PRODUCTION YIELD MODULE DECOMMISSIONING - BRAINSTORM & EXECUTION PLAN

**Project:** Alkana Dashboard  
**Module:** Production Yield (V1 Legacy + V2 Variance Analysis)  
**Operation:** Complete Surgical Removal  
**Status:** BRAINSTORM → READY FOR EXECUTION  
**Date:** 2026-01-08  
**Compliance:** Claude Kit Engineer Standards

---

## 📋 EXECUTIVE SUMMARY

### Objective
Complete removal of Production Yield functionality (V1 + V2) from Alkana Dashboard while preserving critical systems:
- ✅ **Sales Performance** - Untouched
- ✅ **Inventory Dashboard** - Untouched
- ✅ **Supply Chain / Lead Time** - Untouched
- ✅ **AR Collection** - Untouched

### Scope Analysis
**Components to Remove:**
- **Database:** 5 tables (fact_production_chain + V2 tables + legacy archives)
- **Backend:** 2 API routers + 2 core logic files + 1 ETL loader
- **Frontend:** 2 pages + navigation links + TypeScript types
- **Documentation:** References in codebase-summary.md, API_REFERENCE.md

**Critical Constraints:**
- **NO SHARED LOADER DELETION** - loader_mb51.py, loader_cooispi.py power Inventory/Supply Chain
- **NO DOWNTIME** - System must compile/run after each phase
- **GIT SAFETY** - Branch isolation + commit checkpoints

---

## 🔍 PHASE 0: PRE-EXECUTION SAFEGUARDS

### 0.1 Data Backup (MANDATORY)
**Purpose:** Regulatory audit trail + rollback capability

**Action:**
```powershell
# Create backup directory
New-Item -Path "C:\dev\alkana-dashboard\backups\yield-decommission-2026-01-08" -ItemType Directory -Force

# Database backup (via pg_dump)
$backupPath = "C:\dev\alkana-dashboard\backups\yield-decommission-2026-01-08\yield_tables_backup.sql"
$tables = @(
    'fact_production_performance_v2',
    'raw_zrpp062',
    'fact_p02_p01_yield',
    'fact_production_chain',
    'archived_fact_production_chain_v1',
    '_legacy_fact_production_chain_202601'
)

foreach ($table in $tables) {
    pg_dump -h localhost -U postgres -d alkana_dashboard -t $table >> $backupPath
}
```

**Validation:**
- Backup file exists and contains CREATE TABLE statements
- Backup size > 0 bytes

---

### 0.2 Git Branching Strategy
**Action:**
```bash
git checkout -b chore/decommission-yield-module
git commit --allow-empty -m "chore: start yield module decommissioning"
```

**Checkpoint Commits:**
- After Frontend cleanup → `git commit -m "chore(frontend): remove yield pages & nav"`
- After Backend cleanup → `git commit -m "chore(backend): remove yield routers & logic"`
- After ETL cleanup → `git commit -m "chore(etl): remove yield loader"`
- After Database cleanup → `git commit -m "chore(database): drop yield tables"`

---

## 🖥️ PHASE 1: FRONTEND CLEANUP

### 1.1 File Inventory Analysis
**Files to DELETE:**
```
✅ web/src/pages/ProductionYield.tsx        (207 lines - Legacy V1)
✅ web/src/pages/VarianceAnalysisTable.tsx  (346 lines - V2)
```

**Files to EDIT:**
```
⚠️  web/src/App.tsx                          (Remove 2 routes)
⚠️  web/src/components/DashboardLayout.tsx  (Remove 2 nav items)
⚠️  web/src/types/index.ts                  (Remove V2 interfaces)
```

---

### 1.2 Detailed Execution Steps

#### Step 1.2.1: Remove Route Registrations
**File:** `web/src/App.tsx`

**Target Lines (69-81, 100-112):**
```tsx
// LINE 69-81: Remove this entire block
<Route
  path="/yield"
  element={
    <ProtectedRoute>
      <DashboardLayout>
        <ProductionYield />
      </DashboardLayout>
    </ProtectedRoute>
  }
/>

// LINE 100-112: Remove this entire block
<Route
  path="/variance-analysis"
  element={
    <ProtectedRoute>
      <DashboardLayout>
        <VarianceAnalysisTable />
      </DashboardLayout>
    </ProtectedRoute>
  }
/>
```

**Also Remove Imports (Lines 6, 13):**
```tsx
import ProductionYield from './pages/ProductionYield';          // DELETE
import VarianceAnalysisTable from './pages/VarianceAnalysisTable'; // DELETE
```

**Validation:**
```powershell
npm run build
# Must succeed with 0 errors
```

---

#### Step 1.2.2: Clean Navigation Menu
**File:** `web/src/components/DashboardLayout.tsx`

**Target Lines (37-38):**
```tsx
// LINE 37: Remove Production Yield
{ path: '/yield', icon: TrendingUp, label: 'Production Yield' },

// LINE 38: Remove Variance Analysis
{ path: '/variance-analysis', icon: Target, label: 'Variance Analysis' },
```

**Icon Cleanup (Lines 4-5):**
```tsx
// Remove unused imports if no other component uses them
import { TrendingUp } from 'lucide-react';  // Check usage first
import { Target } from 'lucide-react';       // Check usage first
```

**Validation:**
- Frontend dev server runs without errors
- Navigation sidebar displays correctly
- No console warnings about missing routes

---

#### Step 1.2.3: Clean TypeScript Types
**File:** `web/src/types/index.ts`

**Remove Lines 61-93 (V2 Production Yield Interfaces):**
```typescript
// Delete this entire section:
// V2 Production Yield Variance Analysis
export interface VarianceRecord {
  process_order_id: string;
  batch_id: string | null;
  material_code: string | null;
  material_description: string | null;
  product_group_1: string | null;
  output_actual_kg: number | null;
  input_actual_kg: number | null;
  loss_kg: number | null;
  loss_pct: number | null;
  variant_fg_pct: number | null;
  posting_date: string;
}

export interface VarianceAnalysisSummary {
  total_orders: number;
  total_output_kg: number;
  total_input_kg: number;
  total_loss_kg: number;
  avg_loss_pct: number;
  records_above_target: number;
  records_below_target: number;
}

export interface VarianceAnalysisResponse {
  summary: VarianceAnalysisSummary;
  records: VarianceRecord[];
  date_range: {
    start_date: string;
    end_date: string;
  };
}
```

**Validation:**
```powershell
cd web
npm run type-check  # TypeScript compilation must succeed
```

---

#### Step 1.2.4: Delete Component Files
**Action:**
```powershell
Remove-Item "C:\dev\alkana-dashboard\web\src\pages\ProductionYield.tsx" -Force
Remove-Item "C:\dev\alkana-dashboard\web\src\pages\VarianceAnalysisTable.tsx" -Force
```

**Validation:**
- Files no longer exist in filesystem
- No broken imports in other files (verify with `npm run build`)

---

### 1.3 Frontend Phase Validation Checklist
```
✅ npm run build → SUCCESS
✅ npm run type-check → SUCCESS
✅ Dev server runs without errors
✅ All navigation links work (except /yield, /variance-analysis)
✅ No console errors in browser
✅ Inventory/Sales/AR dashboards still accessible
```

**Git Checkpoint:**
```bash
git add .
git commit -m "chore(frontend): remove production yield pages & navigation

- Deleted ProductionYield.tsx (V1 legacy)
- Deleted VarianceAnalysisTable.tsx (V2)
- Removed routes from App.tsx
- Removed nav items from DashboardLayout.tsx
- Cleaned V2 types from index.ts
- Verified: Build succeeds, no TypeScript errors"
```

---

## ⚙️ PHASE 2: BACKEND API CLEANUP

### 2.1 File Inventory Analysis
**Files to DELETE:**
```
✅ src/api/routers/yield_dashboard.py  (201 lines - V1 Legacy)
✅ src/api/routers/yield_v2.py         (161 lines - V2)
```

**Files to EDIT:**
```
⚠️  src/api/main.py                     (Remove 2 router imports + registrations)
⚠️  src/api/routers/__init__.py         (Remove yield imports from __all__)
```

---

### 2.2 Detailed Execution Steps

#### Step 2.2.1: Deregister Routers in main.py
**File:** `src/api/main.py`

**Remove Import (Lines 16-17):**
```python
# LINE 16: Remove this
from src.api.routers import (
    alerts, lead_time,
    auth, ar_aging, mto_orders, 
    yield_dashboard, yield_v2, sales_performance, executive,  # DELETE yield_dashboard, yield_v2
    inventory, upload
)

# After cleanup:
from src.api.routers import (
    alerts, lead_time,
    auth, ar_aging, mto_orders, 
    sales_performance, executive,
    inventory, upload
)
```

**Remove Router Registrations (Lines 58-59):**
```python
# LINE 58: Remove this
app.include_router(yield_dashboard.router, prefix="/api/v1/dashboards")

# LINE 59: Remove this
app.include_router(yield_v2.router, prefix="/api")
```

**Validation:**
```powershell
# Test server startup
uvicorn src.api.main:app --reload

# Should see:
# INFO: Application startup complete
# NO errors about missing yield modules
```

---

#### Step 2.2.2: Clean Router __init__.py
**File:** `src/api/routers/__init__.py`

**Current State (Lines 1-12):**
```python
from . import (
    alerts, lead_time,
    auth, ar_aging, mto_orders, 
    yield_dashboard, sales_performance, executive,  # DELETE yield_dashboard
    inventory
)

__all__ = [
    "alerts", "lead_time",
    "auth", "ar_aging", "mto_orders", 
    "yield_dashboard", "sales_performance", "executive",  # DELETE yield_dashboard
    "inventory"
]
```

**After Cleanup:**
```python
from . import (
    alerts, lead_time,
    auth, ar_aging, mto_orders, 
    sales_performance, executive,
    inventory
)

__all__ = [
    "alerts", "lead_time",
    "auth", "ar_aging", "mto_orders", 
    "sales_performance", "executive",
    "inventory"
]
```

---

#### Step 2.2.3: Delete Router Files
**Action:**
```powershell
Remove-Item "C:\dev\alkana-dashboard\src\api\routers\yield_dashboard.py" -Force
Remove-Item "C:\dev\alkana-dashboard\src\api\routers\yield_v2.py" -Force
```

**Validation:**
```powershell
# Verify API still responds
curl http://localhost:8000/health

# Test critical endpoints (must still work):
curl http://localhost:8000/api/v1/dashboards/sales/summary
curl http://localhost:8000/api/v1/inventory/summary
curl http://localhost:8000/api/v1/lead-time/summary

# Verify yield endpoints are gone (must fail):
curl http://localhost:8000/api/v1/dashboards/yield/summary
# Expected: 404 Not Found

curl http://localhost:8000/api/v2/yield/variance
# Expected: 404 Not Found
```

---

### 2.3 Backend Phase Validation Checklist
```
✅ uvicorn starts without errors
✅ /health endpoint returns 200 OK
✅ Sales API still works
✅ Inventory API still works
✅ Lead Time API still works
✅ Yield API endpoints return 404 (correct behavior)
✅ API docs (/api/docs) loads without errors
```

**Git Checkpoint:**
```bash
git add .
git commit -m "chore(backend): remove yield API routers

- Deleted yield_dashboard.py (V1 legacy)
- Deleted yield_v2.py (V2)
- Removed router imports from main.py
- Cleaned __init__.py
- Verified: Server starts, critical APIs functional"
```

---

## 🔄 PHASE 3: CORE LOGIC & ETL CLEANUP

### 3.1 File Inventory Analysis
**Files to DELETE:**
```
✅ src/core/yield_tracker.py       (396 lines - Production chain logic)
✅ src/core/p02_p01_yield.py       (Yield calculation helper)
✅ src/etl/loaders/loader_zrpp062.py (425 lines - V2 loader)
```

**Files to REVIEW (DO NOT DELETE):**
```
⚠️  src/core/netting.py             (Check for yield functions - keep file)
⚠️  NO shared loaders exist          (Confirmed: no loader_mb51.py, loader_cooispi.py in workspace)
```

---

### 3.2 Detailed Execution Steps

#### Step 3.2.1: Verify No Dependencies on Yield Core Logic
**Action:**
```powershell
# Search for imports of yield_tracker
grep -r "from src.core.yield_tracker" --include="*.py" .
grep -r "import yield_tracker" --include="*.py" .

# Search for imports of p02_p01_yield
grep -r "from src.core.p02_p01_yield" --include="*.py" .
grep -r "import p02_p01_yield" --include="*.py" .

# Expected: NO RESULTS (already removed routers that used them)
```

---

#### Step 3.2.2: Check netting.py for Yield Functions
**File:** `src/core/netting.py`

**Action:**
- Open file and search for functions named `calculate_yield`, `track_yield`, etc.
- **IF FOUND:** Delete only those specific functions
- **IF NOT FOUND:** Keep entire file unchanged (it's used by lead time)

**IMPORTANT:** Do NOT delete netting.py if it contains:
- `calculate_lead_time`
- `stack_netting`
- `process_mvt_601`

---

#### Step 3.2.3: Delete Core Logic Files
**Action:**
```powershell
Remove-Item "C:\dev\alkana-dashboard\src\core\yield_tracker.py" -Force
Remove-Item "C:\dev\alkana-dashboard\src\core\p02_p01_yield.py" -Force
```

**Validation:**
```powershell
# Python import test (must not raise ImportError)
python -c "from src.api.routers import inventory, sales_performance, lead_time"
```

---

#### Step 3.2.4: Delete ETL Loader
**Action:**
```powershell
Remove-Item "C:\dev\alkana-dashboard\src\etl\loaders\loader_zrpp062.py" -Force
```

**Validation:**
- File no longer exists
- No Python scripts reference `Zrpp062Loader` (search codebase)

---

### 3.3 ETL Phase Validation Checklist
```
✅ No Python import errors when importing remaining modules
✅ netting.py still exists (if it has lead time logic)
✅ No references to deleted files in codebase
✅ Test scripts in root directory still run (if they import core modules)
```

**Git Checkpoint:**
```bash
git add .
git commit -m "chore(core): remove yield tracking logic & ETL loader

- Deleted yield_tracker.py (production chain logic)
- Deleted p02_p01_yield.py (yield calculations)
- Deleted loader_zrpp062.py (V2 ETL)
- Verified: No broken imports in remaining modules"
```

---

## 🗄️ PHASE 4: DATABASE CLEANUP

### 4.1 Table Inventory Analysis
**Tables to DROP:**
```sql
-- V2 Production Yield
fact_production_performance_v2  (606 rows - V2 variance analysis)
raw_zrpp062                      (610 rows - V2 staging)

-- Legacy V1 Production Yield
fact_p02_p01_yield              (Unknown rows - P02→P01 tracking)
fact_production_chain           (127 rows - P03→P02→P01 chain)
archived_fact_production_chain_v1
_legacy_fact_production_chain_202601

-- Legacy Alerts (if not used by other modules)
fact_yield_alerts               (ONLY if not referenced by alert system)
_legacy_fact_yield_alerts
```

---

### 4.2 Dependency Check (CRITICAL)
**Action:**
```sql
-- Check if alert system references yield alerts
SELECT DISTINCT alert_type 
FROM fact_alerts 
WHERE alert_type LIKE '%YIELD%';

-- If result = 'LOW_YIELD' exists:
--   → Review alerts.py router to see if it queries LOW_YIELD
--   → If YES: Keep fact_yield_alerts schema but delete data
--   → If NO: Safe to drop
```

**Decision Matrix:**
| Scenario | Action |
|----------|--------|
| Alert system queries LOW_YIELD alerts | Keep table, delete data: `DELETE FROM fact_alerts WHERE alert_type = 'LOW_YIELD'` |
| Alert system doesn't use yield alerts | Drop table entirely |

---

### 4.3 Detailed Execution Steps

#### Step 4.3.1: Execute DROP Statements
**File:** Create `scripts/drop_yield_tables.sql`

```sql
-- Drop V2 Production Yield Tables
DROP TABLE IF EXISTS fact_production_performance_v2 CASCADE;
DROP TABLE IF EXISTS raw_zrpp062 CASCADE;

-- Drop Legacy V1 Tables
DROP TABLE IF EXISTS fact_p02_p01_yield CASCADE;
DROP TABLE IF EXISTS fact_production_chain CASCADE;
DROP TABLE IF EXISTS archived_fact_production_chain_v1 CASCADE;
DROP TABLE IF EXISTS _legacy_fact_production_chain_202601 CASCADE;

-- Optional: Drop yield-specific alerts (verify first!)
-- DROP TABLE IF EXISTS fact_yield_alerts CASCADE;
-- DROP TABLE IF EXISTS _legacy_fact_yield_alerts CASCADE;

-- Clean yield alerts from unified fact_alerts (safer approach)
DELETE FROM fact_alerts WHERE alert_type = 'LOW_YIELD';
```

**Execution:**
```powershell
# Connect to database
psql -h localhost -U postgres -d alkana_dashboard

# Run script
\i C:/dev/alkana-dashboard/scripts/drop_yield_tables.sql

# Verify tables are gone
\dt fact_production*
\dt raw_zrpp*

# Should return: "Did not find any relation"
```

---

#### Step 4.3.2: Clean SQLAlchemy Models
**File:** `src/db/models.py`

**Remove Model Classes (Lines 578-615, 773-927):**
```python
# DELETE Lines 578-615: FactProductionChain class
class FactProductionChain(Base):
    """Fact: Yield Tracking P03→P02→P01"""
    # ... entire class ...

# DELETE Lines 773-802: (If exists) FactP02P01Yield class
class FactP02P01Yield(Base):
    # ... entire class ...

# DELETE Lines 814-878: RawZrpp062 class
class RawZrpp062(Base):
    """Raw: ZRPP062 Excel Upload"""
    # ... entire class ...

# DELETE Lines 881-927: FactProductionPerformanceV2 class
class FactProductionPerformanceV2(Base):
    """Fact: V2 Production Performance"""
    # ... entire class ...
```

**Validation:**
```powershell
# Test SQLAlchemy imports
python -c "from src.db.models import FactInventory, FactBilling, FactLeadTime"

# Must succeed without errors
```

---

### 4.4 Database Phase Validation Checklist
```
✅ Tables dropped successfully (verify with \dt in psql)
✅ SQLAlchemy models removed from models.py
✅ Python import test passes
✅ Backend server starts without ORM errors
✅ Inventory/Sales queries still work
```

**Git Checkpoint:**
```bash
git add .
git commit -m "chore(database): drop production yield tables

- Dropped fact_production_performance_v2 (V2)
- Dropped raw_zrpp062 (V2 staging)
- Dropped fact_p02_p01_yield (V1)
- Dropped fact_production_chain (V1)
- Dropped legacy archives
- Cleaned LOW_YIELD alerts from fact_alerts
- Removed SQLAlchemy models
- Verified: Database queries functional"
```

---

## 📚 PHASE 5: DOCUMENTATION CLEANUP

### 5.1 Files to Update
```
⚠️  docs/codebase-summary.md     (Remove yield sections)
⚠️  docs/API_REFERENCE.md         (Remove yield endpoints)
⚠️  CHANGELOG.md                  (Add decommission entry)
⚠️  V2_PRODUCTION_YIELD_IMPLEMENTATION_REPORT.md (Archive or delete)
```

---

### 5.2 Detailed Execution Steps

#### Step 5.2.1: Update codebase-summary.md
**File:** `docs/codebase-summary.md`

**Sections to Remove:**
- Line 59-77: "yield_v2.py" section
- Line 37: "yield_dashboard.py" from routers list
- Any "V2 Production Yield Module" sections
- Any "Production Yield" frontend pages

---

#### Step 5.2.2: Update API_REFERENCE.md
**File:** `docs/API_REFERENCE.md`

**Remove Entire Section (Lines 429-520):**
```md
## Production Yield
### Get Yield Summary
### Get Batch Yield Details
### Get P02-P01 Yield Tracking
### Get Material Genealogy
```

---

#### Step 5.2.3: Update CHANGELOG.md
**File:** `CHANGELOG.md`

**Add New Entry:**
```md
## [Decommissioned] 2026-01-08

### Removed
- **Production Yield Module (V1 + V2)** - Complete removal
  - Frontend: ProductionYield.tsx, VarianceAnalysisTable.tsx
  - Backend: yield_dashboard.py, yield_v2.py
  - ETL: loader_zrpp062.py, yield_tracker.py, p02_p01_yield.py
  - Database: fact_production_performance_v2, raw_zrpp062, fact_p02_p01_yield, fact_production_chain
  - Reason: Module decommissioned per business directive
  - Migration: Data backed up to backups/yield-decommission-2026-01-08/
```

---

#### Step 5.2.4: Handle Implementation Report
**Options:**

**Option A: Archive**
```powershell
Move-Item "V2_PRODUCTION_YIELD_IMPLEMENTATION_REPORT.md" "backups/yield-decommission-2026-01-08/"
```

**Option B: Delete**
```powershell
Remove-Item "V2_PRODUCTION_YIELD_IMPLEMENTATION_REPORT.md" -Force
```

**Recommendation:** ARCHIVE (keep historical record)

---

### 5.3 Documentation Phase Validation Checklist
```
✅ codebase-summary.md no longer mentions yield
✅ API_REFERENCE.md no longer documents yield endpoints
✅ CHANGELOG.md has decommission entry
✅ Implementation report archived
✅ No broken links in documentation
```

**Git Checkpoint:**
```bash
git add .
git commit -m "docs: remove production yield documentation

- Updated codebase-summary.md (removed yield sections)
- Updated API_REFERENCE.md (removed yield endpoints)
- Added decommission entry to CHANGELOG.md
- Archived V2 implementation report
- Verified: No broken documentation links"
```

---

## ✅ PHASE 6: FINAL VALIDATION & REGRESSION TESTING

### 6.1 System Health Checks
```powershell
# 1. Backend Build Test
uvicorn src.api.main:app --reload
# Must start without errors

# 2. Frontend Build Test
cd web
npm run build
# Must succeed with 0 errors

# 3. TypeScript Type Check
npm run type-check
# Must pass without errors
```

---

### 6.2 Regression Test Suite
**Critical Endpoints to Test:**

```powershell
$API_BASE = "http://localhost:8000/api/v1"

# Executive Dashboard
Invoke-RestMethod "$API_BASE/dashboards/executive/summary"

# Sales Performance
Invoke-RestMethod "$API_BASE/dashboards/sales/summary"

# Inventory
Invoke-RestMethod "$API_BASE/inventory/summary"

# Lead Time
Invoke-RestMethod "$API_BASE/lead-time/summary"

# AR Aging
Invoke-RestMethod "$API_BASE/dashboards/ar-aging/summary"

# Alerts
Invoke-RestMethod "$API_BASE/alerts/summary"
```

**Expected:** All return 200 OK with valid JSON

---

### 6.3 Frontend Navigation Test
**Manual Steps:**
1. Open http://localhost:5173
2. Login with valid credentials
3. Navigate to each menu item:
   - ✅ Executive Dashboard
   - ✅ AR Collection
   - ✅ Inventory
   - ✅ MTO Orders
   - ✅ Sales Performance
   - ✅ Lead Time Analysis
   - ✅ Alert Monitor
   - ✅ Data Upload
4. Verify no console errors
5. Verify no "/yield" or "/variance-analysis" links exist

---

### 6.4 Database Integrity Check
```sql
-- Verify critical tables still exist
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN (
    'fact_billing',
    'fact_inventory',
    'fact_lead_time',
    'fact_ar_aging',
    'fact_alerts'
  );

-- Expected: All 5 tables present

-- Verify yield tables are gone
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename LIKE '%yield%';

-- Expected: 0 rows

SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename LIKE '%production_chain%';

-- Expected: 0 rows
```

---

### 6.5 Final Validation Checklist
```
✅ Backend starts without errors
✅ Frontend builds successfully
✅ All critical APIs respond 200 OK
✅ All navigation links work
✅ No console errors in browser
✅ Inventory dashboard loads correctly
✅ Sales dashboard loads correctly
✅ Lead time dashboard loads correctly
✅ No yield-related database tables exist
✅ No yield-related code files exist
✅ Documentation updated and accurate
```

---

## 🚨 ROLLBACK PROCEDURES

### Scenario 1: Database Rollback
**Issue:** Accidentally dropped wrong table / need to restore data

**Action:**
```powershell
# Restore from backup
psql -h localhost -U postgres -d alkana_dashboard < "C:\dev\alkana-dashboard\backups\yield-decommission-2026-01-08\yield_tables_backup.sql"
```

---

### Scenario 2: Code Rollback
**Issue:** Critical system broken / need to restore yield functionality

**Action:**
```bash
# Revert to commit before decommissioning
git log --oneline  # Find commit hash before "chore/decommission-yield-module"
git revert <commit-hash>..HEAD

# Or reset branch
git reset --hard <commit-hash-before-decommission>
git push origin chore/decommission-yield-module --force
```

---

### Scenario 3: Partial Rollback (Frontend Only)
**Issue:** Frontend broken but backend OK

**Action:**
```bash
# Checkout specific files from previous commit
git checkout HEAD~1 -- web/src/pages/ProductionYield.tsx
git checkout HEAD~1 -- web/src/pages/VarianceAnalysisTable.tsx
git checkout HEAD~1 -- web/src/App.tsx
git checkout HEAD~1 -- web/src/components/DashboardLayout.tsx
```

---

## 📊 RISK ANALYSIS

### High-Risk Operations
| Operation | Risk Level | Mitigation |
|-----------|------------|------------|
| Drop fact_production_chain | 🔴 HIGH | Backup first, verify no foreign keys |
| Delete loader files | 🟡 MEDIUM | Search for imports before deletion |
| Edit main.py | 🟡 MEDIUM | Test server startup immediately after |
| Delete TypeScript types | 🟢 LOW | Type-check validates automatically |

---

## 🎯 SUCCESS CRITERIA

### Definition of Done
- [ ] All 6 phases completed
- [ ] All validation checklists passed
- [ ] No errors in backend logs
- [ ] No errors in frontend console
- [ ] All critical dashboards functional
- [ ] Documentation updated
- [ ] Git history clean with descriptive commits
- [ ] Backup verified and accessible

---

## 📝 POST-EXECUTION REPORT TEMPLATE

```md
# Production Yield Decommissioning - Execution Report
**Date Executed:** YYYY-MM-DD
**Executed By:** [Name]
**Total Duration:** X hours

## Summary
- Files Deleted: X
- Tables Dropped: X
- Lines of Code Removed: X
- Backup Size: X MB

## Validation Results
- Backend Build: ✅ PASS
- Frontend Build: ✅ PASS
- API Tests: ✅ PASS (X/X endpoints)
- Database Integrity: ✅ PASS

## Issues Encountered
[None / List any issues]

## Rollback Performed
[No / Description if yes]

## Final Status
✅ DECOMMISSIONING COMPLETE - SYSTEM OPERATIONAL
```

---

## 🔗 APPENDIX A: COMMAND REFERENCE

### Quick Command Sheet
```powershell
# Phase 1: Frontend
npm run build
npm run type-check

# Phase 2: Backend
uvicorn src.api.main:app --reload
curl http://localhost:8000/health

# Phase 3: ETL
python -c "from src.core import netting"

# Phase 4: Database
psql -h localhost -U postgres -d alkana_dashboard
\dt fact_*
\dt raw_*

# Phase 5: Documentation
code docs/codebase-summary.md

# Phase 6: Validation
Invoke-RestMethod "http://localhost:8000/api/v1/inventory/summary"
```

---

## 🔗 APPENDIX B: FILE INVENTORY SUMMARY

### Frontend (2 files deleted + 3 edited)
```
❌ DELETE: web/src/pages/ProductionYield.tsx
❌ DELETE: web/src/pages/VarianceAnalysisTable.tsx
✏️  EDIT:   web/src/App.tsx
✏️  EDIT:   web/src/components/DashboardLayout.tsx
✏️  EDIT:   web/src/types/index.ts
```

### Backend (2 files deleted + 2 edited)
```
❌ DELETE: src/api/routers/yield_dashboard.py
❌ DELETE: src/api/routers/yield_v2.py
✏️  EDIT:   src/api/main.py
✏️  EDIT:   src/api/routers/__init__.py
```

### Core Logic (2-3 files deleted)
```
❌ DELETE: src/core/yield_tracker.py
❌ DELETE: src/core/p02_p01_yield.py
❌ DELETE: src/etl/loaders/loader_zrpp062.py
⚠️  REVIEW: src/core/netting.py (may need function removal)
```

### Database (6 tables dropped + 1 edited)
```
❌ DROP: fact_production_performance_v2
❌ DROP: raw_zrpp062
❌ DROP: fact_p02_p01_yield
❌ DROP: fact_production_chain
❌ DROP: archived_fact_production_chain_v1
❌ DROP: _legacy_fact_production_chain_202601
✏️ EDIT: src/db/models.py (remove model classes)
```

### Documentation (3 files updated + 1 archived)
```
✏️  EDIT:    docs/codebase-summary.md
✏️  EDIT:    docs/API_REFERENCE.md
✏️  EDIT:    CHANGELOG.md
📦 ARCHIVE: V2_PRODUCTION_YIELD_IMPLEMENTATION_REPORT.md
```

---

## 🔗 APPENDIX C: DEPENDENCY MATRIX

### What Depends on What?
```
ProductionYield.tsx
  └─ Uses: /api/v1/dashboards/yield/summary
  └─ Impact: Frontend only

VarianceAnalysisTable.tsx
  └─ Uses: /api/v2/yield/variance
  └─ Impact: Frontend only

yield_dashboard.py (Router)
  ├─ Uses: fact_p02_p01_yield (table)
  ├─ Uses: p02_p01_yield.py (logic)
  └─ Impact: API endpoints + database

yield_v2.py (Router)
  ├─ Uses: fact_production_performance_v2 (table)
  ├─ Uses: raw_zrpp062 (table)
  └─ Impact: API endpoints + database

yield_tracker.py (Core)
  ├─ Uses: MB51 data (NOT loader - uses DataFrame)
  ├─ Uses: COOISPI data (NOT loader - uses DataFrame)
  └─ Impact: Business logic only (no direct DB)

loader_zrpp062.py (ETL)
  ├─ Writes to: raw_zrpp062, fact_production_performance_v2
  └─ Impact: Data pipeline only
```

**CRITICAL FINDING:** 
- ✅ NO shared loaders exist in workspace
- ✅ yield_tracker.py uses DataFrames, NOT loader classes
- ✅ Safe to delete all yield files without affecting Inventory/Supply Chain

---

## ✅ EXECUTION READY

This brainstorm document is production-ready. All phases have:
- Detailed step-by-step instructions
- Validation checkpoints
- Rollback procedures
- Risk analysis
- Success criteria

**Next Steps:**
1. Review this document with team
2. Schedule maintenance window (estimated 2-4 hours)
3. Execute phases sequentially
4. Validate after each phase
5. Complete post-execution report

**Claude Kit Compliance:**
- ✅ Concise language (sacrifice grammar for concision)
- ✅ Technical specificity (exact file paths, line numbers)
- ✅ Risk awareness (backup, validation, rollback)
- ✅ Executable commands (copy-paste ready)
- ✅ Unresolved questions listed below

---

## ❓ UNRESOLVED QUESTIONS

1. **Alert System Dependency:** Does the current alert monitoring system actively query `LOW_YIELD` alerts from `fact_alerts`? Need to verify alerts.py router logic before deciding table drop strategy.

2. **netting.py Function Inventory:** Does `src/core/netting.py` contain yield-specific functions? Needs manual review to determine if partial deletion required.

3. **Test Scripts:** Are there test scripts in root directory (test_*.py, check_*.py) that reference yield modules? May need cleanup.

4. **Database Foreign Keys:** Do any tables have foreign key constraints pointing to yield tables? Need to verify with `\d+ fact_production_chain` in psql.

5. **Production Data Value:** Should we archive yield data to CSV before deletion for potential future analysis? Current plan only creates SQL dump.

---

**END OF BRAINSTORM DOCUMENT**
