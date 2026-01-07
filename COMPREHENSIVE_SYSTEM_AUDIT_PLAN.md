# COMPREHENSIVE SYSTEM AUDIT PLAN

## Issues Identified

### 1. Date Filters Not Working Universally
- ✅ Working: Lead Time Analysis, Alert Monitor, Executive Dashboard
- ❌ Not Working: AR Collection, Inventory, MTO Orders, Production Yield, Sales Performance

### 2. AR Collection Dashboard Empty
- No data displayed
- Need to check: Backend API, database queries, fact_ar_aging table

### 3. Data Inflated (Much Larger Than Reality)
- Likely cause: Duplicate data from transform running multiple times
- Need to verify: All fact tables for duplicates

### 4. Transform Performance Issues
- Very slow execution
- Need to optimize: Batch processing, indexing, query efficiency

### 5. zrsd004.XLSX Header Detection Failure
- File has headers but loader reads as 'Unnamed: 0', 'Unnamed: 1'...
- Excel file may have formatting issues or merged cells

## Audit Strategy

### Phase 1: DATABASE LAYER AUDIT
**Goal**: Verify data integrity and identify duplicates

```sql
-- Check 1: Row counts in all tables
-- Check 2: Duplicate detection in fact tables
-- Check 3: Validate business key uniqueness
-- Check 4: Check for NULL critical fields
-- Check 5: Verify date ranges are reasonable
```

**Actions**:
1. Query all fact tables for row counts
2. Check for duplicates using business keys
3. Compare against Excel source files
4. Identify orphaned records (no matching raw data)

### Phase 2: LOADER & ETL AUDIT
**Goal**: Fix data loading and transformation issues

**zrsd004.XLSX Header Issue**:
- Problem: pandas.read_excel() not detecting headers correctly
- Possible causes:
  - Empty rows before header
  - Merged cells in header row
  - Special characters or formatting
  - Excel workbook has multiple sheets
  
**Actions**:
1. Manually inspect zrsd004.XLSX structure
2. Update loader to handle edge cases
3. Add header validation before processing
4. Log warnings for malformed files

**Transform Performance**:
- Current issues:
  - No batch processing
  - Full table scans
  - Missing indexes on foreign keys
  - Nested loops instead of bulk operations
  
**Actions**:
1. Add bulk insert/update operations
2. Create indexes on frequently queried columns
3. Use EXPLAIN ANALYZE to find slow queries
4. Implement progress logging

### Phase 3: BACKEND API AUDIT
**Goal**: Ensure all endpoints support date filtering

**API Endpoints to Check**:
```
✅ /api/executive/*           - Date filters working
✅ /api/lead-time/*           - Date filters working  
✅ /api/alerts/*              - Date filters working
❌ /api/ar-aging/*            - Need to verify
❌ /api/inventory/*           - Need to add date filters
❌ /api/mto-orders/*          - Need to add date filters
❌ /api/production-yield/*    - Need to add date filters
❌ /api/sales/*               - Need to add date filters
```

**Actions**:
1. Grep search for all API route files
2. Check each endpoint for date parameter handling
3. Add date filtering to missing endpoints
4. Standardize date parameter names (from_date, to_date)

### Phase 4: FRONTEND AUDIT
**Goal**: Verify UI components send correct parameters

**Actions**:
1. Check DateRangePicker component integration
2. Verify API call includes date parameters
3. Check for hardcoded date values
4. Test each dashboard with date filtering

### Phase 5: DATA VALIDATION & TESTING
**Goal**: Prevent future data quality issues

**Actions**:
1. Add unique constraints on business keys
2. Create automated data quality tests
3. Add pre-load duplicate detection
4. Implement row count validation (Excel vs DB)

## Execution Plan

### Step 1: Database Health Check (15 min)
- Run comprehensive audit script
- Identify all duplicates
- Document row counts vs expected

### Step 2: Fix Critical Data Issues (30 min)
- Truncate duplicate fact tables
- Re-transform from clean raw data
- Validate results

### Step 3: Fix zrsd004 Loader (20 min)
- Inspect Excel file manually
- Update loader header detection
- Add validation logic
- Re-load zrsd004

### Step 4: Fix AR Collection Empty Issue (15 min)
- Check fact_ar_aging table
- Verify API endpoint
- Check frontend data fetching
- Fix root cause

### Step 5: Add Date Filters to All APIs (45 min)
- Inventory API
- MTO Orders API
- Production Yield API
- Sales Performance API
- Standardize implementation

### Step 6: Performance Optimization (30 min)
- Add database indexes
- Optimize transform queries
- Add bulk operations
- Implement caching

### Step 7: Add Prevention Mechanisms (20 min)
- Unique constraints
- Pre-load validation
- Automated tests
- Documentation

## Expected Outcomes

1. ✅ All fact tables have NO duplicates
2. ✅ All Excel files load correctly with proper headers
3. ✅ All dashboards support date filtering
4. ✅ AR Collection displays data correctly
5. ✅ Transform completes in < 2 minutes
6. ✅ Future uploads prevented from creating duplicates
7. ✅ Automated tests catch data quality issues

## Technical Debt to Address

1. **No foreign key constraints** - Add referential integrity
2. **No data validation in loaders** - Add schema validation
3. **No transaction management** - Wrap operations in transactions
4. **No error recovery** - Add rollback mechanisms
5. **No monitoring** - Add logging and metrics
6. **No documentation** - Add inline comments and README

## Risk Mitigation

- Backup database before major operations
- Test on subset of data first
- Validate after each step
- Keep audit trail of changes
- Document all fixes
