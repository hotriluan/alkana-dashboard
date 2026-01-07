# Alkana Dashboard - System Architecture

## High-Level Architecture

```mermaid
graph TB
    subgraph "Data Sources"
        SAP[SAP ERP System]
        Excel[Excel Exports]
    end
    
    subgraph "Backend - Python/FastAPI"
        ETL[ETL Pipeline]
        API[REST API]
        BL[Business Logic]
        
        subgraph "ETL Components"
            Loader[Data Loaders]
            Transform[Transformers]
            Validator[Data Validators]
        end
        
        subgraph "Core Services"
            LeadTime[Lead Time Calculator]
            Netting[Netting Engine]
            Yield[Yield Tracker]
            Alerts[Alert System]
            UOM[UOM Converter]
        end
    end
    
    subgraph "Database - PostgreSQL"
        Raw[(Raw Tables)]
        Warehouse[(Warehouse)]
        Views[(Materialized Views)]
        
        subgraph "Warehouse Schema"
            Dims[Dimension Tables]
            Facts[Fact Tables]
        end
    end
    
    subgraph "Frontend - React/TypeScript"
        Router[React Router]
        Pages[Dashboard Pages]
        Components[UI Components]
        State[TanStack Query]
        
        subgraph "Dashboard Modules"
            Exec[Executive]
            Inv[Inventory]
            Lead[Lead Time]
            Sales[Sales]
            Prod[Production]
            MTO[MTO Orders]
            AR[AR Aging]
            Alert[Alerts]
        end
    end
    
    subgraph "Users"
        Admin[Administrators]
        Manager[Managers]
        Analyst[Analysts]
    end
    
    SAP -->|Manual Export| Excel
    Excel -->|Load| Loader
    Loader -->|Insert| Raw
    Raw -->|Transform| Transform
    Transform -->|Populate| Dims
    Transform -->|Populate| Facts
    Dims --> Views
    Facts --> Views
    
    Views -->|Query| BL
    BL --> LeadTime
    BL --> Netting
    BL --> Yield
    BL --> Alerts
    BL --> UOM
    
    LeadTime --> API
    Netting --> API
    Yield --> API
    Alerts --> API
    UOM --> API
    
    API -->|JSON/REST| State
    State --> Pages
    Pages --> Components
    Router --> Pages
    
    Admin --> Router
    Manager --> Router
    Analyst --> Router
```

## Architecture Layers

### 1. Data Layer

#### Data Sources
- **SAP ERP**: Source of truth for all business data
- **Excel Exports**: Manual exports from SAP (MB51, ZRSD002, ZRSD006, etc.)
- **File Storage**: `demodata/` directory for Excel files

#### Database Schema

**Raw Layer**
- Direct imports from Excel files
- Minimal transformation
- Preserves original data structure
- Tables: `raw_mb51`, `raw_zrsd002`, `raw_zrsd006`, etc.

**Warehouse Layer**
- **Dimension Tables**: Master data (materials, customers, dates, locations)
- **Fact Tables**: Transactional data (inventory, sales, production, movements)
- **Materialized Views**: Pre-aggregated metrics for performance

```mermaid
erDiagram
    DimMaterial ||--o{ FactInventory : "has"
    DimMaterial ||--o{ FactSales : "sold in"
    DimMaterial ||--o{ FactProduction : "produced in"
    DimCustomer ||--o{ FactSales : "purchases"
    DimDate ||--o{ FactInventory : "snapshot on"
    DimDate ||--o{ FactSales : "occurred on"
    DimLocation ||--o{ FactInventory : "stored at"
    
    DimMaterial {
        string material_id PK
        string description
        string material_type
        string uom
        float std_cost
    }
    
    DimCustomer {
        string customer_id PK
        string name
        string channel
        string region
    }
    
    DimDate {
        date date_key PK
        int year
        int month
        int quarter
        string month_name
    }
    
    DimLocation {
        string location_id PK
        string name
        string type
    }
    
    FactInventory {
        int id PK
        string material_id FK
        string location_id FK
        date snapshot_date FK
        float quantity
        float value
    }
    
    FactSales {
        int id PK
        string material_id FK
        string customer_id FK
        date order_date FK
        float quantity
        float revenue
    }
    
    FactProduction {
        int id PK
        string material_id FK
        date production_date FK
        string batch_number
        float quantity
        float yield_pct
    }
```

### 2. ETL Pipeline

#### Extract
- Read Excel files using Pandas/Polars
- Validate file structure and required columns
- Handle encoding issues (UTF-8, Latin-1)

#### Load
- Batch insert into raw tables
- Transaction management for data integrity
- Error logging and rollback on failure

#### Transform
- **Dimension Population**: Extract unique values from raw data
- **Fact Population**: Join raw data with dimensions
- **Data Cleansing**: Handle nulls, duplicates, data type conversions
- **Business Rules**: Apply domain-specific transformations

```mermaid
sequenceDiagram
    participant CLI as CLI (main.py)
    participant Loader as Data Loader
    participant DB as PostgreSQL
    participant Transform as Transformer
    participant BL as Business Logic
    
    CLI->>Loader: load_all_raw_data()
    Loader->>Loader: Read Excel files
    Loader->>Loader: Validate data
    Loader->>DB: Batch insert to raw tables
    DB-->>Loader: Success
    
    CLI->>Transform: transform_all()
    Transform->>DB: Query raw tables
    Transform->>Transform: Populate dimensions
    Transform->>DB: Insert into dim tables
    Transform->>Transform: Populate facts
    Transform->>BL: Calculate metrics
    BL-->>Transform: Calculated values
    Transform->>DB: Insert into fact tables
    Transform->>DB: Refresh materialized views
    DB-->>Transform: Success
```

### 3. Business Logic Layer

#### Core Services

**Lead Time Calculator** (`leadtime_calculator.py`)
- Tracks material flow from P02 (finished goods) to P01 (raw materials)
- Calculates production time, transit time, and total lead time
- Identifies bottlenecks in the supply chain

**Netting Engine** (`netting.py`)
- Reconciles material movements (goods receipts vs. issues)
- Calculates net inventory changes
- Validates stock balances

**Yield Tracker** (`yield_tracker.py`)
- Tracks production yield at batch level
- Links P02 batches to P01 inputs
- Calculates material consumption and waste

**Alert System** (`alerts.py`)
- Monitors inventory thresholds
- Detects production delays
- Flags quality issues
- Identifies financial exceptions

**UOM Converter** (`uom_converter.py`)
- Converts between units of measure (KG, L, EA, etc.)
- Maintains conversion factors
- Standardizes metrics for analytics

### 4. API Layer

#### FastAPI Application

**Endpoints**
- `/api/auth/*`: Authentication (login, logout, token refresh)
- `/api/executive/*`: Executive dashboard KPIs
- `/api/inventory/*`: Inventory levels and movements
- `/api/lead-time/*`: Lead time analytics
- `/api/sales/*`: Sales performance metrics
- `/api/yield/*`: Production yield data
- `/api/mto-orders/*`: Make-to-order tracking
- `/api/ar-aging/*`: Accounts receivable aging
- `/api/alerts/*`: Alert monitoring

**Middleware**
- CORS: Allow frontend origin
- Authentication: JWT token validation
- Error Handling: Global exception handler
- Logging: Request/response logging

**Dependencies**
- Database session injection
- Current user extraction from JWT
- Role-based access control

```mermaid
sequenceDiagram
    participant Client as React Frontend
    participant API as FastAPI
    participant Auth as Auth Middleware
    participant BL as Business Logic
    participant DB as PostgreSQL
    
    Client->>API: GET /api/inventory?date=2024-01-01
    API->>Auth: Validate JWT token
    Auth->>Auth: Extract user
    Auth-->>API: User authenticated
    
    API->>BL: get_inventory_snapshot(date)
    BL->>DB: Query fact_inventory
    DB-->>BL: Result set
    BL->>BL: Calculate metrics
    BL-->>API: Processed data
    
    API->>API: Format response
    API-->>Client: JSON response
```

### 5. Frontend Layer

#### React Application Architecture

**Routing**
- React Router for client-side navigation
- Protected routes requiring authentication
- Lazy loading for code splitting

**State Management**
- **Server State**: TanStack Query (caching, refetching, optimistic updates)
- **Local State**: React hooks (`useState`, `useReducer`)
- **Auth State**: Context API for user session

**Component Hierarchy**
```
App
├── Router
│   ├── Login (public)
│   └── DashboardLayout (protected)
│       ├── Navigation
│       ├── ExecutiveDashboard
│       ├── Inventory
│       ├── LeadTimeDashboard
│       ├── SalesPerformance
│       ├── ProductionYield
│       ├── MTOOrders
│       ├── ArAging
│       └── AlertMonitor
```

**Data Flow**
```mermaid
graph LR
    API[API Client] -->|Fetch| Query[TanStack Query]
    Query -->|Cache| Cache[Query Cache]
    Cache -->|Provide| Hook[useQuery Hook]
    Hook -->|Data| Component[React Component]
    Component -->|Render| UI[User Interface]
    
    UI -->|User Action| Component
    Component -->|Mutation| Mutate[useMutation Hook]
    Mutate -->|POST/PUT| API
    API -->|Success| Query
    Query -->|Invalidate| Cache
```

### 6. Authentication & Authorization

#### JWT-Based Authentication

**Login Flow**
```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant DB
    
    User->>Frontend: Enter credentials
    Frontend->>API: POST /api/auth/login
    API->>DB: Query user by username
    DB-->>API: User record
    API->>API: Verify password (bcrypt)
    API->>API: Generate JWT token
    API-->>Frontend: {access_token, user}
    Frontend->>Frontend: Store token in localStorage
    Frontend->>Frontend: Redirect to dashboard
```

**Protected Request Flow**
```mermaid
sequenceDiagram
    participant Frontend
    participant API
    participant Auth
    
    Frontend->>API: GET /api/inventory (with JWT header)
    API->>Auth: Validate token
    Auth->>Auth: Decode JWT
    Auth->>Auth: Check expiration
    Auth->>Auth: Extract user
    Auth-->>API: User object
    API->>API: Process request
    API-->>Frontend: Response
```

#### Role-Based Access Control (RBAC)
- **Admin**: Full access (CRUD on all resources)
- **Manager**: Read access to all dashboards, limited data export
- **Analyst**: Access to specific modules based on department
- **Viewer**: Read-only access to executive dashboard

### 7. Deployment Architecture

#### Development Environment
```
Developer Machine
├── Backend (localhost:8000)
│   └── Python/FastAPI
├── Frontend (localhost:5173)
│   └── Vite Dev Server
└── Database (localhost:5432)
    └── PostgreSQL
```

#### Production Environment (Docker)
```mermaid
graph TB
    subgraph "Docker Host"
        subgraph "Backend Container"
            FastAPI[FastAPI App]
            Uvicorn[Uvicorn Server]
        end
        
        subgraph "Frontend Container"
            Nginx[Nginx]
            Static[Static Files]
        end
        
        subgraph "Database Container"
            Postgres[(PostgreSQL)]
        end
    end
    
    Internet[Internet] -->|HTTPS| Nginx
    Nginx -->|Proxy| Uvicorn
    FastAPI --> Postgres
```

**Docker Compose Services**
- `backend`: Python/FastAPI application
- `frontend`: Nginx serving React build
- `db`: PostgreSQL database

### 8. Performance Optimizations

#### Database
- **Indexes**: On frequently queried columns (material_id, customer_id, date)
- **Materialized Views**: Pre-aggregated metrics refreshed periodically
- **Connection Pooling**: Reuse database connections
- **Query Optimization**: Avoid N+1 queries, use joins efficiently

#### Backend
- **Caching**: Redis for frequently accessed data (planned)
- **Batch Processing**: Bulk inserts for large datasets
- **Async I/O**: FastAPI async endpoints for I/O-bound operations
- **Pagination**: Limit result sets to prevent memory issues

#### Frontend
- **Code Splitting**: Lazy load routes and components
- **Memoization**: React.memo, useMemo, useCallback
- **Query Caching**: TanStack Query caches API responses
- **Virtual Scrolling**: For large data tables (planned)

### 9. Security Considerations

#### Backend
- **Input Validation**: Pydantic models for request validation
- **SQL Injection Prevention**: SQLAlchemy ORM (parameterized queries)
- **Password Hashing**: bcrypt with salt
- **JWT Expiration**: Tokens expire after 24 hours
- **CORS**: Restrict allowed origins

#### Frontend
- **XSS Prevention**: React escapes output by default
- **CSRF Protection**: SameSite cookies (planned)
- **Secure Storage**: Avoid storing sensitive data in localStorage
- **HTTPS Only**: Enforce HTTPS in production

### 10. Monitoring & Logging

#### Backend Logging
- Request/response logging
- Error tracking with stack traces
- Performance metrics (query execution time)
- ETL pipeline logs

#### Frontend Logging
- Error boundaries for React errors
- API error logging
- User action tracking (planned)

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 19 | UI library |
| | TypeScript | Type safety |
| | Vite | Build tool |
| | TailwindCSS 4 | Styling |
| | Recharts | Data visualization |
| | TanStack Query | Server state management |
| | React Router 7 | Client-side routing |
| **Backend** | Python 3.11+ | Core language |
| | FastAPI | Web framework |
| | SQLAlchemy 2.0 | ORM |
| | Pandas | Data processing |
| | Polars | High-performance data processing |
| | Pydantic | Data validation |
| | Uvicorn | ASGI server |
| **Database** | PostgreSQL 15+ | Relational database |
| **Deployment** | Docker | Containerization |
| | Docker Compose | Orchestration |
| **Auth** | JWT | Token-based authentication |
| | bcrypt | Password hashing |

## Scalability Considerations

### Current Capacity
- **Data Volume**: 100K+ rows per data source
- **Concurrent Users**: 100+ users
- **Response Time**: < 500ms for 95th percentile

### Future Scaling Strategies
- **Horizontal Scaling**: Multiple backend instances behind load balancer
- **Database Replication**: Read replicas for analytics queries
- **Caching Layer**: Redis for frequently accessed data
- **CDN**: Serve static frontend assets from CDN
- **Microservices**: Split monolithic backend into domain services
