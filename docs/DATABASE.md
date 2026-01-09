# Database Documentation

Comprehensive database schema, migrations, and data dictionary for the Alkana Dashboard.

## Table of Contents
- [Overview](#overview)
- [Database Schema](#database-schema)
- [Data Dictionary](#data-dictionary)
- [Data Lineage](#data-lineage)
- [Migrations](#migrations)
- [Materialized Views](#materialized-views)
- [Indexes & Performance](#indexes--performance)
- [Backup & Recovery](#backup--recovery)

---

## Overview

### Database Technology
- **Engine:** PostgreSQL 15+
- **ORM:** SQLAlchemy 2.0
- **Migration Tool:** Alembic
- **Schema Pattern:** Star Schema (Dimensional Modeling)

### Connection Details
```bash
# Development
postgresql://alkana_user:password@localhost:5432/alkana_dashboard

# Production
postgresql://alkana_user:secure_password@prod-db.example.com:5432/alkana_dashboard
```

### Schema Layers

```
┌──────────────────────────────────────────┐
│  Materialized Views (Aggregated Data)   │
├──────────────────────────────────────────┤
│  Fact Tables (Business Events)          │
├──────────────────────────────────────────┤
│  Dimension Tables (Reference Data)       │
├──────────────────────────────────────────┤
│  Raw Tables (SAP Exports)                │
└──────────────────────────────────────────┘
```

---

## Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    raw_mb51 ||--o{ fact_inventory : transforms
    raw_zrsd002 ||--o{ fact_billing : transforms
    raw_cooispi ||--o{ fact_production : transforms
    
    fact_inventory }o--|| dim_material : references
    fact_inventory }o--|| dim_location : references
    fact_inventory }o--|| dim_date : references
    
    fact_billing }o--|| dim_customer : references
    fact_billing }o--|| dim_material : references
    fact_billing }o--|| dim_date : references
    
    fact_production }o--|| dim_material : references
    fact_production }o--|| dim_date : references
    
    fact_production_chain }o--|| fact_production : links
    
    fact_alert }o--|| dim_material : references
    fact_alert }o--|| dim_customer : references
```

### Tables Overview

| Table Type | Count | Purpose | Size Estimate |
|------------|-------|---------|---------------|
| Raw Tables | 8 | SAP data imports | 100K-500K rows each |
| Dimension Tables | 5 | Reference data | 100-10K rows each |
| Fact Tables | 5 | Business events | 50K-1M rows each |
| Materialized Views | 4 | Aggregated metrics | N/A (derived) |
| Auth Tables | 2 | User management | <1K rows |

---

## Data Dictionary

### Raw Tables

#### raw_mb51 (Material Documents)
**Purpose:** All material movements (receipts, issues, transfers)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | SERIAL | No | Primary key |
| `material_code` | VARCHAR(40) | No | Material number (e.g., "P01-12345") |
| `material_description` | VARCHAR(200) | Yes | Product name |
| `plant` | VARCHAR(4) | No | Manufacturing plant code (e.g., "1000") |
| `storage_location` | VARCHAR(4) | Yes | SLOC code (e.g., "FG01") |
| `movement_type` | VARCHAR(3) | No | MVT type (e.g., "101", "261", "601") |
| `quantity` | NUMERIC(15,3) | No | Movement quantity (positive or negative) |
| `unit` | VARCHAR(3) | Yes | Unit of measure (PC, KG, L) |
| `posting_date` | DATE | No | When movement occurred |
| `document_number` | VARCHAR(20) | No | Unique document ID |
| `reference_document` | VARCHAR(20) | Yes | Related document (for reversals) |
| `batch_number` | VARCHAR(20) | Yes | Batch/lot number |
| `vendor_customer` | VARCHAR(100) | Yes | Vendor or customer name |
| `created_at` | TIMESTAMP | No | When record loaded into DB |

**Indexes:**
- `idx_mb51_material` on `material_code`
- `idx_mb51_posting_date` on `posting_date`
- `idx_mb51_doc_number` on `document_number`
- `idx_mb51_batch` on `batch_number`

**Sample Data:**
```sql
SELECT * FROM raw_mb51 LIMIT 3;

 id | material_code | movement_type | quantity | posting_date | batch_number
----|---------------|---------------|----------|--------------|-------------
  1 | P01-12345     | 101          |   100.0  | 2025-01-15   | 25L2535110
  2 | P01-12345     | 261          |   -50.0  | 2025-01-16   | 25L2535110
  3 | P02-67890     | 601          |   -25.0  | 2025-01-17   | 25L2530110
```

---

#### raw_zrsd002 (Sales Orders & Billing)
**Purpose:** Customer orders and billing data

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | SERIAL | No | Primary key |
| `billing_document` | VARCHAR(50) | No | Billing document number |
| `billing_item` | INTEGER | No | Billing item number |
| `billing_date` | TIMESTAMP | Yes | Billing date |
| `customer_name` | VARCHAR(200) | Yes | Customer name (from "Name of Bill to") |
| `material` | VARCHAR(50) | Yes | Material code |
| `material_desc` | VARCHAR(200) | Yes | Material description |
| `billing_qty` | NUMERIC(18,4) | Yes | Billed quantity |
| `net_value` | NUMERIC(18,4) | Yes | Net value |
| `sales_office` | VARCHAR(20) | Yes | Sales office |
| `dist_channel` | VARCHAR(20) | Yes | Distribution channel |
| `so_number` | VARCHAR(50) | Yes | Sales order number |
| `so_date` | TIMESTAMP | Yes | Sales order date |
| `doc_reference_od` | VARCHAR(50) | Yes | Document reference (OD) |
| `source_file` | VARCHAR(100) | Yes | Source Excel filename |
| `source_row` | INTEGER | Yes | Row number in Excel |
| `loaded_at` | TIMESTAMP | No | DB load timestamp |
| `raw_data` | JSONB | Yes | Full raw row as JSON |
| `row_hash` | VARCHAR(32) | Yes | MD5 hash for dedup (excludes source_file) |

**Business Keys:**
- Unique constraint: `(billing_document, billing_item)`
- Deduplication: `row_hash` computed from `raw_data` only (not `source_file`)
- Upsert mode: Uploading overlapping files updates existing records, inserts new ones

**Indexes:**
- `idx_zrsd002_billing_doc` on `billing_document`
- `idx_zrsd002_customer` on `customer_name`
- `idx_zrsd002_material` on `material`
- `idx_zrsd002_billing_date` on `billing_date`
- Unique index on `row_hash`

---

#### raw_zrsd006 (Billing Documents)
**Purpose:** Invoices and billing details

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | SERIAL | No | Primary key |
| `billing_document` | VARCHAR(20) | No | Invoice number |
| `billing_date` | DATE | No | Invoice date |
| `sales_order` | VARCHAR(20) | Yes | Referenced SO |
| `customer_code` | VARCHAR(20) | No | Billed customer |
| `material_code` | VARCHAR(40) | No | Billed product |
| `billing_qty` | NUMERIC(15,3) | Yes | Invoiced quantity |
| `net_value` | NUMERIC(15,2) | Yes | Net invoice amount |
| `distribution_channel` | VARCHAR(2) | Yes | Sales channel |
| `created_at` | TIMESTAMP | No | DB load timestamp |

---

#### raw_cooispi (Production Orders)
**Purpose:** Manufacturing order details

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | SERIAL | No | Primary key |
| `order_number` | VARCHAR(20) | No | Production order number |
| `material_code` | VARCHAR(40) | No | Produced material |
| `order_qty` | NUMERIC(15,3) | Yes | Planned quantity |
| `delivered_qty` | NUMERIC(15,3) | Yes | Actual output |
| `unit` | VARCHAR(3) | Yes | UOM |
| `plant` | VARCHAR(4) | Yes | Production plant |
| `order_type` | VARCHAR(4) | Yes | Order type (MTO/MTS) |
| `system_status` | VARCHAR(50) | Yes | Status (e.g., "REL", "CNF", "TECO") |
| `start_date` | DATE | Yes | Planned start |
| `finish_date` | DATE | Yes | Planned finish |
| `actual_start` | DATE | Yes | Actual start |
| `actual_finish` | DATE | Yes | Actual completion |
| `batch_number` | VARCHAR(20) | Yes | Production batch |
| `created_at` | TIMESTAMP | No | DB load timestamp |

---

#### raw_zrfi005 (AR Aging)
**Purpose:** Accounts receivable aging data

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | SERIAL | No | Primary key |
| `customer_code` | VARCHAR(20) | No | Debtor customer |
| `customer_name` | VARCHAR(200) | Yes | Customer name |
| `invoice_number` | VARCHAR(20) | No | Invoice reference |
| `invoice_date` | DATE | No | Invoice date |
| `due_date` | DATE | Yes | Payment due date |
| `amount` | NUMERIC(15,2) | No | Invoice amount |
| `outstanding` | NUMERIC(15,2) | No | Remaining balance |
| `aging_bucket` | VARCHAR(20) | Yes | Age category |
| `created_at` | TIMESTAMP | No | DB load timestamp |

---

#### raw_cogs (Cost of Goods Sold)
**Purpose:** Product cost information

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | SERIAL | No | Primary key |
| `material_code` | VARCHAR(40) | No | Product |
| `plant` | VARCHAR(4) | No | Plant |
| `standard_cost` | NUMERIC(15,2) | Yes | Standard cost per unit |
| `moving_avg_cost` | NUMERIC(15,2) | Yes | Moving average cost |
| `currency` | VARCHAR(3) | Yes | Currency code |
| `effective_date` | DATE | Yes | Cost effective date |
| `created_at` | TIMESTAMP | No | DB load timestamp |

---

#### raw_zrsd004 (Customer Master)
**Purpose:** Customer reference data

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | SERIAL | No | Primary key |
| `customer_code` | VARCHAR(20) | No | Unique customer ID |
| `customer_name` | VARCHAR(200) | No | Customer name |
| `address` | TEXT | Yes | Full address |
| `city` | VARCHAR(100) | Yes | City |
| `postal_code` | VARCHAR(20) | Yes | Postal code |
| `country` | VARCHAR(3) | Yes | Country code |
| `contact_person` | VARCHAR(100) | Yes | Contact name |
| `phone` | VARCHAR(30) | Yes | Phone number |
| `email` | VARCHAR(100) | Yes | Email address |
| `created_at` | TIMESTAMP | No | DB load timestamp |

---

#### raw_zrmm024 (Material Master)
**Purpose:** Material/product reference data

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | SERIAL | No | Primary key |
| `material_code` | VARCHAR(40) | No | Unique material ID |
| `description` | VARCHAR(200) | No | Material description |
| `material_type` | VARCHAR(4) | Yes | Type (FERT, HALB, ROH) |
| `base_uom` | VARCHAR(3) | Yes | Base unit of measure |
| `material_group` | VARCHAR(20) | Yes | Product category |
| `plant` | VARCHAR(4) | Yes | Plant |
| `created_at` | TIMESTAMP | No | DB load timestamp |

---

### Dimension Tables

#### dim_material
**Purpose:** Material master dimension

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `material_id` | SERIAL | No | Surrogate key |
| `material_code` | VARCHAR(40) | No | Natural key (business key) |
| `description` | VARCHAR(200) | Yes | Product name |
| `material_type` | VARCHAR(10) | Yes | FERT/HALB/ROH/VERP |
| `base_uom` | VARCHAR(3) | Yes | Base unit (KG/PC/L) |
| `sales_uom` | VARCHAR(3) | Yes | Sales unit |
| `conversion_factor` | NUMERIC(10,3) | Yes | Base to sales conversion |
| `material_group` | VARCHAR(20) | Yes | Product category |
| `plant` | VARCHAR(4) | Yes | Primary plant |
| `is_active` | BOOLEAN | Yes | Active flag |
| `created_at` | TIMESTAMP | No | Record creation |
| `updated_at` | TIMESTAMP | Yes | Last update |

**Unique Index:** `material_code`

**Material Types:**
- `FERT` - Finished goods (P01)
- `HALB` - Semi-finished (P02)
- `ROH` - Raw materials (P03)
- `VERP` - Packaging materials

---

#### dim_customer
**Purpose:** Customer master dimension

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `customer_id` | SERIAL | No | Surrogate key |
| `customer_code` | VARCHAR(20) | No | Natural key |
| `customer_name` | VARCHAR(200) | No | Customer name |
| `city` | VARCHAR(100) | Yes | City |
| `country` | VARCHAR(3) | Yes | Country code |
| `customer_group` | VARCHAR(10) | Yes | Segmentation |
| `credit_limit` | NUMERIC(15,2) | Yes | Credit limit |
| `payment_terms` | VARCHAR(10) | Yes | Payment terms |
| `is_active` | BOOLEAN | Yes | Active flag |
| `created_at` | TIMESTAMP | No | Record creation |

**Unique Index:** `customer_code`

---

#### dim_location
**Purpose:** Plant and storage location dimension

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `location_id` | SERIAL | No | Surrogate key |
| `plant` | VARCHAR(4) | No | Plant code |
| `storage_location` | VARCHAR(4) | Yes | SLOC code |
| `location_name` | VARCHAR(100) | Yes | Descriptive name |
| `location_type` | VARCHAR(20) | Yes | Warehouse/Production/Transit |
| `is_active` | BOOLEAN | Yes | Active flag |

**Unique Index:** `plant, storage_location`

---

#### dim_date
**Purpose:** Date dimension for time-based analytics

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `date_id` | SERIAL | No | Surrogate key |
| `date` | DATE | No | Natural key |
| `year` | INTEGER | No | Year (2025) |
| `quarter` | INTEGER | No | Quarter (1-4) |
| `month` | INTEGER | No | Month (1-12) |
| `week` | INTEGER | No | Week of year (1-53) |
| `day_of_month` | INTEGER | No | Day (1-31) |
| `day_of_week` | INTEGER | No | Day (1-7) |
| `day_name` | VARCHAR(10) | No | Monday/Tuesday/etc |
| `is_weekend` | BOOLEAN | No | Weekend flag |
| `is_holiday` | BOOLEAN | Yes | Holiday flag |

**Unique Index:** `date`

**Coverage:** 2020-01-01 to 2030-12-31

---

### Fact Tables

#### fact_inventory
**Purpose:** Net inventory positions by material/location

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `inventory_id` | SERIAL | No | Primary key |
| `material_id` | INTEGER | No | FK to dim_material |
| `location_id` | INTEGER | No | FK to dim_location |
| `date_id` | INTEGER | No | FK to dim_date |
| `quantity` | NUMERIC(15,3) | No | Net quantity |
| `value` | NUMERIC(15,2) | Yes | Inventory value |
| `unit` | VARCHAR(3) | Yes | UOM |
| `last_movement_date` | DATE | Yes | Last stock change |
| `movement_count` | INTEGER | Yes | Number of movements |
| `created_at` | TIMESTAMP | No | ETL timestamp |

**Indexes:**
- PK: `inventory_id`
- FK: `material_id`, `location_id`, `date_id`
- Composite: `(material_id, location_id, date_id)` UNIQUE

**Grain:** One row per material/location/date combination

---

#### fact_production
**Purpose:** Production order execution details

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `production_id` | SERIAL | No | Primary key |
| `order_number` | VARCHAR(20) | No | Production order |
| `batch_number` | VARCHAR(20) | Yes | Batch identifier |
| `material_id` | INTEGER | No | FK to dim_material |
| `date_id` | INTEGER | No | FK to dim_date (production date) |
| `order_qty` | NUMERIC(15,3) | Yes | Planned quantity |
| `delivered_qty` | NUMERIC(15,3) | Yes | Actual output |
| `unit` | VARCHAR(3) | Yes | UOM |
| `yield_pct` | NUMERIC(5,2) | Yes | Yield percentage |
| `plant` | VARCHAR(4) | Yes | Production plant |
| `order_type` | VARCHAR(10) | Yes | MTO/MTS |
| `system_status` | VARCHAR(50) | Yes | Order status |
| `start_date` | DATE | Yes | Production start |
| `finish_date` | DATE | Yes | Production finish |
| `created_at` | TIMESTAMP | No | ETL timestamp |

**Indexes:**
- PK: `production_id`
- FK: `material_id`, `date_id`
- Unique: `order_number`
- Index: `batch_number`

**Grain:** One row per production order

---

#### fact_billing
**Purpose:** Sales and billing transactions

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `billing_id` | SERIAL | No | Primary key |
| `sales_order` | VARCHAR(20) | Yes | SO reference |
| `billing_document` | VARCHAR(20) | No | Invoice number |
| `customer_id` | INTEGER | No | FK to dim_customer |
| `material_id` | INTEGER | No | FK to dim_material |
| `date_id` | INTEGER | No | FK to dim_date (billing date) |
| `billing_qty` | NUMERIC(15,3) | Yes | Invoiced quantity |
| `sales_amount` | NUMERIC(15,2) | Yes | Net revenue |
| `cost_amount` | NUMERIC(15,2) | Yes | COGS |
| `gross_margin` | NUMERIC(15,2) | Yes | Revenue - COGS |
| `distribution_channel` | VARCHAR(2) | Yes | Sales channel |
| `plant` | VARCHAR(4) | Yes | Fulfilling plant |
| `created_at` | TIMESTAMP | No | ETL timestamp |

**Indexes:**
- PK: `billing_id`
- FK: `customer_id`, `material_id`, `date_id`
- Index: `sales_order`, `billing_document`

**Grain:** One row per billing document line item

---

#### fact_production_chain
**Purpose:** Material genealogy linking (P03→P02→P01)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `chain_id` | SERIAL | No | Primary key |
| `parent_batch` | VARCHAR(20) | No | Input batch |
| `child_batch` | VARCHAR(20) | No | Output batch |
| `parent_material_id` | INTEGER | No | FK to dim_material (input) |
| `child_material_id` | INTEGER | No | FK to dim_material (output) |
| `parent_qty` | NUMERIC(15,3) | Yes | Consumed quantity |
| `child_qty` | NUMERIC(15,3) | Yes | Produced quantity |
| `yield_pct` | NUMERIC(5,2) | Yes | Conversion yield |
| `production_date` | DATE | Yes | When produced |
| `created_at` | TIMESTAMP | No | ETL timestamp |

**Indexes:**
- PK: `chain_id`
- Index: `parent_batch`, `child_batch`
- FK: `parent_material_id`, `child_material_id`

**Grain:** One row per parent-child batch relationship

**Example:**
```
parent_batch | child_batch | parent_material | child_material | yield_pct
-------------|-------------|-----------------|----------------|----------
25L2520110   | 25L2530110  | P03-11111       | P02-67890      | 95.0
25L2530110   | 25L2535110  | P02-67890       | P01-12345      | 96.8
```

---

#### fact_alert
**Purpose:** System alerts and notifications

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `alert_id` | SERIAL | No | Primary key |
| `alert_type` | VARCHAR(50) | No | Type (stuck_transit/low_yield/etc) |
| `severity` | VARCHAR(20) | No | critical/warning/info |
| `title` | VARCHAR(200) | No | Alert title |
| `description` | TEXT | Yes | Detailed description |
| `related_entity` | VARCHAR(100) | Yes | Batch/customer/material |
| `material_id` | INTEGER | Yes | FK to dim_material |
| `customer_id` | INTEGER | Yes | FK to dim_customer |
| `created_at` | TIMESTAMP | No | When alert triggered |
| `acknowledged_at` | TIMESTAMP | Yes | When acknowledged |
| `resolved_at` | TIMESTAMP | Yes | When resolved |
| `status` | VARCHAR(20) | No | active/acknowledged/resolved |

**Indexes:**
- PK: `alert_id`
- Index: `status`, `severity`, `created_at`

**Grain:** One row per alert instance

---

### Authentication Tables

#### users
**Purpose:** User accounts

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | SERIAL | No | Primary key |
| `username` | VARCHAR(50) | No | Login username |
| `email` | VARCHAR(100) | No | Email address |
| `hashed_password` | VARCHAR(200) | No | Bcrypt hash |
| `role` | VARCHAR(20) | No | admin/manager/analyst |
| `is_active` | BOOLEAN | No | Account active flag |
| `created_at` | TIMESTAMP | No | Account creation |
| `last_login` | TIMESTAMP | Yes | Last login timestamp |

**Unique:** `username`, `email`

---

## Data Lineage

### Raw → Dimension → Fact Flow

```mermaid
graph LR
    subgraph "Raw Layer"
        MB51[raw_mb51]
        ZRSD002[raw_zrsd002]
        COOISPI[raw_cooispi]
        ZRMM024[raw_zrmm024]
        ZRSD004[raw_zrsd004]
    end
    
    subgraph "Dimension Layer"
        DimMaterial[dim_material]
        DimCustomer[dim_customer]
        DimLocation[dim_location]
        DimDate[dim_date]
    end
    
    subgraph "Fact Layer"
        FactInventory[fact_inventory]
        FactProduction[fact_production]
        FactBilling[fact_billing]
        FactChain[fact_production_chain]
    end
    
    ZRMM024 -->|Extract unique materials| DimMaterial
    ZRSD004 -->|Extract customers| DimCustomer
    MB51 -->|Extract plants/SLOCs| DimLocation
    
    MB51 -->|Aggregate by material/location| FactInventory
    FactInventory --> DimMaterial
    FactInventory --> DimLocation
    FactInventory --> DimDate
    
    COOISPI -->|Production orders| FactProduction
    FactProduction --> DimMaterial
    FactProduction --> DimDate
    
    ZRSD002 -->|Sales data| FactBilling
    FactBilling --> DimCustomer
    FactBilling --> DimMaterial
    FactBilling --> DimDate
    
    MB51 -->|MVT 261 linkage| FactChain
    FactChain --> DimMaterial
```

### Transformation Examples

**Example 1: raw_mb51 → fact_inventory**

```sql
-- Simplified transformation logic
INSERT INTO fact_inventory (material_id, location_id, date_id, quantity, value)
SELECT 
    dm.material_id,
    dl.location_id,
    dd.date_id,
    SUM(CASE 
        WHEN movement_type IN ('101', '311', '561') THEN quantity  -- Receipts
        WHEN movement_type IN ('261', '601', '311') THEN -quantity  -- Issues
        ELSE 0 
    END) as net_quantity,
    SUM(quantity * price) as value
FROM raw_mb51 mb
INNER JOIN dim_material dm ON mb.material_code = dm.material_code
INNER JOIN dim_location dl ON mb.plant = dl.plant AND mb.storage_location = dl.storage_location
INNER JOIN dim_date dd ON mb.posting_date = dd.date
GROUP BY dm.material_id, dl.location_id, dd.date_id;
```

**Example 2: raw_cooispi + raw_mb51 → fact_production_chain**

```sql
-- P02 to P01 linking
INSERT INTO fact_production_chain (parent_batch, child_batch, parent_material_id, child_material_id, yield_pct)
SELECT 
    p02.batch_number as parent_batch,
    p01.batch_number as child_batch,
    dm_p02.material_id as parent_material_id,
    dm_p01.material_id as child_material_id,
    (p01.delivered_qty / p02.delivered_qty * 100) as yield_pct
FROM raw_cooispi p02
INNER JOIN raw_mb51 mvt ON mvt.batch_number = p02.batch_number AND mvt.movement_type = '261'
INNER JOIN raw_cooispi p01 ON p01.order_number = mvt.order_number
INNER JOIN dim_material dm_p02 ON p02.material_code = dm_p02.material_code
INNER JOIN dim_material dm_p01 ON p01.material_code = dm_p01.material_code
WHERE dm_p02.material_type = 'HALB'  -- P02
  AND dm_p01.material_type = 'FERT'; -- P01
```

---

## Migrations

### Alembic Setup

**Initialize Alembic:**
```bash
cd /path/to/alkana-dashboard
alembic init alembic
```

**Configure `alembic.ini`:**
```ini
sqlalchemy.url = postgresql://alkana_user:password@localhost:5432/alkana_dashboard
```

**Configure `alembic/env.py`:**
```python
from src.db.database import Base
from src.db.models import *  # Import all models
target_metadata = Base.metadata
```

### Creating Migrations

**Auto-generate migration:**
```bash
alembic revision --autogenerate -m "Add distribution_channel to fact_billing"
```

**Manual migration:**
```bash
alembic revision -m "Add index on fact_inventory.material_id"
```

**Edit migration file:**
```python
# alembic/versions/abc123_add_index.py
def upgrade():
    op.create_index(
        'idx_fact_inventory_material',
        'fact_inventory',
        ['material_id']
    )

def downgrade():
    op.drop_index('idx_fact_inventory_material')
```

### Running Migrations

**Upgrade to latest:**
```bash
alembic upgrade head
```

**Upgrade to specific version:**
```bash
alembic upgrade abc123
```

**Downgrade one version:**
```bash
alembic downgrade -1
```

**Show current version:**
```bash
alembic current
```

**Show migration history:**
```bash
alembic history
```

### Migration Best Practices

1. **Always backup before migrating production**
2. **Test migrations on dev/staging first**
3. **Write both upgrade() and downgrade()**
4. **Avoid data migrations in schema migrations** (use separate scripts)
5. **Review auto-generated migrations carefully**
6. **Document breaking changes in migration docstring**

**Example Data Migration:**
```python
# alembic/versions/def456_backfill_yield.py
"""Backfill yield_pct in fact_production

Revision ID: def456
"""

def upgrade():
    # Add column
    op.add_column('fact_production', sa.Column('yield_pct', sa.Numeric(5,2)))
    
    # Backfill data
    op.execute("""
        UPDATE fact_production
        SET yield_pct = (delivered_qty / NULLIF(order_qty, 0) * 100)
        WHERE order_qty > 0
    """)

def downgrade():
    op.drop_column('fact_production', 'yield_pct')
```

---

## Materialized Views

### view_sales_performance

**Purpose:** Pre-aggregated sales metrics for dashboard

**Definition:**
```sql
CREATE MATERIALIZED VIEW view_sales_performance AS
SELECT 
    fb.billing_document,
    fb.sales_order,
    dc.customer_name,
    dm.material_code,
    dm.description as material_description,
    dd.date,
    fb.sales_amount,
    fb.billing_qty,
    fb.distribution_channel,
    CASE fb.distribution_channel
        WHEN '10' THEN 'Direct Sales'
        WHEN '20' THEN 'Distributor'
        WHEN '30' THEN 'Retail'
        ELSE 'Other'
    END as channel_name
FROM fact_billing fb
INNER JOIN dim_customer dc ON fb.customer_id = dc.customer_id
INNER JOIN dim_material dm ON fb.material_id = dm.material_id
INNER JOIN dim_date dd ON fb.date_id = dd.date_id;

CREATE UNIQUE INDEX idx_view_sales_perf_billing ON view_sales_performance(billing_document);
```

**Refresh:**
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY view_sales_performance;
```

---

### view_inventory_summary

**Purpose:** Current inventory snapshot

**Definition:**
```sql
CREATE MATERIALIZED VIEW view_inventory_summary AS
SELECT 
    dm.material_code,
    dm.description,
    dl.plant,
    dl.storage_location,
    SUM(fi.quantity) as current_quantity,
    dm.base_uom as unit,
    SUM(fi.value) as inventory_value,
    MAX(fi.last_movement_date) as last_movement_date
FROM fact_inventory fi
INNER JOIN dim_material dm ON fi.material_id = dm.material_id
INNER JOIN dim_location dl ON fi.location_id = dl.location_id
GROUP BY dm.material_code, dm.description, dl.plant, dl.storage_location, dm.base_uom;
```

---

### view_production_yield

**Purpose:** Production yield metrics

**Definition:**
```sql
CREATE MATERIALIZED VIEW view_production_yield AS
SELECT 
    fp.batch_number,
    dm.material_code,
    dm.description,
    fp.order_qty,
    fp.delivered_qty,
    fp.yield_pct,
    fp.plant,
    dd.date as production_date,
    CASE 
        WHEN fp.yield_pct >= 95 THEN 'Excellent'
        WHEN fp.yield_pct >= 85 THEN 'Good'
        WHEN fp.yield_pct >= 75 THEN 'Fair'
        ELSE 'Poor'
    END as yield_rating
FROM fact_production fp
INNER JOIN dim_material dm ON fp.material_id = dm.material_id
INNER JOIN dim_date dd ON fp.date_id = dd.date_id
WHERE fp.delivered_qty IS NOT NULL;
```

---

### Refresh Schedule

**Automated refresh via cron:**
```bash
# Refresh all materialized views daily at 6:30 AM
30 6 * * * psql -U alkana_user -d alkana_dashboard -c "REFRESH MATERIALIZED VIEW CONCURRENTLY view_sales_performance; REFRESH MATERIALIZED VIEW CONCURRENTLY view_inventory_summary; REFRESH MATERIALIZED VIEW CONCURRENTLY view_production_yield;"
```

**Manual refresh:**
```python
# In Python ETL
from src.db.database import engine

with engine.connect() as conn:
    conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY view_sales_performance")
    conn.commit()
```

---

## Indexes & Performance

### Index Strategy

**Primary Keys:** Automatically indexed

**Foreign Keys:** Indexed for join performance
```sql
CREATE INDEX idx_fact_inventory_material_id ON fact_inventory(material_id);
CREATE INDEX idx_fact_inventory_location_id ON fact_inventory(location_id);
CREATE INDEX idx_fact_inventory_date_id ON fact_inventory(date_id);
```

**Filter Columns:** Indexed for WHERE clauses
```sql
CREATE INDEX idx_raw_mb51_posting_date ON raw_mb51(posting_date);
CREATE INDEX idx_fact_alert_status ON fact_alert(status);
```

**Composite Indexes:** For multi-column queries
```sql
CREATE INDEX idx_fact_inventory_composite ON fact_inventory(material_id, location_id, date_id);
```

### Query Optimization

**Use EXPLAIN ANALYZE:**
```sql
EXPLAIN ANALYZE
SELECT m.material_code, SUM(i.quantity)
FROM fact_inventory i
JOIN dim_material m ON i.material_id = m.material_id
WHERE m.material_type = 'FERT'
GROUP BY m.material_code;
```

**Optimize with covering indexes:**
```sql
-- If query frequently accesses specific columns
CREATE INDEX idx_fact_inventory_covering ON fact_inventory(material_id, quantity, value);
```

**Partition large tables:**
```sql
-- For fact_inventory (if >10M rows)
CREATE TABLE fact_inventory_2025_01 PARTITION OF fact_inventory
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

### Performance Monitoring

**Check table sizes:**
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Check index usage:**
```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

**Unused indexes:**
```sql
SELECT 
    schemaname,
    tablename,
    indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexname NOT LIKE '%_pkey';  -- Exclude primary keys
```

---

## Backup & Recovery

### Automated Backups

**Daily backup script:**
```bash
#!/bin/bash
# /opt/alkana/backup-db.sh

BACKUP_DIR="/var/backups/alkana"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="alkana_dashboard_${DATE}.sql.gz"

mkdir -p $BACKUP_DIR

pg_dump -U alkana_user alkana_dashboard | gzip > "$BACKUP_DIR/$FILENAME"

# Keep last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $FILENAME"
```

**Schedule with cron:**
```bash
# Daily at 2 AM
0 2 * * * /opt/alkana/backup-db.sh
```

### Restore from Backup

**Full restore:**
```bash
# Stop application
sudo systemctl stop alkana-backend

# Drop and recreate database
dropdb alkana_dashboard
createdb alkana_dashboard

# Restore
gunzip < /var/backups/alkana/alkana_dashboard_20251229_020000.sql.gz | psql -U alkana_user alkana_dashboard

# Restart application
sudo systemctl start alkana-backend
```

**Partial restore (specific table):**
```bash
pg_restore -U alkana_user -d alkana_dashboard -t fact_inventory backup.dump
```

### Point-in-Time Recovery

**Enable WAL archiving:**
```ini
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'
```

**Create base backup:**
```bash
pg_basebackup -U postgres -D /var/backups/alkana/base -Fp -Xs -P
```

---

## Database Maintenance

### Vacuum and Analyze

**Auto-vacuum (configured):**
```ini
# postgresql.conf
autovacuum = on
autovacuum_naptime = 1min
```

**Manual vacuum:**
```sql
-- Full database
VACUUM ANALYZE;

-- Specific table
VACUUM ANALYZE fact_inventory;

-- Reclaim space (locks table)
VACUUM FULL fact_inventory;
```

### Statistics Update

```sql
ANALYZE fact_inventory;
ANALYZE fact_production;
ANALYZE fact_billing;
```

---

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md#database-issues) for database-specific issues.

**Common Issues:**
- Connection pool exhausted → Increase `pool_size`
- Slow queries → Add indexes, refresh materialized views
- Disk space full → Vacuum, archive old data
- Deadlocks → Review transaction isolation levels

---

## Related Documentation

- [system-architecture.md](./system-architecture.md) - Overall architecture
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Database setup in production
- [API_REFERENCE.md](./API_REFERENCE.md) - API endpoints and data models

---

**Last Updated:** December 30, 2025
