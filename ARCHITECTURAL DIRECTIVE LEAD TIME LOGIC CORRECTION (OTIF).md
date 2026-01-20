
---

```markdown
# 🚀 ARCHITECTURAL DIRECTIVE: LEAD TIME LOGIC CORRECTION (OTIF)

**To:** AI Development Agent
**From:** Chief Architect
**Date:** January 13, 2026
**Subject:** CRITICAL FIX - Lead Time & On-Time Delivery Logic
**Context:** The current logic incorrectly links `zrsd002` (Billing) to calculate OTIF. This is semantically wrong because Billing Date != Requested Delivery Date.
**Objective:** Refactor the "On Time" calculation to rely **exclusively** on the Logistics Data (`zrsd004`).

---

## 🟢 1. BUSINESS LOGIC REVISION

### 1.1 The Source of Truth
We are moving away from Cross-Module Linking (Finance vs Logistics) to **Single-Source Evaluation**.

* **OLD Logic (Incorrect):**
    * Target Date = `zrsd002.requested_delivery_date` (or Billing Date).
    * Actual Date = `zrsd004.actual_gi_date`.
* **NEW Logic (Correct):**
    * Target Date = **`zrsd004.delivery_date`** (The Planned Delivery Date in the Delivery Note).
    * Actual Date = **`zrsd004.actual_gi_date`** (The Actual Goods Issue Date).

### 1.2 Evaluation Formula
For every record in `fact_delivery` (derived from `zrsd004`):

```python
# Pseudo-code logic
if actual_gi_date is NULL:
    status = "Pending"  # Goods not yet issued
elif actual_gi_date <= delivery_date:
    status = "On Time"  # Green
else:
    status = "Late"     # Red

```

---

## 🟡 2. BACKEND IMPLEMENTATION TASKS

### Task 2.1: Verify Data Loader (`loader_zrsd004.py`)

* **Action:** Ensure the loader for `ZRSD004` correctly maps the Excel columns to the database schema.
* **Check:**
* Excel Column: `Delivery Date` (Planned)  DB Column: `fact_delivery.delivery_date`
* Excel Column: `Actual GI Date` (Actual)  DB Column: `fact_delivery.actual_gi_date`


* *Note:* If the database table `fact_delivery` is missing the `delivery_date` column, you must add it via a migration.

### Task 2.2: Refactor Calculation Engine (`lead_time.py`)

* **Action:** Modify the function responsible for generating "Recent Orders" and "OTIF Stats".
* **Change:**
* **Remove** the SQL JOIN with `fact_sales` (`zrsd002`) for the purpose of getting dates.
* **Select** both dates directly from `fact_delivery`.
* **Apply** the new formula defined in Section 1.2.



### Task 2.3: Update API Response (`/api/lead-time/recent-orders`)

* **Action:** Ensure the JSON response reflects the new logic.
* **Field Mapping:**
* `order_date`: Can still come from SO reference (optional) or use `created_on`.
* `target_date`: Must return `fact_delivery.delivery_date`.
* `actual_date`: Must return `fact_delivery.actual_gi_date`.
* `status`: Calculated based on the two fields above.



---

## 🔵 3. FRONTEND VISUALIZATION

### Task 3.1: Update Columns

* **File:** `web/src/components/dashboard/leadtime/RecentOrdersTable.tsx`
* **Action:**
* Rename column header from "Requested Date" to **"Planned Delivery Date"**.
* Ensure the "Status" column renders the tag (Green/Red) based on the new API response.



---

## ✅ VALIDATION CHECKLIST

1. **Data Integrity:** Verify that a record in `zrsd004` with `Delivery Date = 2026-01-20` and `Actual GI = 2026-01-22` is marked as **LATE**.
2. **Data Integrity:** Verify that a record with `Delivery Date = 2026-01-20` and `Actual GI = 2026-01-20` is marked as **ON TIME**.
3. **Independence:** Confirm that the calculation works even if the `zrsd002` (Billing) file has not been uploaded yet.

**Action:** Execute immediately.

```

```