# 🚀 AR AGING FIX - QUICK START GUIDE

## TÓM TẮT (VIETNAMESE SUMMARY)

**Vấn đề:** Biểu đồ AR Aging hiển thị giá trị sai 211 Tỷ thay vì 26.7 Tỷ (sai 7.95 lần)

**Nguyên nhân:** Thiếu lọc theo `snapshot_date` → hệ thống cộng dồn 8 ngày snapshot

**Đã sửa:**
- ✅ Backend API: Thêm `snapshot_date` parameter và WHERE clause
- ✅ Frontend Service: Truyền snapshot parameter đến API
- ✅ Frontend Component: Kết nối dropdown snapshot với API

**Kết quả:** Biểu đồ giờ hiển thị đúng 26.7 Tỷ cho snapshot 2026-01-19

---

## WHAT WAS FIXED

### Problem Statement
- **UI Displayed:** 211 Billion VND (1-30 Days bucket)
- **Actual Value:** 26.7 Billion VND
- **Cause:** Missing `WHERE snapshot_date = :date` in SQL query
- **Impact:** All 8 snapshots summed together (7.95x inflation)

### Solution Applied
Three files modified to add snapshot date filtering:

1. **Backend:** [src/api/routers/ar_aging.py](src/api/routers/ar_aging.py)
   - Added `snapshot_date` parameter to `/by-bucket` endpoint
   - Added SQL WHERE clause to filter by snapshot
   - Defaults to latest snapshot if not provided

2. **Frontend Service:** [web/src/services/api.ts](web/src/services/api.ts)
   - Updated `getByBucket()` to accept `snapshotDate` parameter
   - Pass snapshot to API request

3. **Frontend Component:** [web/src/pages/ArAging.tsx](web/src/pages/ArAging.tsx)
   - Pass `selectedSnapshot` from dropdown to API

---

## HOW TO VERIFY

### Step 1: Restart Services

**Backend:**
```bash
cd c:\dev\alkana-dashboard\src
uvicorn api.main:app --reload
```

**Frontend:**
```bash
cd c:\dev\alkana-dashboard\web
npm run dev
```

### Step 2: Open Dashboard
Navigate to: http://localhost:5173/ar-aging

### Step 3: Verify Values

**Select snapshot: "2026-01-19"**

Expected values:
- Total AR: ~44.1 Billion ✅
- 1-30 Days: ~26.7 Billion ✅ (NOT 211B)
- 31-60 Days: ~10.2 Billion ✅ (NOT 82B)

**Change snapshot to older date (e.g., "2026-01-16")**
- Values should update to that snapshot's data
- Should be slightly different from 2026-01-19

### Step 4: Run Verification Script (Optional)

```bash
python verify_ar_aging_fix.py
```

Expected output:
```
✅ VERIFICATION PASSED
   - Snapshot filtering works correctly
   - Buckets sum to total_target
   - Data inflation prevented
```

---

## FILES CHANGED

| File | Lines Changed | Purpose |
|------|---------------|---------|
| [src/api/routers/ar_aging.py](src/api/routers/ar_aging.py) | ~15 | Add snapshot filtering to backend |
| [web/src/services/api.ts](web/src/services/api.ts) | 3 | Pass snapshot to API |
| [web/src/pages/ArAging.tsx](web/src/pages/ArAging.tsx) | 1 | Connect dropdown to API |

## DOCUMENTATION CREATED

| File | Purpose |
|------|---------|
| [AR_AGING_AUDIT_REPORT.md](AR_AGING_AUDIT_REPORT.md) | Full forensic audit and root cause analysis |
| [AR_AGING_FIX_SUMMARY.md](AR_AGING_FIX_SUMMARY.md) | Implementation summary and testing checklist |
| [audit_ar_aging_snapshot.py](audit_ar_aging_snapshot.py) | Database forensics tool |
| [verify_ar_aging_fix.py](verify_ar_aging_fix.py) | Verification testing script |
| [AR_AGING_FIX_QUICKSTART.md](AR_AGING_FIX_QUICKSTART.md) | This guide |

---

## TECHNICAL DETAILS

### Before (Incorrect Query)
```python
# NO snapshot filter - aggregates ALL snapshots
SELECT SUM(target_1_30) FROM fact_ar_aging
# Result: 211,996,256,074 VND ❌ (8 snapshots combined)
```

### After (Correct Query)
```python
# WITH snapshot filter - single snapshot only
SELECT SUM(target_1_30) FROM fact_ar_aging 
WHERE snapshot_date = '2026-01-19'
# Result: 26,673,248,426 VND ✅ (single snapshot)
```

### Data in Database
```
Snapshot      | 1-30 Days Amount
--------------|-----------------
2026-01-19    | 26,673,248,426 VND ← Latest (now shown in UI)
2026-01-16    | 26,658,619,178 VND
2026-01-14    | 26,601,515,708 VND
2026-01-13    | 26,532,970,237 VND
2026-01-12    | 26,500,153,328 VND
2026-01-09    | 26,442,397,757 VND
2026-01-08    | 26,367,268,301 VND
2026-01-07    | 26,220,083,139 VND
--------------|-----------------
TOTAL (8)     | 211,996,256,074 VND ← What was shown before (WRONG!)
```

---

## SUPPORT

**If values still look wrong after restart:**

1. Check browser console for errors (F12)
2. Check backend terminal for API errors
3. Verify snapshot dropdown shows available dates
4. Try hard refresh: Ctrl+Shift+R (Chrome) or Ctrl+F5

**If issues persist:**
- Review [AR_AGING_AUDIT_REPORT.md](AR_AGING_AUDIT_REPORT.md) for technical details
- Run `python audit_ar_aging_snapshot.py` to check database
- Check that all 3 files were saved correctly

---

## SUCCESS CRITERIA

✅ AR Aging dashboard loads without errors  
✅ Snapshot dropdown shows available dates  
✅ 1-30 Days bucket shows ~26.7B VND (not 211B)  
✅ Changing snapshot updates chart values  
✅ Total AR card matches bucket sum (~44B)  

---

**Status:** READY TO TEST  
**Date:** January 20, 2026  
**Agent:** AI Development Agent (ClaudeKit)
