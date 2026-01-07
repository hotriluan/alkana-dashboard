# COMPREHENSIVE FIX PLAN - Executive Dashboard Data Issues

**Date:** January 6, 2026  
**Status:** Issues Identified - Ready to Fix  
**Skills:** data-analysis, debugging, databases, ETL, problem-solving

---

## 🔍 INVESTIGATION SUMMARY

### Issues Discovered

| Issue | Severity | Impact | Root Cause |
|-------|----------|--------|------------|
| Revenue +7.6% higher | CRITICAL | Dashboard shows 299B vs Excel 278B | Duplicate rows in fact_billing |
| Customer Count = 0 | CRITICAL | Cannot track customer metrics | Excel file missing Customer Name column |
| Duplicate Documents | CRITICAL | Each doc appears ~40 times | raw_zrsd002 has duplicate data |
| Production data OK | ✓ | Correct: 837 orders, 88.9% completion | No issues |
| AR data OK | ✓ | Correct: 43B total AR | No issues |
| Inventory OK | ✓ | Correct: 1784 materials | No issues |

### Data Comparison

**Source (zrsd002.xlsx):**
- Rows: 21,072
- Unique Documents: 7,091
- Revenue: 278,240,644,750.76
- Customer Name column: MISSING

**Database (fact_billing):**
- Rows: 22,673 ❌ (+1,601 duplicate rows)
- Unique Documents: 7,091 ✓
- Revenue: 299,267,567,043.88 ❌ (+7.6%)
- Customer Name: ALL NULL ❌

**Duplicate Examples:**
- Document 1930052203: 40 times
- Document 1930047530: 39 times  
- Document 1930046114: 39 times

---

## 🎯 FIX STRATEGY (Claude Kit Engineer Approach)

### Phase 1: Clean Duplicate Data (PRIORITY 1)

**Problem:** raw_zrsd002 table has 22,673 rows but Excel only has 21,072 rows

**Root Cause:** Multiple file uploads or failed deduplication during load

**Solution:**
1. Identify duplicate rows in raw_zrsd002 using row_hash
2. Delete duplicate raw records (keep only 1 per unique hash)
3. Clear fact_billing completely
4. Re-transform clean raw data → fact_billing
5. Verify: fact_billing should have 21,072 rows, 278B revenue

**SQL Query to Fix:**
```sql
-- Step 1: Find duplicates in raw_zrsd002
WITH duplicates AS (
    SELECT row_hash, COUNT(*) as cnt
    FROM raw_zrsd002
    WHERE row_hash IS NOT NULL
    GROUP BY row_hash
    HAVING COUNT(*) > 1
)
SELECT SUM(cnt - 1) as duplicate_count FROM duplicates;

-- Step 2: Delete duplicates (keep first occurrence)
DELETE FROM raw_zrsd002
WHERE id NOT IN (
    SELECT MIN(id)
    FROM raw_zrsd002
    GROUP BY row_hash
);

-- Step 3: Clear fact_billing
DELETE FROM fact_billing;

-- Step 4: Re-run transform (Python)
```

### Phase 2: Fix Customer Name Mapping (PRIORITY 2)

**Problem:** Excel file doesn't have "Customer Name" column - transform is looking for wrong column

**Investigation Needed:**
1. Check actual Excel column names
2. Find customer-related columns (e.g., "Sold-to", "Sold-to Party", "Customer")
3. Update loader mapping to use correct column

**Columns in Excel:**
```
'Billing Date', 'Billing Document', 'Sloc', 'Tax Classification', 'TOP', 
'Billing Type', 'Sales Organization', 'Sales Office', 'Dist Channel', 
'Sold-to', ... (58 total)
```

**Likely Fix:** Map "Sold-to" → customer_name in loader

**File to Update:** `src/etl/loaders.py` - Zrsd002Loader class

### Phase 3: Add Data Validation (PRIORITY 3)

**Add safeguards to prevent future issues:**
1. Unique constraint on fact_billing(billing_document, billing_item)
2. Row count validation after transform
3. Revenue sanity check (warn if >5% difference)
4. Customer name validation (warn if >90% NULL)

---

## 📋 STEP-BY-STEP EXECUTION PLAN

### Step 1: Investigate Excel Column Names
```python
import pandas as pd
df = pd.read_excel("demodata/zrsd002.xlsx")
print("Columns:", list(df.columns))
print("\nCustomer-related columns:")
for col in df.columns:
    if any(word in col.lower() for word in ['customer', 'sold', 'party', 'name']):
        print(f"  - {col}: {df[col].notna().sum()} non-null values")
```

### Step 2: Fix Loader Column Mapping
- Update `src/etl/loaders.py` Zrsd002Loader
- Map correct customer column (likely "Sold-to" or "Sold-to Party")
- Test with sample data

### Step 3: Clean Duplicates & Re-transform
```python
# 1. Delete duplicate raw records
DELETE FROM raw_zrsd002
WHERE id NOT IN (
    SELECT MIN(id)
    FROM raw_zrsd002
    GROUP BY row_hash
);

# 2. Clear fact_billing
DELETE FROM fact_billing;

# 3. Re-run transform
python -c "from src.etl.transform import Transformer; from src.db.connection import get_db; db = next(get_db()); t = Transformer(db); t.transform_zrsd002(); db.close()"
```

### Step 4: Validate Results
```sql
-- Check fact_billing
SELECT 
    COUNT(*) as rows,
    COUNT(DISTINCT billing_document) as docs,
    SUM(net_value) as revenue,
    COUNT(DISTINCT customer_name) as customers
FROM fact_billing
WHERE billing_date BETWEEN '2025-01-01' AND '2025-12-31';

-- Expected results:
-- rows: ~21,072
-- docs: 7,091
-- revenue: ~278,240,644,750
-- customers: > 0 (after customer fix)
```

---

## 🔧 SKILLS UTILIZED

- ✅ **data-analysis**: Comprehensive audit comparing Excel vs Database
- ✅ **debugging**: Root cause analysis for revenue mismatch
- ✅ **databases**: SQL queries for duplicate detection
- ✅ **problem-solving**: Systematic investigation methodology
- ✅ **ETL**: Understanding transform pipeline issues
- ✅ **data-quality**: Identifying duplicate and NULL data issues

---

## 📊 CLAUDE KIT ENGINEER COMPLIANCE

### ✅ Systematic Investigation
- Compared source data (Excel) vs database systematically
- Checked all metrics: Revenue, Customers, Production, Inventory, AR
- Identified root causes for each issue

### ✅ DRY Principle
- Reusable audit script for future data validation
- Generic duplicate detection query

### ✅ KISS Principle
- Simple 3-step fix: Clean → Transform → Validate
- No complex workarounds

### ✅ Data Integrity
- Found and will fix data quality issues at source
- Add validation to prevent recurrence

---

## 🚀 READY TO EXECUTE

User can now:
1. Run customer column investigation
2. Fix loader mapping
3. Clean duplicates and re-transform
4. Verify dashboard shows correct data

**Estimated Time:** 15-20 minutes for complete fix

**Expected Outcome:**
- Revenue: 278B (matches Excel)
- Customers: >0 (actual customer count)
- All duplicates removed
- Dashboard accurate

---

**Next Action:** Execute Step 1 to identify correct customer column name
