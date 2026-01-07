# Phase 4: Fix ZRSD004 Header Detection

**Priority:** 🔴 CRITICAL  
**Effort:** 2 hours  
**Risk:** LOW - Proven fix already exists  
**Dependencies:** None

---

## 🎯 OBJECTIVE

Fix Zrsd004Loader to read actual column names instead of 'Unnamed: 0', 'Unnamed: 1', etc., preventing NULL data in all 24,856 rows.

---

## 📊 CURRENT STATE

### Issue: Complete Data Loss

**Upload Output:**
```
Loading C:\dev\alkana-dashboard\demodata\zrsd004.XLSX...
Found 24856 rows, 34 columns
Columns: ['Unnamed: 0', 'Unnamed: 1', 'Unnamed: 2', ..., 'Unnamed: 33']
```

**Result:**
```python
row.get('Delivery')  # Returns None ❌
row.get('Actual GI Date')  # Returns None ❌
```

**All 24,856 rows have NULL in every column!**

### Root Cause

Excel file has **merged cells or special formatting** in Row 1 (headers). Pandas cannot parse them, returns generic names.

**Current Code:**
```python
# src/etl/loaders.py, line 542
df = pd.read_excel(file_path, header=0, dtype=str)  # ❌ Fails on formatted headers
```

**Same Issue in Mb51Loader** → Fixed successfully:
```python
df = pd.read_excel(file_path, header=None, skiprows=1, dtype=str)  # ✅ Skip problematic row
df.columns = ['Material Document', 'Material Doc.Item', ...]  # ✅ Assign manually
```

---

## 🛠️ IMPLEMENTATION

### Task 4.1: Update Zrsd004Loader.read_excel()

**File:** `src/etl/loaders.py`

**Location:** Line 542 (in `Zrsd004Loader` class)

**Find:**
```python
def read_excel(self):
    """Read and parse ZRSD004 Excel file"""
    file_path = self.get_latest_file('zrsd004')
    if not file_path:
        raise FileNotFoundError("No ZRSD004 file found")
    
    df = pd.read_excel(file_path, header=0, dtype=str)  # ❌ PROBLEM LINE
    return df
```

**Replace With:**
```python
def read_excel(self):
    """Read and parse ZRSD004 Excel file"""
    file_path = self.get_latest_file('zrsd004')
    if not file_path:
        raise FileNotFoundError("No ZRSD004 file found")
    
    # Skip formatted header row, assign column names manually
    df = pd.read_excel(file_path, header=None, skiprows=1, dtype=str)
    
    # Assign all 34 column names from actual Excel structure
    df.columns = [
        'Delivery Date',        # 0
        'Actual GI Date',       # 1
        'Delivery',             # 2
        'SO Reference',         # 3
        'Req. Type',            # 4
        'Delivery Type',        # 5
        'Shipping Point',       # 6
        'Sloc',                 # 7
        'Sales Office',         # 8
        'Dist. Channel',        # 9
        'Cust. Group',          # 10
        'Sold-to Party',        # 11
        'Ship-to Party',        # 12
        'Name of Ship-to',      # 13
        'City of Ship-to',      # 14
        'Regional Stru. Grp.',  # 15
        'Transportation Zone',  # 16
        'Salesman ID',          # 17
        'Salesman Name',        # 18
        'Material',             # 19
        'Description',          # 20
        'Delivery Qty',         # 21
        'Tonase',               # 22
        'Tonase Unit',          # 23
        'Actual Delivery Qty',  # 24
        'Sales Unit',           # 25
        'Net Weight',           # 26
        'Weight Unit',          # 27
        'Volume',               # 28
        'Volume Unit',          # 29
        'Created By',           # 30
        'Product Hierarchy',    # 31
        'Line Item',            # 32
        'Total Movement Goods Stat'  # 33
    ][:len(df.columns)]  # Handle if Excel has fewer columns
    
    return df
```

---

### Task 4.2: Update Column Name Mappings

**File:** `src/etl/loaders.py`

**Location:** Lines 554-575 (in `Zrsd004Loader.load()` method)

**Current Mappings (Incorrect):**
```python
fact_delivery = FactDelivery(
    delivery_date=safe_date(row.get('Delivery Date')),  # ✅ OK
    actual_gi_date=safe_date(row.get('Actual GI Date')),  # ✅ OK
    delivery=safe_str(row.get('Delivery')),  # ✅ OK
    
    # BROKEN MAPPINGS:
    dist_channel=safe_str(row.get('Distribution Channel')),  # ❌ Should be 'Dist. Channel'
    ship_to_name=safe_str(row.get('Ship-to Name')),  # ❌ Should be 'Name of Ship-to'
    ship_to_city=safe_str(row.get('Ship-to City')),  # ❌ Should be 'City of Ship-to'
    material_desc=safe_str(row.get('Material Description')),  # ❌ Should be 'Description'
    prod_hierarchy=safe_str(row.get('Prod. Hierarchy')),  # ❌ Should be 'Product Hierarchy'
    sloc=safe_str(row.get('SLoc')),  # ❌ Case mismatch: should be 'Sloc'
)
```

**Fix All Mappings:**
```python
fact_delivery = FactDelivery(
    # Date fields ✅
    delivery_date=safe_date(row.get('Delivery Date')),
    actual_gi_date=safe_date(row.get('Actual GI Date')),
    
    # IDs ✅
    delivery=safe_str(row.get('Delivery')),
    so_reference=safe_str(row.get('SO Reference')),
    sold_to_party=safe_str(row.get('Sold-to Party')),
    ship_to_party=safe_str(row.get('Ship-to Party')),
    material=safe_str(row.get('Material')),
    line_item=safe_str(row.get('Line Item')),
    
    # Text fields - CORRECTED NAMES
    dist_channel=safe_str(row.get('Dist. Channel')),  # ✅ Fixed
    ship_to_name=safe_str(row.get('Name of Ship-to')),  # ✅ Fixed
    ship_to_city=safe_str(row.get('City of Ship-to')),  # ✅ Fixed
    material_desc=safe_str(row.get('Description')),  # ✅ Fixed
    prod_hierarchy=safe_str(row.get('Product Hierarchy')),  # ✅ Fixed
    sloc=safe_str(row.get('Sloc')),  # ✅ Fixed (case)
    
    # Quantities
    delivery_qty=safe_float(row.get('Delivery Qty')),
    tonase=safe_float(row.get('Tonase')),
    actual_delivery_qty=safe_float(row.get('Actual Delivery Qty')),
    net_weight=safe_float(row.get('Net Weight')),
    volume=safe_float(row.get('Volume')),
    
    # Other fields
    req_type=safe_str(row.get('Req. Type')),
    delivery_type=safe_str(row.get('Delivery Type')),
    shipping_point=safe_str(row.get('Shipping Point')),
    sales_office=safe_str(row.get('Sales Office')),
    cust_group=safe_str(row.get('Cust. Group')),
    regional_struct=safe_str(row.get('Regional Stru. Grp.')),
    transport_zone=safe_str(row.get('Transportation Zone')),
    salesman_id=safe_str(row.get('Salesman ID')),
    salesman_name=safe_str(row.get('Salesman Name')),
    tonase_unit=safe_str(row.get('Tonase Unit')),
    sales_unit=safe_str(row.get('Sales Unit')),
    weight_unit=safe_str(row.get('Weight Unit')),
    volume_unit=safe_str(row.get('Volume Unit')),
    created_by=safe_str(row.get('Created By')),
    total_mvmt_goods_stat=safe_str(row.get('Total Movement Goods Stat'))
)
```

---

### Task 4.3: Re-Load ZRSD004 Data

**Steps:**

1. **Clear existing NULL data:**
```sql
TRUNCATE TABLE raw_zrsd004;
TRUNCATE TABLE fact_delivery;
```

2. **Re-upload file via API:**
```bash
curl -X POST http://localhost:8000/api/upload/zrsd004 \
  -F "file=@demodata/zrsd004.XLSX"
```

3. **Run transform:**
```bash
curl -X POST http://localhost:8000/api/etl/transform
```

4. **Verify data loaded:**
```sql
-- Check raw table
SELECT COUNT(*) FROM raw_zrsd004;
-- Should be 24,856

-- Check columns are populated (not NULL)
SELECT delivery, material, ship_to_name
FROM raw_zrsd004
WHERE delivery IS NOT NULL
LIMIT 10;
-- Should show actual values, not NULL

-- Check fact table
SELECT COUNT(*) FROM fact_delivery;
-- Should be 24,856 (or less if duplicates removed)

SELECT delivery, material_desc, ship_to_name
FROM fact_delivery
LIMIT 10;
-- Should show actual values
```

---

## 🧪 TESTING

### Test 4.1: Header Detection

**Create Test Script:** `test_zrsd004_headers.py`

```python
import pandas as pd

file_path = 'demodata/zrsd004.XLSX'

# Test NEW approach
df = pd.read_excel(file_path, header=None, skiprows=1, dtype=str)
df.columns = ['Delivery Date', 'Actual GI Date', 'Delivery', ...]  # All 34

print(f"Columns: {df.columns.tolist()[:5]}")
# Expected: ['Delivery Date', 'Actual GI Date', 'Delivery', 'SO Reference', 'Req. Type']
# NOT: ['Unnamed: 0', 'Unnamed: 1', ...]

print(f"Sample data:")
print(df[['Delivery', 'Material', 'Name of Ship-to']].head())
# Expected: Actual values, not NaN

assert 'Delivery' in df.columns
assert df['Delivery'].iloc[0] is not None
print("✅ Headers detected correctly!")
```

### Test 4.2: Data Integrity

**After re-load, verify:**

```python
from sqlalchemy import create_engine, text

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check raw table
    result = conn.execute(text("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN raw_data->>'Delivery' IS NOT NULL THEN 1 END) as delivery_not_null,
               COUNT(CASE WHEN raw_data->>'Material' IS NOT NULL THEN 1 END) as material_not_null
        FROM raw_zrsd004
    """))
    row = result.fetchone()
    
    print(f"Total rows: {row[0]}")
    print(f"Delivery NOT NULL: {row[1]} ({row[1]/row[0]*100:.1f}%)")
    print(f"Material NOT NULL: {row[2]} ({row[2]/row[0]*100:.1f}%)")
    
    # Should be 100% or close
    assert row[1] > row[0] * 0.95, "Too many NULL deliveries!"
    
    # Check fact table
    result = conn.execute(text("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN delivery IS NOT NULL THEN 1 END) as has_delivery,
               COUNT(CASE WHEN ship_to_name IS NOT NULL THEN 1 END) as has_name
        FROM fact_delivery
    """))
    row = result.fetchone()
    
    print(f"Fact total: {row[0]}")
    print(f"Has delivery: {row[1]} ({row[1]/row[0]*100:.1f}%)")
    print(f"Has ship_to_name: {row[2]} ({row[2]/row[0]*100:.1f}%)")
    
    assert row[1] > 0, "No deliveries in fact table!"
    
    print("✅ Data integrity check passed!")
```

---

## 📊 SUCCESS CRITERIA

**Before Fix:**
- ❌ Columns: `['Unnamed: 0', 'Unnamed: 1', ...]`
- ❌ All fields: NULL
- ❌ Data loss: 100%

**After Fix:**
- ✅ Columns: `['Delivery Date', 'Actual GI Date', 'Delivery', ...]`
- ✅ All fields: Populated
- ✅ Data recovery: 100% (24,856 rows)

**Checklist:**
- [ ] Headers read correctly (not 'Unnamed')
- [ ] All 34 column names assigned
- [ ] Column mappings updated (5 fixes)
- [ ] 24,856 rows loaded successfully
- [ ] raw_zrsd004: <5% NULL values in key fields
- [ ] fact_delivery: >95% populated
- [ ] No 'Unnamed' in logs

---

## 🚀 DEPLOYMENT

**Files Changed:**
- `src/etl/loaders.py` (2 changes: read_excel + column mappings)

**Database Impact:**
- Truncate and reload raw_zrsd004
- Truncate and rebuild fact_delivery

**Downtime:** None (can reload anytime)

**Rollback:** Restore previous code, keep old data if needed

---

## 🔄 COMPARISON WITH MB51 LOADER

| Aspect | Mb51Loader | Zrsd004Loader (Before) | Zrsd004Loader (After) |
|--------|-----------|------------------------|----------------------|
| **Excel Headers** | Merged cells | Formatted cells | Formatted cells |
| **pd.read_excel** | `header=None, skiprows=1` | `header=0` ❌ | `header=None, skiprows=1` ✅ |
| **Column Assignment** | Manual (76 cols) | Auto (fails) ❌ | Manual (34 cols) ✅ |
| **Data Loss** | 0% ✅ | 100% ❌ | 0% ✅ |

**Proven Pattern:** Mb51Loader already uses this fix successfully for 172,268 rows. Applying same pattern to Zrsd004Loader.

---

**Phase 4 Complete When:**
✅ ZRSD004 loads with actual column names  
✅ All 24,856 rows have populated data  
✅ fact_delivery table rebuilt correctly  
✅ No more 'Unnamed' in logs
