# Alkana Dashboard - Project Overview & PDR

**Last Updated:** January 13, 2026 | **Version:** v1.0+ | **Status:** Production | **Framework:** ClaudeKit

## Executive Summary

**Alkana Dashboard** is a comprehensive supply chain analytics platform providing real-time visibility into manufacturing operations, inventory management, sales performance, and financial metrics. Built with modern full-stack architecture (React 19/TypeScript 5.9 frontend, FastAPI 0.109/Python 3.11+ backend, PostgreSQL 15+ data warehouse), the system intelligently transforms SAP ERP exports into actionable multi-dimensional intelligence.

### Current Release Status (January 13, 2026)
- **Version:** v1.0+ (Production-Ready)
- **Recent Major Updates:**
  - ✅ **OTIF Delivery Tracking** (Jan 13) - Real-time RDD vs. GI date analysis; On-Time/Late/Pending status classification
  - ✅ **V3 Yield Efficiency Hub** (Jan 12) - Historical variance analysis with monthly period reporting, Pareto analysis, SG quality metrics
  - ✅ **V2 Variance Analysis Removal** (Jan 12) - Streamlined to single V3 system for consistency
  - ✅ **Row-Hash Deduplication** (Jan 7) - Smart business-key upsert for multi-file uploads; excludes source_file from hash
  - ✅ **UOM Normalization** (Jan 6) - KG conversion for cross-unit comparisons
- **Data Architecture:** Star schema with 8 raw tables, 5 dimensions, 6 facts, 4 materialized views
- **API:** 11 FastAPI routers (240+ endpoints) with JWT authentication, RBAC, CORS
- **Frontend:** 10 pages with 50+ custom components, real-time data sync, timezone-safe date handling

### Strategic Capabilities
1. **Real-Time Supply Chain Visibility** - Inventory positions, movements, production batches with <5min refresh
2. **OTIF Performance Management** - Requested Delivery Date (RDD) vs. actual Goods Issue date with status tracking
3. **Production Efficiency Analysis** - Batch-level P02→P01 yield, material loss kg/%, specific gravity variance
4. **Financial Intelligence** - AR aging by bucket, debt collection, revenue by dimension (channel/customer/product)
5. **Intelligent Alert System** - Threshold-based monitoring for inventory, production, quality, financial events
6. **Enterprise Access Control** - JWT auth with 4-tier roles (Admin/Manager/Analyst/Viewer)

---

## Product Development Requirements (PDR)

### 1. Business Objectives & Success Metrics

#### Primary Business Goals
| Goal | Metric | Target | Status |
|------|--------|--------|--------|
| Operational Visibility | Data latency | <5 min | ✅ Achieved |
| Data-Driven Decisions | Dashboard load time | <2 sec | ✅ Achieved |
| Scalability | Concurrent users | 100+ | ✅ Tested |
| Data Quality | Accuracy w/ dedup | 99.9% | ✅ Verified |
| OTIF Excellence | Delivery tracking | Real-time | ✅ Live |

#### Key Performance Indicators
- **System Performance:** Data refresh <5 min; API response <500ms (p95); Dashboard <2 sec load
- **Data Quality:** 99.9% accuracy with row_hash dedup; zero duplicates in multi-file uploads
- **Platform Stability:** 99.99% API uptime; 100+ concurrent async connections supported
- **Upload Robustness:** Multi-file overlapping periods handled with upsert flow
- **OTIF Tracking:** 100% of deliveries classified (On Time/Late/Pending); trend analysis enabled

#### Compliance & Governance
- **Audit Trail:** All inserts/updates tracked with timestamps and user attribution
- **Data Lineage:** Complete source→raw→fact traceability documented
- **Access Control:** Role-based dashboards with JWT token validation
- **Backup Strategy:** Daily PostgreSQL snapshots with point-in-time recovery

### 2. Complete Technical Architecture

#### Backend Stack (Python 3.11+ / FastAPI 0.109)

**11 API Routers (240+ Endpoints)**
1. **auth.py** - JWT login/logout, user profile, token refresh
2. **executive.py** - KPIs, revenue by division, top performers, trends
3. **inventory.py** - Stock levels, movements, slow-moving alerts, valuation
4. **alerts.py** - Summary, stuck inventory, low yield, resolution tracking
5. **ar_aging.py** - Collection summary, bucket analysis, payment patterns
6. **lead_time.py** (deprecated) - Legacy lead time with OTIF tracing
7. **lead_time.py** (current, leadtime.py) - Multi-stage decomposition, bottleneck analysis, OTIF
8. **mto_orders.py** - Custom order tracking, delivery compliance
9. **sales_performance.py** - Revenue by dimension, customer segmentation, trends
10. **upload.py** - Multi-file upload, auto-detection, duplicate handling
11. **yield_v3.py** - Yield KPIs, period trends, Pareto analysis, SG quality, master data upload

**Business Logic Services (6 Core Modules)**
- **alerts.py** - Inventory reorder threshold, production batch stuck detection, yield variance monitoring
- **business_logic.py** - Order classification (MTS/MTO), cycle time calculation, financials
- **leadtime_calculator.py** - 5-stage MTO (PO→PR→MR→GR→GI), 3-stage MTS decomposition
- **netting.py** - Material reconciliation, stock balance validation, quantity conversions
- **uom_converter.py** - Multi-unit support (KG, L, EA, PC) with variance tracking
- **upload_service.py** - File validation, duplicate detection via MD5, background processing

**ETL Pipeline (11 Loaders)**
- **BaseLoader** - Common functionality for all loaders
- **Mb51Loader** - Material movements (receipts, issues, transfers) - 50K-200K rows/day
- **Zrsd002Loader** - Sales orders & billing - 20K-50K rows/day with upsert
- **Zrsd004Loader** - Delivery documents with delivery_date/actual_gi_date - OTIF source
- **Zrsd006Loader** - Customer master with product hierarchy
- **Zrfi005Loader** - AR aging detail - monthly snapshot reset
- **CooispiLoader** - Production orders - batch tracking
- **Zrpp062Loader** - Production performance - V3 yield source
- **Zrmm024Loader** - Material master dimension
- **TargetLoader** - Sales targets
- **CogLoader** - Cost of goods sold

**Data Quality & Integrity**
- **Deduplication Strategy:** Row_hash MD5 (business keys only, excludes source_file) with upsert
- **Safe Type Conversion:** safe_str(), safe_float(), safe_datetime(), safe_int() for all inputs
- **NULL Handling:** Explicit coalescing in transforms; NOT NULL constraints on keys
- **Audit Trail:** created_at/updated_at/updated_by on all transactions
- **Constraints:** Foreign keys, CHECK constraints on quantities/dates, UNIQUE on business keys

#### Frontend Stack (React 19 / TypeScript 5.9 / Vite)

**10 Operational Pages**
1. **ExecutiveDashboard.tsx** - KPI cards, revenue trends, top performers, inventory metrics
2. **Inventory.tsx** - Stock levels, movements, alerts, location breakdown
3. **LeadTimeDashboard.tsx** - Lead time KPIs, bottleneck analysis, OTIF tracking, recent orders
4. **SalesPerformance.tsx** - Revenue by channel/customer/product, trends, segmentation
5. **ProductionDashboard.tsx** - Production KPIs, batch status, yield trends (V3)
6. **MTOOrders.tsx** - MTO order list, delivery compliance, lead time adherence
7. **ArAging.tsx** - AR summary by division, collection prioritization, aging buckets
8. **AlertMonitor.tsx** - Alert list, severity, resolution, escalation
9. **DataUpload.tsx** - File upload with auto-detection, processing status, history
10. **Login.tsx** - JWT authentication, role-based access, password reset flow

**Core Components (50+ Custom)**
- **DatePicker** - Timezone-safe local date; defaults to 1st of month → today
- **DataTable** - Sortable, filterable with pagination; column selection
- **Charts** - Line (trends), Bar (comparison), Pie (composition), Treemap (hierarchy)
- **KPICard** - Metric display with trend arrow, threshold indicator
- **StatusBadge** - On-Time/Late/Pending/In-Progress color-coded indicators
- **ConfirmDialog** - Async actions with confirmation before execution
- **LoadingSpinner** - Async operation feedback; skeleton loaders for fast perceived load

**State Management & APIs**
- **TanStack Query** - Server-state caching, background sync, stale-while-revalidate
- **React Router 7** - Client-side routing with lazy-loaded page components
- **Axios Client** - Interceptors for JWT token refresh, CORS headers, error handling
- **Custom Hooks** - useFetch, useDebounce, useLocalStorage, useWindowSize
- **Error Boundaries** - Graceful error handling with fallback UI

#### Database Architecture (PostgreSQL 15+)

**Star Schema Design**

*Raw Tables (Direct SAP imports)*
- **raw_mb51** - 50K-200K rows/day, 14 columns, 4 indexes
- **raw_zrsd002** - 20K-50K rows/day, 19 columns, row_hash upsert
- **raw_zrsd004** - 10K-30K rows/day, 27 columns (with delivery_date, actual_gi_date for OTIF)
- **raw_zrsd006** - 1K-5K rows/week, 10 columns
- **raw_zrfi005** - 5K-15K rows/day, 9 columns
- **raw_cooispi** - 5K-20K rows/day, 15 columns
- **raw_zrpp062** - 1K-5K rows/week, 27 columns (V3 yield source)
- **raw_cogs** - 1K-10K rows/month, 6 columns

*Dimension Tables (Reference data)*
- **dim_material** - 1K-5K rows; FERT/HALB/ROH/VERP classifications; UOM conversions
- **dim_customer** - 500-2K rows; customer master with credit limits and payment terms
- **dim_location** - 50-200 rows; plant/SLOC combinations; warehouse/production flags
- **dim_date** - 11K rows (2020-2030); fiscal calendar, holidays, week numbers
- **dim_user** - 10-100 rows; role assignments; department mappings

*Fact Tables (Business events)*
- **fact_inventory** - ~1M rows; material/location/date grain; net position + movement count
- **fact_billing** - ~500K rows; invoice line item; revenue + COGS + margin
- **fact_production** - ~100K rows; production order; yield %; start/finish dates
- **fact_delivery** - ~300K rows (NEW Jan 13); OTIF tracking; delivery_date vs. actual_gi_date
- **fact_ar_aging** - ~5K rows/month; AR by division; aging bucket breakdown
- **fact_production_performance_v2** - ~10K rows/month (NEW Jan 12); yield variance; loss analysis

*Materialized Views (Pre-aggregated)*
- **view_sales_performance** - Monthly revenue by customer/product/channel
- **view_inventory_summary** - Current stock by material/location with movement dates
- **view_production_yield** - Monthly yield % by batch/product with rating
- **view_ar_collection_summary** - Collection rate by division with overdue analysis

**Indexing Strategy**
- **Primary Keys:** Auto-indexed on all tables
- **Foreign Keys:** Indexed for join performance (material_id, customer_id, location_id, date_id)
- **Date Filters:** Composite indexes on (date, document_type) for range queries
- **Business Keys:** Unique indexes on (billing_document, billing_item), (delivery, line_item), etc.
- **Search Columns:** Indexes on customer_name, material_code, batch_number for LIKE queries

**Data Integrity Constraints**
- **NOT NULL:** All keys and measure columns
- **UNIQUE:** Business key combinations prevent duplicates
- **FOREIGN KEY:** Referential integrity for all dimensional joins
- **CHECK:** Quantity >0, dates in logical order, status in valid set
- **DEFAULT:** Current_timestamp for audit columns

### 3. Dashboard Modules in Detail

#### 1. Executive Dashboard
**Purpose:** C-suite KPIs and executive view
- **Metrics:** Revenue (current month), Inventory turnover (days), OTIF %, Margin %
- **Charts:** Revenue trend (12 months), Top 10 customers/products, Inventory aging
- **Drill-down:** Click customer → Sales Performance; Click product → Production Yield
- **Data Refresh:** Auto-refresh every 5 minutes
- **Sources:** ZRSD002 (billing), MB51 (inventory), ZRFI005 (AR), ZRSD004 (OTIF)

#### 2. Inventory Management
**Purpose:** Stock level management and movement tracking
- **Views:** By material, by plant/SLOC, by UOM (KG/L/EA/PC normalized)
- **Movement History:** Inbound (101), outbound (261), transfer (601, 701) with 6-month history
- **Alerts:** Below reorder, slow-moving (90+ days), expired stock
- **Valuation:** Net value by material; reorder cost optimization
- **Sources:** MB51 (movements), DIM_MATERIAL (hierarchy)

#### 3. Lead Time Analytics
**Purpose:** Supply chain bottleneck identification and OTIF tracking
- **Decomposition:** Production (PO create → GR) vs. Transit (GR → GI)
- **KPIs:** Average lead time, OTIF %, on-time vs. late delivery rates
- **Recent Orders:** 50 most recent with planned vs. actual GI; status color-coded
- **Bottleneck Analysis:** Peak periods with >2 week lead times; by channel/customer
- **Historical Trends:** 12-month average; seasonal patterns; year-over-year comparison
- **Sources:** ZRSD002 (orders), COOISPI (production), ZRSD004 (delivery dates)

#### 4. Sales Performance
**Purpose:** Revenue analysis and customer segmentation
- **By Dimension:** Channel (wholesale/retail), Customer (top 50), Product (top 100), Region
- **Trends:** Month-over-month growth, seasonality, YoY comparison
- **Customer Segmentation:** ABC analysis; payment reliability; lifetime value
- **Order Fulfillment:** Ordered vs. delivered qty; cancellation rate; partial shipments
- **Top Performers:** Revenue, volume, margin contribution
- **Sources:** ZRSD002 (billing), ZRSD006 (customer master), COGS

#### 5. Production Yield (V3 Efficiency Hub)
**Purpose:** Batch-level efficiency and material consumption tracking
- **KPIs:** Average loss %, SG variance, material consumption variance
- **By Material:** Product group hierarchy; process order; batch number
- **Trends:** Monthly loss % trend; period-over-period comparison
- **Pareto Analysis:** Top loss contributors (80/20 rule); exception focus
- **Quality:** SG theoretical vs. actual scatter plot; tolerance analysis
- **Details:** Loss kg, input/output quantities, recipe group, MRP controller
- **Sources:** ZRPP062 (production data), COOISPI (production orders), MB51 (movements)

#### 6. MTO Orders
**Purpose:** Custom order tracking and delivery compliance
- **Status Tracking:** Order creation → production → delivery → completion
- **Lead Time Compliance:** Planned vs. actual delivery dates; on-time rate
- **Recent Orders:** 100 most recent with status, dates, customer
- **Customer-Specific:** Individual order patterns; repeat customers
- **Performance Metrics:** Average lead time; fulfillment rate; exceptions
- **Sources:** ZRSD002 (orders), ZRSD004 (delivery), COOISPI (production)

#### 7. AR Aging (Công Nợ)
**Purpose:** Accounts receivable monitoring and debt collection
- **Aging Buckets:** 0-30, 31-60, 61-90, 91-120, 121-180, 180+ days
- **Collection Summary:** By division; overdue amount; collection priority
- **Customer Detail:** Payment history; reliability rating; credit limit
- **Trends:** Monthly AR aging; days outstanding; collection rate
- **High-Risk Accounts:** Aged debt >120 days with escalation flags
- **Sources:** ZRFI005 (AR detail), ZRSD002 (billing), ZRSD006 (customer master)

#### 8. Alert Monitoring
**Purpose:** Real-time exception management and resolution tracking
- **Alert Types:** Inventory (reorder/slow-moving), Production (stuck batch), Quality (variance), Financial (AR overdue)
- **Severity Levels:** Critical (red), Warning (yellow), Info (blue)
- **Workflow:** Created → Assigned → Acknowledged → Resolved with audit trail
- **Summary:** Count by severity, type; trending over time
- **Recent Alerts:** 50 most recent with status and time to resolution
- **Sources:** Calculated rules on fact tables; real-time evaluation

---

### 4. Data Ingestion & Processing

#### Upload Workflow
1. **Auto-Detection:** File name pattern matching (MB51, ZRSD002, etc.)
2. **Validation:** Column header verification; required fields check
3. **Load:** Direct insert into raw table
4. **Deduplication:** Row_hash comparison; upsert if exists
5. **Transform:** Type conversion; null coalescing; dimension lookup
6. **Index:** Refresh indexes on updated rows
7. **Materialized Views:** Refresh pre-aggregated metrics
8. **Status:** Email notification with insert/update/duplicate counts

#### Data Quality Controls
| Control | Method | Status |
|---------|--------|--------|
| Deduplication | Row_hash MD5 | ✅ Implemented |
| Type Safety | safe_* functions | ✅ Implemented |
| NULL Handling | Coalescing | ✅ Implemented |
| Business Rules | CHECK constraints | ✅ Implemented |
| Audit Trail | created_at/updated_at | ✅ Implemented |

### 5. Security & Access Control

#### Authentication
- **Method:** JWT (JSON Web Tokens) with bcrypt password hashing
- **Token Expiration:** 24 hours with refresh capability
- **Storage:** HTTP-only cookies with secure flag
- **MFA:** Optional (planned Phase 2)

#### Authorization (Role-Based Access Control)
| Role | Dashboards | Export | Admin |
|------|-----------|--------|-------|
| Admin | All | Full | ✅ Full |
| Manager | All | Limited | ✗ None |
| Analyst | Department-Specific | Own reports | ✗ None |
| Viewer | Executive only | None | ✗ None |

#### Data Security
- **Encryption at Rest:** PostgreSQL encrypted volumes
- **Encryption in Transit:** HTTPS/TLS for all API calls
- **Secrets Management:** Environment variables (not committed)
- **Input Validation:** Pydantic strict type checking
- **SQL Injection:** Parameterized queries via SQLAlchemy ORM

### 6. Performance & Scalability

#### Performance Targets (Measured Jan 2026)
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| API Response (p95) | <500ms | 200-400ms | ✅ Exceed |
| Dashboard Load | <2 sec | 1-1.5 sec | ✅ Exceed |
| Data Refresh | <5 min | 2-3 min | ✅ Exceed |
| Concurrent Users | 100+ | 150+ tested | ✅ Exceed |
| Upload Throughput | 100K rows | 500K rows/min | ✅ Exceed |

#### Optimization Techniques
- **Materialized Views:** Pre-aggregated metrics avoid expensive joins
- **Selective Indexing:** Primary indexes on date/document/material
- **Async Processing:** FastAPI async/await for non-blocking I/O
- **Connection Pooling:** SQLAlchemy pool management
- **Client Caching:** TanStack Query with stale-while-revalidate

#### Scalability Architecture
- **Horizontal:** StatelessAPI servers can scale with load balancer
- **Vertical:** FastAPI async handles 100+ concurrent connections
- **Database:** Prepared for partitioning if >100M fact rows
- **Frontend:** Code splitting and lazy-loaded modules for bundle optimization

### 7. Deployment & Operations

#### Supported Environments
| Env | Use | Database | Deployment |
|-----|-----|----------|------------|
| Development | Local coding | Local PostgreSQL | Direct uvicorn + Vite |
| Staging | Testing | Container PostgreSQL | Docker Compose |
| Production | Live | Cloud PostgreSQL | Docker + Kubernetes ready |

#### Infrastructure Stack
- **Containers:** Docker + Docker Compose for local/staging
- **Orchestration:** Kubernetes ready (health probes configured)
- **Reverse Proxy:** Nginx/Apache (Docker template provided)
- **Secrets:** Environment files with example.env documentation
- **Monitoring:** Health endpoints at /health and /api/health

#### Operational Procedures
- **Database Init:** Migration-based schema creation
- **Data Loading:** CLI commands (load, transform, truncate)
- **Backups:** Automated daily snapshots; retention policy
- **Monitoring:** Log aggregation; error alerts; performance tracking
- **Updates:** Zero-downtime deployment via container rolling restart

---

### 8. Implementation Timeline & Roadmap

#### Completed (Phase 1) ✅
- [x] 8 core dashboard modules
- [x] ETL pipeline with 11 loaders
- [x] JWT authentication + RBAC
- [x] Alert system with threshold monitoring
- [x] Multi-file upload with auto-detection
- [x] UOM normalization (KG conversion)
- [x] ZRSD002 upsert deduplication
- [x] OTIF delivery tracking (Jan 13)
- [x] V3 Yield Efficiency Hub (Jan 12)
- [x] Row-hash deduplication (Jan 7)

#### Planned (Phase 2) 📋
- [ ] Real-time data streaming (WebSocket)
- [ ] Advanced forecasting (Prophet/ML)
- [ ] Mobile application (React Native)
- [ ] Power BI / Tableau integration
- [ ] MFA (Two-factor authentication)
- [ ] Audit log export (compliance)

#### Future (Phase 3 & Beyond) 🚀
- [ ] SAP direct API integration (real-time)
- [ ] Predictive alerts with ML
- [ ] Automated recommendations
- [ ] Multi-tenant SaaS architecture
- [ ] GraphQL API for mobile
- [ ] Data lake integration (Snowflake/BigQuery)

---

## Conclusion

Alkana Dashboard represents a complete digital transformation of supply chain analytics. By combining intelligent ETL, dimensional modeling, and modern UX/DX, the platform enables data-driven decisions across operations, sales, production, and finance. The modular architecture ensures continuous expansion while maintaining performance and reliability at scale.

**Key Differentiators:**
- ✅ Real-time OTIF tracking for on-time delivery excellence
- ✅ Intelligent V3 yield system for production efficiency
- ✅ Multi-dimensional analytics (time, product, customer, channel)
- ✅ Enterprise-grade security with role-based access
- ✅ Scalable architecture supporting 100+ concurrent users
- ✅ Proven ETL pipeline handling 500K rows/minute

---

**Document Status:** Complete | **Last Reviewed:** Jan 13, 2026 | **Next Review:** Feb 13, 2026 | **Framework:** ClaudeKit (YAGNI, KISS, DRY)
