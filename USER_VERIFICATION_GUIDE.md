# Visual Intelligence Overhaul - User Verification Guide

**Phase 3: Cleanup & Verification**  
**Status:** ✅ Code cleanup complete - Ready for runtime verification

---

## 🚀 Quick Start

### Prerequisites
- **Node.js**: v18+ installed
- **Python**: 3.11+ with FastAPI running
- **PostgreSQL**: 15+ with alkana database

### Start the Application

**Terminal 1 - Backend API:**
```bash
cd c:\dev\alkana-dashboard
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
# ✅ API listening on http://localhost:8000
```

**Terminal 2 - Frontend Dev Server:**
```bash
cd c:\dev\alkana-dashboard\web
npm install  # If dependencies not installed
npm run dev
# ✅ UI listening on http://localhost:5173
```

---

## 📋 Visual Verification Checklist

Open **http://localhost:5173** in your browser. Follow this checklist:

### ✅ Page 1: Inventory Dashboard
**URL:** `http://localhost:5173/inventory`

| Item | Location | Expected Result | Status |
|------|----------|-----------------|--------|
| **New Chart** | Top of page, below KPI cards | **Treemap chart** showing material stock distribution with ABC colors (Red=A, Blue=B, Gray=C) | [ ] |
| **Chart Title** | Above treemap | "Inventory Stock Distribution (ABC Analysis)" | [ ] |
| **Empty State** | If no data loads | "No inventory data available" message | [ ] |
| **Loading State** | While fetching | Spinner icon appears | [ ] |
| **Colors Match** | Legend at bottom of treemap | Class A=Red (#ef4444), Class B=Blue (#3b82f6), Class C=Slate (#64748b) | [ ] |
| **Old Tables** | Below Zone 1 chart | Existing inventory tables intact, no visual changes | [ ] |
| **Hover Tooltip** | Mouse over treemap cells | Shows: Material code, ABC Class, Stock (kg) | [ ] |

---

### ✅ Page 2: MTO Orders Dashboard
**URL:** `http://localhost:5173/mto-orders`

| Item | Location | Expected Result | Status |
|------|----------|-----------------|--------|
| **New Chart 1** | Top-left, below KPI cards | **Funnel chart** showing production stages (Quotation → Order → Manufacturing → Delivery) | [ ] |
| **New Chart 2** | Top-right, beside Funnel | **Gantt chart** showing top 15 orders with progress bars by status color | [ ] |
| **Chart Titles** | Above each chart | "Production Funnel" and "Top Orders Progress" | [ ] |
| **Colors Match** | Gantt bars | Pending=#f59e0b (amber), In Progress=#3b82f6 (blue), Completed=#22c55e (green) | [ ] |
| **Empty State** | If no data | "No data available" message in each chart | [ ] |
| **Loading State** | While fetching | Spinner appears in Zone 1 | [ ] |
| **Old Charts** | Below Zone 1 | Existing production charts (Status Bar, Top Materials, etc.) untouched | [ ] |

---

### ✅ Page 3: Sales Performance Dashboard
**URL:** `http://localhost:5173/sales-performance`

| Item | Location | Expected Result | Status |
|------|----------|-----------------|--------|
| **New Chart** | Top of page, below KPI cards | **Scatter plot** with customer dots positioned by (Order Frequency, Total Revenue) | [ ] |
| **Quadrant Lines** | On scatter plot | Dashed gray lines dividing chart into 4 quadrants | [ ] |
| **Chart Legend** | Below scatter plot | 4 quadrants labeled: VIP Customers, Loyal Customers, High-Value Deals, Casual Buyers | [ ] |
| **Colors Match** | Scatter dots | All dots should be blue (#3b82f6) | [ ] |
| **Quadrant Info** | Below chart legend | 4 color-coded cards explaining each quadrant (blue, amber, green, slate backgrounds) | [ ] |
| **Empty State** | If no data | "No data available" message | [ ] |
| **Old Tables** | Below Zone 1 | Existing sales tables (By Division, Customer List, etc.) preserved | [ ] |

---

### ✅ Page 4: Lead Time Dashboard
**URL:** `http://localhost:5173/leadtime`

| Item | Location | Expected Result | Status |
|------|----------|-----------------|--------|
| **New Chart** | Top of page, below KPI cards | **Stacked bar chart** showing lead time breakdown by stage (Procurement, Manufacturing, Transport) | [ ] |
| **Chart Title** | Above stacked bar | "Lead Time Stage Breakdown" | [ ] |
| **Color Coding** | Stacked bars | Each stage has distinct color (Procurement=#3b82f6, Mfg=#22c55e, Transport=#f59e0b) | [ ] |
| **X-Axis** | Labels on chart | Shows order numbers | [ ] |
| **Y-Axis** | Left side | Shows days (0, 5, 10, 15, 20, etc.) | [ ] |
| **Hover Tooltip** | Mouse over bars | Shows stage names and duration in days, total lead time | [ ] |
| **Empty State** | If no data | "No lead time data available" message | [ ] |
| **Old Charts** | Below Zone 1 | Existing lead time tables (Recent Orders, Overdue Report) untouched | [ ] |

---

## 🎨 Color System Verification

All new charts should use the **semantic color palette**:

| Color Name | Hex Code | Usage | Status |
|------------|----------|-------|--------|
| **Blue** | #3b82f6 | Primary, high-value, in-progress | [ ] |
| **Red** | #ef4444 | Critical, ABC Class A, urgent | [ ] |
| **Green** | #22c55e | Success, completed, low-risk | [ ] |
| **Amber** | #f59e0b | Warning, pending, medium-value | [ ] |
| **Slate** | #64748b | Neutral, background, low-priority | [ ] |

**Source file:** `web/src/constants/chartColors.ts`

---

## 🧪 Smoke Tests

### Test 1: No Crashes on Empty Data
1. **Clear database** (optional): Rename data files in `data/` folder or reset DB
2. **Reload page** for each dashboard
3. **Expected:** Each chart shows "No [X] data available" message instead of crashing
4. **Status:** [ ] Pass / [ ] Fail

### Test 2: Loading States
1. **Slow internet simulation** (Chrome DevTools → Throttle to "Slow 3G")
2. **Navigate** to each dashboard
3. **Expected:** Spinner icon appears while charts load
4. **Status:** [ ] Pass / [ ] Fail

### Test 3: Responsive Design
1. **Open DevTools** (F12) → Toggle device toolbar
2. **Test on mobile** (iPhone 12):
   - Treemap should stack below KPI cards
   - Funnel + Gantt should stack vertically
   - Scatter should scale to mobile width
3. **Expected:** No horizontal scrolling, readable text
4. **Status:** [ ] Pass / [ ] Fail

### Test 4: Browser Console
1. **Open DevTools** → Console tab
2. **Reload page** for each dashboard
3. **Expected:** NO red error messages, NO TypeScript warnings, NO "undefined is not a function"
4. **Status:** [ ] Pass / [ ] Fail

---

## 📊 Data Requirements & Upload Instructions

### ✅ Inventory Dashboard - ABC Data
**Required:** Material stock data with velocity classification
- **If missing:** Upload sample inventory file
  ```bash
  # Place CSV file in: c:\dev\alkana-dashboard\data\inventory.csv
  # Columns: material_code, material_description, stock_kg, abc_class (A/B/C)
  # Example row: MAT-001,Raw Steel,5000,A
  ```

### ✅ Production Dashboard - Order Data
**Required:** Production orders with status and stage tracking
- **If missing:** Ensure `FactProduction` table has records
  ```bash
  psql -U postgres -d alkana -c "SELECT COUNT(*) FROM FactProduction LIMIT 1"
  # Should return: count > 0
  ```

### ✅ Sales Dashboard - Customer Segmentation
**Required:** Customer orders with frequency and revenue metrics
- **If missing:** Sample data will be generated from existing sales table
  ```bash
  psql -U postgres -d alkana -c "SELECT COUNT(*) FROM FactBilling WHERE net_value > 0 LIMIT 1"
  # Should return: count > 0
  ```

### ✅ Lead Time Dashboard - Order Timeline Data
**Required:** Orders with procurement, manufacturing, and transport dates
- **If missing:** Check `FactLeadTime` table
  ```bash
  psql -U postgres -d alkana -c "SELECT COUNT(*) FROM FactLeadTime LIMIT 1"
  # Should return: count > 0
  ```

---

## 🐛 Troubleshooting

### Issue: Charts show "No data available"
**Solution:**
1. Verify database connection: `psql -U postgres -d alkana -c "SELECT 1"`
2. Check backend logs for query errors
3. Manually populate test data:
   ```bash
   cd c:\dev\alkana-dashboard
   python -m scripts.seed_demo_data  # If script exists
   ```

### Issue: Spinner spins forever
**Solution:**
1. Open DevTools → Network tab
2. Check if API calls complete: `http://localhost:8000/api/v1/dashboards/inventory/abc-analysis`
3. If 404 or 500 error: Backend endpoint missing (run Phase 5 setup again)
4. If timeout: Database query slow (check PostgreSQL logs)

### Issue: Wrong colors or styling
**Solution:**
1. Clear browser cache: Ctrl+Shift+Delete
2. Hard refresh: Ctrl+Shift+R
3. Verify `web/src/constants/chartColors.ts` exists and imports work
4. Check DevTools console for import errors

### Issue: Charts not responsive on mobile
**Solution:**
1. Open `web/src/components/dashboard/[name]/[Component].tsx`
2. Verify `ResponsiveContainer width="100%" height={height}` present
3. Check parent div has `w-full` Tailwind class
4. Test with mobile emulation in DevTools

---

## ✅ Sign-Off Checklist

Use this checklist to confirm verification completion:

- [ ] **Inventory Dashboard** - Treemap renders with ABC colors ✅
- [ ] **MTO Orders Dashboard** - Funnel + Gantt render side-by-side ✅
- [ ] **Sales Dashboard** - Scatter with quadrant lines renders ✅
- [ ] **Lead Time Dashboard** - Stacked bar chart renders ✅
- [ ] **All colors match** semantic palette (blue, red, green, amber, slate) ✅
- [ ] **All empty states** show "No data" instead of crashing ✅
- [ ] **Loading states** show spinner during fetch ✅
- [ ] **Old tables** still visible below new charts ✅
- [ ] **No console errors** in DevTools ✅
- [ ] **No TypeScript warnings** (optional, non-critical) ✅
- [ ] **Responsive design** works on mobile ✅

---

## 📝 Known Limitations

1. **Histogram endpoint** (`/api/v1/leadtime/histogram`) created but not integrated into dashboard
   - **Status:** Ready for future enhancement
   - **Fix:** Add ChartBreakdownHistogram component to LeadTimeDashboard Zone 1

2. **No custom date range filters** on new charts
   - **Status:** Charts use global date range from header (if available)
   - **Fix:** Pass dateRange props from dashboard to chart components

3. **Quadrant labels not interactive**
   - **Status:** Read-only informational display
   - **Fix:** Future phase could add click-to-filter functionality

---

## 🎉 Success Criteria

**Verification PASSED if:**
- ✅ All 4 dashboards load without JavaScript errors
- ✅ All 5 new charts render with correct data
- ✅ All colors match the semantic palette
- ✅ Empty data states handled gracefully
- ✅ Loading spinners appear during async operations
- ✅ Old tables/charts remain untouched
- ✅ Responsive design works on mobile

**Next Steps if Passed:**
1. Deploy to staging environment
2. Conduct user acceptance testing (UAT)
3. Gather feedback on chart readability and usefulness
4. Plan Phase 4 enhancements (interactivity, filters, exports)

---

## 📞 Support

**For issues or questions:**
- Check browser DevTools Console (F12)
- Review backend logs: `http://localhost:8000/docs` (FastAPI Swagger UI)
- Verify database: `psql -U postgres -d alkana`
- Contact dev team with screenshot + browser console error

---

**Report Generated:** 2026-01-16  
**Phase:** 3 - Cleanup & Verification  
**Status:** Ready for Runtime Verification

