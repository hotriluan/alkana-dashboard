# 🔬 ORDER COUNT DISCREPANCY FORENSIC AUDIT REPORT

**Audit Date:** January 20, 2026  
**Auditor:** AI Development Agent  
**Status:** INVESTIGATION COMPLETE (READ-ONLY)

---

## 🚨 EXECUTIVE SUMMARY

**Critical Data Integrity Issue Identified:**  
Three different dashboards report conflicting "Total Orders" counts for period `2025-01-01` to `2025-12-31`:

| Dashboard | Reported Count | Actual Meaning | Error Magnitude |
|:----------|---------------:|:---------------|----------------:|
| **Executive Dashboard** | **12,185** | Production Orders (Wrong Entity) | +242% vs Ground Truth |
| **Sales Performance Dashboard** | **7,091** | Billing Documents (Partial Match) | +99% vs Ground Truth |
| **Ground Truth (ZRSD002)** | **3,564** | Unique Sales Orders (SO Number) | ✓ Correct |

**Root Cause:** Mixing different business entities (Production vs Billing vs Sales Orders) without proper dimensional modeling.

---

## 🕵️ A. THE DETECTIVE WORK

### Investigation Results

| Metric Source | Current Value | Actual SQL/Logic Used | Why is it Wrong? (Root Cause) |
|:--------------|:--------------|:----------------------|:-------------------------------|
| **Executive Dashboard** (`/executive/summary`) | **12,185** | ```sql<br>SELECT COUNT(*) as total_orders<br>FROM fact_production<br>WHERE actual_finish_date BETWEEN '2025-01-01' AND '2025-12-31'<br>``` | **WRONG TABLE**: Counting Production Orders instead of Sales Orders. These are Manufacturing Work Orders, not Customer Orders. |
| **Sales Performance Dashboard** (`/sales/summary`) | **7,091** | ```sql<br>SELECT COUNT(DISTINCT billing_document) as total_orders<br>FROM fact_billing<br>WHERE billing_date BETWEEN '2025-01-01' AND '2025-12-31'<br>``` | **WRONG ENTITY**: Counting Billing Documents (Invoices). One Sales Order can generate multiple Billing Documents due to partial deliveries. Avg: 1.99 billing docs per SO. |
| **Raw Data Validation** | **3,564** | ```sql<br>SELECT COUNT(DISTINCT so_number)<br>FROM raw_zrsd002<br>WHERE billing_date BETWEEN '2025-01-01' AND '2025-12-31'<br>``` | ✓ **CORRECT**: This is the true Sales Order count. |

### Supporting Evidence from Database Forensics

```sql
-- Actual query results from PostgreSQL:
SELECT 
  COUNT(DISTINCT so_number) as unique_sales_orders,
  COUNT(DISTINCT billing_document) as unique_billing_docs,
  COUNT(*) as total_billing_line_items
FROM raw_zrsd002
WHERE billing_date BETWEEN '2025-01-01' AND '2025-12-31';

-- Result:
-- unique_sales_orders: 3,564
-- unique_billing_docs: 7,091
-- total_billing_line_items: 21,072
```

**Key Finding:** One Sales Order generates an average of **2 billing documents** and **6 line items**.

**Example Case:**
- Sales Order `210030226` → 43 billing documents → 126 line items
- This is typical for large orders with multiple partial deliveries

---

## 📊 B. IMPACT ANALYSIS

### Business Meaning of Wrong Numbers

#### 1. Executive Dashboard (12,185 - Production Orders)
**What it actually shows:** Manufacturing work orders (internal production batches).

**Business Impact:**
- **Misleading KPI:** CEO sees inflated order volume by 242%
- **Wrong Story:** Dashboard implies "we have 12K customer orders" when reality is only 3.5K
- **Strategic Failure:** Business decisions (capacity planning, hiring, inventory) based on Production Volume instead of Customer Demand
- **Cross-functional Confusion:** Sales team reports 3.5K orders, Finance reports 7K invoices, CEO sees 12K — trust in analytics erodes

#### 2. Sales Performance Dashboard (7,091 - Billing Documents)
**What it actually shows:** Number of invoices issued (not number of orders received).

**Business Impact:**
- **Inflated by 99%:** Reports nearly 2x the actual customer orders
- **Partial Shipment Distortion:** Customers who receive partial deliveries get counted multiple times
- **Sales Rep Performance:** Metrics like "Orders per Rep" are doubled, making underperformers look better
- **Customer Segmentation:** "High-frequency" customers may just be large orders split into multiple invoices

#### 3. Cascading Data Quality Issues
- **AR Aging:** If customer aging uses billing_document count for "number of invoices," it's correct
- **OTIF Calculation:** Likely measuring on-time delivery of invoices, not orders
- **Revenue Per Order:** Artificially deflated (total revenue / inflated order count)

---

## 🔧 C. PROPOSED CORRECTION PLAN

### Root Cause Summary
**Missing Dimension:** No `dim_sales_order` or `fact_sales` table exists. The system conflates:
1. Sales Orders (Customer Intent) - ZRSD002 `so_number`
2. Billing Documents (Invoices) - ZRSD002 `billing_document`
3. Production Orders (Manufacturing) - COOISPI/MB51 `order_number`

### Corrected SQL Queries

#### ✅ For Executive Dashboard (`/executive/summary`)
**Current (WRONG):**
```python
production_result = db.execute(text(f"""
    SELECT 
        COUNT(*) as total_orders,  -- ❌ PRODUCTION ORDERS
        ...
    FROM fact_production
    {prod_date_filter}
"""))
```

**Corrected (RIGHT):**
```python
# Option 1: Quick Fix - Query from raw_zrsd002
sales_result = db.execute(text(f"""
    SELECT 
        COUNT(DISTINCT so_number) as total_orders,
        COUNT(DISTINCT customer_name) as active_customers
    FROM raw_zrsd002
    WHERE billing_date BETWEEN :start_date AND :end_date
        AND so_number IS NOT NULL
"""), {"start_date": start_date, "end_date": end_date})

# Option 2: Proper Fix - Create fact_sales_orders table
sales_result = db.execute(text(f"""
    SELECT 
        COUNT(DISTINCT so_number) as total_orders,
        COUNT(DISTINCT customer_name) as active_customers
    FROM fact_sales_orders  -- New table needed
    WHERE order_date BETWEEN :start_date AND :end_date
"""), {"start_date": start_date, "end_date": end_date})
```

#### ✅ For Sales Performance Dashboard (`/sales/summary`)
**Current (ACCEPTABLE BUT MISLEADING):**
```python
query = f"""
    SELECT 
        COUNT(DISTINCT billing_document) as total_orders,  -- ❌ INVOICES, NOT ORDERS
        ...
    FROM fact_billing
    {where_sql}
"""
```

**Corrected (RIGHT):**
```python
# Query sales orders, not billing documents
query = f"""
    SELECT 
        COUNT(DISTINCT so_number) as total_orders,  -- ✅ SALES ORDERS
        COUNT(DISTINCT billing_document) as total_invoices,  -- Add this metric
        SUM(net_value) as total_revenue,
        COUNT(DISTINCT customer_name) as total_customers
    FROM fact_billing  -- Or better: fact_sales_orders
    {where_sql}
        AND so_number IS NOT NULL
"""
```

### Target Validation
**Expected Result After Fix:**
```
Executive Dashboard: Total Orders = 3,564 ✓
Sales Performance Dashboard: Total Orders = 3,564 ✓
```

**Additional Metric (Recommended):**
```
Sales Performance Dashboard: Total Invoices = 7,091
Sales Performance Dashboard: Avg Invoices per Order = 1.99
```

---

## 🏗️ D. RECOMMENDED ARCHITECTURAL IMPROVEMENTS

### 1. Create `fact_sales_orders` Table
```sql
CREATE TABLE fact_sales_orders (
    id SERIAL PRIMARY KEY,
    so_number VARCHAR(50) UNIQUE NOT NULL,
    order_date DATE NOT NULL,
    customer_name VARCHAR(200),
    sales_office VARCHAR(20),
    dist_channel VARCHAR(20),
    total_order_value NUMERIC(18,2),
    total_order_qty_kg NUMERIC(18,2),
    billing_document_count INT,  -- How many invoices issued
    line_item_count INT,         -- How many SKUs ordered
    status VARCHAR(50),           -- Open/Closed/Cancelled
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_fact_sales_orders_date ON fact_sales_orders(order_date);
CREATE INDEX idx_fact_sales_orders_customer ON fact_sales_orders(customer_name);
```

### 2. Add ETL Transform
```python
# In src/etl/transform.py
def transform_sales_orders(self):
    """Aggregate raw_zrsd002 by so_number to create fact_sales_orders"""
    query = """
        INSERT INTO fact_sales_orders (
            so_number, order_date, customer_name, sales_office, 
            dist_channel, total_order_value, billing_document_count, line_item_count
        )
        SELECT 
            so_number,
            MIN(so_date) as order_date,
            MAX(customer_name) as customer_name,
            MAX(sales_office) as sales_office,
            MAX(dist_channel) as dist_channel,
            SUM(net_value) as total_order_value,
            COUNT(DISTINCT billing_document) as billing_document_count,
            COUNT(*) as line_item_count
        FROM raw_zrsd002
        WHERE so_number IS NOT NULL
        GROUP BY so_number
        ON CONFLICT (so_number) DO UPDATE SET
            total_order_value = EXCLUDED.total_order_value,
            billing_document_count = EXCLUDED.billing_document_count,
            line_item_count = EXCLUDED.line_item_count
    """
```

### 3. Update API Response Models
```python
# In src/api/routers/sales_performance.py
class SalesKPIs(BaseModel):
    total_orders: int          # COUNT(DISTINCT so_number)
    total_invoices: int        # COUNT(DISTINCT billing_document)
    total_line_items: int      # COUNT(*)
    avg_invoices_per_order: float
    total_sales: float
    avg_order_value: float
```

---

## ⚠️ UNRESOLVED QUESTIONS

1. **Naming Convention:** Should we rename `fact_billing` to `fact_invoices` to avoid confusion?
2. **Historical Data:** Are there Sales Orders in the system that have NO billing documents yet (unfulfilled)?
3. **Production Order Link:** Is there a mapping between Sales Orders and Production Orders? (e.g., `so_number` → `order_number`)
4. **Dashboard Labels:** Should Executive Dashboard show both "Customer Orders" and "Production Orders" as separate KPIs?
5. **OTIF Calculation:** Does OTIF currently measure invoice delivery or order fulfillment? Should validate against `fact_delivery`.

---

## 📋 NEXT STEPS (OUT OF SCOPE FOR THIS AUDIT)

1. ✅ **Approve this report** - Confirm findings with stakeholders
2. 🔧 **Create fact_sales_orders table** - Implement dimensional model fix
3. 🔧 **Update ETL pipeline** - Add transform_sales_orders() step
4. 🔧 **Fix Executive Dashboard** - Replace fact_production query with fact_sales_orders
5. 🔧 **Fix Sales Dashboard** - Use so_number instead of billing_document
6. ✅ **Add automated tests** - Validate order counts match ground truth
7. 📊 **Update frontend labels** - Clearly distinguish "Orders" vs "Invoices" vs "Production Batches"

---

**Audit Completed: January 20, 2026**  
**Status: READ-ONLY INVESTIGATION COMPLETE**  
**Action Required: Executive Approval Before Implementation**
