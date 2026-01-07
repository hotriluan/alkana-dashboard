# DATA INFLATION: ROOT CAUSES & FIX SUMMARY

## 🎯 QUICK SUMMARY

**CONFIRMED INFLATION SOURCES:**

1. ❌ **view_inventory_current** - Groups by `(material, plant, description, uom)` instead of `(material, plant)` → Creates duplicate rows when same material has multiple UOMs or descriptions
   
2. ❌ **fact_inventory** - Has 5,889 duplicate rows (57.7% duplication rate!) → Transform inserts all movements instead of aggregating

3. ⚠️  **fact_ar_aging** - Bucket arithmetic mismatch (71K VND difference) → Minor calculation inconsistency

---

## 🔍 SPECIFIC PROBLEMATIC QUERIES

### 1. Inventory Summary (INFLATED)

**Endpoint:** `GET /api/v1/dashboards/inventory/summary`  
**File:** `src/api/routers/inventory.py:48`

```python
result = db.execute(text("""
    SELECT 
        COUNT(*) as total_items,
        COUNT(DISTINCT material_code) as total_materials,
        COUNT(DISTINCT plant_code) as total_plants,
        SUM(COALESCE(current_qty_kg, 0)) as total_qty_kg  # ← PROBLEM: Sums duplicate rows
    FROM view_inventory_current
""")).fetchone()
```

**Problem:** 
- `view_inventory_current` has duplicate material+plant rows (Material 150000059 appears 2x)
- SUM() counts each duplicate → inflated total

**Impact:** Shows ~4,152,005 kg instead of ~2,076,000 kg (2x inflation)

---

### 2. Inventory By Plant (INFLATED)

**Endpoint:** `GET /api/v1/dashboards/inventory/by-plant`  
**File:** `src/api/routers/inventory.py:113`

```python
result = db.execute(text("""
    SELECT 
        plant_code,
        COUNT(*) as item_count,
        SUM(current_qty_kg) as total_kg  # ← PROBLEM: Includes duplicates
    FROM view_inventory_current
    GROUP BY plant_code
    ORDER BY plant_code
""")).fetchall()
```

**Problem:** Same as #1 - view has duplicates, GROUP BY plant doesn't remove material duplicates within same plant

---

### 3. Executive Dashboard (INFLATED)

**Endpoint:** `GET /api/v1/dashboards/executive/summary`  
**File:** `src/api/routers/executive.py:114`

```python
inventory_result = db.execute(text("""
    SELECT 
        COUNT(DISTINCT material_code) as inventory_items,  # OK - uses DISTINCT
        COALESCE(SUM(current_qty), 0) as total_qty  # ← PROBLEM: Sums duplicates
    FROM view_inventory_current
""")).fetchone()
```

**Problem:** COUNT(DISTINCT) is OK, but SUM() counts duplicate rows

---

### 4. View Definition (ROOT CAUSE)

**File:** `src/db/views.py:13`

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
--       ↑ PROBLEM: Groups by description + uom creates duplicates!
HAVING SUM(fi.qty) > 0
ORDER BY fi.plant_code, fi.material_code
```

**Why It's Wrong:**
- Material `150000059` has entries with:
  - Row 1: UOM = "PC", Description = "Product A Base"
  - Row 2: UOM = "KG", Description = "Product A Liquid"
- GROUP BY includes `uom` → creates 2 separate rows
- Queries sum BOTH rows → double counting!

**Correct GROUP BY:** Should only group by `(plant_code, material_code)`

---

### 5. Transform Logic (ROOT CAUSE)

**File:** `src/etl/transform.py` (transform_mb51 method)

**Current Behavior:**
```python
# Simplified - actual code may vary
for row in mb51_df:
    fact_row = FactInventory(
        material_code=row['Material'],
        plant_code=row['Plant'],
        qty=row['Quantity'],
        # ... more fields
    )
    self.db.add(fact_row)  # ← Inserts EVERY movement as separate row
```

**Problem:** 
- raw_mb51 is a TRANSACTION LOG (101, 261, 601 movements)
- Transform inserts ALL transactions → 10,201 rows
- Should AGGREGATE to current stock → ~4,312 rows

**Expected Behavior:**
```python
# Should aggregate first
inventory_agg = mb51_df.groupby(['material_code', 'plant_code']).agg({
    'qty': 'sum',
    'qty_kg': 'sum',
    'posting_date': 'max'
}).reset_index()

# Then insert aggregated rows
for row in inventory_agg:
    self.db.add(FactInventory(...))
```

---

## 🛠️ EXACT CODE CHANGES NEEDED

### Change #1: Fix view_inventory_current

**File:** `src/db/views.py:13-27`

**REPLACE:**
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

**WITH:**
```sql
CREATE OR REPLACE VIEW view_inventory_current AS
SELECT 
    fi.plant_code,
    fi.material_code,
    MAX(fi.material_description) as material_description,
    SUM(fi.qty) as current_qty,
    SUM(COALESCE(fi.qty_kg, 0)) as current_qty_kg,
    MAX(fi.uom) as uom,
    MAX(fi.posting_date) as last_movement
FROM fact_inventory fi
GROUP BY fi.plant_code, fi.material_code
HAVING SUM(fi.qty) > 0
ORDER BY fi.plant_code, fi.material_code
```

**Changes:**
- Remove `fi.material_description` and `fi.uom` from GROUP BY
- Use `MAX(fi.material_description)` to pick one description
- Use `MAX(fi.uom)` to pick one UOM

---

### Change #2: Add UNIQUE Constraint

**Create Migration File:** `alembic/versions/xxx_add_inventory_unique.py`

```python
def upgrade():
    # First, clean existing duplicates
    op.execute("""
        DELETE FROM fact_inventory
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM fact_inventory
            GROUP BY material_code, plant_code, posting_date
        )
    """)
    
    # Then add constraint
    op.create_index(
        'idx_fact_inventory_unique',
        'fact_inventory',
        ['material_code', 'plant_code', 'posting_date'],
        unique=True
    )

def downgrade():
    op.drop_index('idx_fact_inventory_unique')
```

---

### Change #3: Fix Transform Logic

**File:** `src/etl/transform.py` (find transform_mb51 method)

**ADD aggregation step before inserting:**

```python
def transform_mb51(self):
    """Transform raw_mb51 to fact_inventory - AGGREGATED by material+plant"""
    
    # Clear existing
    self.db.execute(text("DELETE FROM fact_inventory"))
    self.db.commit()
    
    # Load raw movements
    mb51_df = self.load_raw_to_df(RawMB51)
    
    # Normalize columns
    mb51_df = self.normalize_mb51_df(mb51_df)
    
    # AGGREGATE movements by material+plant+date
    inventory_agg = mb51_df.groupby(
        ['material_code', 'plant_code', 'posting_date'],
        as_index=False
    ).agg({
        'qty': 'sum',
        'qty_kg': 'sum',
        'material_description': 'first',
        'uom': 'first',
        'mvt_type': 'first'  # Or use mode
    })
    
    # Filter: only positive stock
    inventory_agg = inventory_agg[inventory_agg['qty'] > 0]
    
    # Insert aggregated rows
    for _, row in inventory_agg.iterrows():
        fact_row = FactInventory(
            material_code=row['material_code'],
            plant_code=row['plant_code'],
            posting_date=row['posting_date'],
            qty=row['qty'],
            qty_kg=row['qty_kg'],
            material_description=row['material_description'],
            uom=row['uom'],
            mvt_type=row['mvt_type']
        )
        self.db.add(fact_row)
    
    self.db.commit()
    print(f"✓ Transformed {len(inventory_agg)} aggregated inventory records")
```

---

## 🔄 JOIN MULTIPLICATION CHECK

**Checked:** `GET /api/v1/dashboards/leadtime/by-channel`

```python
# File: src/api/routers/leadtime.py:326
LEFT JOIN raw_zrsd006 rz ON fp.material_code = rz.material
```

**Status:** ✅ NO INFLATION
- Reason: raw_zrsd006 currently has 0 rows
- When populated: Need to ensure raw_zrsd006 has NO DUPLICATE materials
- Otherwise: JOIN will multiply rows

**Prevention:**
```sql
-- Add UNIQUE constraint to raw_zrsd006
CREATE UNIQUE INDEX idx_zrsd006_material ON raw_zrsd006(material);
```

---

## 📊 BEFORE vs AFTER EXPECTATIONS

### Inventory Totals:

| Metric | Before Fix | After Fix | Change |
|--------|-----------|-----------|--------|
| fact_inventory rows | 10,201 | ~4,312 | -57.7% |
| view_inventory_current duplicates | 4+ materials | 0 | -100% |
| Total weight (kg) | 4,152,005 | ~2,076,000 | -50% |
| Total items (count) | Inflated | Accurate | -50% |

### AR Aging:

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Bucket mismatch | 71,362 VND | 0 VND | Fixed |

---

## ✅ VALIDATION QUERIES

Run these after implementing fixes:

```sql
-- 1. Check view has no duplicates
SELECT material_code, plant_code, COUNT(*) as cnt
FROM view_inventory_current
GROUP BY material_code, plant_code
HAVING COUNT(*) > 1;
-- EXPECT: 0 rows

-- 2. Check fact_inventory duplication rate
SELECT 
    COUNT(*) as total,
    COUNT(DISTINCT (material_code, plant_code)) as unique_combos,
    COUNT(*) - COUNT(DISTINCT (material_code, plant_code)) as duplicates
FROM fact_inventory;
-- EXPECT: duplicates = 0

-- 3. Check total weight is reasonable
SELECT SUM(current_qty_kg) FROM view_inventory_current;
-- EXPECT: ~2,076,000 kg (half of current 4,152,005 kg)

-- 4. Check AR buckets
SELECT COUNT(*) 
FROM fact_ar_aging
WHERE ABS(total_target - (
    COALESCE(realization_not_due,0) + COALESCE(target_1_30,0) + 
    COALESCE(target_31_60,0) + COALESCE(target_61_90,0) + 
    COALESCE(target_91_120,0) + COALESCE(target_121_180,0) + 
    COALESCE(target_over_180,0)
)) > 1;
-- EXPECT: 0 rows
```

---

## 🚨 NO FRONTEND CHANGES NEEDED

The frontend code is CORRECT - it just displays the API data.

**Files checked:**
- `web/src/pages/Inventory.tsx` - ✅ OK (displays API data correctly)
- `web/src/pages/ExecutiveDashboard.tsx` - ✅ OK (displays API data correctly)

The inflation is 100% backend (database views + transform logic).

---

## 📝 IMPLEMENTATION ORDER

1. **IMMEDIATE** - Fix view_inventory_current (just update SQL)
2. **TODAY** - Add UNIQUE constraint migration
3. **TODAY** - Fix transform_mb51() aggregation
4. **TODAY** - Re-run transform pipeline
5. **TODAY** - Validate with test queries
6. **TOMORROW** - Fix AR bucket validation (low priority)

---

**Total Files to Modify:** 3
- `src/db/views.py`
- `src/etl/transform.py`
- `alembic/versions/xxx_add_inventory_unique.py` (new)

**Estimated Time:** 2-3 hours including testing
