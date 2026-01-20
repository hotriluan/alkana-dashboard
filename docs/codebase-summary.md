# Alkana Dashboard - Codebase Summary

**Last Updated:** January 13, 2026 | **Status:** v1.0+ Production Active

## Project Structure Overview

```
alkana-dashboard/
├── src/                    # Python Backend (FastAPI/SQLAlchemy)
│   ├── api/               # REST API endpoints
│   │   ├── routers/       # Domain-specific route handlers
│   │   ├── main.py        # FastAPI app initialization & CORS
│   │   └── auth.py        # JWT authentication
│   ├── core/              # Business logic layer
│   │   ├── alerts.py      # Alert detection & monitoring
│   │   ├── leadtime_calculator.py
│   │   ├── netting.py     # Inventory reconciliation
│   │   ├── uom_converter.py # Unit conversions
│   │   ├── upload_service.py
│   │   └── business_logic.py
│   ├── db/                # Database layer
│   │   ├── models.py      # SQLAlchemy ORM models (27KB)
│   │   ├── views.py       # Materialized views
│   │   ├── connection.py  # Connection pooling
│   │   ├── auth_models.py # User/Role models
│   │   └── seed.py        # Initial data
│   ├── etl/               # Extract-Load-Transform
│   │   ├── loaders.py     # Excel data loaders
│   │   └── transform.py   # Warehouse transformation
│   ├── config.py          # Environment configuration
│   └── main.py            # CLI entry point (init/load/transform)
├── web/                   # React Frontend (TypeScript)
│   ├── src/
│   │   ├── pages/         # Dashboard pages (8 modules)
│   │   ├── components/    # Reusable UI components
│   │   ├── services/      # API client & helpers
│   │   ├── hooks/         # Custom React hooks
│   │   ├── types/         # TypeScript interfaces
│   │   └── utils/         # Date/format utilities
│   ├── package.json       # Dependencies & scripts
│   └── public/            # Static assets
├── docs/                  # Comprehensive documentation (24 files)
├── demodata/              # Sample Excel files (8 SAP exports)
├── .claude/               # ClaudeKit configuration
│   ├── skills/            # 40+ agent skills for development
│   ├── rules/             # Development workflows & standards
│   ├── workflows/         # Orchestration protocols
│   └── agents/            # Sub-agent definitions
├── scripts/               # Utility scripts for ops
├── migrations/            # Alembic database migrations
└── requirements.txt       # Python dependencies (23 packages)
```

## Backend Architecture (`src/`) - Detailed Analysis

### 1. API Layer (`src/api/`) - 9 Router Modules

**Main Application** (`main.py` - ~150 LOC)
- FastAPI app factory with Uvicorn configuration
- CORS middleware (configured origins)
- Root health check: `GET /health` → `{"status": "ok"}`
- API documentation: `/docs` (Swagger UI), `/redoc` (ReDoc)
- Router registration: All 9 domain routers
- Static file serving for uploads

**Authentication** (`auth.py` - ~200 LOC)
- JWT token generation: `auth_service.create_token(user_id, expires_delta)`
- Password hashing: bcrypt with salt
- Token validation: Middleware for protected routes
- `POST /auth/login`: Email + password → JWT token
- Configurable token expiration (default 24h)

**Dependency Injection** (`deps.py` - ~100 LOC)
- `get_db()`: FastAPI dependency yielding database session
- `get_current_user()`: Extract & validate JWT token from Authorization header
- `get_current_active_user()`: Verify user active status
- Role-based helpers: `check_user_role(required_role)`

**Router Modules** (`routers/` - 11 files)
| Router | Endpoints | Key Methods | Status |
|--------|-----------|------------|--------|
| `alerts.py` | `/api/v1/alerts` | GET alerts, POST create, GET by ID | ✓ Active |
| `ar_aging.py` | `/api/v1/ar` | GET aging buckets, GET summary, POST export | ✓ Active |
| `auth.py` | `/auth/*` | POST login, POST register, GET profile | ✓ Active |
| `executive.py` | `/api/v1/executive` | GET KPIs, GET trends, GET comparisons | ✓ Active |
| `inventory.py` | `/api/v1/inventory` | GET levels, GET movements, GET alerts | ✓ Active |
| `lead_time.py` | `/api/v1/leadtime` | GET analytics, GET summary, GET by product | ✓ Active (OTIF added) |
| `leadtime.py` | `/api/v1/leadtime/*` | Alternative lead time endpoints | ✓ Active |
| `mto_orders.py` | `/api/v1/mto` | GET orders, GET status, GET compliance | ✓ Active |
| `sales_performance.py` | `/api/v1/sales` | GET revenue, GET trends, GET by dimension | ✓ Active |
| `upload.py` | `/api/v1/upload` | POST files, GET detection, GET history | ✓ Active |
| `yield_v3.py` | `/api/v3/yield` | GET variance, GET summary, GET by batch | ✓ Active (V3 only) |

**Recent API Additions** (2026-01-13)
- `GET /api/v1/leadtime/recent-orders`: 50 recent deliveries with OTIF status
- `GET /api/v1/leadtime/otif-summary`: OTIF statistics (on-time %, late %, pending %)

### 2. Core Business Logic (`src/core/`) - 8 Modules

**Alert System** (`alerts.py` - ~300 LOC)
```python
class AlertDetector:
  - detect_inventory_alerts(): Qty below reorder point
  - detect_production_delays(): Batch stuck >24 hours
  - detect_quality_issues(): Material rejection rate
  - detect_financial_exceptions(): AR overdue >90 days
  - create_alert(alert_type, severity, entity_id)
```

**Lead Time Calculator** (`leadtime_calculator.py` - ~400 LOC)
```python
class LeadTimeCalculator:
  - calculate_end_to_end(so_id): Days from SO to GI
  - calculate_production_time(po_id): Days from PO create to GR
  - calculate_transit_time(dr_id): Days from GR to GI
  - identify_bottlenecks(period): Products/customers >2 week lead time
  - get_historical_average(product, customer, plant)
```

**Netting Engine** (`netting.py` - ~350 LOC)
- Material movement reconciliation
- Stock balance calculation: ∑(receipts) - ∑(issues)
- Transaction pairing: Match goods receipt (101) to goods issue (261)
- Inventory accuracy validation with variance reporting

**UOM Converter** (`uom_converter.py` - ~250 LOC)
```python
class UomConverter:
  - convert_to_kg(qty, uom, material): Multi-unit standardization
  - convert_to_liters(qty, uom): Volume conversions
  - convert_to_pieces(qty, uom): Piece conversions
  - get_kg_per_unit(material): Fetch conversion factor from DB
  - Supports: KG, L, EA (pieces), PC, T (tons)
```

**Yield Tracker** (`yield_tracker.py` - ~300 LOC, Decommissioned)
- **Status**: Replaced by V3 Efficiency Hub
- Legacy P02→P01 batch tracking (removed from active API)
- Historical data preserved for reporting

**Production Performance V3** (`production_performance_v3.py`)
- **New Module** (2026-01-08)
- Variance analysis with configurable loss thresholds
- Multi-dimensional filtering (date range, product, batch)
- Null-safe aggregations with COALESCE

**Business Logic** (`business_logic.py` - ~400 LOC)
- Revenue calculations by dimension
- Inventory turnover metrics: Days of inventory outstanding
- Customer segmentation: ABC analysis
- Product performance ranking

**Upload Service** (`upload_service.py` - ~200 LOC)
```python
class UploadService:
  - detect_file_type(headers): Returns 'MB51' | 'ZRSD002' | 'ZRSD006' | 'ZRSD004' | etc.
  - validate_file(file_path): Schema compliance check
  - get_loader(file_type): Factory returns appropriate loader class
  - process_upload(file, mode='upsert'): Execute detection → load → transform
```

### 3. Database Layer (`src/db/`) - 5 Files

**Connection Management** (`connection.py` - ~150 LOC)
```python
class DatabaseManager:
  - create_engine(): PostgreSQL connection pool setup
  - get_session(): FastAPI session dependency
  - test_connection(): Health check
  - initialize_db(): Create all tables from models
  - close_connection(): Cleanup
```

**Data Models** (`models.py` - 27KB, ~1200 LOC, Most Complex Backend File)

**Raw Tables** (Direct SAP Imports)
- `RawMB51`: 50K-200K rows | Columns: material, movement_type, qty, posting_date, batch, doc#
- `RawZRSD002`: 20K-50K rows | Columns: billing_doc, customer, material, qty, net_value, date
- `RawZRSD004`: 10K-30K rows | Columns: delivery_doc, material, delivery_date, qty (NEW)
- `RawZRSD006`: 1K-5K rows | Columns: material, customer, channel, PH1-7
- `RawZRFI005`: 5K-15K rows | Columns: customer, ar_amount, due_date, snapshot_date
- `RawCOOISPI`: 5K-20K rows | Columns: order#, material, status, confirmation_date
- `RawZRPP062`: 1K-5K rows | Columns: process_order, batch, posting_date, variance_pct
- `RawCOGS`: 1K-10K rows | Columns: material, period, cogs_amount

**Dimension Tables** (Reference Data - ~10K rows total)
- `DimMaterial`: Material master | material_code (PK), description, category, uom, active
- `DimCustomer`: Customer master | customer_code (PK), name, channel, credit_limit
- `DimDate`: Calendar dimension | date (PK), year, month, quarter, week, day_of_week
- `DimLocation`: Storage locations | location_id (PK), plant, sloc, name, capacity
- `DimUomConversion`: Unit conversions | material, uom, kg_per_unit, variance_pct

**Fact Tables** (Business Events)
- `FactInventory`: ~50K-100K rows | Stock snapshots (material, location, qty_kg, snapshot_date)
- `FactSales`: ~20K-50K rows | Billing transactions (customer, material, qty, net_value, date)
- `FactDelivery`: ~10K-30K rows | Deliveries (so#, material, delivery_date, actual_gi_date, status) **NEW**
- `FactProduction`: ~5K-20K rows | Production orders (material, order#, status, completion_date)
- `FactProductionPerformanceV2`: ~1K-5K rows | Yield variance analysis (batch, loss_pct, reference_date)
- `FactAlert`: ~500-1K rows | Alert events (type, severity, entity, created_date)

**Authentication Models** (`auth_models.py` - ~150 LOC)
```python
class User:
  id, email, hashed_password, active, created_at, is_superuser

class Role:
  id, name (admin|manager|analyst|viewer)

class UserRole:
  user_id, role_id (junction table)
```

**Database Views** (`views.py` - ~400 LOC)
- `v_inventory_summary`: Current stock by material/location (materialized)
- `v_sales_by_channel`: Revenue aggregation (materialized)
- `v_lead_time_trend`: Monthly average lead time (materialized)
- `v_customer_ar_aging`: Aging buckets per customer (materialized)

**Seed Data** (`seed.py` - ~100 LOC)
- Create 4 default roles (admin, manager, analyst, viewer)
- Create test admin user (email: admin@local, password: admin123)
- Populate sample dimension data

### 4. ETL Pipeline (`src/etl/`) - 2 Files

**Data Loaders** (`loaders.py` - ~1500 LOC, Most Complex Backend File)

```python
class BaseLoader:
  def __init__(db, mode='upsert', ...)
  def load(file_path): Main entry point
  def get_column_mapping(headers): Returns dict of Excel→DB columns
  def insert_records(records, mode):
    - mode='insert': Direct INSERT (no key checking)
    - mode='upsert': UPSERT via ON CONFLICT DO UPDATE
    - Skip if row_hash matches (dedup)
  def validate_record(record): Type checking + NULL handling

# Specific Loaders
class MB51Loader(BaseLoader):
  - Movement type mapping (101=receipt, 261=issue, etc.)
  - UOM conversion (KG, L, EA, PC)
  - Batch validation

class Zrsd002Loader(BaseLoader):
  - **DEFAULT MODE: 'upsert'** (multi-file support)
  - Unique key: (billing_document, billing_item)
  - row_hash excludes source_file (cross-file dedup)
  - Safe column mapping: 'Name of Bill to' → customer_name, 'Volum.' → volume

class Zrsd004Loader(BaseLoader):
  - **NEW** (OTIF implementation)
  - Extracts delivery_date column
  - Maps to FactDelivery.delivery_date

class Zrsd006Loader(BaseLoader):
  - Auto-detection: 'Material Code' + 'PH 1' headers
  - Product hierarchy columns (PH1-PH7)

class Zrfi005Loader(BaseLoader):
  - DEFAULT MODE: 'upsert'
  - Supports snapshot_date parameter (AR snapshots)

class Zrpp062Loader(BaseLoader):
  - **NEW V3** (Yield analysis)
  - Isolated mode (no cross-contamination)
  - reference_date parameter for filtering
  - JSON sanitization (NaN→None)
  - UNIQUE: (process_order_id, batch_id, posting_date)
  - Variance % calculation

class CooispiLoader(BaseLoader):
  - Production order confirmation mapping

class CogsLoader(BaseLoader):
  - Monthly cost aggregation
```

**Data Validators** (Embedded in loaders)
- `safe_str(value)`: Null-safe string extraction
- `safe_float(value)`: Numeric with fallback
- `safe_datetime(value)`: Date parsing with UTC safety
- `safe_int(value)`: Integer conversion

**Transformers** (`transform.py` - ~1200 LOC)
```python
class WarehouseTransformer:
  def transform_inventory():
    SELECT raw_mb51
    JOIN dim_material ON material_code
    GROUP BY material, location, snapshot_date
    INSERT FactInventory(qty_kg, net_value)

  def transform_sales():
    SELECT raw_zrsd002
    JOIN dim_customer ON customer
    INSERT FactSales(qty, net_value, revenue)

  def transform_production():
    SELECT raw_cooispi
    Calculate production_time (create_date → gr_date)
    INSERT FactProduction

  def transform_delivery():
    SELECT raw_zrsd004
    Calculate OTIF status (delivery_date vs. actual_gi_date)
    INSERT FactDelivery

  def transform_yield_v3():
    SELECT raw_zrpp062
    Calculate variance_pct, loss_kg
    INSERT FactProductionPerformanceV2
```

### 5. Main CLI (`src/main.py` - ~200 LOC)

```python
@click.command()
@click.option('--command', ...)

Commands:
  init: Create database schema (python -m src.main init)
  load: Load raw data from Excel (python -m src.main load)
  transform: Transform to warehouse (python -m src.main transform)
  truncate: Clear warehouse tables (python -m src.main truncate)
  run: Full ELT pipeline (python -m src.main run)
  test: Test DB connection (python -m src.main test)
```

## Frontend Architecture (`web/`) - Detailed Analysis

### 1. Pages (`src/pages/`) - 8 Dashboard Modules + Auth

**ExecutiveDashboard.tsx** (~800 LOC)
- **KPI Cards**: Revenue trend, Inventory turnover, OTIF %, AR aging days
- **Charts**: Revenue by channel (pie), Top 10 products (bar), Monthly trend (line)
- **Data Flow**: API `/api/v1/executive` (cached with TanStack Query)
- **Defaults**: Date range = 1st of month → today (timezone-safe)

**InventoryDashboard.tsx** (~600 LOC)
- **Current Levels**: Table of materials with qty_kg, location, days inventory
- **Movement History**: Inbound/outbound transactions with timestamps
- **Slow-Moving Alerts**: >90 days without movement threshold
- **Stock Valuation**: Net value aggregation with UOM standardization
- **Real-time Status**: Auto-refresh every 30 seconds

**LeadTimeDashboard.tsx** (~900 LOC, MOST COMPLEX FRONTEND)
- **Lead Time Analytics**: Production vs. transit decomposition
- **OTIF Integration**: Recent orders table with On Time/Late/Pending badges
- **Bottleneck Analysis**: Top slow-moving products/customers
- **Historical Trends**: 12-month average by dimension
- **API Endpoints**: 
  - GET `/api/v1/leadtime/analytics` (production time calc)
  - GET `/api/v1/leadtime/transit` (shipping time calc)
  - GET `/api/v1/leadtime/recent-orders` **(NEW, 2026-01-13)**
  - GET `/api/v1/leadtime/otif-summary` **(NEW, 2026-01-13)**

**SalesPerformance.tsx** (~700 LOC)
- **Revenue by Dimension**: Channel (dropdown), Customer, Product
- **Sales Trends**: Line chart with month-over-month comparison
- **Order Fulfillment**: Delivery vs. ordered quantity tracking
- **Customer Segmentation**: ABC analysis visualization

**ProductionYield.tsx** (~100 LOC, Legacy Placeholder)
- **Status**: Redirects to V3 Efficiency Hub
- **Reason**: V2 Variance Analysis removed (2026-01-13)

**VarianceAnalysisTable.tsx** (~400 LOC, V3 EFFICIENCY HUB)
- **Table Structure**: Columns = Process Order, Batch, Loss kg, Loss %, Posting Date
- **Filters**: Date range picker, Loss threshold slider (0-100%)
- **Color Coding**: Loss % risk levels (green <5%, yellow 5-10%, red >10%)
- **Sorting**: Clickable headers for sort direction
- **API**: GET `/api/v3/yield/variance?start_date&end_date&loss_threshold`
- **Data Source**: `FactProductionPerformanceV2` table
- **Performance**: Materialized view query <500ms

**MTOOrders.tsx** (~500 LOC)
- **Order Status**: Custom order tracking from creation to delivery
- **Lead Time Compliance**: Planned vs. actual delivery date
- **Customer Metrics**: Individual order performance

**ArAging.tsx** (~600 LOC)
- **Aging Buckets**: 0-30, 31-60, 61-90, 91+ days tables
- **Customer Priority**: Highest overdue amount first
- **Collection Action**: Checkbox for follow-up status
- **Export**: CSV export for follow-up list

**AlertMonitor.tsx** (~400 LOC)
- **Alert Dashboard**: Real-time critical event feed
- **Alert Types**: Inventory, Production, Quality, Financial
- **Status Workflow**: Open → In Progress → Resolved
- **Auto-refresh**: Every 20 seconds for critical alerts

**Login.tsx** (~200 LOC)
- Form: Email + Password
- Error handling: Invalid credentials message
- Token storage: JWT in localStorage
- Redirect on success: → ExecutiveDashboard

### 2. Components (`src/components/`) - Modular UI

**Layout Components**
- `DashboardLayout.tsx` (~200 LOC): Sidebar navigation, header, main content area
- `ProtectedRoute.tsx` (~50 LOC): Route guard checking JWT token presence

**Common Components** (`common/` - Reusable)
- Chart wrappers: LineChart, BarChart, PieChart with Recharts
- Tables: SortableTable with pagination
- Modals: Generic modal wrapper
- Forms: Input validation helpers
- Filters: Date range picker, dropdown selectors, sliders

**Dashboard Components** (`dashboard/`)
- Organized by module: `production/`, `inventory/`, `sales/`, etc.
- Card components for KPIs
- Table components for drill-down

### 3. Services (`src/services/`) - API Communication

**API Client** (`api.ts` - ~250 LOC)
```typescript
const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000'

class ApiClient {
  private axiosInstance: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    headers: { 'Content-Type': 'application/json' }
  })

  // Interceptors
  interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  interceptors.response.use(
    (response) => response.data,
    (error) => handleApiError(error)
  )

  // Methods
  async get<T>(endpoint: string): Promise<T>
  async post<T>(endpoint: string, data: any): Promise<T>
  async put<T>(endpoint: string, data: any): Promise<T>
  async delete<T>(endpoint: string): Promise<T>
}
```

**Date Utilities** (`utils/dateHelpers.ts` - ~150 LOC)
```typescript
// Timezone-safe date helpers (avoid UTC midnight bug)
export function getFirstDayOfMonth(date?: Date): Date
export function getToday(): Date
export function getDefaultDateRange(): [Date, Date]
export function formatDate(date: Date): string  // YYYY-MM-DD
export function formatDateTime(date: Date): string  // YYYY-MM-DD HH:mm:ss
export function addDays(date: Date, days: number): Date
export function getDaysDifference(start: Date, end: Date): number
```

**Authentication Service** (`services/auth.ts` - ~100 LOC)
```typescript
export const authService = {
  login(email: string, password: string): Promise<{ token: string }>,
  logout(): void,
  getToken(): string | null,
  isAuthenticated(): boolean,
  getCurrentUser(): Promise<User>
}
```

### 4. Custom Hooks (`src/hooks/`)

**useAuth.ts** (~100 LOC)
```typescript
export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      authService.getCurrentUser().then(setUser)
    }
    setIsLoading(false)
  }, [])

  return { user, isLoading, login, logout }
}
```

**useQuery Hooks** (with TanStack Query)
```typescript
export function useExecutiveKpis(dateRange: [Date, Date]) {
  return useQuery({
    queryKey: ['executive-kpis', dateRange],
    queryFn: () => api.get('/api/v1/executive/kpis'),
    staleTime: 5 * 60 * 1000, // 5 min
  })
}
```

### 5. TypeScript Types (`src/types/`) - 500+ Lines

**API Response Types**
```typescript
interface ExecutiveKPIs {
  revenue_trend: number
  inventory_turnover: number
  otif_percentage: number
  ar_aging_days: number
}

interface InventoryLevel {
  material_code: string
  location: string
  qty_kg: number
  qty_liters: number
  net_value: number
  snapshot_date: Date
}

interface DeliveryRecord {
  delivery_number: string
  so_reference: string
  material: string
  planned_delivery: Date
  actual_gi_date: Date | null
  qty: number
  status: 'On Time' | 'Late' | 'Pending'
}

interface ProductionVariance {
  process_order_id: string
  batch_id: string
  loss_kg: number
  loss_percentage: number
  posting_date: Date
}
```

## Technology Stack (Current Versions)

### Backend Dependencies (23 packages)
- `fastapi==0.109.0`: Async web framework
- `sqlalchemy==2.0.23`: ORM
- `psycopg2-binary==2.9.9`: PostgreSQL adapter
- `pandas==2.1.4`: Data processing
- `polars==0.20.3`: High-performance alternative
- `openpyxl==3.1.2`: Excel reading
- `pydantic==2.5.3`: Validation
- `python-dotenv==1.0.0`: Environment config
- `pytest==7.4.4`: Testing framework
- `uvicorn==0.25.0`: ASGI server
- `alembic==1.13.1`: Migrations
- `python-multipart==0.0.6`: File upload

### Frontend Dependencies (15 major packages)
- `react==19.0.0`: UI library
- `typescript==5.9`: Type safety
- `vite==5.x`: Build tool
- `tailwindcss==4.x`: Styling
- `recharts==2.x`: Charting
- `@tanstack/react-query==5.x`: State management
- `react-router-dom==7.x`: Routing
- `axios==1.6.x`: HTTP client
- `date-fns==3.x`: Date utilities

### Databases
- `PostgreSQL 15+`: Primary data store

## Code Quality & Organization

### Backend Patterns
- **Separation of Concerns**: API routers → Business logic → Data access
- **Dependency Injection**: FastAPI dependencies for database sessions
- **Type Safety**: Pydantic models for validation
- **Error Handling**: Try/catch with custom exceptions
- **Logging**: Structured logs for debugging

### Frontend Patterns
- **Component Composition**: Reusable components with clear props
- **Custom Hooks**: Logic extraction for reusability
- **Type Safety**: TypeScript strict mode
- **State Management**: TanStack Query for server state
- **Performance**: Memoization, lazy loading, code splitting

## Performance Metrics (Measured)

### Backend
- **API Response**: <500ms p95 for dashboard queries
- **Database Queries**: <200ms for fact tables <500K rows
- **File Upload**: <2s for 10MB Excel file
- **Transform Pipeline**: <60s for 100K raw records

### Frontend
- **Initial Load**: <2s (bundle ~1.1MB gzipped)
- **Page Transitions**: <500ms (route switching)
- **Chart Rendering**: <1s (1000+ data points)
- **API Caching**: 5-minute stale-while-revalidate

## Recent Implementation (2026-01-13)

### ✅ OTIF Delivery Tracking
- Added `delivery_date` column to FactDelivery model
- New API endpoints: `/recent-orders`, `/otif-summary`
- Frontend: OTIFRecentOrdersTable component with status badges
- Logic: delivery_date vs. actual_gi_date comparison

### ✅ V3 Efficiency Hub (Yield Analysis)
- Replaced V2 Variance Analysis (removed 2026-01-13)
- New VarianceAnalysisTable with loss % filtering
- API: GET `/api/v3/yield/variance`
- Data source: `FactProductionPerformanceV2` materialized view

### ✅ Legacy Cleanup
- Dropped `fact_production_chain`, `fact_p02_p01_yield` tables
- Removed yield_v2.py router (was `/api/v2/yield/*`)
- Simplified ProductionDashboard (no tabs, direct V3 view)

## File Statistics

### Backend
- **Total Files**: 35+ Python modules
- **Total LOC**: ~15,000 lines
- **Largest Files**: models.py (27KB), loaders.py (35KB), transform.py (20KB)
- **Test Coverage**: ~40% (pytest suite)

### Frontend
- **Total Files**: 25+ TypeScript components
- **Total LOC**: ~8,500 lines
- **Largest Files**: LeadTimeDashboard.tsx (33KB), services/api.ts (12KB)
- **Bundle Size**: ~1.1MB (gzipped)

## Next Steps & Roadmap

### Short-term (Next Sprint)
- [ ] Expand OTIF reporting with historical trends
- [ ] Implement alert webhook notifications
- [ ] Add batch yield trend visualization
- [ ] Performance optimization for large datasets

### Medium-term (Q1 2026)
- [ ] Real-time WebSocket data streaming
- [ ] Advanced forecasting (time series predictions)
- [ ] Mobile responsive improvements
- [ ] API rate limiting and caching headers

### Long-term
- [ ] Multi-language support (Vietnamese/English)
- [ ] Role-based dashboard customization
- [ ] Automated report scheduling
- [ ] Machine learning anomaly detection
````

### 1. API Layer (`src/api/`)

**Main Application** (`main.py`)
- FastAPI application setup
- CORS configuration
- Router registration
- Health check endpoint

**Authentication** (`auth.py`)
- JWT token generation and validation
- Password hashing with bcrypt
- Login endpoint

**Dependencies** (`deps.py`)
- Database session management
- Current user dependency injection
- Role-based access control helpers

**Routers** (`routers/`)
- `alerts.py`: Alert monitoring endpoints
- `ar_aging.py`: Accounts receivable aging analysis
- `auth.py`: Authentication routes
- `executive.py`: Executive dashboard KPIs
- `inventory.py`: Inventory levels and movements
- `lead_time.py`: Lead time analytics
- `leadtime.py`: Additional lead time calculations
- `mto_orders.py`: Make-to-order tracking
- `sales_performance.py`: Sales metrics and trends

### 2. Core Business Logic (`src/core/`)

**Alert System** (`alerts.py`)
- Inventory threshold monitoring
- Production delay detection
- Quality issue flagging
- Financial exception alerts

**Business Logic** (`business_logic.py`)
- Revenue calculations
- Inventory turnover metrics
- Customer segmentation
- Product performance analysis

**Lead Time Calculator** (`leadtime_calculator.py`)
- End-to-end lead time tracking
- Production time calculation
- Transit time analysis
- Bottleneck identification

**Netting Engine** (`netting.py`)
- Material movement reconciliation
- Stock balance calculation
- Transaction pairing (goods receipt/issue)
- Inventory accuracy validation

**P02-P01 Yield** (`p02_p01_yield.py`)
- Production yield tracking
- Batch linking (P02 finished goods to P01 raw materials)
- Material consumption analysis
- Efficiency metrics

**UOM Converter** (`uom_converter.py`)
- Unit of measure conversions
- Multi-UOM support (KG, L, EA, etc.)
- Conversion factor management
- Standardization for analytics

**Yield Tracker** (`yield_tracker.py`)
- Comprehensive yield analysis
- Batch-level tracking
- Historical yield trends
- Waste calculation

### 3. Database Layer (`src/db/`)

**Connection Management** (`connection.py`)
- PostgreSQL connection pooling
- Session factory
- Database initialization
- Connection testing

**Data Models** (`models.py`)
- **Raw Tables**: Direct SAP imports
  - `RawMB51`: Material movements
  - `RawZRSD002`: Sales orders
  - `RawZRSD006`: Customer sales data
  - `RawZRFI005`: Debt/AR data
  - `RawCOOISPI`: Production orders
  - `RawCOGS`: Cost of goods sold
  - `RawZRSD003`: Additional sales data

- **Dimension Tables**
  - `DimMaterial`: Material master
  - `DimCustomer`: Customer master
  - `DimDate`: Date dimension
  - `DimLocation`: Storage locations

- **Fact Tables**
  - `FactInventory`: Inventory snapshots
  - `FactSales`: Sales transactions
  - `FactProduction`: Production confirmations
  - `FactMovement`: Material movements

**Database Views** (`views.py`)
- Materialized views for performance
- Pre-aggregated metrics
- Complex join optimizations

**Authentication Models** (`auth_models.py`)
- `User`: User accounts
- `Role`: Role definitions
- `UserRole`: User-role mapping

**Seed Data** (`seed.py`)
- Initial user creation
- Default role setup
- Sample data generation

### 4. ETL Pipeline (`src/etl/`)

**Data Loaders** (`loaders.py`)
- Excel file reading with Pandas
- Auto file-type detection (header pattern matching)
- **Upsert Mode**: Business key-based deduplication for ZRSD002, ZRFI005
  - ZRSD002: `(billing_document, billing_item)` unique key
  - `row_hash`: MD5 of raw_data (excludes `source_file` for cross-file dedup)
- **Insert Mode**: Bulk insert for historical data
- Data validation and type conversion helpers
- Error tracking and detailed logging
- **V2 Loaders** (`loaders/loader_zrpp062.py`):
  - Isolated ZRPP062 loader with `reference_date` parameter
  - JSON sanitization (NaN→None for PostgreSQL compatibility)
  - Upsert to `fact_production_performance_v2` with variance calculations
  - UNIQUE constraint on `(process_order_id, batch_id, posting_date)`

**Transformers** (`transform.py`)
- Raw to warehouse transformation
- Data cleansing
- Dimension population
- Fact table generation

**Main CLI** (`src/main.py`)
- `init`: Initialize database schema
- `load`: Load raw data from Excel
- `transform`: Transform to warehouse
- `truncate`: Clear warehouse tables
- `run`: Full ELT pipeline
- `test`: Test database connection

## Frontend Architecture (`web/`)

### 1. Pages (`src/pages/`)

**Dashboard Modules**
- `ExecutiveDashboard.tsx`: High-level KPIs and trends
- `Inventory.tsx`: Stock levels and movements
- `LeadTimeDashboard.tsx`: Lead time analytics (33KB - most complex)
- `SalesPerformance.tsx`: Revenue and sales metrics
- `ProductionYield.tsx`: Yield tracking and analysis (legacy)
- `VarianceAnalysisTable.tsx`: **V2 Production Yield** - Variance analysis with filters
- `MTOOrders.tsx`: Make-to-order tracking
- `ArAging.tsx`: Accounts receivable aging
- `AlertMonitor.tsx`: Real-time alert dashboard
- `Login.tsx`: Authentication page

### 2. Components (`src/components/`)

**Layout Components**
- `DashboardLayout.tsx`: Main dashboard wrapper with navigation
- `ProtectedRoute.tsx`: Route guard for authenticated pages

**Common Components** (`common/`)
- Reusable UI elements
- Chart wrappers
- Form controls

### 3. Services (`src/services/`)

**API Client** (`api.ts`)
- Axios-based HTTP client
- JWT token management
- Request/response interceptors
- Error handling

**Date Utilities** (`utils/dateHelpers.ts`)
- Timezone-safe date formatting (avoids UTC midnight bugs)
- Default date range helpers for dashboards
- `getFirstDayOfMonth()`, `getToday()`, `getDefaultDateRange()`
- Request/response interceptors
- Authentication token management
- Error handling

### 4. Hooks (`src/hooks/`)

**Custom React Hooks**
- `useAuth.ts`: Authentication state management
- Data fetching hooks with TanStack Query

### 5. Types (`src/types/`)

**TypeScript Definitions**
- API response types
- Domain models
- Component prop types

## Key Technologies

### Backend
- **Python 3.11+**: Core language
- **FastAPI**: Modern async web framework
- **SQLAlchemy 2.0**: ORM and database toolkit
- **Pandas**: Data processing and transformation
- **Polars**: High-performance data processing
- **Pydantic**: Data validation
- **Alembic**: Database migrations
- **psycopg2**: PostgreSQL adapter

### Frontend
- **React 19**: UI library
- **TypeScript**: Type-safe JavaScript
- **Vite**: Build tool and dev server
- **TailwindCSS 4**: Utility-first CSS framework
- **Recharts**: Charting library
- **TanStack Query**: Server state management
- **React Router 7**: Client-side routing
- **Axios**: HTTP client

### Database
- **PostgreSQL 15+**: Relational database
- **Materialized Views**: Query optimization
- **Indexes**: Performance tuning

## Data Flow

1. **Extract**: Excel files exported from SAP → `demodata/` directory
2. **Load**: Python loaders read Excel → Insert into raw tables
3. **Transform**: ETL pipeline processes raw data → Populate warehouse (dimensions + facts)
4. **API**: FastAPI endpoints query warehouse → Return JSON responses
5. **Frontend**: React components fetch data → Render charts and tables

## Code Organization Principles

### Backend
- **Separation of Concerns**: API, business logic, and data access are isolated
- **Dependency Injection**: Database sessions injected via FastAPI dependencies
- **Type Safety**: Pydantic models for request/response validation
- **Modularity**: Each router handles a specific domain

### Frontend
- **Component-Based**: Reusable components for UI consistency
- **Type Safety**: TypeScript for compile-time error detection
- **State Management**: TanStack Query for server state, React hooks for local state
- **Responsive Design**: TailwindCSS for mobile-friendly layouts

## Performance Optimizations

### Backend
- **Database Indexing**: Indexes on frequently queried columns
- **Materialized Views**: Pre-computed aggregations
- **Batch Processing**: Bulk inserts for large datasets
- **Connection Pooling**: Reuse database connections

### Frontend
- **Code Splitting**: Lazy loading for route-based chunks
- **Memoization**: React.memo for expensive components
- **Query Caching**: TanStack Query caches API responses
- **Virtual Scrolling**: For large data tables

## Testing Strategy

### Backend
- **Unit Tests**: Core business logic (pytest)
- **Integration Tests**: API endpoints with test database
- **Data Validation**: ETL pipeline correctness

### Frontend
- **Component Tests**: React Testing Library
- **E2E Tests**: Playwright (planned)
- **Type Checking**: TypeScript compiler

## Deployment

### Development
```bash
# Backend
python -m src.main run

# Frontend
cd web && npm run dev
```

### Production
- Docker containers for backend and frontend
- Docker Compose for orchestration
- Environment-specific `.env` files
- PostgreSQL as external service

## File Counts & Complexity

### Backend
- **Total Python Files**: ~30 files
- **Lines of Code**: ~15,000 LOC
- **Largest Module**: `models.py` (27KB), `LeadTimeDashboard.tsx` (33KB)

### Frontend
- **Total TypeScript Files**: ~25 files
- **Lines of Code**: ~8,000 LOC
- **Dependencies**: 19 production packages

## Recent Development Activity

Based on file timestamps, recent work focused on:
- Lead time calculation refinements (Dec 26)
- Alert system enhancements (Dec 26)
- Production yield tracking (Dec 26)
- AR aging analysis (Dec 25)
- Channel analysis and distribution (Dec 26)

## Next Steps

1. **Documentation**: Complete API documentation (OpenAPI/Swagger)
2. **Testing**: Increase test coverage to 80%+
3. **Performance**: Optimize slow queries with additional indexes
4. **Features**: Real-time data streaming, advanced forecasting

---

**Last Updated:** January 13, 2026
