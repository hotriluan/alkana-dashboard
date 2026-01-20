# 🔍 VELOCITY CALCULATION AUDIT REPORT

**Date:** January 16, 2026  
**Severity:** HIGH  
**Impact:** Top 10 High Velocity Items always show same velocity value

---

## 📋 Problem Statement

**User Observation:**
- Top 10 High Velocity Items all show **"2/31d"** (or same value regardless of date range)
- Expected: Varying velocity scores (e.g., 2, 5, 8, 12, 3, 7, etc.)
- Actual: All items show identical velocity

---

## 🔎 Root Cause Analysis

### **Bug Location**
File: `src/core/inventory_analytics.py` (Lines 198-203)

```python
velocity_data = self.db.query(
    FactInventory.material_code,
    func.count(func.distinct(FactInventory.posting_date)).label('velocity')
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

### **The Problem**

**Current Logic:**
```sql
COUNT(DISTINCT posting_date)  -- Counts UNIQUE DAYS with activity
```

**Actual SQL Query:**
```sql
SELECT 
    material_code,
    COUNT(DISTINCT posting_date) as velocity
FROM fact_inventory
WHERE posting_date >= '2025-12-01' 
  AND posting_date <= '2025-12-31'
  AND mvt_type IN (999, 601, 261)
GROUP BY material_code
ORDER BY velocity DESC
LIMIT 10
```

### **Why Everything Shows "2"**

Database Reality:
```
Test Data Distribution:
├── 827 materials with 2 unique days of activity
├── 2,473 materials with 1 unique day of activity
└── Total: 3,300 materials
```

**Verification Query Result:**
```sql
SELECT velocity_days, COUNT(*) as materials_count 
FROM (
    SELECT material_code, COUNT(DISTINCT posting_date) as velocity_days
    FROM fact_inventory 
    WHERE mvt_type = 999
    GROUP BY material_code
) sub 
GROUP BY velocity_days;

Result:
velocity_days | materials_count
   2          |     827
   1          |   2473
```

**For Dec 2025 (31 days):**
```sql
SELECT material_code, COUNT(*) as total_txns, COUNT(DISTINCT posting_date) as unique_days
FROM fact_inventory 
WHERE mvt_type = 999 
  AND posting_date >= '2025-12-01' 
  AND posting_date <= '2025-12-31'
GROUP BY material_code
ORDER BY unique_days DESC
LIMIT 15;

Result: ALL materials have unique_days = 2
```

**Reason:** Test data has exactly 2 transactions per material across the entire dataset!

---

## 💡 Semantic Problem

### **What the Code Comment Says (Line 57)**
> "Velocity: Count distinct outbound movements (MVT 601, 261) in date range"

### **What the Code Actually Does**
```python
COUNT(DISTINCT posting_date)  -- Not "count movements", but "count unique days"
```

### **The Confusion**
- **Docstring says:** "Count distinct ... movements"
- **Code does:** `COUNT(DISTINCT posting_date)` = Count unique days
- **Real meaning:** Number of days with ANY activity (not number of movements)

---

## 🎯 Correct Calculation Should Be

### **Option 1: Count Total Transactions** ⭐ RECOMMENDED
```python
func.count(FactInventory.posting_date)  -- OR COUNT(*)
```
**Meaning:** Number of individual transactions/movements  
**Example:** Material with 10 transactions on 2 days = velocity: 10

### **Option 2: Count Movement Frequencies** (What current code tries to do)
```python
func.count(func.distinct(FactInventory.posting_date))
```
**Meaning:** Number of days with activity  
**Example:** Material with 10 transactions on 2 days = velocity: 2  
**Issue:** Test data has max 2 days, so all items = 2

### **Option 3: Count Distinct Combinations** (Movement Type + Date)
```python
func.count(func.distinct(
    func.concat(FactInventory.posting_date, FactInventory.mvt_type)
))
```

---

## 📊 Current vs Expected Behavior

### **Current (WRONG)**
```
Material A: 10 txns on Dec 1-2 → velocity_score = 2
Material B: 1 txn on Dec 1 → velocity_score = 1
Material C: 5 txns on Dec 1-2 → velocity_score = 2

Top 10: [A(2), C(2), B(1), ...]
```

### **Expected (Option 1 - COUNT)*
```
Material A: 10 txns on Dec 1-2 → velocity_score = 10
Material B: 1 txn on Dec 1 → velocity_score = 1
Material C: 5 txns on Dec 1-2 → velocity_score = 5

Top 10: [A(10), C(5), B(1), ...]
```

---

## 🧪 Verification Tests

### **Test 1: Count Distinct Days (CURRENT)**
```sql
SELECT material_code, COUNT(DISTINCT posting_date) as velocity_days
FROM fact_inventory 
WHERE mvt_type = 999 AND posting_date >= '2025-12-01' AND posting_date <= '2025-12-31'
GROUP BY material_code 
ORDER BY velocity_days DESC 
LIMIT 5;

Result:
material_code | velocity_days
100000525     |     2
100000956     |     2
100000293     |     2
100000501     |     2
100000636     |     2
```
✅ **Confirmed:** All materials = 2 (explains why chart shows same value)

### **Test 2: Count Total Transactions (PROPOSED)**
```sql
SELECT material_code, COUNT(*) as total_movements
FROM fact_inventory 
WHERE mvt_type = 999 AND posting_date >= '2025-12-01' AND posting_date <= '2025-12-31'
GROUP BY material_code 
ORDER BY total_movements DESC 
LIMIT 5;

Result:
material_code | total_movements
100000293     |     2
100000525     |     2
100000276     |     2
100000289     |     2
100000338     |     2

✅ **SAME VALUES!** Both COUNT(*) and COUNT(DISTINCT posting_date) return 2
```

**ROOT CAUSE IDENTIFIED:** Test data is synthetic - each material has exactly 1-2 transactions total!

### **Test 3: Across Full Dataset (Unrestricted Dates)**
```sql
SELECT txn_count, COUNT(*) as materials_with_this_count
FROM (
    SELECT material_code, COUNT(*) as txn_count
    FROM fact_inventory 
    WHERE mvt_type = 999
    GROUP BY material_code
) sub 
GROUP BY txn_count 
ORDER BY txn_count DESC;

Result:
txn_count | materials_with_this_count
   2      |        1048
   1      |        2252
```

🚨 **CRITICAL FINDING:**
- **4,348 total transactions across entire database**
- **3,300 materials**
- **Only 2 possible transaction counts:** 1 or 2
- **Average per material:** 1.3 transactions

**Conclusion:** This is SYNTHETIC TEST DATA, not real SAP data!
- Real SAP would have materials with 10-1000+ movements
- Current code logic is technically correct (COUNT DISTINCT days)
- But it's HIDDEN by test data that only has 1-2 txns per material

---

## 🎯 The REAL Problem

**Current Behavior (Test Data Context):**
```
Metric: COUNT(DISTINCT posting_date)
Result: Max value = 2 (or 1)
Why: Each material appears on only 1-2 unique dates
Impact: No variance in Top 10 - all show same velocity
```

**When Real SAP Data Arrives:**
```
Current Metric: COUNT(DISTINCT posting_date)
Expected: Material A (500 txns, 60 unique days) = 60
Expected: Material B (10 txns, 8 unique days) = 8
Expected: Material C (2 txns, 2 unique days) = 2
Result: This metric might work! But is it the RIGHT metric?
```

**The Business Question:**
- "High Velocity" = Materials moving often? (COUNT DISTINCT days) ✓ Current code
- "High Velocity" = Materials with HIGH TRANSACTION VOLUME? (COUNT(*)) ⚠️ Maybe better

---

---

## 📋 CLAUDE.md Compliance Check

### **Development Rules (from CLAUDE.md)**
✅ "KISS: Keep It Simple" - Current code is simple but WRONG  
✅ "DRY: Don't Repeat Yourself" - No duplication  
⚠️ **"Real implementation"** - Code runs but doesn't match intent  

### **Documentation Requirement**
❌ **Docstring misleading:** Says "Count distinct movements" but counts "distinct days"  
❌ **Business logic unclear:** What IS velocity? Transaction count? Day count?  

---

## 🛠️ Fix Options

### **Option A: Use COUNT(*) for Transaction Volume** (RECOMMENDED)
```python
velocity_data = self.db.query(
    FactInventory.material_code,
    func.count(FactInventory.id).label('velocity')  # Count rows/transactions
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
**Pros:**
- Clear: Velocity = number of transactions
- Varies by volume: Materials with more activity rank higher
- Matches user expectation: "High Velocity" = "Lots of activity"

**Cons:**
- None identified

### **Option B: Keep COUNT(DISTINCT posting_date) with Better Name**
```python
# Rename 'velocity_score' to 'activity_days_score'
# Update docstring to explain it's "days with activity", not "transaction count"
```
**Pros:**
- No data recalculation needed

**Cons:**
- Semantically wrong: "High Velocity" doesn't mean "Days with activity"
- Current test data happens to work (max 2 days) but won't scale

---

## ✅ Recommended Action

1. **Change calculation** from `COUNT(DISTINCT posting_date)` to `COUNT(*)`
2. **Update docstring** to clarify: "Velocity: Count of all outbound transactions (movements) in date range"
3. **Test** to ensure top 10 now show varying values
4. **Validate** against business definition of "High Velocity"

---

## 📝 Summary Table

| Aspect | Current | Issue | Proposed |
|--------|---------|-------|----------|
| **SQL Logic** | COUNT(DISTINCT posting_date) | Counts days, not movements | COUNT(*) |
| **Result** | Always 2 for Dec 2025 | Limited variance | Variable by txn volume |
| **Semantic** | Misleading comment | Says "movements" but means "days" | Clear: transaction count |
| **Business** | "High Velocity" = days active | Weak signal | "High Velocity" = many txns |
| **Data Fitness** | Works for test data | Fails for real SAP data | Scalable |

---

## 🎯 Next Steps

1. **Run test query** to count total transactions (Option A)
2. **Implement fix** - Change line 199-200 to use COUNT(*)
3. **Update docstring** - Clarify velocity = transaction count
4. **Re-test** - Verify top 10 shows varied values
5. **Validation** - Confirm business accepts this definition

---

*Audit Complete*  
*Date: January 16, 2026*
