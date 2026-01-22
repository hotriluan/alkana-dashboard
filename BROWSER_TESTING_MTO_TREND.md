# 🧪 MTO TREND CHART - BROWSER TESTING CHECKLIST

**Feature:** Dynamic Completion Rate Trend Chart  
**Component:** MTO Orders Dashboard  
**Date:** January 20, 2026

---

## ✅ PRE-FLIGHT CHECKS

- [ ] Backend API running (`uvicorn api.main:app --reload`)
- [ ] Frontend dev server running (`npm run dev`)
- [ ] Database contains MTO order data
- [ ] User authenticated and logged in

---

## 📋 FUNCTIONAL TESTS

### Test 1: Full Year Range (Monthly Display)
**Steps:**
1. Navigate to MTO Orders Dashboard
2. Open Date Range Picker
3. Select: **Start Date = 2025-01-01**, **End Date = 2025-12-31**
4. Click Apply

**Expected Result:**
- ✅ Chart X-Axis shows: **Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec**
- ✅ 12 data points displayed
- ✅ Tooltip shows "Period: Jan", "Period: Feb", etc.
- ✅ Green line (Completed %) and Orange line (Pending %) visible
- ✅ Y-Axis formatted as percentages (0%, 25%, 50%, etc.)

---

### Test 2: Quarter Range (Monthly Display)
**Steps:**
1. Select: **Start Date = 2025-10-01**, **End Date = 2025-12-31**
2. Click Apply

**Expected Result:**
- ✅ Chart X-Axis shows: **Oct, Nov, Dec**
- ✅ 3 data points displayed
- ✅ Chart updates smoothly (no page refresh)

---

### Test 3: Current Month (Weekly Display)
**Steps:**
1. Select: **Start Date = 2026-01-01**, **End Date = 2026-01-20**
2. Click Apply

**Expected Result:**
- ✅ Chart X-Axis shows: **01/01, 08/01, 15/01** (weekly format DD/MM)
- ✅ 2-3 data points displayed (depending on actual data)
- ✅ Format switches from monthly to weekly

---

### Test 4: Default Behavior
**Steps:**
1. Refresh page (F5)
2. Observe initial chart state

**Expected Result:**
- ✅ Date picker defaults to **First Day of Month → Today**
- ✅ Chart displays weekly data for current month
- ✅ No hardcoded "Jan - Jun" labels

---

### Test 5: No Data Scenario
**Steps:**
1. Select a future date range: **Start Date = 2030-01-01**, **End Date = 2030-12-31**
2. Click Apply

**Expected Result:**
- ✅ Chart shows message: **"No trend data available for selected period"**
- ✅ No chart rendering errors
- ✅ Empty state UI displays properly

---

### Test 6: Loading State
**Steps:**
1. Open Network tab in DevTools
2. Throttle network to "Slow 3G"
3. Change date range

**Expected Result:**
- ✅ Chart shows: **"Loading trend data..."** during fetch
- ✅ Smooth transition to data display
- ✅ No layout shift or flicker

---

## 🎨 VISUAL TESTS

### Chart Aesthetics
- [ ] Lines are smooth and visible (2px width)
- [ ] Grid lines are subtle (not distracting)
- [ ] Colors match design:
  - Completed: Green (`#10b981`)
  - Pending: Orange (`#f59e0b`)
- [ ] Dots on data points are visible (4px radius)
- [ ] Legend shows "Completed %" and "Pending %"

### Tooltip Behavior
- [ ] Hover over data points shows tooltip
- [ ] Tooltip displays:
  - "Period: [label]"
  - "Completed: XX%"
  - "Pending: XX%"
- [ ] Tooltip follows cursor smoothly

### Responsive Layout
- [ ] Chart width fills container (responsive)
- [ ] Chart height: 300px (consistent)
- [ ] Works on different screen sizes (desktop, tablet)

---

## 🔄 INTERACTION TESTS

### Date Picker Integration
**Steps:**
1. Change start date only (keep end date)
2. Change end date only (keep start date)
3. Change both dates simultaneously

**Expected Result:**
- ✅ Chart updates on **every date change**
- ✅ Query parameters include both dates
- ✅ React Query cache updates correctly

### Global State Sync
**Steps:**
1. Set date range: 2025-01-01 to 2025-06-30
2. Navigate to different dashboard tab
3. Return to MTO Orders tab

**Expected Result:**
- ✅ Date range persists (stays 2025-01-01 to 2025-06-30)
- ✅ Chart data matches selected range
- ✅ No unnecessary re-fetching

---

## 🛡️ ERROR HANDLING TESTS

### API Failure
**Steps:**
1. Stop backend server
2. Try changing date range

**Expected Result:**
- ✅ Frontend shows error state (graceful degradation)
- ✅ No JavaScript console errors
- ✅ User sees meaningful error message

### Invalid Date Range
**Steps:**
1. Manually test API: `?start_date=invalid&end_date=2025-12-31`

**Expected Result:**
- ✅ Backend returns 400 Bad Request OR defaults to current month
- ✅ Frontend handles invalid response gracefully

---

## 📊 DATA ACCURACY TESTS

### Cross-Reference with Raw Data
**Steps:**
1. Note completion rate for a specific month (e.g., "Oct: 85%")
2. Query database directly:
   ```sql
   SELECT 
     COUNT(*) FILTER (WHERE status = 'COMPLETE') * 100.0 / COUNT(*) 
   FROM view_mto_orders 
   WHERE DATE_TRUNC('month', release_date) = '2025-10-01';
   ```
3. Compare chart value with SQL result

**Expected Result:**
- ✅ Chart data matches database calculation
- ✅ Percentages are accurate (±0.1% rounding acceptable)

---

## 🚀 PERFORMANCE TESTS

### Large Date Range
**Steps:**
1. Select 2-year range: 2024-01-01 to 2025-12-31
2. Observe chart render time

**Expected Result:**
- ✅ Chart renders in < 2 seconds
- ✅ No browser lag or freezing
- ✅ Query execution < 500ms (check Network tab)

### Multiple Quick Changes
**Steps:**
1. Rapidly change date range 5 times in a row
2. Observe behavior

**Expected Result:**
- ✅ React Query debounces/cancels stale requests
- ✅ Only latest request completes
- ✅ No race conditions or stale data

---

## 📱 BROWSER COMPATIBILITY

Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Edge (latest)
- [ ] Safari (if available)

**Expected Result:**
- ✅ Chart renders identically across browsers
- ✅ Date picker works in all browsers
- ✅ No CSS layout issues

---

## ✅ ACCEPTANCE CRITERIA

**ALL MUST PASS:**
- [x] Hardcoded "Jan - Jun" removed
- [x] Chart displays dynamic months based on date range
- [x] Full year (Jan-Dec) shows all 12 months
- [x] Q4 (Oct-Dec) shows only 3 months
- [x] Current month shows weekly format (DD/MM)
- [x] Tooltip shows period labels correctly
- [x] Loading and empty states work
- [x] Data accuracy matches database
- [x] No console errors
- [x] Performance is acceptable (< 2s render)

---

## 🐛 KNOWN ISSUES / EDGE CASES

**Document any found issues here:**

1. **Issue:** _[Describe if found]_  
   **Severity:** Low/Medium/High  
   **Workaround:** _[If available]_

---

## 📝 TESTER NOTES

**Date Tested:** ___________  
**Tested By:** ___________  
**Browser:** ___________  
**Result:** ☐ PASS  ☐ FAIL  ☐ PARTIAL  

**Comments:**
```
[Any additional observations, bugs, or suggestions]
```

---

**✅ Sign-off:** __________________  
**Date:** __________________
