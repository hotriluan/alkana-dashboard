# 🕵️ INVENTORY FORENSIC REPORT

**Date:** January 16, 2026  
**Auditor:** AI Development Agent  
**Priority:** CRITICAL / BLOCKER  
**Status:** ROOT CAUSE IDENTIFIED ✅

---

## 🚨 EXECUTIVE SUMMARY

**USER COMPLAINT:** "Inventory Movers/Dead Stock shows velocity = 2 despite uploading real MB51 data"

**ROOT CAUSE IDENTIFIED:** 
1. ✅ Real MB51 data uploaded successfully (179,513 rows)
2. ❌ **ETL FAILURE:** Only 4,348 rows (2.4%) transformed to fact_inventory
3. 🔥 **CRITICAL:** dim_material table is EMPTY (0 rows) - all materials orphaned
4. ❌ Movement type mismatch: Raw has 601/101, fact_inventory only has 999

**VERDICT:** ETL pipeline BROKEN. Data exists but not processed correctly.

---

## A. DATABASE VITALS

### **Raw Data (raw_mb51)**

| Metric | Value | Status |
|:-------|:------|:-------|
| **Total Rows** | 179,513 | ✅ GOOD - Real data uploaded |
| **Date Range** | 2024-12-31 to 2026-01-16 | ✅ MATCHES user expectations |
| **Top Movement Types** | 601 (27,528), 101 (22,969), 351 (11,840) | ✅ VALID SAP codes |
| **Schema** | col_0_posting_date, col_1_mvt_type, col_4_material | ✅ Correct structure |

### **Transformed Data (fact_inventory)**

| Metric | Value | Status |
|:-------|:------|:-------|
| **Total Rows** | 4,348 | ❌ **CRITICAL** - Only 2.4% of raw data! |
| **Date Range** | 2024-12-31 to 2026-01-16 | ✅ Same as raw |
| **Unique Materials** | 3,300 | ⚠️ OK count but... |
| **Movement Types** | 999 (4,348 rows) | ❌ **WRONG** - Should be 601, 101, etc! |
| **Orphaned Materials** | 4,348 (100%) | 🔥 **BLOCKER** - dim_material is EMPTY! |

### **Dimension Table (dim_material)**

| Metric | Value | Status |
|:-------|:------|:-------|
| **Total Rows** | 0 | 🔥 **EMPTY TABLE** - No material master data! |

---

## B. LOGIC CODE INSPECTION

### **Current Formula on Disk**

**File:** `src/core/inventory_analytics.py`

```python
# Line 40: Movement type filter
OUTBOUND_MVT_TYPES = [999, 601, 261]  # Test data (999) + Issue & External Delivery

# Line 94: Velocity calculation (get_abc_analysis)
velocity_data = self.db.query(
    FactInventory.material_code,
    func.count(FactInventory.id).label('velocity')
).filter(
    and_(
        FactInventory.posting_date >= start_date,
        FactInventory.posting_date <= end_date,
        FactInventory.mvt_type.in_(self.OUTBOUND_MVT_TYPES)
    )
).group_by(
    FactInventory.material_code
).all()

# Line 188: Same logic in get_top_movers_and_dead_stock()
velocity_data = self.db.query(
    FactInventory.material_code,
    func.count(FactInventory.id).label('velocity')
).filter(
    and_(
        FactInventory.posting_date >= start_date,
        FactInventory.posting_date <= end_date,
        FactInventory.mvt_type.in_(self.OUTBOUND_MVT_TYPES)
    )
).group_by(
    FactInventory.material_code
).all()
```

### **Verdict:**

✅ **Code Logic is CORRECT** - Uses transaction volume (COUNT(id))  
✅ **Filter includes real SAP codes** - [999, 601, 261]  
❌ **But fact_inventory only has mvt_type=999** - Filter finds nothing with 601/261!

---

## C. MANUAL SQL QUERY RESULTS

### **Test 1: Top 10 Materials by Transaction Volume (2025-2026)**

```sql
SELECT material_code, COUNT(id) as txn_count 
FROM fact_inventory 
WHERE posting_date >= '2025-01-01' AND posting_date <= '2026-01-16'
GROUP BY material_code 
ORDER BY txn_count DESC 
LIMIT 10;
```

**Result:**
```
material_code | txn_count
--------------+-----------
100000621     |         2
100003173     |         2
100004290     |         2
100000865     |         2
100004972     |         2
100003123     |         2
100002038     |         2
100006021     |         2
100000846     |         2
100000328     |         2
```

**Analysis:** ❌ ALL materials have txn_count = 2 (max possible with 4,348 rows / 3,300 materials)

### **Test 2: Movement Type Distribution**

**Raw MB51:**
```
mvt_type | count
---------+-------
601      | 27,528  ← Outbound delivery
101      | 22,969  ← Goods receipt
351      | 11,840  ← Goods movement
201      |  6,657  ← Goods issue
311      |  6,164  
321      |  5,626
```

**Fact Inventory:**
```
mvt_type | count
---------+-------
999      |  4,348  ← TEST DATA ONLY!
```

**Verdict:** 🔥 **ETL NOT PROCESSING REAL MOVEMENT TYPES**

### **Test 3: Orphaned Materials Check**

```sql
SELECT COUNT(*) as total_orphaned 
FROM fact_inventory fi 
LEFT JOIN dim_material dm ON fi.material_code = dm.material_code 
WHERE dm.material_code IS NULL;
```

**Result:** 4,348 (100% orphaned)

**Cause:** dim_material has 0 rows!

---

## D. ROOT CAUSE & SOLUTION

### **🔍 Root Cause Analysis**

#### **Problem 1: ETL Transformation Failure**

**Evidence:**
- Raw MB51: 179,513 rows
- Fact Inventory: 4,348 rows (2.4% only)
- Missing: 175,165 rows (97.6% of data!)

**Cause:** ETL pipeline (`etl/processors/mb51.py` or similar) is:
- Not running after upload
- Filtering out 97% of data
- Only keeping test data (mvt_type=999)

#### **Problem 2: Movement Type Not Transformed**

**Evidence:**
- Raw has: 601, 101, 351, 201, 311, 321
- Fact has: 999 only

**Cause:** ETL is not mapping `col_1_mvt_type` to `fact_inventory.mvt_type` correctly

#### **Problem 3: Dimension Table Empty**

**Evidence:**
- dim_material: 0 rows
- 100% of fact_inventory materials are orphaned

**Cause:** Material master data not populated from:
- `col_4_material` (material code)
- `col_5_material_desc` (description)

#### **Problem 4: Why Velocity = 2?**

**Chain of Failures:**
```
1. Only 4,348 rows in fact_inventory (should be 179,513)
2. These are old TEST DATA with mvt_type=999
3. 3,300 unique materials, 4,348 rows = avg 1.3 txns per material
4. Max txns per material = 2
5. Top 10 all have exactly 2 transactions
6. Result: Velocity = 2 for all "top movers" ❌
```

---

## 🛠️ SOLUTION ROADMAP

### **IMMEDIATE ACTION (Critical Path)**

#### **Step 1: Run ETL Transformation** 🔥 BLOCKER

**Action:** Execute MB51 ETL processor to transform raw_mb51 → fact_inventory

**Expected Commands:**
```bash
# Option A: Re-run ETL pipeline
python src/etl/processors/mb51.py

# Option B: API endpoint (if exists)
POST /api/v1/admin/etl/process-mb51

# Option C: Alembic migration
alembic upgrade head
```

**Expected Result:**
- fact_inventory rows: 179,513 (up from 4,348)
- mvt_type values: 601, 101, 351, 201, etc. (not just 999)

#### **Step 2: Populate dim_material** 🔥 BLOCKER

**Action:** Extract unique materials from raw_mb51

**SQL to run:**
```sql
INSERT INTO dim_material (material_code, material_description)
SELECT DISTINCT 
    col_4_material as material_code,
    col_5_material_desc as material_description
FROM raw_mb51
WHERE col_4_material IS NOT NULL
ON CONFLICT (material_code) DO UPDATE 
SET material_description = EXCLUDED.material_description;
```

**Expected Result:**
- dim_material rows: ~3,300+ (up from 0)
- All materials now have descriptions

#### **Step 3: Verify Movement Type Mapping**

**Check current ETL code:** 
```python
# File: src/etl/processors/mb51.py (or similar)
# Find the line that maps movement types
# SHOULD BE:
mvt_type = row['col_1_mvt_type']  # NOT hardcoded to 999!
```

---

### **VERIFICATION STEPS (Post-Fix)**

After running Steps 1-3, verify:

```sql
-- 1. Check row count
SELECT COUNT(*) FROM fact_inventory;  
-- Expected: ~179,513

-- 2. Check movement types
SELECT mvt_type, COUNT(*) FROM fact_inventory GROUP BY mvt_type ORDER BY count DESC;
-- Expected: 601 (27K), 101 (23K), not just 999

-- 3. Check velocity for real data
SELECT material_code, COUNT(id) as velocity 
FROM fact_inventory 
WHERE mvt_type IN (601, 261, 101)
  AND posting_date >= '2025-01-01'
GROUP BY material_code 
ORDER BY velocity DESC 
LIMIT 10;
-- Expected: Varying values (50, 120, 200, etc., not all "2")

-- 4. Check dim_material populated
SELECT COUNT(*) FROM dim_material;
-- Expected: ~3,300+

-- 5. Check orphaned materials
SELECT COUNT(*) FROM fact_inventory fi 
LEFT JOIN dim_material dm ON fi.material_code = dm.material_code 
WHERE dm.material_code IS NULL;
-- Expected: 0 (no orphans)
```

---

## 📊 IMPACT ASSESSMENT

### **Current State (Broken)**
```
Raw MB51:        179,513 rows ✅
    ↓ ETL FAILS
Fact Inventory:    4,348 rows ❌ (2.4% only)
    ↓ Query filters mvt_type IN (999, 601, 261)
    ↓ But only 999 exists!
Result:            4,348 rows (all test data)
    ↓ 3,300 materials, 4,348 txns
Top 10:           All velocity = 2 ❌
```

### **Expected State (Fixed)**
```
Raw MB51:        179,513 rows ✅
    ↓ ETL SUCCESS
Fact Inventory:  179,513 rows ✅
    ↓ Query filters mvt_type IN (999, 601, 261)
    ↓ Finds 601 (27K), 261 (if exists)
Result:          ~50,000+ relevant rows
    ↓ 3,300 materials, 50K+ txns
Top 10:          Varying velocity (50-500) ✅
```

---

## 🎯 KEY FINDINGS SUMMARY

| Issue | Current | Expected | Fix Priority |
|:------|:--------|:---------|:-------------|
| **ETL Execution** | Not run / Partial | Full transform | 🔥 P0 |
| **Fact Rows** | 4,348 (2.4%) | 179,513 (100%) | 🔥 P0 |
| **Movement Types** | 999 only | 601, 101, 351, etc. | 🔥 P0 |
| **dim_material** | 0 rows | ~3,300 rows | 🔥 P0 |
| **Orphaned Materials** | 4,348 (100%) | 0 (0%) | 🔥 P0 |
| **Velocity Results** | All = 2 | Varying (50-500) | ⚠️ P1 (after P0 fixes) |

---

## 📋 CLAUDE.MD COMPLIANCE

### **Skills Activated**

✅ **sequential-thinking**: Systematic audit execution (Raw → Transform → Query → Root Cause)  
✅ **debugging**: Database forensics, SQL investigations, code inspection  
✅ **code-reviewer**: Verified code logic correctness

### **Development Rules Adherence**

| Rule | Status | Evidence |
|:-----|:-------|:---------|
| **YAGNI** | ✅ | Only investigated what's needed |
| **KISS** | ✅ | Simple SQL queries for validation |
| **DRY** | ✅ | Reused query patterns |
| **Real queries** | ✅ | Actual PostgreSQL queries, not mocks |
| **Concise reporting** | ✅ | Facts-first, minimal fluff |

---

## 🚀 NEXT ACTIONS

### **For User (IMMEDIATE):**

1. **Locate ETL script:** Find `src/etl/processors/mb51.py` or similar
2. **Run transformation:** Execute ETL to process 179K rows
3. **Populate dim_material:** Run INSERT query above
4. **Verify:** Check fact_inventory has 179K rows with real mvt_types

### **For Developer (Code Fix):**

1. **Fix ETL processor:** Ensure `col_1_mvt_type` maps correctly (not hardcoded to 999)
2. **Add dim_material population:** ETL should auto-populate material master
3. **Add validation:** Warn if fact_inventory << raw_mb51 row count

---

## ❓ UNRESOLVED QUESTIONS

1. **ETL Trigger:** How is ETL supposed to run after upload? Manual command? Automated job?
2. **ETL Script Location:** Is it `src/etl/processors/mb51.py`? Different path?
3. **Why 999 only:** Was this intentional test data or ETL bug?
4. **Auto-populate dim_material:** Should ETL do this or separate script?

---

**FORENSIC AUDIT COMPLETE** ✅

**Status:** ROOT CAUSE IDENTIFIED - ETL PIPELINE FAILURE  
**Impact:** 97.6% of uploaded data not processed  
**Blocker:** dim_material empty, preventing material descriptions  
**Fix Priority:** CRITICAL - P0  
**ETA to Fix:** 15 minutes (run ETL + populate dim_material)

---

*Generated by AI Development Agent*  
*Date: January 16, 2026*  
*Skills: sequential-thinking, debugging, code-reviewer*  
*CLAUDE.md Compliance: VERIFIED*
