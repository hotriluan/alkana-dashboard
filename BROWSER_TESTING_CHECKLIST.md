# V4 Smart Ingestion - Browser Testing Checklist

## ✅ Completed (Backend Validation)
- [x] Extract actual column headers from all 12 demo files
- [x] Update all 9 detection signatures with verified column names
- [x] Fix MB51 vs ZRMM024 misclassification
- [x] Synchronize test scripts with TypeScript signatures
- [x] Achieve 100% detection accuracy (12/12 files)
- [x] Verify all signatures with final_validation.py

## ⏳ Pending (Browser Testing - User Action Required)

### 1. ZRSD006 (Product Hierarchy) - Priority: HIGH
Test with: `11.XLSX`, `12.XLSX`, `13.XLSX`, `15.XLSX`

**Expected Behavior:**
- Drop file → Auto-detect as "Product Hierarchy Master"
- Auto-upload without period modal
- Route to `/api/v3/yield/upload-master-data`
- Trigger auto-population of `dim_product_hierarchy` table
- Show upload status with rows loaded/updated/skipped

**Validation:**
```sql
-- Check dim_product_hierarchy populated
SELECT COUNT(*) FROM dim_product_hierarchy;

-- Check upload history
SELECT file_name, file_type, status, rows_loaded, rows_skipped 
FROM upload_history 
WHERE file_type = 'ZRSD006' 
ORDER BY uploaded_at DESC 
LIMIT 4;
```

### 2. ZRPP062 (Production Yield) - Priority: HIGH
Test with: `zrpp062.XLSX`

**Expected Behavior:**
- Drop file → Auto-detect as "Production Yield Result"
- **Show period modal** (Month/Year selector)
- User selects month and year
- Route to `/api/v3/yield/upload` with month/year parameters
- Show upload status

**Validation:**
```sql
SELECT file_name, file_type, status, rows_loaded 
FROM upload_history 
WHERE file_type = 'ZRPP062' 
ORDER BY uploaded_at DESC 
LIMIT 1;
```

### 3. ZRSD002 (Sales Orders) - Priority: MEDIUM
Test with: `zrsd002.xlsx`

**Expected Behavior:**
- Drop file → Auto-detect as "Sales Orders"
- Auto-upload without modal
- Route to `/api/v1/upload`
- Show upload status

### 4. ZRSD004 (Delivery Report) - Priority: MEDIUM
Test with: `zrsd004.XLSX`

**Expected Behavior:**
- Drop file → Auto-detect as "Delivery"
- Auto-upload
- Show upload status

### 5. ZRFI005 (AR Aging Report) - Priority: MEDIUM
Test with: `ZRFI005.XLSX`

**Expected Behavior:**
- Drop file → Auto-detect as "AR Aging Report"
- Auto-upload
- Show upload status

### 6. MB51 (Material Movements) - Priority: HIGH (Regression Test)
Test with: `mb51.XLSX`

**Expected Behavior:**
- Drop file → Auto-detect as "Material Movements" (NOT ZRMM024)
- Auto-upload
- Show upload status

**Critical Validation:**
- Console logs should show: "✅ Detected as MB51"
- Should NOT show: "Detected as ZRMM024"

### 7. ZRMM024 (MRP Controller) - Priority: HIGH (Regression Test)
Test with: `zrmm024.XLSX`

**Expected Behavior:**
- Drop file → Auto-detect as "MRP Controller"
- Auto-upload
- Show upload status

### 8. COOISPI (Production Orders) - Priority: MEDIUM
Test with: `cooispi.XLSX`

**Expected Behavior:**
- Drop file → Auto-detect as "Production Orders"
- Auto-upload
- Show upload status

### 9. TARGET (Sales Targets) - Priority: LOW
Test with: `target.xlsx`

**Expected Behavior:**
- Drop file → Auto-detect as "Sales Targets"
- Auto-upload
- Show upload status

## Browser Testing Steps (Per File)

1. **Open Data Upload Page**
   - Navigate to `/data-upload`
   - Verify file upload area visible

2. **Drop File**
   - Drag file from `demodata/` to upload area
   - **Check browser console** for detection logs:
     ```
     🔍 Excel headers detected: [column names]
     - Checking "Column1": ✓
     - Checking "Column2": ✓
     Rule ZRSD006: 4/4 matches (threshold: 3)
     ✅ Detected as ZRSD006
     ```

3. **Verify Period Modal (ZRPP062 only)**
   - Modal should appear with month/year selectors
   - Select values and click upload

4. **Monitor Upload Status**
   - Check upload progress indicator
   - Verify success message shows correct stats
   - Check Upload History table updated

5. **Validate Database**
   - Run SQL queries to verify data loaded
   - Check upload_history record created

## Known Issues to Watch For

❌ **If file detected as "Unknown":**
- Check browser console for signature matching logs
- Verify column names match expected signatures
- Report actual column names found

❌ **If MB51 detected as ZRMM024:**
- This indicates signature rule ordering issue
- Check console logs for match counts
- Verify fileDetection.ts has correct ZRMM024 signature

❌ **If ZRPP062 modal doesn't appear:**
- Check `requiresPeriod: true` flag in detection rule
- Verify handleFileDropped sets detectedFile state
- Check console for errors

❌ **If upload fails with 404:**
- Check endpoint URL in network tab
- Verify backend server running on localhost:8000
- Check endpoint path matches detection rule

## Success Criteria

✅ All 12 files detect correctly with proper file type
✅ ZRPP062 shows period modal, others auto-upload
✅ MB51 NOT misclassified as ZRMM024
✅ Upload History records created with correct stats
✅ ZRSD006 triggers dim_product_hierarchy auto-population
✅ No console errors or warnings

## Reporting Results

Please report:
1. File name tested
2. Detected file type (from console logs)
3. Upload status (success/fail)
4. Any errors or unexpected behavior
5. Screenshot of Upload History table

Format:
```
✅ 11.XLSX → ZRSD006 → Uploaded successfully (326 loaded, 2 skipped)
❌ mb51.XLSX → ZRMM024 → Incorrect detection (should be MB51)
```
