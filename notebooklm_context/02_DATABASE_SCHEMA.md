# 02. Database Schema

## Overview
The database is built on PostgreSQL and follows a Star Schema design optimized for analytics. It consists of three main layers:
1.  **Raw Layer:** Staging tables matching Excel structures 1:1.
2.  **Fact Layer:** Transactional data (Orders, Movements, Sales).
3.  **Dimension Layer:** Reference data (Materials, Plants, Customers).

## 1. Fact Tables

### `fact_production` (Production Orders)
Contains manufacturing orders (COOISPI).
```sql
CREATE TABLE fact_production (
    id SERIAL PRIMARY KEY,
    plant_code INT NOT NULL,
    sales_order VARCHAR(20),       -- Null for Make-to-Stock
    order_number VARCHAR(20) NOT NULL,
    order_type VARCHAR(10),        -- 201O (MTO) vs 201S (MTS)
    material_code VARCHAR(20),
    material_description VARCHAR(100),
    release_date DATE,
    actual_finish_date DATE,
    bom_alternative INT,
    batch VARCHAR(20),
    system_status VARCHAR(100),    -- REL, PCNF, DLV, TECO
    mrp_controller VARCHAR(10),    -- P01, P02, P03
    order_qty DECIMAL(10,2),
    order_qty_kg DECIMAL(10,2),    -- Normalized to KG
    delivered_qty DECIMAL(10,2),
    delivered_qty_kg DECIMAL(10,2),
    uom VARCHAR(10),
    is_mto BOOLEAN,                -- Computed classification
    order_status VARCHAR(20),      -- WIP, COMPLETED, CANCELLED
    UNIQUE(order_number, plant_code)
);
```

### `fact_inventory` (Material Movements)
Contains goods movements (MB51). Aggregated by Material + Plant for performance.
```sql
CREATE TABLE fact_inventory (
    id SERIAL PRIMARY KEY,
    posting_date DATE NOT NULL,
    mvt_type INT NOT NULL,         -- 101, 601, 261, etc.
    plant_code INT NOT NULL,
    sloc_code INT,
    material_code VARCHAR(20),
    material_description VARCHAR(100),
    batch VARCHAR(20),
    qty DECIMAL(10,2),
    qty_kg DECIMAL(10,2),          -- Normalized to KG
    stock_impact INT,              -- +1 (Inc), -1 (Dec), 0 (Transfer)
    UNIQUE(material_document, batch, mvt_type)
);
```

### `fact_billing` (Sales Revenue)
Contains billing documents (ZRSD002).
```sql
CREATE TABLE fact_billing (
    id SERIAL PRIMARY KEY,
    billing_date DATE,
    billing_document VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100),
    salesman_name VARCHAR(100),
    material_code VARCHAR(20),
    billing_qty DECIMAL(10,2),
    billing_qty_kg DECIMAL(10,2),  -- Normalized to KG
    net_value DECIMAL(15,2),       -- Revenue
    total DECIMAL(15,2),           -- Revenue + Tax
    so_number VARCHAR(20),
    UNIQUE(billing_document, billing_item)
);
```

### `fact_production_chain` (Yield Tracking)
Links the 3-stage production process: P03 (Mixing) -> P02 (Intermediate) -> P01 (Filling).
```sql
CREATE TABLE fact_production_chain (
    chain_id SERIAL PRIMARY KEY,
    p01_order VARCHAR(20),
    p01_material VARCHAR(20),
    
    p02_order VARCHAR(20),
    p02_yield_pct DECIMAL(5,2),    -- Efficiency of intermediate stage
    
    p03_order VARCHAR(20),
    p03_yield_pct DECIMAL(5,2),    -- Efficiency of mixing stage
    
    total_yield_pct DECIMAL(5,2),  -- End-to-end efficiency
    total_loss_kg DECIMAL(10,2)
);
```

## 2. Dimension Tables

### `dim_material`
Product hierarchy flows.
```sql
CREATE TABLE dim_material (
    material_code VARCHAR(20) PRIMARY KEY,
    material_description VARCHAR(100),
    ph1 VARCHAR(50), -- Division
    ph2 VARCHAR(50), -- Business
    ph3 VARCHAR(50), -- Sub Business
    ...
    ph9 VARCHAR(50)  -- SKU
);
```

### `dim_uom_conversion`
Learned conversion factors.
```sql
CREATE TABLE dim_uom_conversion (
    material_code VARCHAR(20) PRIMARY KEY,
    kg_per_unit DECIMAL(10,4),     -- e.g., 18.5 KG/PC
    sample_count INT,              -- Reliability score
    source VARCHAR(20)             -- 'billing' or 'master'
);
```

## 3. Relationships
*   **Production -> Inventory:** Linked via `Order Number` (MVT 101/261).
*   **Sales -> Production:** Linked via `Sales Order` (for MTO items).
*   **Billing -> Sales:** Linked via `SO Number`.
*   **All -> Material:** Linked via `Material Code`.
