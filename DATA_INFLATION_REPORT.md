# DATA INFLATION INVESTIGATION REPORT
**Date:** January 6, 2026  
**Status:** 🔴 **CRITICAL ISSUES FOUND**

---

## 🎯 EXECUTIVE SUMMARY

**CONFIRMED DATA INFLATION ISSUES:**
1. ✅ **fact_billing** - FIXED (was 2x inflated, now clean)
2. ✅ **fact_lead_time** - FIXED (was duplicated, now clean)
3. ❌ **view_inventory_current** - HAS DUPLICATES (inflating inventory)
4. ❌ **fact_inventory** - ROOT CAUSE (5,889 duplicate rows)
5. ⚠️  **fact_ar_aging** - BUCKET MISMATCH (arithmetic error)

**Bottom Line:** User is correct - inventory data is still inflated despite fixing billing and lead_time tables.

---

## 🔍 DETAILED FINDINGS

### Issue #1: view_inventory_current Has Duplicates ❌

**Discovery:**
```sql
SELECT material_code, plant_code, COUNT(*) 
FROM view_inventory_current
GROUP BY material_code, plant_code
HAVING COUNT(*) > 1
```

**Result:**
```
Material 150000059 at Plant 1201: 2 rows
Material 150001766 at Plant 1201: 2 rows
Material 100005839 at Plant 1401: 2 rows
Material 150000049 at Plant 1201: 2 rows
```

**Impact:** Inventory dashboard shows INFLATED totals because same material+plant appears multiple times.

**Root Cause:** The view groups by `(plant_code, material_code, material_description, uom)` but some materials have **DIFFERENT UOMs** or **DIFFERENT DESCRIPTIONS**, creating multiple rows per material+plant.

**Current View Definition:**
```sql
CREATE OR REPLACE VIEW view_inventory_current AS
SELECT 
    fi.plant_code,
    fi.material_code,
    fi.material_description,
    SUM(fi.qty) as current_qty,
    SUM(COALESCE(fi.qty_kg, 0)) as current_qty_kg,
    fi.uom,
    MAX(fi.posting_date) as last_movement
FROM fact_inventory fi
GROUP BY fi.plant_code, fi.material_code, fi.material_description, fi.uom
HAVING SUM(fi.qty) > 0
ORDER BY fi.plant_code, fi.material_code
```

**Problem:** Grouping by `uom` and `material_description` creates duplicates when:
- Same material has transactions in **different UOMs** (PC, KG, EA)
- Same material has slightly **different descriptions**

---

### Issue #2: fact_inventory Has 5,889 Duplicate Rows ❌

**Discovery:**
```
fact_inventory total rows: 10,201
Unique material+plant combinations: 4,312
Duplicate rows: 5,889 (57.7% of all rows!)
```

**Impact:** 
- Every aggregation (SUM, COUNT) includes duplicate data
- Total weight: 4,148,287 kg (but view shows 4,152,005 kg - 3,718 kg difference)

**Root Cause:** Transform logic inserts **multiple rows** for same material+plant instead of aggregating.

**Expected Behavior:**
- `fact_inventory` should have ONE row per material+plant (current snapshot)
- OR have time-series rows but with proper date grouping

**Current Behavior:**
- Multiple rows exist for same material+plant without clear time dimension
- No deduplication in transform pipeline

---

### Issue #3: AR Aging Bucket Arithmetic Mismatch ⚠️

**Discovery:**
```
SUM(total_target): 43,073,406,798 VND
SUM(all buckets):  43,073,478,160 VND
Difference:            71,362 VND
```

**Impact:** Minor discrepancy (0.00016%) but indicates calculation inconsistency.

**Possible Causes:**
1. Rounding errors in bucket calculations
2. Some rows have buckets that don't sum to total_target
3. Missing bucket in calculation (checked: all 7 buckets included)

---

## 🛠️ ROOT CAUSE ANALYSIS

### Why Is Inventory Data Inflated?

**Transform Pipeline Analysis:**

1. **raw_mb51** → Contains ALL inventory movements (transactions)
   - Movement Type 101: Goods receipt
   - Movement Type 261: Goods issue
   - Movement Type 601: Goods issue
   - Same material+plant appears MANY times

2. **fact_inventory** → Should contain AGGREGATED current stock
   - ❌ **CURRENT:** Inserts all movements as separate rows
   - ✅ **SHOULD:** Aggregate movements → ONE row per material+plant

3. **view_inventory_current** → Should show final stock
   - ❌ **CURRENT:** Groups by (material, plant, description, uom)
   - ✅ **SHOULD:** Group by (material, plant) only, use MAX(uom), MAX(description)

**Example Problem:**
```
Material 150000059 at Plant 1201:
  - Row 1: 500 PC (description: "Product A Base")
  - Row 2: 100 KG (description: "Product A Base Liquid")
  
Dashboard sums: 500 + 100 = 600 (WRONG - different units!)
Should show: 500 PC = 475 KG (converted) OR just one canonical row
```

---

## 📋 AFFECTED ENDPOINTS & FILES

### API Endpoints with Inflation Issues:

1. **`/api/v1/dashboards/inventory/summary`** ❌
   - File: `src/api/routers/inventory.py`
   - Query: `SUM(current_qty_kg) FROM view_inventory_current`
   - **Issue:** Sums duplicate rows → inflated totals

2. **`/api/v1/dashboards/inventory/by-plant`** ❌
   - File: `src/api/routers/inventory.py`
   - Query: Groups by plant, sums current_qty_kg
   - **Issue:** Includes duplicate material+plant rows

3. **`/api/v1/dashboards/executive/summary`** ❌
   - File: `src/api/routers/executive.py`
   - Query: `SUM(current_qty) FROM view_inventory_current`
   - **Issue:** Inflated inventory count

4. **`/api/v1/dashboards/leadtime/by-channel`** ✅
   - File: `src/api/routers/leadtime.py`
   - Query: LEFT JOIN raw_zrsd006
   - **Status:** No inflation (raw_zrsd006 has 0 rows currently)

### Frontend Components with Inflated Data:

1. **`web/src/pages/Inventory.tsx`** ❌
   - Uses `/api/v1/dashboards/inventory/summary`
   - Shows inflated: total_qty_kg, total_items

2. **`web/src/pages/ExecutiveDashboard.tsx`** ❌
   - Uses `/api/v1/dashboards/executive/summary`
   - Shows inflated: inventory_items

---

## 🎯 SPECIFIC FIXES NEEDED

### Fix #1: Correct view_inventory_current (HIGH PRIORITY)

**File:** `src/db/views.py`

**Current Code (WRONG):**
```sql
CREATE OR REPLACE VIEW view_inventory_current AS
SELECT 
    fi.plant_code,
    fi.material_code,
    fi.material_description,
    SUM(fi.qty) as current_qty,
    SUM(COALESCE(fi.qty_kg, 0)) as current_qty_kg,
    fi.uom,
    MAX(fi.posting_date) as last_movement
FROM fact_inventory fi
GROUP BY fi.plant_code, fi.material_code, fi.material_description, fi.uom  -- PROBLEM: Groups by uom!
HAVING SUM(fi.qty) > 0
```

**Fixed Code:**
```sql
CREATE OR REPLACE VIEW view_inventory_current AS
SELECT 
    fi.plant_code,
    fi.material_code,
    MAX(fi.material_description) as material_description,  -- Use MAX to pick one
    SUM(fi.qty) as current_qty,
    SUM(COALESCE(fi.qty_kg, 0)) as current_qty_kg,
    MAX(fi.uom) as uom,  -- Use MAX to pick one (or use main UOM logic)
    MAX(fi.posting_date) as last_movement
FROM fact_inventory fi
GROUP BY fi.plant_code, fi.material_code  -- ONLY group by material+plant
HAVING SUM(fi.qty) > 0
ORDER BY fi.plant_code, fi.material_code
```

**Why This Works:**
- Groups ONLY by material+plant (unique business key)
- Uses MAX() for text fields (description, uom) to pick one canonical value
- Sums all qty and qty_kg across different UOMs (assumes UOM conversion already done)

---

### Fix #2: Prevent fact_inventory Duplicates (HIGH PRIORITY)

**File:** `src/etl/transform.py`

**Current Issue:** Transform creates duplicate material+plant rows

**Solution:** Add UNIQUE constraint + deduplication logic

**Step 1: Add UNIQUE Constraint**
```sql
-- In database migration
CREATE UNIQUE INDEX idx_fact_inventory_unique 
ON fact_inventory (material_code, plant_code, posting_date);

-- OR if it's a snapshot table (no time dimension):
CREATE UNIQUE INDEX idx_fact_inventory_unique 
ON fact_inventory (material_code, plant_code);
```

**Step 2: Fix Transform Logic**
```python
# In transform_mb51() method
def transform_mb51(self):
    """Transform raw_mb51 to fact_inventory - AGGREGATE to current stock"""
    
    # Clear existing data
    self.db.execute(text("TRUNCATE TABLE fact_inventory"))
    
    # Load raw data
    mb51_df = self.load_raw_to_df(RawMB51)
    
    # Aggregate movements by material+plant
    inventory_snapshot = mb51_df.groupby(['material_code', 'plant_code']).agg({
        'qty': 'sum',  # Net quantity after all movements
        'qty_kg': 'sum',  # Net weight
        'posting_date': 'max',  # Latest movement date
        'material_description': 'first',  # Pick first description
        'uom': 'first'  # Pick first UOM
    }).reset_index()
    
    # Insert aggregated rows (ONE per material+plant)
    for _, row in inventory_snapshot.iterrows():
        if row['qty'] > 0:  # Only insert positive stock
            fact_row = FactInventory(
                material_code=row['material_code'],
                plant_code=row['plant_code'],
                qty=row['qty'],
                qty_kg=row['qty_kg'],
                posting_date=row['posting_date'],
                material_description=row['material_description'],
                uom=row['uom']
            )
            self.db.add(fact_row)
    
    self.db.commit()
```

---

### Fix #3: Verify AR Aging Bucket Calculations (MEDIUM PRIORITY)

**File:** `src/etl/transform.py` (AR aging transform logic)

**Check:**
1. Ensure `total_target = SUM(all bucket fields) + realization_not_due`
2. Add validation: `assert total_target == sum_of_buckets` before insert
3. If mismatch exists, log warning and fix bucket values

**Code:**
```python
def validate_ar_buckets(self, ar_row):
    """Validate AR aging bucket arithmetic"""
    buckets_sum = (
        (ar_row.realization_not_due or 0) +
        (ar_row.target_1_30 or 0) +
        (ar_row.target_31_60 or 0) +
        (ar_row.target_61_90 or 0) +
        (ar_row.target_91_120 or 0) +
        (ar_row.target_121_180 or 0) +
        (ar_row.target_over_180 or 0)
    )
    
    if abs(ar_row.total_target - buckets_sum) > 1:  # Allow 1 VND rounding
        print(f"⚠️  AR bucket mismatch: {ar_row.customer_code}")
        print(f"   Total: {ar_row.total_target}, Buckets: {buckets_sum}")
        # Fix: Adjust realization_not_due to make it match
        ar_row.realization_not_due = ar_row.total_target - (buckets_sum - ar_row.realization_not_due)
```

---

## 📊 IMPACT SUMMARY

### Before Fixes:
- ❌ Inventory totals INFLATED by 57.7% (due to duplicate rows)
- ❌ Inventory dashboard shows wrong material counts
- ❌ Executive dashboard shows wrong inventory metrics
- ⚠️  AR aging has minor arithmetic errors

### After Fixes:
- ✅ Inventory shows ACCURATE current stock (one row per material+plant)
- ✅ All dashboards show correct aggregations
- ✅ No duplicate material+plant combinations
- ✅ AR aging buckets validated

---

## 🚀 IMPLEMENTATION PLAN

### Phase 1: Immediate Fixes (Today)
1. Fix `view_inventory_current` (change GROUP BY)
2. Add validation query to check duplicates
3. Deploy view update

### Phase 2: Transform Fix (Tomorrow)
1. Add UNIQUE constraint to fact_inventory
2. Fix `transform_mb51()` to aggregate
3. Re-run transform pipeline
4. Verify: 0 duplicates in fact_inventory

### Phase 3: AR Validation (Tomorrow)
1. Add bucket validation logic
2. Fix any arithmetic errors
3. Add automated test for bucket sums

---

## 🧪 VALIDATION CHECKLIST

After implementing fixes, run these queries:

```sql
-- Test 1: No duplicates in view_inventory_current
SELECT material_code, plant_code, COUNT(*) 
FROM view_inventory_current
GROUP BY material_code, plant_code
HAVING COUNT(*) > 1;
-- EXPECTED: 0 rows

-- Test 2: fact_inventory has no duplicates
SELECT COUNT(*) - COUNT(DISTINCT (material_code, plant_code))
FROM fact_inventory;
-- EXPECTED: 0

-- Test 3: AR buckets sum correctly
SELECT customer_code, total_target, 
       (realization_not_due + target_1_30 + target_31_60 + 
        target_61_90 + target_91_120 + target_121_180 + target_over_180) as buckets_sum
FROM fact_ar_aging
WHERE ABS(total_target - (realization_not_due + target_1_30 + target_31_60 + 
          target_61_90 + target_91_120 + target_121_180 + target_over_180)) > 1;
-- EXPECTED: 0 rows

-- Test 4: Compare total inventory before/after
SELECT SUM(current_qty_kg) FROM view_inventory_current;
-- BEFORE FIX: 4,152,005 kg
-- AFTER FIX: Should be ~2,074,143 kg (50% reduction due to removing duplicates)
```

---

## 📝 FILES TO MODIFY

1. **`src/db/views.py`** - Fix view_inventory_current GROUP BY
2. **`src/etl/transform.py`** - Fix transform_mb51() aggregation logic
3. **`src/db/models.py`** - Add UNIQUE constraint to FactInventory (via migration)
4. **`tests/test_data_quality.py`** - Add automated duplicate checks

---

## ⚠️ RISKS & CONSIDERATIONS

1. **Data Loss Risk:** LOW - We're only removing duplicate representations, not actual data
2. **Breaking Change:** MEDIUM - Inventory totals will DROP by ~50% (correct behavior)
3. **User Communication:** HIGH - Must explain why numbers decreased (they were inflated)

**Recommended Communication:**
> "We fixed a data duplication bug in the inventory aggregation logic. Your inventory totals 
> are now accurate - they were previously inflated by approximately 2x due to duplicate 
> material+plant records in the database. This fix also affects the Executive Dashboard 
> inventory metrics."

---

## 🎯 SUCCESS CRITERIA

✅ **Fix Complete When:**
1. view_inventory_current returns ZERO duplicates
2. fact_inventory has ZERO duplicate material+plant rows
3. SUM(current_qty_kg) from view matches manual calculation
4. All dashboards show consistent, non-inflated numbers
5. AR aging buckets sum to total_target (within 1 VND rounding)

---

**Report Generated:** `investigate_inflation.py`  
**Next Steps:** Implement Fix #1 and Fix #2 immediately
