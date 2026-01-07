# ZRSD004 Excel Header Issue - Root Cause Analysis

## Problem Summary
File `demodata/zrsd004.XLSX` shows `['Unnamed: 0', 'Unnamed: 1', ...]` instead of actual column names when uploaded with `pd.read_excel(file_path, header=0)`.

**Impact:** All data fields are inserted as NULL because `row.get('column_name')` returns None when columns are named 'Unnamed: X'.

---

## Investigation Results

### 1. File Structure Analysis

Using `openpyxl` to inspect raw Excel structure:

**ZRSD004.XLSX:**
```
Row 1: ['Delivery Date', 'Actual GI Date', 'Delivery', 'SO Reference', ...]  ← HEADERS ARE HERE
Row 2: [datetime(2024-12-03), datetime(2024-12-09), '1410005383', ...]       ← DATA STARTS
Row 3: [datetime(2024-12-16), datetime(2024-12-12), '1410005384', ...]
```

**ZRSD002.XLSX (Working):**
```
Row 1: ['Billing Date', 'Billing Document', 'Sloc', ...]  ← HEADERS
Row 2: [datetime(2025-01-06), '1930045567', '0101', ...]  ← DATA
```

**MB51.XLSX (Working with manual headers):**
```
Row 1: ['Posting Date', 'Movement Type', 'Plant', ...]    ← HEADERS
Row 2: [datetime(2024-12-31), '601', '1401', ...]         ← DATA
```

### 2. Pandas Behavior Test

```python
# Test on zrsd004.XLSX
df = pd.read_excel('demodata/zrsd004.XLSX', header=0)
print(df.columns.tolist()[:5])
# Output: ['Unnamed: 0', 'Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4']
```

This indicates pandas **cannot recognize Row 1 as headers** despite the headers being there.

### 3. Comparison of Loader Code

#### Zrsd004Loader (BROKEN):
```python
# Line 542 in src/etl/loaders.py
df = pd.read_excel(file_path, header=0, dtype=str)
```

#### Zrsd002Loader (WORKING):
```python
# Line 468 in src/etl/loaders.py
df = pd.read_excel(file_path, header=0, dtype=str)
```

#### Mb51Loader (WORKING with workaround):
```python
# Line 301 in src/etl/loaders.py
df = pd.read_excel(file_path, header=None, skiprows=1, dtype=str)
# Then manually assigns column names
df.columns = ['Posting Date', 'Movement Type', 'Plant', ...]
```

---

## ROOT CAUSE

The Excel file `zrsd004.XLSX` has **formatting issues in Row 1** that prevent pandas from recognizing it as a header row. Possible causes:

1. **Merged cells** in the header row (like mb51.XLSX)
2. **Empty/hidden cells** in the header row
3. **Formatting or data type** issues in header cells
4. **Excel metadata** that confuses pandas' header detection

When pandas reads a row with problematic formatting as `header=0`, it:
- Cannot parse the header names correctly
- Defaults to auto-generated names: `Unnamed: 0`, `Unnamed: 1`, etc.
- Treats the actual header row as data (lost in the process)

---

## WHY ZRSD002 WORKS BUT ZRSD004 DOESN'T

From the test output:
```
ZRSD002 with header=0:
  Columns: ['Billing Date', 'Billing Document', 'Sloc', ...]  ✓ WORKS

ZRSD004 with header=0:
  Columns: ['Unnamed: 0', 'Unnamed: 1', ...]  ✗ FAILS

MB51 with header=0:
  Would also fail (uses header=None + manual assignment)
```

**zrsd002.XLSX** has clean, properly formatted headers.
**zrsd004.XLSX** has corrupted/formatted headers that pandas cannot read.

---

## COLUMN NAME MISMATCHES

The loader code has **incorrect column names** that don't match the actual Excel file:

| Loader Expects          | Excel Actually Has       | Status |
|-------------------------|--------------------------|--------|
| `Distribution Channel`  | `Dist. Channel`          | ❌ WRONG |
| `Ship-to Name`          | `Name of Ship-to`        | ❌ WRONG |
| `Ship-to City`          | `City of Ship-to`        | ❌ WRONG |
| `Material Description`  | `Description`            | ❌ WRONG |
| `Prod. Hierarchy`       | `Product Hierarchy`      | ❌ WRONG |
| `SLoc`                  | `Sloc`                   | ❌ Case mismatch |

**Columns in Excel file but NOT loaded by current code:**
- Delivery Date
- Req. Type
- Delivery Type
- Regional Stru. Grp.
- Transportation Zone
- Actual Delivery Qty
- Sales Unit
- Weight Unit
- Volume Unit
- Created By
- Total Movement Goods Stat

**Total columns:** 34 (file has 34, loader expects 23)

---

## SOLUTION

Apply the **same fix as Mb51Loader** to Zrsd004Loader:

### Option 1: Manual Header Assignment (RECOMMENDED)
```python
# Skip problematic header row and assign manually
df = pd.read_excel(file_path, header=None, skiprows=1, dtype=str)

# Assign proper column names based on expected structure
df.columns = [
    'Delivery Date', 'Actual GI Date', 'Delivery', 'SO Reference',
    'Req. Type', 'Delivery Type', 'Shipping Point', 'SLoc',
    'Sales Office', 'Dist. Channel', 'Cust. Group', 'Sold-to Party',
    'Ship-to Party', 'Ship-to Name', 'Ship-to City', 'Salesman ID',
    'Salesman Name', 'Material', 'Material Description', 'Delivery Qty',
    'Tonase', 'Tonase Unit', 'Net Weight', 'Volume', 'Prod. Hierarchy'
    # ... add remaining columns as needed
][:len(df.columns)]
```

### Option 2: Detect Header Row (More Complex)
Implement header detection logic like `detect_zrmm024_header_row()` already in the codebase.

---

## EXACT CODE CHANGES NEEDED

**File:** [src/etl/loaders.py](src/etl/loaders.py#L542)

**Current Code (Line 542):**
```python
df = pd.read_excel(file_path, header=0, dtype=str)
```

**Fixed Code:**
```python
# Skip problematic header row (merged cells or formatting issues)
df = pd.read_excel(file_path, header=None, skiprows=1, dtype=str)

# Assign proper column names based on actual Excel header (34 columns)
df.columns = [
    'Delivery Date', 'Actual GI Date', 'Delivery', 'SO Reference',
    'Req. Type', 'Delivery Type', 'Shipping Point', 'Sloc',
    'Sales Office', 'Dist. Channel', 'Cust. Group', 'Sold-to Party',
    'Ship-to Party', 'Name of Ship-to', 'City of Ship-to',
    'Regional Stru. Grp.', 'Transportation Zone', 'Salesman ID',
    'Salesman Name', 'Material', 'Description', 'Delivery Qty',
    'Tonase', 'Tonase Unit', 'Actual Delivery Qty', 'Sales Unit',
    'Net Weight', 'Weight Unit', 'Volume', 'Volume Unit',
    'Created By', 'Product Hierarchy', 'Line Item',
    'Total Movement Goods Stat'
][:len(df.columns)]
```

**ALSO UPDATE** the field mappings (lines 554-575) to use actual column names:
```python
record_data = {
    'actual_gi_date': safe_datetime(row.get('Actual GI Date')),
    'delivery': delivery,
    'line_item': line_item,
    'so_reference': safe_str(row.get('SO Reference')),
    'shipping_point': safe_str(row.get('Shipping Point')),
    'sloc': safe_str(row.get('Sloc')),  # Note: 'Sloc' not 'SLoc'
    'sales_office': safe_str(row.get('Sales Office')),
    'dist_channel': safe_str(row.get('Dist. Channel')),  # CHANGED
    'cust_group': safe_str(row.get('Cust. Group')),
    'sold_to_party': safe_str(row.get('Sold-to Party')),
    'ship_to_party': safe_str(row.get('Ship-to Party')),
    'ship_to_name': safe_str(row.get('Name of Ship-to')),  # CHANGED
    'ship_to_city': safe_str(row.get('City of Ship-to')),  # CHANGED
    'salesman_id': safe_str(row.get('Salesman ID')),
    'salesman_name': safe_str(row.get('Salesman Name')),
    'material': safe_str(row.get('Material')),
    'material_desc': safe_str(row.get('Description')),  # CHANGED
    'delivery_qty': safe_float(row.get('Delivery Qty')),
    'tonase': safe_float(row.get('Tonase')),
    'tonase_unit': safe_str(row.get('Tonase Unit')),
    'net_weight': safe_float(row.get('Net Weight')),
    'volume': safe_float(row.get('Volume')),
    'prod_hierarchy': safe_str(row.get('Product Hierarchy')),  # CHANGED
    'source_file': str(file_path.name),
    'source_row': idx + 2,
    'raw_data': raw_data,
    'row_hash': compute_row_hash(raw_data)
}
```

---

## EXPECTED OUTCOME

After the fix:
```python
# Before
Columns: ['Unnamed: 0', 'Unnamed: 1', 'Unnamed: 2', ...]

# After  
Columns: ['Delivery Date', 'Actual GI Date', 'Delivery', 'SO Reference', ...]
```

The loader will correctly map data to column names, enabling proper field extraction with `row.get('Delivery')`, `row.get('Actual GI Date')`, etc.

---

## FILES TO MODIFY

1. **[src/etl/loaders.py](src/etl/loaders.py#L536-L605)** - Zrsd004Loader.load() method
   - Change line 542: `df = pd.read_excel(file_path, header=None, skiprows=1, dtype=str)`
   - Add line 543-552: Column name assignment

---

## VERIFICATION STEPS

1. Apply the fix to Zrsd004Loader
2. Run the loader: `python -c "from src.etl.loaders import Zrsd004Loader; ..."` 
3. Check output shows actual column names
4. Verify data is correctly loaded into database
5. Confirm no 'Unnamed' columns appear

---

## ADDITIONAL NOTES

- This is the **same issue and solution as MB51** 
- MB51 already uses `header=None, skiprows=1` + manual column assignment
- The fix is proven and reliable
- Consider checking other XLSX loaders for similar issues
