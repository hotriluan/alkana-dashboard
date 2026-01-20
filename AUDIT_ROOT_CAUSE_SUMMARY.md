# 🔍 AUDIT SUMMARY: Velocity Always "2" - ROOT CAUSE EXPLAINED

---

## Quick Answer

**Question:** Why do all items show `Movements: 2/31d`?

**Answer:** Because the test database has exactly **1 or 2 transactions per material maximum** - it's synthetic data!

---

## The Flow

```
Database Reality:
├── 4,348 total transactions
├── 3,300 materials
├── Transaction distribution:
│   ├── 1,048 materials with 2 transactions ← Most items land here
│   └── 2,252 materials with 1 transaction
└── Result: Max velocity (days) = 2

When user selects date range (Dec 1-31):
├── Query: COUNT(DISTINCT posting_date) 
├── Finds all materials with activity in Dec 2025
├── Almost all have activity on exactly 2 different days
└── Result: Top 10 all show velocity = 2 ✅ Correct for test data
```

---

## Code Logic (CORRECT ✅)

```python
# What the code does:
COUNT(DISTINCT posting_date)

# For Material X in Dec 2025:
# - Txn 1: Dec 1 → posting_date = '2025-12-01'
# - Txn 2: Dec 15 → posting_date = '2025-12-15'
# - COUNT(DISTINCT posting_date) = 2 ✓

# Business meaning: 
# "Velocity = number of UNIQUE DAYS with activity"
```

---

## The Real Issue (NOT Code, But Documentation)

```
Docstring says: "Count distinct movements"
Code actually: COUNT(DISTINCT posting_date) → counts DAYS, not movements

Example:
Material A: 10 transactions on 2 different days
├── Docstring says: "10 distinct movements"
├── Code counts: 2 (unique days)
└── Result: Misleading! ❌
```

---

## When Real SAP Data Arrives

```
Real scenario:
├── Material A: 500 txns across 60 days → velocity = 60 ✅
├── Material B: 50 txns across 30 days → velocity = 30 ✅
├── Material C: 2 txns across 2 days → velocity = 2 ✅
└── Top 10 will show: [60, 55, 48, 45, 42, 38, 35, 32, 28, 25] ✅ VARIED!

Current test data:
├── Material A: 2 txns across 2 days → velocity = 2
├── Material B: 2 txns across 2 days → velocity = 2
├── Material C: 1 txn across 1 day → velocity = 1
└── Top 10 will show: [2, 2, 2, 2, 2, 2, 2, 2, 2, 2] ❌ IDENTICAL
```

---

## Database Proof

### Query 1: Show Distribution
```sql
SELECT txn_count, COUNT(*) as num_materials
FROM (SELECT material_code, COUNT(*) as txn_count 
      FROM fact_inventory WHERE mvt_type = 999 
      GROUP BY material_code) sub
GROUP BY txn_count;

Result:
txn_count │ num_materials
──────────┼──────────────
        2 │        1,048  ← Most items here
        1 │        2,252
```

### Query 2: Dec 2025 Velocity
```sql
SELECT material_code, COUNT(DISTINCT posting_date) as velocity
FROM fact_inventory
WHERE mvt_type = 999 AND posting_date BETWEEN '2025-12-01' AND '2025-12-31'
GROUP BY material_code
ORDER BY velocity DESC
LIMIT 5;

Result:
material_code │ velocity
──────────────┼──────────
 100000293    │        2  ← Most have 2
 100000525    │        2
 100000276    │        2
 100000289    │        2
 100000338    │        2
```

---

## Audit Findings (Per CLAUDE.md)

| Aspect | Status | Details |
|--------|--------|---------|
| **Code Correctness** | ✅ PASS | SQL logic is correct for stated logic |
| **Documentation** | ❌ FAIL | Docstring says "movements" but counts "days" |
| **Business Meaning** | ⚠️ UNCLEAR | Is "high velocity" = frequency or volume? |
| **Test Data** | ⚠️ ISSUE | Too simplistic - hides real variance |
| **Real Data Ready** | ⚠️ NEEDS FIX | Will need metric clarification |

---

## Recommendations

### Immediate (For Current Test Data)
✅ **No action needed** - Code works correctly

### Documentation Fix (Clarify Intent)
```python
# File: src/core/inventory_analytics.py, line 57
# CHANGE FROM:
"""
- Velocity: Count distinct outbound movements (MVT 601, 261) in date range
"""

# CHANGE TO:
"""
- Velocity: Number of unique days with outbound activity (MVT 601, 261) in date range
"""
```

### Future (When Real SAP Data Arrives)
**Option A: Keep as-is**
- Metric stays as "days of activity"
- Will show natural variance with real data

**Option B: Switch to transaction count** ⭐ RECOMMENDED
```python
# Line 199-200:
# func.count(func.distinct(FactInventory.posting_date))
# becomes:
func.count()  # Count all transactions, not just days
```

---

## Conclusion

✅ **The code is NOT broken**  
❌ **The documentation is misleading**  
⚠️ **The test data is too uniform to show variance**  

Fix the documentation to match the code logic, or change the logic to match the documentation!

---

*Audit Date: January 16, 2026*  
*Auditor: AI Development Agent*  
*Compliance: CLAUDE.md rules verified*
