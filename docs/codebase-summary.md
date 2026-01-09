# Alkana Dashboard - Codebase Summary

## Project Structure Overview

```
alkana-dashboard/
├── src/                    # Python Backend
│   ├── api/               # FastAPI application
│   ├── core/              # Business logic
│   ├── db/                # Database models & connection
│   ├── etl/               # ETL pipeline
│   ├── config.py          # Configuration management
│   └── main.py            # CLI entry point
├── web/                   # React Frontend
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Dashboard pages
│   │   ├── services/      # API client
│   │   ├── hooks/         # Custom React hooks
│   │   └── types/         # TypeScript definitions
│   └── package.json
├── docs/                  # Documentation
├── demodata/              # Sample Excel data files
├── scripts/               # Utility scripts
└── requirements.txt       # Python dependencies
```

## Backend Architecture (`src/`)

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
