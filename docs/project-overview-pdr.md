# Alkana Dashboard - Project Overview & PDR

## Executive Summary

**Alkana Dashboard** is a comprehensive supply chain analytics platform designed to provide real-time visibility into manufacturing operations, inventory management, sales performance, and financial metrics. The system processes data from SAP ERP systems and transforms it into actionable insights through an intuitive web-based dashboard.

### Key Capabilities
- **Real-time Supply Chain Monitoring**: Track inventory levels, material movements, and production yields
- **Financial Analytics**: AR aging analysis, debt monitoring, and revenue tracking
- **Production Intelligence**: Lead time calculation, MTO order tracking, and yield optimization
- **Alert System**: Proactive notifications for critical business events
- **Multi-dimensional Analysis**: Executive dashboards with drill-down capabilities

## Product Development Requirements (PDR)

### 1. Business Objectives

#### Primary Goals
- **Operational Visibility**: Provide stakeholders with real-time insights into supply chain operations
- **Data-Driven Decision Making**: Enable informed decisions through comprehensive analytics
- **Process Optimization**: Identify bottlenecks and inefficiencies in production and logistics
- **Financial Control**: Monitor receivables, payables, and cash flow metrics

#### Success Metrics
- Data refresh latency < 5 minutes
- Dashboard load time < 2 seconds
- 99.9% data accuracy
- Support for 100+ concurrent users

### 2. Technical Architecture

#### System Components

**Backend (Python/FastAPI)**
- **ELT Pipeline**: Extract data from Excel exports, Load into PostgreSQL, Transform to warehouse schema
- **Business Logic Layer**: Complex calculations for lead time, netting, yield tracking, and alerts
- **REST API**: FastAPI-based endpoints serving frontend with authentication

**Frontend (React/TypeScript)**
- **SPA Architecture**: Single-page application with React Router
- **Data Visualization**: Recharts library for interactive charts and graphs
- **State Management**: TanStack Query for server state caching
- **Responsive Design**: TailwindCSS for mobile-friendly UI

**Database (PostgreSQL)**
- **Raw Layer**: Direct imports from SAP exports (MB51, ZRSD002, ZRSD006, etc.)
- **Warehouse Layer**: Dimensional model with fact and dimension tables
- **Views**: Optimized materialized views for complex queries

### 3. Core Features

#### Dashboard Modules

1. **Executive Dashboard**
   - Revenue trends and forecasts
   - Inventory turnover metrics
   - Top products and customers
   - Key performance indicators (KPIs)

2. **Inventory Management**
   - Current stock levels by material and location
   - Movement history and trends
   - Slow-moving inventory alerts
   - Stock valuation

3. **Lead Time Analytics**
   - End-to-end lead time tracking
   - Production vs. transit time breakdown
   - Bottleneck identification
   - Historical trend analysis

4. **Sales Performance**
   - Revenue by channel, customer, and product
   - Sales trends and seasonality
   - Order fulfillment metrics
   - Customer segmentation

5. **Production Yield**
   - P02 to P01 yield tracking
   - Batch-level yield analysis
   - Material consumption patterns
   - Waste and efficiency metrics

6. **MTO Orders**
   - Make-to-order tracking
   - Order status and progress
   - Lead time compliance
   - Customer-specific orders

7. **AR Aging**
   - Accounts receivable aging buckets
   - Customer payment patterns
   - Overdue analysis
   - Collection prioritization

8. **Alert Monitor**
   - Critical inventory alerts
   - Production delays
   - Quality issues
   - Financial exceptions

9. **Data Upload & Management**
   - Multi-file upload with auto-detection (ZRSD006, ZRSD002, MB51, etc.)
   - Smart deduplication (business key upsert for ZRSD002)
   - Snapshot date support (ZRFI005 AR data)
   - Frontend date defaults (first day of month → today, timezone-safe)

### 4. Data Sources

#### SAP Exports (Excel Format)
- **MB51**: Material movements and transactions
- **ZRSD002**: Sales orders and deliveries
- **ZRSD006**: Customer master and sales data
- **ZRFI005**: Accounts receivable and debt
- **COOISPI**: Production orders and confirmations
- **COGS**: Cost of goods sold
- **ZRSD003**: Additional sales metrics

### 5. User Roles & Authentication

#### Role-Based Access Control
- **Admin**: Full access to all modules and data management
- **Manager**: Read access to all dashboards, limited data export
- **Analyst**: Access to specific modules based on department
- **Viewer**: Read-only access to executive dashboard

#### Security Features
- JWT-based authentication
- Session management
- Password hashing (bcrypt)
- Role-based route protection

### 6. Performance Requirements

#### Data Processing
- **Batch Processing**: Handle 100K+ rows per data source
- **Incremental Updates**: Support delta loads for efficiency
- **Parallel Processing**: Multi-threaded ETL for large datasets

#### API Performance
- **Response Time**: < 500ms for 95th percentile
- **Throughput**: 1000+ requests per second
- **Caching**: Redis-based caching for frequently accessed data

#### Frontend Performance
- **Initial Load**: < 3 seconds
- **Chart Rendering**: < 1 second for 10K data points
- **Lazy Loading**: Code splitting for optimal bundle size

### 7. Deployment & Infrastructure

#### Technology Stack
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Pandas
- **Frontend**: React 19, TypeScript, Vite, TailwindCSS
- **Database**: PostgreSQL 15+
- **Deployment**: Docker containers, Docker Compose

#### Environment Configuration
- Development, Staging, Production environments
- Environment-specific configuration via `.env` files
- Database migrations with Alembic

### 8. Future Roadmap

#### Phase 1 (Completed - Jan 2026)
- ✅ Core dashboard modules (8 dashboards)
- ✅ ELT pipeline with smart deduplication
- ✅ Authentication system (JWT)
- ✅ Alert monitoring
- ✅ Multi-file upload with auto-detection
- ✅ Frontend date range defaults (timezone-safe)
- ✅ ZRSD002 upsert deduplication
- ✅ UOM conversion (KG normalization)

#### Phase 2 (Planned)
- [ ] Real-time data streaming
- [ ] Advanced forecasting with ML
- [ ] Mobile application
- [ ] Export to PDF/Excel

#### Phase 3 (Future)
- [ ] Integration with SAP APIs (direct connection)
- [ ] Predictive analytics
- [ ] Automated recommendations
- [ ] Multi-tenant support

## Conclusion

Alkana Dashboard transforms raw SAP data into actionable intelligence, empowering stakeholders to make data-driven decisions. The platform's modular architecture ensures scalability, while its comprehensive feature set addresses critical supply chain and financial analytics needs.
