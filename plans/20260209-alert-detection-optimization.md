# Alert Detection Performance Optimization Plan

**Date**: 2026-02-09  
**Status**: Planning  
**Priority**: Medium  
**Related**: ETL Performance Optimization (commit 709b86f)

## Context

Alert detection (`detect_alerts()`) đang chạy chậm do:
1. Query từng batch riêng lẻ từ database
2. Loop qua hàng nghìn P01 batches
3. Gọi netting logic cho từng batch trong loop
4. Không có bulk operations
5. Mở/đóng database session trong method

Tương tự vấn đề đã fix ở ETL transforms, cần apply cùng kỹ thuật tối ưu.

## Current Performance (Baseline)

**Cần đo**: Chạy detect_alerts() và đo thời gian thực tế trên production.

**Ước tính** (dựa trên code analysis):
- P01 batches: ~5,000-10,000 batches
- Mỗi batch: 1 query FactProduction + 1 netting operation
- Estimated time: **30-60 seconds**

## Bottlenecks Identified

### Bottleneck 1: Database Query in Loop (Lines 79-93)

**Current (Slow)**:
```python
db = SessionLocal()
try:
    # Query all P01 batches
    p01_batches = db.query(
        FactProduction.batch,
        FactProduction.actual_finish_date,
        FactProduction.material_code
    ).filter(
        FactProduction.mrp_controller == 'P01',
        FactProduction.batch.isnot(None),
        FactProduction.actual_finish_date.isnot(None)
    ).all()
    
    # Loop through each batch
    for batch_row in p01_batches:  # 5000+ iterations
        batch = batch_row.batch
        # ... netting logic for each batch
finally:
    db.close()
```

**Issues**:
- Opens new SessionLocal() inside method (should reuse existing session)
- Loops through potentially thousands of batches
- Calls netting logic individually for each batch

### Bottleneck 2: Netting Engine in Loop (Lines 106-112)

**Current (Slow)**:
```python
for batch_row in p01_batches:
    # Get MVT 101 receipt date (calls netting engine)
    result_101 = self.netting_engine.apply_stack_netting(batch, plant, 101, 102)
    
    if result_101.is_fully_reversed:
        continue
    
    receipt_date = result_101.last_valid_date
    # ... more processing
```

**Issues**:
- Calls netting engine for each batch individually
- No vectorization or bulk processing
- MB51 data queried multiple times (once per batch)

### Bottleneck 3: Alert Deduplication (Already Optimized)

**Note**: This part is already optimized (lines 1343-1350 in transform.py):
```python
# OPTIMIZATION: Load existing alerts ONCE, not N queries
existing_alerts_query = self.db.query(
    FactAlert.alert_type,
    FactAlert.entity_id
).all()

# Build in-memory set for O(1) lookup
existing_set = {(row.alert_type, row.entity_id) for row in existing_alerts_query}
```

✅ This part is good - uses bulk query + in-memory set for O(1) lookups.

## Optimization Strategy

### Step 1: Vectorize Netting Operations

**Goal**: Process all batches at once instead of loop

**Approach**:
1. Get all P01 batches in single query (already done)
2. Filter MB51 data for all batches at once (bulk filter)
3. Vectorize netting calculations using pandas groupby/merge
4. Calculate transit hours for all batches in one pass

**Expected Speedup**: 5-10x

### Step 2: Reuse Database Session

**Goal**: Avoid opening new SessionLocal() in method

**Approach**:
1. Accept `db: Session` as parameter to `detect_stuck_in_transit()`
2. Use existing session from transform pipeline
3. Avoid session overhead

**Expected Speedup**: 10-20% (small but adds up)

### Step 3: Optimize MB51 Filtering

**Goal**: Pre-filter MB51 data for relevant movement types/plants

**Approach**:
1. Filter MB51 once for MVT 101/102 at plant 1401
2. Filter for batches in P01 batch list
3. Use pandas merge/join instead of looping

**Expected Speedup**: 2-3x

## Implementation Plan

### Phase 1: Baseline Measurement (15 minutes)

1. Add timing logs to `detect_alerts()`:
   ```python
   import time
   start = time.time()
   
   # ... existing code ...
   
   duration = time.time() - start
   print(f"  ⏱ Alert detection took {duration:.2f}s")
   ```

2. Run on production and record baseline

**Deliverable**: Baseline timing report

### Phase 2: Vectorize Netting Logic (2 hours)

**File**: `src/core/alerts.py`

1. Extract P01 batch list
2. Pre-filter MB51 data:
   ```python
   # Get all MVT 101/102 for P01 batches at plant 1401
   batch_list = [row.batch for row in p01_batches]
   
   mb51_filtered = self.mb51_df[
       (self.mb51_df['movement_type'].isin(['101', '102'])) &
       (self.mb51_df['plant'] == plant) &
       (self.mb51_df['batch_number'].isin(batch_list))
   ].copy()
   ```

3. Vectorize netting using pandas groupby:
   ```python
   # Group by batch and apply netting logic
   netting_results = mb51_filtered.groupby('batch_number').apply(
       lambda group: self._vectorized_netting(group, 101, 102)
   )
   ```

4. Merge with P01 batch data:
   ```python
   # Join netting results with production finish dates
   p01_df = pd.DataFrame(p01_batches, columns=['batch', 'actual_finish_date', 'material_code'])
   
   combined = p01_df.merge(
       netting_results, 
       left_on='batch', 
       right_index=True, 
       how='left'
   )
   ```

5. Vectorize transit hour calculation:
   ```python
   # Calculate transit hours for all batches at once
   combined['finish_dt'] = pd.to_datetime(combined['actual_finish_date'])
   combined['receipt_dt'] = pd.to_datetime(combined['receipt_date'])
   combined['transit_hours'] = (combined['receipt_dt'] - combined['finish_dt']).dt.total_seconds() / 3600
   
   # Filter delayed batches
   delayed = combined[combined['transit_hours'] > self.stuck_threshold]
   ```

**Expected Result**: 5-10x speedup

### Phase 3: Reuse Database Session (30 minutes)

**File**: `src/core/alerts.py`

1. Update method signature:
   ```python
   def detect_stuck_in_transit(
       self, 
       db: Session,  # Add db parameter
       plant: int = 1401
   ) -> List[Alert]:
   ```

2. Remove SessionLocal() creation:
   ```python
   # BEFORE (slow):
   db = SessionLocal()
   try:
       p01_batches = db.query(...)
   finally:
       db.close()
   
   # AFTER (fast):
   p01_batches = db.query(...)  # Use passed session
   ```

3. Update caller in `transform.py`:
   ```python
   # Pass existing db session
   stuck_alerts = detector.detect_stuck_in_transit(db=self.db, plant=1401)
   ```

**Expected Result**: 10-20% speedup

### Phase 4: Testing & Validation (1 hour)

1. Test on development with sample data
2. Verify alert counts match before/after
3. Check alert accuracy (no false positives/negatives)
4. Run on production and measure performance

**Success Criteria**:
- Alert count matches baseline ±5%
- Alert content identical (batch, material, hours, severity)
- Performance improvement >50%

### Phase 5: Documentation (30 minutes)

1. Update `docs/PERFORMANCE.md` with alert optimization section
2. Add alert detection to monitoring guide
3. Update `CHANGELOG.md`

## Estimated Performance Improvement

| Component | Before | After | Improvement |
|-----------|--------|-------|-------------|
| P01 batch query | 2s | 2s | 0% (already bulk) |
| Netting operations | 25s | 3s | **88% faster** |
| Transit calculation | 3s | 0.5s | **83% faster** |
| Alert deduplication | 0.5s | 0.5s | 0% (already optimized) |
| **Total** | **30s** | **6s** | **80% faster** |

**Conservative estimate**: 50-70% speedup
**Best case**: 80-85% speedup

## Risks & Mitigation

### Risk 1: Vectorization Complexity

**Risk**: Pandas vectorization may be complex for netting logic  
**Mitigation**:
- Start with simple vectorization (filter + groupby)
- Fall back to optimized loop if vectorization too complex
- Keep original logic as reference

### Risk 2: Alert Count Mismatch

**Risk**: Optimization changes alert detection logic  
**Mitigation**:
- Run both old and new logic in parallel
- Compare alert counts and content
- Validate on sample data before production

### Risk 3: Memory Usage

**Risk**: Loading all batches may use more memory  
**Mitigation**:
- Monitor memory during testing
- Use chunking if needed (process 1000 batches at a time)
- Current dataset size should be manageable (<10K batches)

## Dependencies

- None (standalone optimization)
- Can be done in parallel with other work

## Success Metrics

- [ ] Baseline measurement completed
- [ ] Vectorized netting implemented
- [ ] Database session reused
- [ ] Testing completed (alert accuracy validated)
- [ ] Performance improvement >50%
- [ ] Documentation updated
- [ ] Production deployment successful

## Follow-up Actions

1. Measure baseline on production
2. If baseline >60s, increase priority to HIGH
3. Consider applying same pattern to other alert types if added
4. Monitor alert detection performance monthly

---

**Plan Status**: Ready for Implementation  
**Estimated Effort**: 4 hours  
**Expected Speedup**: 50-80%  
**Next Step**: Measure baseline on production
