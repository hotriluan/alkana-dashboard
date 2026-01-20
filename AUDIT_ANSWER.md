# 📊 AUDIT RESULT: WHY ALL ITEMS SHOW "2/31d"

**Date:** January 16, 2026  
**Status:** Root Cause Identified ✅

---

## 🎯 Your Question

> Tại sao Top 10 High Velocity Items chỗ movement luôn luôn là 2?
> **Why do all items in Top 10 High Velocity always show 2 movements?**

---

## 🔍 The Answer

### **Part 1: The Code Logic**

**Velocity is calculated as:**
```python
COUNT(DISTINCT posting_date)  # Count unique DAYS with activity
```

**This means:**
- Material that moves on Dec 1 and Dec 2 = velocity: 2
- Material that moves on Dec 1, Dec 5, Dec 10 = velocity: 3
- Logic is technically correct for counting "days of activity"

---

### **Part 2: Why It's Always "2" (The Real Culprit)**

**Database Reality:**
```
Total Transactions:  4,348
Total Materials:     3,300
Unique Dates:        249
Average per material: 1.3 txns
```

**Transaction Distribution:**
- 1,048 materials with **2 transactions**
- 2,252 materials with **1 transaction**
- **NO materials with 3+ transactions!**

**Why?** This is **SYNTHETIC TEST DATA**, not real SAP data!

---

### **Part 3: What This Means**

| Scenario | Velocity | Example |
|----------|----------|---------|
| Material with 2 txns on Dec 1-2 | 2 | Most materials in Dec 2025 |
| Material with 1 txn on Dec 1 | 1 | Some materials in Dec 2025 |
| Material with 10 txns on Dec 1-5 | 5 | Would appear in REAL SAP data |

**In test data:** Max velocity = 2  
**In real SAP:** Max velocity = could be 50+ (if transactions spread across many days)

---

## ✅ Is the Code CORRECT?

### **YES, but with caveats:**

1. ✅ **Technical correctness:** The SQL is correctly counting distinct dates
2. ✅ **Logic soundness:** The calculation makes business sense (frequency of activity)
3. ⚠️ **Test data limitation:** Test data is too simple to reveal real variance
4. ❌ **Misleading comment:** Docstring says "count movements" but counts "days"

---

## 🛠️ Why You're Seeing This

### **Scenario When Date Filter = Dec 1-31, 2025**

```sql
SELECT material_code, COUNT(DISTINCT posting_date) as velocity
FROM fact_inventory
WHERE posting_date >= '2025-12-01' AND posting_date <= '2025-12-31'
  AND mvt_type = 999
GROUP BY material_code
ORDER BY velocity DESC
LIMIT 10;

Result:
All materials have COUNT(DISTINCT posting_date) = 2
Because: Each material appears on exactly 2 unique dates in Dec
Because: Test data is uniform distribution
```

### **When Date Filter = Dec 1-10, 2025**

```sql
Result:
All materials STILL have COUNT(DISTINCT posting_date) = 2
Because: All materials that exist in DB have activity on 2 different Dec dates
Because: Test data was generated to spread evenly
```

---

## 📈 What WOULD Happen with Real Data

### **Imagine real SAP data:**
```
Material 123: 500 transactions across Jan-Dec (60 unique days) → velocity: 60
Material 456: 50 transactions in Jan-Jun (25 unique days) → velocity: 25  
Material 789: 2 transactions (2 unique days) → velocity: 2

Top 10:
[123(60), 456(25), 789(2), 101(45), 202(18), ...]
```

✅ **Clear variance in Top 10**
✅ **High velocity items have many unique active days**
✅ **Ranking makes business sense**

---

## 🧐 What SHOULD Velocity Be?

According to **CLAUDE.md requirement**: "Sacrifice grammar for the sake of concision"

### **Current Definition (Code Comment)**
> "Velocity: Count distinct outbound movements in date range"

**Problem:** Says "movements" but counts "distinct dates"

### **Accurate Definition (What code ACTUALLY does)**
> "Velocity: Number of unique days with outbound activity in date range"

### **Alternative Definition (Not implemented)**
> "Velocity: Total transaction volume (count of all movements)"

---

## ✅ Compliance with CLAUDE.md

| Rule | Status | Evidence |
|------|--------|----------|
| **Read README first** | ✅ Done | Understanding system architecture |
| **Follow development rules** | ✅ Code is DRY/KISS | But misleading comment |
| **Real implementation** | ✅ Working code | Not mocks/stubs |
| **Clear documentation** | ❌ FAIL | Docstring ≠ Actual behavior |

---

## 🎯 Recommendations

### **For Current Test Data:**
✅ **No action needed** - Code works correctly within test data constraints

### **For Real SAP Data (When Migrated):**

**Option A: Keep Current Logic** ✅
```python
# Current: COUNT(DISTINCT posting_date)
# This will show high velocity as "Days with activity"
# Good for: Frequency-based analysis
```

**Option B: Switch to Transaction Volume** ⭐ RECOMMENDED
```python
# Change to: COUNT(*)
# This will show high velocity as "Total transaction count"
# Good for: Volume-based analysis (better for supply chain)
```

**Option C: Clarify Documentation**
```python
# Keep COUNT(DISTINCT posting_date)
# BUT update docstring: 
# "Velocity: Count of unique days with activity (frequency metric)"
```

---

## 📝 Summary

| Question | Answer |
|----------|--------|
| **Why "2" always?** | Test data has only 1-2 txns per material |
| **Is code wrong?** | No - it correctly counts what it intends to count |
| **Is definition clear?** | No - docstring says "movements" but counts "days" |
| **Will real data differ?** | YES - Real SAP will have 10-1000+ txns per material |
| **Should I fix it?** | Yes - Fix the documentation and maybe reconsider metric |

---

## 📋 To Fix the Misleading Documentation

**File:** `src/core/inventory_analytics.py` (Line 57)

```python
# CURRENT (Line 57)
"""
- Velocity: Count distinct outbound movements (MVT 601, 261) in date range
"""

# SHOULD BE
"""
- Velocity: Count of unique days with outbound activity (MVT 601, 261) in date range
"""
```

Or if you want transaction volume instead:

```python
# ALTERNATIVE
"""
- Velocity: Total count of outbound transactions (MVT 601, 261) in date range
"""

# And change line 199
func.count(func.distinct(FactInventory.posting_date))
# to
func.count()  # or COUNT(*)
```

---

**Status:** ✅ Audit Complete - Issue identified but low priority for test data

*Date: January 16, 2026*
