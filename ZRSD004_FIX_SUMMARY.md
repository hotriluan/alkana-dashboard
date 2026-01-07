# ZRSD004 Header Issue - Executive Summary

## 🔴 CRITICAL FINDING

**Problem:** `zrsd004.XLSX` upload shows `['Unnamed: 0', 'Unnamed: 1', ...]` instead of column headers.

**Root Cause:** Excel file has **merged cells or formatting issues** in the header row that pandas cannot parse.

**Impact:** ALL DATA IS LOST - records inserted with NULL values because column lookups fail.

---

## 📊 Evidence

### Test Results
```bash
$ python -c "import pandas as pd; df = pd.read_excel('demodata/zrsd004.XLSX', header=0); print(df.columns.tolist()[:5])"
['Unnamed: 0', 'Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4']
```

### Actual Headers (from openpyxl inspection)
```
Row 1: ['Delivery Date', 'Actual GI Date', 'Delivery', 'SO Reference', ...]
Row 2: [datetime(2024-12-03), datetime(2024-12-09), '1410005383', ...]
```

Headers exist but pandas **cannot read them** due to formatting.

---

## ✅ Solution

Use the **same fix as Mb51Loader** (already working in codebase):

```python
# Skip header row and assign manually
df = pd.read_excel(file_path, header=None, skiprows=1, dtype=str)
df.columns = ['Delivery Date', 'Actual GI Date', 'Delivery', ...]  # 34 columns
```

---

## 📝 Changes Required

**File:** `src/etl/loaders.py`  
**Class:** `Zrsd004Loader` (lines 536-605)

### Change 1: Fix read_excel call (line 542)
```python
# OLD:
df = pd.read_excel(file_path, header=0, dtype=str)

# NEW:
df = pd.read_excel(file_path, header=None, skiprows=1, dtype=str)
df.columns = [...]  # See full list in detailed report
```

### Change 2: Fix column name mappings (lines 554-575)
```python
# Examples of changes needed:
'dist_channel': safe_str(row.get('Dist. Channel')),      # was 'Distribution Channel'
'ship_to_name': safe_str(row.get('Name of Ship-to')),    # was 'Ship-to Name'
'ship_to_city': safe_str(row.get('City of Ship-to')),    # was 'Ship-to City'
'material_desc': safe_str(row.get('Description')),       # was 'Material Description'
'prod_hierarchy': safe_str(row.get('Product Hierarchy')) # was 'Prod. Hierarchy'
```

---

## 🎯 Files to Review

1. **Main Report:** [ZRSD004_HEADER_FIX_REPORT.md](ZRSD004_HEADER_FIX_REPORT.md) - Full technical details
2. **Code to Fix:** [src/etl/loaders.py](src/etl/loaders.py#L536-L605) - Zrsd004Loader class

---

## ✨ Expected Outcome

**Before Fix:**
```
Columns: ['Unnamed: 0', 'Unnamed: 1', 'Unnamed: 2', ...]
Data loaded: 0 valid records (all NULL)
```

**After Fix:**
```
Columns: ['Delivery Date', 'Actual GI Date', 'Delivery', 'SO Reference', ...]
Data loaded: 1000+ valid records with actual values
```

---

## 🔍 Why This Happened

1. **zrsd002.XLSX** - Clean headers → Works with `header=0`
2. **mb51.XLSX** - Merged cells → Uses `header=None + manual assignment`
3. **zrsd004.XLSX** - Merged/formatted headers → **Needs same fix as MB51**

The fix is proven and already in production for MB51.

---

## 📌 Recommendations

1. ✅ Apply fix immediately (critical data loss issue)
2. ✅ Test with actual file upload
3. ✅ Verify data appears in database
4. ⚠️ Check other loaders for similar issues (ZRMM024, ZRFI005, ZRSD006)
5. 📋 Document Excel file format requirements for future uploads
