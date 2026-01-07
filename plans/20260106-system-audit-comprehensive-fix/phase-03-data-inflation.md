# Phase 3: Fix Data Inflation Issues

**Priority:** 🔴 CRITICAL  
**Effort:** 6 hours  
**Risk:** HIGH - Database schema changes required  
**Dependencies:** Database backup completed

---

## 🎯 OBJECTIVE

Fix inventory data inflation where totals show ~2x actual values due to duplicate rows and improper aggregation.

---

## 📊 CURRENT STATE

### Issue #1: fact_inventory Has 5,889 Duplicate Rows (57.7%)

```
Total rows: 10,201
Unique (material_code + plant_code): 4,312
Duplicate rows: 5,889 (57.7% of table!)
```

**Example:**
```
Material 150000059, Plant 1201: 4 rows (should be 1)
Material 150001766, Plant 1201: 3 rows (should be 1)
```

### Issue #2: view_inventory_current Creates Duplicates

**Current GROUP BY:**
```sql
GROUP BY fi.plant_code, fi.material_code, fi.material_description, fi.uom
```

**Problem:** Same material with different UOMs or descriptions creates multiple rows:
```
Material 150000059, Plant 1201, UOM=PC  → 1 row
Material 150000059, Plant 1201, UOM=KG  → 1 row (DUPLICATE!)
```

### Issue #3: Transform Doesn't Aggregate

`transform_mb51()` inserts each raw transaction as separate row instead of aggregating to current stock.

**Result:** 
- Inventory weight: 4,152,005 kg
- **Should be:** ~2,076,000 kg (50% lower)

---

## 🛠️ IMPLEMENTATION

### Task 3.1: Clean Existing Duplicates

**File:** `plans/20260106-system-audit-comprehensive-fix/scripts/clean_inventory_duplicates.py`

**Create Script:**
```python
"""
Clean existing inventory duplicates before adding constraints
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

print("Cleaning fact_inventory duplicates...")

with engine.connect() as conn:
    # Check before
    before = conn.execute(text("SELECT COUNT(*) FROM fact_inventory")).scalar()
    print(f"Before: {before:,} rows")
    
    # Get duplicates
    result = conn.execute(text("""
        SELECT material_code, plant_code, COUNT(*) as cnt
        FROM fact_inventory
        GROUP BY material_code, plant_code
        HAVING COUNT(*) > 1
    """))
    duplicates = result.fetchall()
    print(f"Found {len(duplicates)} duplicate combinations")
    
    # Delete duplicates keeping MIN(id)
    for material_code, plant_code, count in duplicates:
        conn.execute(text("""
            DELETE FROM fact_inventory
            WHERE material_code = :mat
            AND plant_code = :plant
            AND id NOT IN (
                SELECT MIN(id)
                FROM fact_inventory
                WHERE material_code = :mat
                AND plant_code = :plant
            )
        """), {'mat': material_code, 'plant': plant_code})
    
    # Check after
    after = conn.execute(text("SELECT COUNT(*) FROM fact_inventory")).scalar()
    print(f"After: {after:,} rows")
    print(f"Removed: {before - after:,} duplicates")
    
    # Verify
    result = conn.execute(text("""
        SELECT COUNT(*) - COUNT(DISTINCT (material_code, plant_code))
        FROM fact_inventory
    """))
    remaining = result.scalar()
    
    if remaining == 0:
        print("✅ All duplicates removed!")
    else:
        print(f"⚠️ Still {remaining} duplicates remaining")
```

**Run:**
```bash
python plans/20260106-system-audit-comprehensive-fix/scripts/clean_inventory_duplicates.py
```

**Expected Output:**
```
Before: 10,201 rows
Found 1,889 duplicate combinations
After: 4,312 rows
Removed: 5,889 duplicates
✅ All duplicates removed!
```

---

### Task 3.2: Update view_inventory_current

**File:** `src/db/views.py` or migration script

**Current View Definition:**
```sql
CREATE OR REPLACE VIEW view_inventory_current AS
SELECT 
    fi.plant_code,
    fi.material_code,
    fi.material_description,
    fi.uom,
    SUM(fi.qty) as total_qty,
    SUM(fi.qty_kg) as total_qty_kg
FROM fact_inventory fi
GROUP BY fi.plant_code, fi.material_code, fi.material_description, fi.uom;
```

**Updated View (Fix):**
```sql
CREATE OR REPLACE VIEW view_inventory_current AS
SELECT 
    fi.plant_code,
    fi.material_code,
    MAX(fi.material_description) as material_description,  -- Use MAX to pick one
    MAX(fi.uom) as uom,                                    -- Use MAX to pick one
    SUM(fi.qty) as total_qty,
    SUM(fi.qty_kg) as total_qty_kg
FROM fact_inventory fi
GROUP BY fi.plant_code, fi.material_code;  -- Only group by unique keys
```

**Migration Script:**
```python
# migrations/fix_inventory_view.py
from alembic import op

def upgrade():
    op.execute("""
        CREATE OR REPLACE VIEW view_inventory_current AS
        SELECT 
            fi.plant_code,
            fi.material_code,
            MAX(fi.material_description) as material_description,
            MAX(fi.uom) as uom,
            SUM(fi.qty) as total_qty,
            SUM(fi.qty_kg) as total_qty_kg
        FROM fact_inventory fi
        GROUP BY fi.plant_code, fi.material_code
    """)

def downgrade():
    op.execute("""
        CREATE OR REPLACE VIEW view_inventory_current AS
        SELECT 
            fi.plant_code,
            fi.material_code,
            fi.material_description,
            fi.uom,
            SUM(fi.qty) as total_qty,
            SUM(fi.qty_kg) as total_qty_kg
        FROM fact_inventory fi
        GROUP BY fi.plant_code, fi.material_code, fi.material_description, fi.uom
    """)
```

**Run:**
```bash
alembic upgrade head
```

---

### Task 3.3: Add UNIQUE Constraint

**File:** `migrations/add_inventory_unique_constraint.py`

**Create Migration:**
```python
"""Add UNIQUE constraint to fact_inventory

Revision ID: add_inventory_unique
"""
from alembic import op

def upgrade():
    # Add UNIQUE constraint
    op.execute("""
        CREATE UNIQUE INDEX idx_fact_inventory_unique
        ON fact_inventory (material_code, plant_code, posting_date)
    """)

def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_fact_inventory_unique")
```

**Why posting_date?**
- Inventory is time-series data
- Same material+plant can have different quantities on different dates
- UNIQUE on (material, plant, date) prevents duplicate snapshots

**Alternative (if current stock only):**
```sql
CREATE UNIQUE INDEX idx_fact_inventory_unique
ON fact_inventory (material_code, plant_code)
WHERE posting_date = (SELECT MAX(posting_date) FROM fact_inventory)
```

---

### Task 3.4: Fix Transform Aggregation

**File:** `src/etl/transform.py`

**Current Code (Problem):**
```python
def transform_mb51(self):
    """Transform raw MB51 to fact_inventory"""
    raw_data = self.session.query(RawMb51).all()
    
    for row in raw_data:
        data = row.raw_data
        
        # Insert each transaction as separate row ❌
        inventory = FactInventory(
            material_code=data.get('Material'),
            plant_code=data.get('Plant'),
            qty=float(data.get('Quantity', 0)),
            qty_kg=float(data.get('Qty in kg', 0)),
            posting_date=data.get('Posting Date')
        )
        self.session.add(inventory)
    
    self.session.commit()
```

**Fixed Code (Aggregate):**
```python
def transform_mb51(self):
    """Transform raw MB51 to fact_inventory with aggregation"""
    
    # TRUNCATE first to prevent accumulation
    self.session.execute(text("TRUNCATE TABLE fact_inventory"))
    self.session.commit()
    
    # Get all raw data
    raw_data = self.session.query(RawMb51).all()
    
    # Convert to DataFrame for aggregation
    import pandas as pd
    
    data_list = []
    for row in raw_data:
        data = row.raw_data
        data_list.append({
            'material_code': data.get('Material'),
            'plant_code': data.get('Plant'),
            'batch': data.get('Batch'),
            'qty': float(data.get('Quantity', 0) or 0),
            'qty_kg': float(data.get('Qty in kg', 0) or 0),
            'posting_date': data.get('Posting Date'),
            'material_description': data.get('Material Description'),
            'uom': data.get('Unit of Entry')
        })
    
    df = pd.DataFrame(data_list)
    
    # Aggregate by material + plant + date
    agg_df = df.groupby(['material_code', 'plant_code', 'posting_date']).agg({
        'qty': 'sum',
        'qty_kg': 'sum',
        'material_description': 'first',  # Take first occurrence
        'uom': 'first',
        'batch': 'first'
    }).reset_index()
    
    # Insert aggregated data
    for _, row in agg_df.iterrows():
        inventory = FactInventory(
            material_code=row['material_code'],
            plant_code=row['plant_code'],
            qty=row['qty'],
            qty_kg=row['qty_kg'],
            posting_date=row['posting_date'],
            material_description=row['material_description'],
            uom=row['uom'],
            batch=row['batch']
        )
        self.session.add(inventory)
    
    self.session.commit()
    
    # Log results
    total_raw = len(data_list)
    total_agg = len(agg_df)
    logger.info(f"Aggregated {total_raw} raw movements → {total_agg} inventory records")
```

**Key Changes:**
1. `TRUNCATE` before insert (prevent accumulation)
2. Convert to DataFrame for easy aggregation
3. `groupby()` material + plant + date
4. `sum()` quantities, `first()` for text fields
5. Insert aggregated data only

---

## ⚠️ RISKS & MITIGATION

### Risk #1: Data Loss
**Impact:** Aggregation might lose detail (batch-level tracking)

**Mitigation:**
- Keep raw_mb51 intact (source of truth)
- fact_inventory is summary only
- Can rebuild from raw if needed

### Risk #2: Breaking Change
**Impact:** Apps expecting detailed transactions break

**Mitigation:**
- Check if any apps query fact_inventory for transaction detail
- If yes, create separate fact_inventory_transactions table
- Keep aggregated view for reporting

### Risk #3: Performance
**Impact:** Aggregation in Python might be slow

**Mitigation:**
- Use pandas (fast for aggregation)
- Consider SQL-based aggregation:
  ```sql
  INSERT INTO fact_inventory
  SELECT 
      material_code,
      plant_code,
      posting_date,
      SUM(qty),
      SUM(qty_kg),
      MAX(material_description),
      MAX(uom)
  FROM (SELECT raw_data->>'Material' as material_code, ...FROM raw_mb51)
  GROUP BY material_code, plant_code, posting_date
  ```

---

## 🧪 TESTING CHECKLIST

- [ ] Duplicates removed (10,201 → ~4,312 rows)
- [ ] UNIQUE constraint prevents re-insertion of duplicates
- [ ] view_inventory_current shows 1 row per material+plant
- [ ] Total inventory weight drops ~50% (4.15M → 2.08M kg)
- [ ] Transform completes successfully with aggregation
- [ ] No data loss (can verify totals match raw_mb51)
- [ ] Inventory dashboards show correct values

**Validation Queries:**
```sql
-- Check duplicates
SELECT COUNT(*) - COUNT(DISTINCT (material_code, plant_code, posting_date))
FROM fact_inventory;
-- Should be 0

-- Check view duplicates
SELECT COUNT(*) - COUNT(DISTINCT (material_code, plant_code))
FROM view_inventory_current;
-- Should be 0

-- Compare totals
SELECT SUM(qty_kg) FROM fact_inventory;
SELECT SUM(CAST(raw_data->>'Qty in kg' AS FLOAT)) FROM raw_mb51;
-- Should match
```

---

## 📊 SUCCESS CRITERIA

- [ ] fact_inventory: 0 duplicates ✅
- [ ] view_inventory_current: 0 duplicates ✅
- [ ] Total weight: ~2M kg (50% reduction) ✅
- [ ] UNIQUE constraint active ✅
- [ ] Transform uses aggregation ✅
- [ ] No duplicate accumulation on re-run ✅

---

## 🚀 DEPLOYMENT SEQUENCE

1. **Backup database** ⚠️ CRITICAL
2. Run `clean_inventory_duplicates.py`
3. Apply view migration
4. Apply UNIQUE constraint migration
5. Update transform.py code
6. Run transform to rebuild fact_inventory
7. Verify totals match
8. Test dashboards

**Rollback:**
```bash
alembic downgrade -1  # Undo constraint
# Restore from backup if needed
```

---

**Phase 3 Complete When:**
✅ All data inflation issues resolved  
✅ Inventory shows correct values (~50% lower)  
✅ No duplicates possible (UNIQUE constraint)  
✅ Transform aggregates properly
