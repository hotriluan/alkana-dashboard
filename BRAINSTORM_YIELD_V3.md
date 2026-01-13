# 🧠 BRAINSTORM: PRODUCTION YIELD V3 (OPERATIONAL EFFICIENCY HUB)

**Date:** January 12, 2026  
**Status:** PENDING CLARIFICATION  
**Author:** Claude Kit Engineer

---

## 📊 CURRENT STATE ANALYSIS

### V2 Hiện có:
| Component | Status | Notes |
|-----------|--------|-------|
| DB Table `fact_production_performance_v2` | ✅ Exists | 6,299 records loaded |
| `posting_date` column | ✅ Exists | Nhưng NULL (file gốc không có date) |
| Unique constraint | ❌ Missing | Chưa có UNIQUE(process_order_id, batch_id) |
| API `/api/v2/yield/*` | ✅ Exists | 5 endpoints |
| Frontend Dashboard | ✅ Exists | Tab-based, KPI cards, table |

### V3 Cần thay đổi:
| Component | Action | Complexity |
|-----------|--------|------------|
| Add `reference_date` column | New column + index | Low |
| Add UNIQUE constraint | Migration | Medium |
| Add `updated_at` column | Audit trail | Low |
| New Upload API | New endpoint + params | Medium |
| Upsert Logic | Change from INSERT to UPSERT | Medium |
| Date Range Filter | All endpoints | Medium |
| New Analytics Endpoints | 5 new endpoints | High |
| Frontend Redesign | 3-zone layout | High |

---

## 🔍 CRITICAL QUESTIONS (Cần clarify trước khi thực hiện)

### 1. **Schema Migration Strategy**

**Option A:** ALTER TABLE (In-place migration)
```sql
ALTER TABLE fact_production_performance_v2 
ADD COLUMN reference_date DATE DEFAULT CURRENT_DATE;
ADD COLUMN updated_at TIMESTAMP;
ADD CONSTRAINT uq_order_batch UNIQUE (process_order_id, batch_id);
```
- ✅ Pros: Giữ data hiện có, đơn giản
- ⚠️ Risk: Nếu đã có duplicate (process_order, batch), sẽ fail

**Option B:** Create V3 Table (Fresh start)
```sql
CREATE TABLE fact_production_performance_v3 (...);
```
- ✅ Pros: Clean, no migration risk
- ❌ Cons: Phải re-load data, thêm bảng mới

**❓ Question:** Bạn muốn approach nào? (Recommend Option A với data validation trước)

---

### 2. **Existing Data: 6,299 Records**

Hiện tại đã có 6,299 records với `reference_date = NULL`. 

**Options:**
1. Set default = `2026-01-01` (Jan 2026) cho tất cả records cũ
2. Set default = `CURRENT_DATE` (ngày load)
3. Xóa hết và yêu cầu re-upload

**❓ Question:** Reference date mặc định cho data cũ nên là gì?

---

### 3. **Duplicate Check**

Cần verify có duplicates không trước khi add UNIQUE constraint:
```sql
SELECT process_order_id, batch_id, COUNT(*) 
FROM fact_production_performance_v2 
GROUP BY process_order_id, batch_id 
HAVING COUNT(*) > 1;
```

**❓ Action:** Chạy query này để check?

---

### 4. **API Versioning Strategy**

**Option A:** Upgrade V2 → V3 (replace)
- `/api/v2/yield/*` → Deprecated
- `/api/v3/yield/*` → Active

**Option B:** Extend V2 (backward compatible)
- `/api/v2/yield/*` → Keep (no filter)
- `/api/v3/yield/*` → New (with filter)

**Option C:** Upgrade in-place
- Modify `/api/v2/yield/*` trực tiếp
- Add optional `reference_date` params

**❓ Question:** Bạn muốn approach nào? (Directive nói V3, nhưng có thể extend V2)

---

### 5. **Upload Flow Clarification**

Current flow:
```
User → Data Upload page → Select zrpp062.XLSX → Load all
```

V3 flow (theo directive):
```
User → Production Dashboard → Upload Modal → Select Month/Year → Upload file → Upsert
```

**❓ Questions:**
1. Upload modal nằm ở Production Dashboard hay vẫn ở Data Upload page?
2. Có cần validate file structure trước khi upload?
3. Progress indicator cần không? (6,299 rows có thể mất vài giây)

---

### 6. **Yield Calculation**

Directive nói `avg_yield_pct` nhưng trong data V2 chỉ có:
- `loss_pct` (% mất mát)
- Không có `yield_pct` trực tiếp

**Formula options:**
```
yield_pct = 100 - loss_pct  (nếu loss_pct là % of input)
yield_pct = (output_actual_kg / input_actual_kg) * 100
```

**❓ Question:** Công thức nào đúng với business logic?

---

### 7. **Trend Chart X-Axis**

Directive: "X-Axis = Month, Y-Axis = Yield %"

Nhưng `reference_date` chỉ là first day of month. Nếu user upload nhiều năm:
- 2025-01, 2025-02, ..., 2026-01

Chart có nên format là "Jan 25", "Feb 25" hay "2025-01"?

**❓ Question:** Format mong muốn cho X-axis labels?

---

## 🏗️ PROPOSED IMPLEMENTATION PLAN

### Phase 1: Database (Estimate: 1 hour)
1. ✅ Check duplicates
2. ✅ Add `reference_date` column with default
3. ✅ Add `updated_at` column
4. ✅ Add UNIQUE constraint
5. ✅ Create index on `reference_date`

### Phase 2: Backend (Estimate: 3 hours)
1. ✅ Create `yield_v3.py` router (new file)
2. ✅ `POST /api/v3/yield/upload` - Accept month/year + file
3. ✅ Update Loader with UPSERT logic
4. ✅ `GET /api/v3/yield/kpi` - With date filter
5. ✅ `GET /api/v3/yield/trend` - Time series
6. ✅ `GET /api/v3/yield/distribution` - By group
7. ✅ `GET /api/v3/yield/pareto` - Top 10 losers
8. ✅ `GET /api/v3/yield/quality` - SG scatter

### Phase 3: Frontend (Estimate: 4 hours)
1. ✅ Period Range Selector component
2. ✅ Upload Modal with Month/Year pickers
3. ✅ Zone 1: KPI Cards (4 cards)
4. ✅ Zone 2: 4 Charts (Trend, Donut, Bar, Scatter)
5. ✅ Zone 3: Data Grid with status badges

---

## 📋 SKILLS TO ACTIVATE

| Skill | Use Case |
|-------|----------|
| PostgreSQL | Schema migration, UPSERT syntax |
| FastAPI | New endpoints, file upload handling |
| Pandas | Data transformation in loader |
| React + TypeScript | Frontend components |
| Recharts | 4 chart types (Line, Donut, Bar, Scatter) |
| TanStack Query | Data fetching with filters |

---

## ⚠️ RISKS & MITIGATIONS

| Risk | Impact | Mitigation |
|------|--------|------------|
| Duplicate key violation | Migration fails | Check duplicates FIRST |
| Large file upload timeout | UX issue | Add progress indicator |
| Chart performance with 1000s of points | Slow render | Aggregate data server-side |
| Month/Year filter confusion | Wrong data | Clear UI labels |

---

## 🎯 DELIVERABLES CHECKLIST

### Database
- [ ] Migration script for `reference_date`, `updated_at`
- [ ] UNIQUE constraint on (process_order_id, batch_id)
- [ ] Index on reference_date

### Backend (5 new endpoints)
- [ ] `POST /api/v3/yield/upload`
- [ ] `GET /api/v3/yield/kpi`
- [ ] `GET /api/v3/yield/trend`
- [ ] `GET /api/v3/yield/distribution`
- [ ] `GET /api/v3/yield/pareto`
- [ ] `GET /api/v3/yield/quality`

### Frontend
- [ ] `PeriodRangeSelector.tsx`
- [ ] `UploadYieldModal.tsx`
- [ ] `YieldKPICards.tsx`
- [ ] `YieldTrendChart.tsx`
- [ ] `LossDistributionChart.tsx`
- [ ] `ParetoChart.tsx`
- [ ] `QualityScatterChart.tsx`
- [ ] `YieldDataGrid.tsx`
- [ ] Main dashboard layout (3 zones)

---

## ❓ UNRESOLVED QUESTIONS

1. **Migration approach:** ALTER TABLE hay CREATE new table?
2. **Default reference_date** cho 6,299 records cũ?
3. **Yield formula:** `100 - loss_pct` hay `output/input * 100`?
4. **Upload location:** Production Dashboard modal hay Data Upload page?
5. **API versioning:** V3 mới hay extend V2?
6. **Chart X-axis format:** "Jan 25" hay "2025-01"?

---

## 📝 DECISION LOG

| # | Question | Decision | Decided By | Date |
|---|----------|----------|------------|------|
| 1 | Migration approach | _Pending_ | - | - |
| 2 | Default reference_date | _Pending_ | - | - |
| 3 | Yield formula | _Pending_ | - | - |
| 4 | Upload location | _Pending_ | - | - |
| 5 | API versioning | _Pending_ | - | - |
| 6 | Chart format | _Pending_ | - | - |

---

## 🚀 NEXT STEPS

1. **Review & Decide:** Chief Architect cần quyết định các câu hỏi trên
2. **Validate Data:** Chạy duplicate check query
3. **Approve Plan:** Confirm implementation phases
4. **Execute:** Bắt đầu Phase 1 sau khi có quyết định

---

**End of Brainstorm Document**  
*Awaiting decisions before implementation begins.*
