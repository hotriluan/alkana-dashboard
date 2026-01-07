# DUPLICATE PREVENTION STRATEGY
**Comprehensive Plan to Eliminate and Prevent Database Duplicates**

## Executive Summary

**Current State (After Audit):**
- ✅ fact_billing: Fixed (was 21,072 duplicates → now 0)
- ✅ fact_lead_time: Fixed (was 1,849 duplicates → now 0)
- ❌ fact_p02_p01_yield: **2,214 duplicates (34.8%)** - NEEDS FIX
- ❌ fact_target: **36 duplicates (50.0%)** - NEEDS FIX  
- ❌ raw_mb51: **583 duplicates (0.3%)** - NEEDS FIX
- **Total Remaining: 2,833 duplicate rows**

**Root Cause:** Transform pipeline runs multiple times without truncating tables first, causing accumulation.

---

## PART 1: IMMEDIATE FIXES

### 1.1 Fix fact_p02_p01_yield Duplicates (2,214 rows)

**Business Keys:** `p02_batch + p01_batch`

```sql
-- Remove duplicates, keeping earliest record
DELETE FROM fact_p02_p01_yield
WHERE id NOT IN (
    SELECT MIN(id)
    FROM fact_p02_p01_yield
    GROUP BY p02_batch, p01_batch
);

-- Verify
SELECT 
    COUNT(*) as total,
    COUNT(DISTINCT (p02_batch, p01_batch)) as unique_count
FROM fact_p02_p01_yield;
-- Should show: total = unique_count = 4,139
```

### 1.2 Fix fact_target Duplicates (36 rows)

**Business Keys:** `salesman_name + semester + year`

```sql
-- Remove duplicates, keeping earliest record
DELETE FROM fact_target
WHERE id NOT IN (
    SELECT MIN(id)
    FROM fact_target
    GROUP BY salesman_name, semester, year
);

-- Verify
SELECT 
    COUNT(*) as total,
    COUNT(DISTINCT (salesman_name, semester, year)) as unique_count
FROM fact_target;
-- Should show: total = unique_count = 36
```

### 1.3 Fix raw_mb51 Duplicates (583 rows)

**Business Key:** `row_hash` (already computed MD5 hash of row content)

```sql
-- Remove duplicates based on row_hash
DELETE FROM raw_mb51
WHERE id NOT IN (
    SELECT MIN(id)
    FROM raw_mb51
    GROUP BY row_hash
);

-- Verify
SELECT 
    COUNT(*) as total,
    COUNT(DISTINCT row_hash) as unique_count
FROM raw_mb51;
-- Should show: total = unique_count = 171,685
```

---

## PART 2: DATABASE-LEVEL PREVENTION (CONSTRAINTS)

### 2.1 Strategy: UNIQUE Constraints on Business Keys

**Challenge:** Cannot create UNIQUE constraints directly on computed columns or JSONB expressions.

**Solution:** Use PostgreSQL **Functional Indexes** with UNIQUE modifier.

### 2.2 Implementation for FACT Tables

```sql
-- fact_billing
CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_billing_unique_key
ON fact_billing (billing_document, billing_item);

-- fact_production  
CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_production_unique_key
ON fact_production (order_number, batch);

-- fact_delivery
CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_delivery_unique_key
ON fact_delivery (delivery, line_item);

-- fact_lead_time
CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_lead_time_unique_key
ON fact_lead_time (order_number, batch);

-- fact_p02_p01_yield
CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_p02_p01_yield_unique_key
ON fact_p02_p01_yield (p02_batch, p01_batch);

-- fact_target
CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_target_unique_key
ON fact_target (salesman_name, semester, year);

-- fact_inventory (if not aggregated)
CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_inventory_unique_key
ON fact_inventory (material_code, plant_code, batch, snapshot_date);
```

### 2.3 Implementation for RAW Tables (Using row_hash)

```sql
-- All raw tables already have row_hash column

-- raw_cooispi
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_cooispi_row_hash
ON raw_cooispi (row_hash);

-- raw_mb51
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_mb51_row_hash
ON raw_mb51 (row_hash);

-- raw_zrmm024
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_zrmm024_row_hash
ON raw_zrmm024 (row_hash);

-- raw_zrsd002
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_zrsd002_row_hash
ON raw_zrsd002 (row_hash);

-- raw_zrsd004
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_zrsd004_row_hash
ON raw_zrsd004 (row_hash);

-- raw_zrsd006
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_zrsd006_row_hash
ON raw_zrsd006 (row_hash);

-- raw_zrfi005
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_zrfi005_row_hash
ON raw_zrfi005 (row_hash);

-- raw_target
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_target_row_hash
ON raw_target (row_hash);
```

**Effect:** Any INSERT that would create duplicates will **fail immediately** with error:
```
IntegrityError: duplicate key value violates unique constraint
```

---

## PART 3: APPLICATION-LEVEL PREVENTION

### 3.1 Fix Transform Pipeline - TRUNCATE Before Load

**File:** `src/etl/transform.py`

**Current Problem:** Transform appends to tables without clearing first.

**Solution:** Add truncate before inserting.

```python
# In Transformer class, before each fact table insert:

def transform_billing(self):
    """Transform billing data"""
    # TRUNCATE FIRST to prevent duplicates
    self.session.execute(text("TRUNCATE TABLE fact_billing"))
    self.session.commit()
    
    # Then insert fresh data
    raw_data = self.session.query(RawZrsd002).all()
    for row in raw_data:
        # ... transform logic ...
        self.session.add(fact_row)
    self.session.commit()

# Apply same pattern to ALL transform methods:
# - transform_production() → TRUNCATE fact_production
# - transform_delivery() → TRUNCATE fact_delivery
# - transform_lead_time() → TRUNCATE fact_lead_time
# - transform_ar_aging() → TRUNCATE fact_ar_aging
# - etc.
```

### 3.2 Fix Loaders - Upsert Instead of Insert

**File:** `src/etl/loaders.py`

**Current Problem:** Loaders always INSERT, even if data already exists.

**Solution:** Use `ON CONFLICT DO NOTHING` for raw tables.

```python
# Example for Zrsd002Loader

def load(self):
    """Load with duplicate prevention"""
    df = self.read_excel()
    
    for _, row in df.iterrows():
        row_data = row.to_dict()
        row_hash = hashlib.md5(json.dumps(row_data, sort_keys=True).encode()).hexdigest()
        
        # Use raw SQL with ON CONFLICT to prevent duplicates
        self.session.execute(text("""
            INSERT INTO raw_zrsd002 (raw_data, row_hash, billing_document, billing_item)
            VALUES (:raw_data, :row_hash, :billing_document, :billing_item)
            ON CONFLICT (row_hash) DO NOTHING
        """), {
            'raw_data': json.dumps(row_data),
            'row_hash': row_hash,
            'billing_document': row_data.get('Billing Document'),
            'billing_item': row_data.get('Billing Item')
        })
    
    self.session.commit()
```

**Requires:** UNIQUE constraints on row_hash (see Part 2.3).

### 3.3 Add Pre-Load Validation

**File:** `src/etl/loaders.py`

Add validation checks BEFORE loading:

```python
class BaseLoader:
    def validate_before_load(self, df):
        """Validate data before loading to database"""
        
        # Check 1: No duplicates in Excel file itself
        if df.duplicated().any():
            dup_count = df.duplicated().sum()
            logger.warning(f"Found {dup_count} duplicates in Excel file!")
            # Remove duplicates
            df = df.drop_duplicates()
        
        # Check 2: Check if data already exists in DB
        existing_count = self.session.query(self.model).count()
        if existing_count > 0:
            logger.warning(f"Table {self.model.__tablename__} already has {existing_count} rows")
            logger.warning("Will use UPSERT to prevent duplicates")
        
        # Check 3: Validate row count is reasonable
        if len(df) == 0:
            raise ValueError("Excel file is empty!")
        
        logger.info(f"Validation passed: {len(df)} rows to load")
        return df
```

---

## PART 4: MONITORING & ALERTS

### 4.1 Automated Duplicate Detection Job

**File:** `check_duplicates_daily.py` (new file)

```python
"""
Daily duplicate check - runs as cron job
Sends alert if duplicates found
"""

from sqlalchemy import create_engine, text
import os
from datetime import datetime

def check_all_tables():
    """Check all tables for duplicates"""
    
    tables_to_check = {
        'fact_billing': ['billing_document', 'billing_item'],
        'fact_production': ['order_number', 'batch'],
        'fact_lead_time': ['order_number', 'batch'],
        'fact_p02_p01_yield': ['p02_batch', 'p01_batch'],
        'fact_target': ['salesman_name', 'semester', 'year'],
        'raw_mb51': ['row_hash'],
        # ... all other tables
    }
    
    duplicates_found = []
    
    for table, keys in tables_to_check.items():
        result = conn.execute(text(f"""
            SELECT COUNT(*) - COUNT(DISTINCT ({','.join(keys)}))
            FROM {table}
        """))
        dup_count = result.scalar()
        
        if dup_count > 0:
            duplicates_found.append({
                'table': table,
                'count': dup_count
            })
    
    if duplicates_found:
        # Send alert email/Slack
        send_alert(duplicates_found)
        return False
    
    return True

# Run daily at 6 AM
if __name__ == '__main__':
    check_all_tables()
```

### 4.2 Add to CI/CD Pipeline

**File:** `.github/workflows/data-quality.yml` (if using GitHub Actions)

```yaml
name: Data Quality Check

on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM
  workflow_dispatch:

jobs:
  check-duplicates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Check for duplicates
        run: |
          python check_duplicates_daily.py
      - name: Alert on failure
        if: failure()
        run: |
          # Send notification
```

---

## PART 5: AUTOMATED TESTING

### 5.1 Data Quality Tests

**File:** `tests/test_data_quality.py` (new file)

```python
"""
Data quality tests - run after every ETL
"""

import pytest
from sqlalchemy import create_engine, text

class TestDataQuality:
    
    def test_no_duplicates_fact_billing(self, db_session):
        """Ensure fact_billing has no duplicates"""
        result = db_session.execute(text("""
            SELECT COUNT(*) - COUNT(DISTINCT (billing_document, billing_item))
            FROM fact_billing
        """))
        dup_count = result.scalar()
        assert dup_count == 0, f"Found {dup_count} duplicates in fact_billing!"
    
    def test_no_duplicates_fact_production(self, db_session):
        """Ensure fact_production has no duplicates"""
        result = db_session.execute(text("""
            SELECT COUNT(*) - COUNT(DISTINCT (order_number, batch))
            FROM fact_production
        """))
        dup_count = result.scalar()
        assert dup_count == 0, f"Found {dup_count} duplicates in fact_production!"
    
    def test_no_duplicates_raw_tables(self, db_session):
        """Ensure all raw tables have no duplicate row_hash"""
        raw_tables = [
            'raw_cooispi', 'raw_mb51', 'raw_zrmm024',
            'raw_zrsd002', 'raw_zrsd004', 'raw_zrsd006',
            'raw_zrfi005', 'raw_target'
        ]
        
        for table in raw_tables:
            result = db_session.execute(text(f"""
                SELECT COUNT(*) - COUNT(DISTINCT row_hash)
                FROM {table}
            """))
            dup_count = result.scalar()
            assert dup_count == 0, f"Found {dup_count} duplicates in {table}!"
    
    def test_all_fact_tables_have_data(self, db_session):
        """Ensure fact tables are not empty after transform"""
        fact_tables = [
            'fact_billing', 'fact_production', 'fact_delivery',
            'fact_lead_time', 'fact_ar_aging'
        ]
        
        for table in fact_tables:
            count = db_session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            assert count > 0, f"{table} is empty!"
```

### 5.2 Run Tests After Every Transform

**File:** `src/etl/transform.py`

```python
def run_transform():
    """Run transform with validation"""
    transformer = Transformer()
    transformer.transform_all()
    
    # Run data quality tests
    import subprocess
    result = subprocess.run(['pytest', 'tests/test_data_quality.py', '-v'])
    
    if result.returncode != 0:
        logger.error("Data quality tests FAILED!")
        # Send alert
        # Optionally rollback transform
    else:
        logger.info("Data quality tests PASSED ✓")
```

---

## PART 6: IMPLEMENTATION PLAN

### Phase 1: Immediate (Today)

1. ✅ **Audit Complete** - Found 3 tables with duplicates
2. ⬜ **Fix Duplicates** - Run SQL to remove 2,833 duplicate rows
3. ⬜ **Add UNIQUE Constraints** - Create indexes to prevent future duplicates

**Files to Create:**
- `fix_remaining_duplicates.py` - Auto-fix script for 3 tables

**Time Estimate:** 1 hour

### Phase 2: Short-term (This Week)

1. ⬜ **Fix Transform Pipeline** - Add TRUNCATE before each fact table insert
2. ⬜ **Fix Loaders** - Add ON CONFLICT DO NOTHING
3. ⬜ **Add Validation** - Pre-load checks in loaders

**Files to Modify:**
- `src/etl/transform.py` - Add truncate logic
- `src/etl/loaders.py` - Add upsert + validation

**Time Estimate:** 4 hours

### Phase 3: Medium-term (Next 2 Weeks)

1. ⬜ **Create Tests** - Data quality test suite
2. ⬜ **Add Monitoring** - Daily duplicate check job
3. ⬜ **Documentation** - Update README with data quality standards

**Files to Create:**
- `tests/test_data_quality.py`
- `check_duplicates_daily.py`
- `docs/DATA_QUALITY.md`

**Time Estimate:** 8 hours

### Phase 4: Long-term (Ongoing)

1. ⬜ **CI/CD Integration** - Automated testing on every deploy
2. ⬜ **Performance Optimization** - Bulk operations, better indexes
3. ⬜ **Data Lineage Tracking** - Track transform runs and data freshness

---

## PART 7: VALIDATION CHECKLIST

After implementing all fixes, verify:

### Database State:
- [ ] fact_billing: 0 duplicates ✓
- [ ] fact_production: 0 duplicates ✓
- [ ] fact_delivery: 0 duplicates ✓
- [ ] fact_lead_time: 0 duplicates ✓
- [ ] fact_p02_p01_yield: 0 duplicates
- [ ] fact_target: 0 duplicates
- [ ] All raw tables: 0 duplicates
- [ ] UNIQUE constraints exist on all tables

### Application:
- [ ] Transform truncates before inserting
- [ ] Loaders use upsert (ON CONFLICT)
- [ ] Pre-load validation works
- [ ] Tests pass after transform
- [ ] Daily monitoring job runs

### Functionality:
- [ ] Revenue numbers correct (277B VND)
- [ ] No NULL customer names
- [ ] All dashboards show data
- [ ] Date filters work on all APIs
- [ ] AR Collection displays correctly

---

## CONCLUSION

**Before:**
- 5 tables with duplicates
- 24,754 total duplicate rows
- No prevention mechanisms
- Manual detection required

**After (Full Implementation):**
- 0 duplicates in any table
- Database-level prevention (UNIQUE constraints)
- Application-level prevention (TRUNCATE + UPSERT)
- Automated testing
- Daily monitoring
- **Duplicates IMPOSSIBLE going forward**

**Next Steps:**
1. Run `fix_remaining_duplicates.py` to clean 3 tables
2. Apply UNIQUE constraints
3. Update transform.py and loaders.py
4. Test thoroughly
5. Deploy with confidence! 🚀
