# Kế Hoạch Tổng Thể - Alkana Dashboard

**Cập nhật**: 2026-02-09  
**Tình trạng**: Đang thực hiện

---

## ✅ ĐÃ HOÀN THÀNH

### 1. ETL Performance Optimization ✅ (09/02/2026)
- **Kết quả**: Giảm 69.4% thời gian (47s → 14.40s)
- **Commits**: 709b86f, 41c25cc, ee223f4, f884156, 5614f4d
- **Chi tiết**: 
  - transform_cooispi: 30s → 5.43s (81.9% nhanh hơn)
  - transform_lead_time: 17s → 8.97s (47.2% nhanh hơn)
  - 8 database indexes
  - Bulk operations
  - Query consolidation (4→1)
  - JSONB operators
  - Documentation updates
  - Monitoring guide

### 2. OTIF Implementation ✅ (13/01/2026)
- Delivery date logic từ ZRSD004
- Endpoints: /otif-summary, /recent-orders
- Frontend: OTIFRecentOrdersTable

### 3. Variance Analysis V2 Removal ✅ (13/01/2026)  
- Xóa UI V2 từ Production Dashboard
- Xóa backend yield_v2.py
- Giữ V3 Efficiency Hub

---

## 🔄 ĐANG THỰC HIỆN

### 1. Alert Detection Optimization ⏳ (Mới - Ưu tiên Medium)

**Vấn đề**: 
- detect_alerts() chạy ~30-60s (ước tính)
- Query từng batch riêng lẻ
- Loop qua 5,000-10,000 P01 batches
- Gọi netting logic cho từng batch
- Không có vectorization

**Kế hoạch**: [plans/20260209-alert-detection-optimization.md](plans/20260209-alert-detection-optimization.md)

**Bước thực hiện**:
1. ⏳ Phase 1: Đo baseline trên production (15 phút)
2. ⏳ Phase 2: Vectorize netting logic (2 giờ)
3. ⏳ Phase 3: Reuse database session (30 phút)
4. ⏳ Phase 4: Testing & validation (1 giờ)
5. ⏳ Phase 5: Documentation (30 phút)

**Ước tính**:
- Thời gian: 4 giờ
- Speedup: 50-80% (30s → 6-15s)
- Ưu tiên: Medium (sau khi xong System Audit critical issues)

---

## ❌ CHƯA BẮT ĐẦU - CRITICAL

### 1. System Audit: Phase 3 - Data Inflation 🔴 (Ưu tiên cao nhất)

**Vấn đề**:
- fact_inventory: 5,889 duplicate rows (57.7%)
- Inventory totals gấp đôi thực tế (4.15M kg → nên 2.08M kg)
- view_inventory_current GROUP BY sai
- transform_mb51() không aggregate

**Công việc**:
1. Backup database trước khi làm
2. Sửa view_inventory_current GROUP BY
3. Thêm UNIQUE constraint vào fact_inventory
4. Fix transform_mb51() aggregate movements
5. Re-run transform và validate

**Ước tính**: 6 giờ  
**Rủi ro**: Cao - Cần database migration  
**Ưu tiên**: 🔴 CRITICAL - Làm đầu tiên

### 2. System Audit: Phase 4 - ZRSD004 Headers 🔴 (Ưu tiên cao)

**Vấn đề**:
- 24,856 rows load với NULL values
- Excel merged cells, pandas đọc headers sai
- Tất cả dữ liệu bị mất

**Công việc**:
1. Skip header row khi read_excel()
2. Manually assign 34 column names
3. Update column mappings
4. Re-load ZRSD004 data

**Ước tính**: 2 giờ  
**Rủi ro**: Thấp  
**Ưu tiên**: 🔴 CRITICAL

### 3. System Audit: Phase 2 - AR Collection Display (Ưu tiên trung bình)

**Vấn đề**:
- AR Aging dashboard hiển thị rỗng dù có 93 rows
- Cần investigation root cause

**Ước tính**: 2 giờ  
**Ưu tiên**: ⚠️ HIGH

### 4. System Audit: Phase 5 - Performance Indexes (Ưu tiên thấp)

**Công việc**:
- Thêm indexes cho date filters còn thiếu
- TRUNCATE trước fact table inserts
- Prevent duplicate accumulation

**Ước tính**: 2 giờ  
**Ưu tiên**: ⚠️ MEDIUM (ETL đã tối ưu, các index này là bonus)

---

## 📋 BACKLOG - KHẢ DỤ

### 1. Legacy Yield Decommission (Ưu tiên thấp)

**Mục tiêu**: Xóa hoàn toàn legacy/V2 yield modules

**Phases**:
1. Phase 1: Frontend navigation cleanup
2. Phase 2: Remove obsolete components  
3. Phase 3: Backend router cleanup
4. Phase 4: Database schema cleanup (DROP tables)
5. Phase 5: ETL cleanup
6. Phase 6: Verification

**Rủi ro**:
- Alert Monitor có thể phụ thuộc legacy tables
- External BI tools có thể query tables này
- DROP TABLE không rollback được

**Ước tính**: 12 giờ  
**Ưu tiên**: 🟡 LOW - Có thể delay, không ảnh hưởng chức năng

---

## 📊 TỔNG KẾT CÔNG VIỆC

| Kế hoạch | Status | Ưu tiên | Tiến độ | Thời gian |
|----------|--------|---------|---------|-----------|
| ETL Optimization | ✅ Complete | - | 100% | 0h |
| **System Audit Phase 3** | ❌ Not Started | 🔴 CRITICAL | 0% | **6h** |
| **System Audit Phase 4** | ❌ Not Started | 🔴 CRITICAL | 0% | **2h** |
| System Audit Phase 2 | ❌ Not Started | ⚠️ HIGH | 0% | 2h |
| **Alert Detection Opt** | ⏳ Planning | ⚠️ MEDIUM | 0% | **4h** |
| System Audit Phase 5 | ❌ Not Started | ⚠️ MEDIUM | 0% | 2h |
| Legacy Yield Decommission | ❌ Not Started | 🟡 LOW | 0% | 12h |

**Tổng công việc còn lại**: ~28 giờ

---

## 🎯 LỘ TRÌNH KHUYẾN NGHỊ

### Tuần 1 (Ngay bây giờ - CRITICAL)

**Ngày 1-2: System Audit Critical Issues** (8h)
1. ✅ Phase 3: Data Inflation (6h)
   - Backup database
   - Fix view + constraint + transform
   - Validate dữ liệu
2. ✅ Phase 4: ZRSD004 Headers (2h)
   - Fix loader
   - Re-load data

**Kết quả**: Dữ liệu chính xác, không bị inflate, ZRSD004 có data

### Tuần 2 (Tối ưu hiệu năng)

**Ngày 3: Alert Detection Optimization** (4h)
1. Đo baseline
2. Vectorize netting logic
3. Testing + documentation

**Ngày 4: System Audit Remaining** (4h)
1. Phase 2: AR Collection Display (2h)
2. Phase 5: Performance Indexes (2h)

**Kết quả**: Toàn bộ System Audit complete, Alert detection nhanh hơn 50-80%

### Tuần 3+ (Backlog - Optional)

**Khi có thời gian**: Legacy Yield Decommission (12h)
- Không gấp, có thể làm từ từ
- Cần investigation kỹ trước khi DROP tables

---

## 📈 PERFORMANCE METRICS

### Current Baseline (09/02/2026)

| Component | Performance | Status |
|-----------|-------------|--------|
| transform_cooispi | 5.43s | ✅ Optimized |
| transform_lead_time | 8.97s | ✅ Optimized |
| Total ETL | 14.40s | ✅ Optimized (69.4% faster) |
| detect_alerts | ~30-60s (ước tính) | ⏳ Needs optimization |

### Target After Alert Optimization

| Component | Target | Expected |
|-----------|--------|----------|
| detect_alerts | <15s | 50-80% faster |
| Total transform + alerts | <30s | Combined speedup |

---

## 🔔 MONITORING & ALERTS

### Performance Regression Thresholds

**ETL Transforms** (đã setup monitoring):
- ⚠️ Warning: >150% baseline
- 🚨 Critical: >200% baseline

**Alert Detection** (sau khi optimize):
- ⏱️ Baseline: TBD (cần đo)
- ⚠️ Warning: >150% baseline
- 🚨 Critical: >200% baseline

### Daily Checks

1. Transform performance (automated via MONITORING-PERFORMANCE.md)
2. Alert detection performance (sau khi optimize)
3. Data integrity (no duplicates in fact_inventory)
4. ZRSD004 data quality (no NULL columns)

---

**Người phụ trách**: Engineering Team  
**Review**: Hàng tuần  
**Cập nhật tiếp theo**: 2026-02-16
