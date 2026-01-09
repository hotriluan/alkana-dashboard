# Changelog

All notable changes to the Alkana Dashboard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### [Decommissioned] 2026-01-08

**PRODUCTION YIELD MODULE REMOVED**
- Removed entire Production Yield functionality (V1 Legacy + V2 Variance Analysis)
- Business directive: Module no longer required for operations
- All data backed up to: `backups/yield-decommission-2026-01-08/yield_tables_backup.sql` (2.4 MB)

#### Removed Components

**Frontend:**
- Deleted `/yield` route and ProductionYield.tsx component
- Deleted `/variance-analysis` route and VarianceAnalysisTable.tsx component
- Removed V2 TypeScript interfaces (VarianceRecord, VarianceAnalysisSummary, VarianceAnalysisResponse)
- Removed navigation menu items for Production Yield and Variance Analysis

**Backend:**
- Deleted `src/api/routers/yield_dashboard.py` (V1 legacy router)
- Deleted `src/api/routers/yield_v2.py` (V2 variance analysis router)
- Removed router registrations from `main.py`

**ETL & Core Logic:**
- Deleted `src/etl/loaders/loader_zrpp062.py` (V2 ETL loader, 425 lines)
- Deleted `src/core/yield_tracker.py` (Production chain logic, 396 lines)
- Deleted `src/core/p02_p01_yield.py` (Yield calculation helper)
- Preserved `src/core/netting.py` (still required for Supply Chain/Lead Time)

**Database:**
- Dropped `fact_production_performance_v2` (606 records)
- Dropped `raw_zrpp062` (610 records)
- Dropped `fact_p02_p01_yield`
- Dropped `fact_production_chain` (127 records)

**Files:**
- Deleted `demodata/zrpp062.XLSX` (source data file)
- Archived `V2_PRODUCTION_YIELD_IMPLEMENTATION_REPORT.md` to backups folder

**Documentation:**
- Updated `docs/codebase-summary.md` (removed yield sections)
- Updated this CHANGELOG.md

#### System Impact
- ✅ Sales Performance: Unaffected
- ✅ Inventory Dashboard: Unaffected  
- ✅ Supply Chain / Lead Time: Unaffected
- ✅ AR Collection: Unaffected
- ✅ Alert System: Unaffected

#### Rollback Instructions
If yield functionality needs to be restored:
1. Restore database: `psql -U postgres -d alkana_dashboard < backups/yield-decommission-2026-01-08/yield_tables_backup.sql`
2. Revert git commits: `git revert <commit-hash>..HEAD`
3. Restore archived report from backups folder

---

### 2026-01-08
- **V2 Production Yield Module**
  - Backend: New isolated tables `raw_zrpp062`, `fact_production_performance_v2`
  - Backend: Dedicated loader `Zrpp062Loader` with reference_date parameter
  - Backend: API endpoint `/api/v2/yield/variance` with date range and loss threshold filters
  - Backend: Null-safe SQL aggregation (COALESCE for empty results)
  - Frontend: New page `VarianceAnalysisTable` at `/variance-analysis`
  - Frontend: KPI cards (Total Orders, Avg Loss %, Total Loss kg, Analysis Period)
  - Frontend: Interactive filters (date range, loss threshold slider)
  - Frontend: Sortable table with color-coded loss percentages
  - Docs: Updated codebase-summary.md with V2 module details

### 2026-01-07
- Backend: ZRSD002 loader column mappings fixed (customer name, description, volume), row_hash excludes source_file, default loader mode set to upsert
- Backend: ZRSD006 detection and loader mappings updated to match actual headers (Material Code, PH 1..7)
- Backend: MB51 transform UOM conversion corrected (handles KG without conversion data)
- Backend: DimUomConversion.variance_pct widened to NUMERIC(10,2)
- Frontend: Default dashboard date range set to first day of current month → today
- Frontend: Timezone-safe date helpers added; DateRangePicker syncs props via useEffect
- Docs: Added ETL fixes report and Upload Guide; updated README

### Planned Features
- Webhook support for alert notifications
- Mobile responsive improvements
- Automated report scheduling
- Real-time data refresh (WebSocket)
- Multi-language support (Vietnamese/English)

---

## [1.0.0] - 2025-12-30

### Added
- **Executive Dashboard**
  - High-level KPIs (revenue, customers, orders, inventory, AR)
  - Revenue trends chart
  - Top 10 customers and products
  - Division performance breakdown

- **Inventory Management**
  - Current inventory levels by material/location
  - Material movement history with filtering
  - Slow-moving items detection (configurable threshold)
  - Movement type analysis

- **Lead Time Analytics**
  - End-to-end lead time tracking
  - Procurement/production/distribution breakdown
  - Bottleneck identification
  - MTO vs MTS comparison

- **Sales Performance**
  - Revenue analysis by channel, customer, product
  - Sales trends (daily/weekly/monthly)
  - Top customer rankings
  - Distribution channel breakdown

- **Production Yield**
  - Batch-level yield tracking
  - P03→P02→P01 material genealogy
  - Low yield alerts (threshold: 85%)
  - Yield trends and analysis

- **MTO Orders**
  - Make-to-order tracking
  - On-time delivery metrics (OTIF)
  - Order status monitoring
  - Lead time compliance

- **AR Aging**
  - Receivables aging analysis (Current, 1-30, 31-60, 61-90, 90+)
  - Customer-level AR breakdown
  - Overdue AR identification
  - Collection priority ranking

- **Alert Monitor**
  - Stuck-in-transit detection (>48 hours)
  - Low yield alerts (<85%)
  - Overdue AR notifications (>90 days)
  - Alert acknowledgment and resolution tracking

- **Backend Features**
  - FastAPI REST API with 10 routers
  - JWT authentication and authorization
  - Role-based access control (admin/manager/analyst)
  - ETL pipeline for 8 SAP Excel files
  - PostgreSQL dimensional warehouse
  - Materialized views for performance
  - Business logic: netting, yield tracking, lead time calculation
  - UOM auto-learning converter
  - Health check endpoints

- **Frontend Features**
  - React 19 with TypeScript
  - 9 interactive dashboard modules
  - TanStack Query for data fetching
  - Responsive layout
  - Data export (Excel/PDF)
  - Date range filtering
  - Protected routes with authentication

- **Database**
  - 8 raw tables (SAP import tables)
  - 5 dimension tables (material, customer, location, date, etc.)
  - 5 fact tables (inventory, production, billing, chain, alerts)
  - 4 materialized views
  - 2 auth tables (users, roles)
  - Alembic migrations setup

- **Documentation**
  - Comprehensive README
  - System architecture diagrams
  - Code standards guide
  - API reference
  - User guide
  - Deployment guide
  - Troubleshooting guide
  - Testing guide
  - Contributing guide
  - Database documentation
  - Glossary

### Technical Details
- Python 3.11+ backend
- FastAPI 0.109
- PostgreSQL 15+
- SQLAlchemy 2.0 ORM
- React 19 frontend
- TypeScript 5.9
- Vite build tool
- Docker deployment support

---

## [0.9.0] - 2025-12-15 (Beta)

### Added
- Core data model and ETL pipeline
- Basic API endpoints
- Initial dashboard prototypes
- Authentication system

### Changed
- Migrated from Flask to FastAPI
- Switched to SQLAlchemy 2.0
- Updated React to v19

### Fixed
- Inventory netting algorithm for reversals
- UOM conversion accuracy
- Duplicate data handling in ETL

---

## [0.5.0] - 2025-11-01 (Alpha)

### Added
- Initial project setup
- Database schema design
- Excel file loaders
- Basic data transformations

### Known Issues
- Performance issues with large datasets
- Incomplete error handling
- Limited test coverage

---

## Migration Guide

### Upgrading from 0.9.0 to 1.0.0

**Database Changes:**
```bash
# Backup database first
pg_dump alkana_dashboard > backup_v0.9.sql

# Run migrations
alembic upgrade head

# Refresh materialized views
psql -U alkana_user -d alkana_dashboard -c "
  REFRESH MATERIALIZED VIEW view_sales_performance;
  REFRESH MATERIALIZED VIEW view_inventory_summary;
  REFRESH MATERIALIZED VIEW view_production_yield;
"
```

**Code Changes:**
- Update `.env` file with new variables:
  ```bash
  JWT_SECRET_KEY=<generate-new-secret>
  JWT_EXPIRATION_MINUTES=1440
  CORS_ORIGINS=http://localhost:5173
  ```

- Update import paths (Flask → FastAPI):
  ```python
  # Old (Flask)
  from flask import jsonify
  
  # New (FastAPI)
  from fastapi import FastAPI
  from fastapi.responses import JSONResponse
  ```

- Frontend API calls now use `/api` prefix:
  ```typescript
  // Old
  fetch('/executive/summary')
  
  // New
  fetch('/api/executive/summary')
  ```

**Breaking Changes:**
- Authentication now uses JWT instead of session cookies
- API endpoints relocated to `/api/*` namespace
- Response format changed to Pydantic models
- Date format standardized to ISO 8601 (YYYY-MM-DD)

---

## Version History

| Version | Release Date | Status | Highlights |
|---------|--------------|--------|------------|
| 1.0.0 | 2025-12-30 | Stable | Initial production release |
| 0.9.0 | 2025-12-15 | Beta | Feature complete, testing |
| 0.5.0 | 2025-11-01 | Alpha | Initial prototype |

---

## Deprecation Notices

### v1.0.0
- None (initial release)

### Planned Deprecations (v2.0.0)
- Legacy `/health` endpoint → Use `/api/health`
- Session-based auth support removed (JWT only)

---

## Security Updates

### v1.0.0
- Implemented JWT token authentication
- Added role-based access control
- SQL injection prevention via parameterized queries
- XSS protection with CSP headers
- CORS restriction to trusted origins
- Password hashing with bcrypt

---

## Performance Improvements

### v1.0.0
- Materialized views for dashboard queries (10x faster)
- Database indexes on frequently queried columns
- Connection pooling (pool_size: 20)
- Frontend code splitting and lazy loading
- Gzip compression for API responses

---

## Bug Fixes

### v1.0.0
- Fixed inventory netting for MVT 122 reversals
- Corrected P02→P01 yield calculation edge cases
- Resolved duplicate alert generation
- Fixed date timezone handling (UTC standardization)
- Corrected UOM conversion for multi-level materials

---

## Contributors

### v1.0.0
- Development Team - Initial implementation
- QA Team - Testing and validation
- Product Team - Requirements and design
- DevOps Team - Deployment and infrastructure

---

## Release Notes

### How to Read This Changelog

**Added**: New features or capabilities
**Changed**: Changes to existing functionality
**Deprecated**: Features marked for future removal
**Removed**: Features removed in this version
**Fixed**: Bug fixes
**Security**: Security improvements

### Semantic Versioning

Given a version number MAJOR.MINOR.PATCH:
- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

**Examples:**
- `1.0.0` → `1.1.0`: New dashboard added (backwards compatible)
- `1.1.0` → `1.1.1`: Bug fix (backwards compatible)
- `1.1.1` → `2.0.0`: API endpoint restructure (breaking change)

---

## Future Roadmap

### v1.1.0 (Q1 2026)
- [ ] Email alert notifications
- [ ] Export scheduler
- [ ] Advanced filtering and saved views
- [ ] Dashboard customization

### v1.2.0 (Q2 2026)
- [ ] Forecasting and predictive analytics
- [ ] Batch comparison tool
- [ ] Supply chain simulation
- [ ] What-if analysis

### v2.0.0 (Q3 2026)
- [ ] Real-time data streaming
- [ ] Mobile app (iOS/Android)
- [ ] AI-powered insights
- [ ] Multi-tenant support

---

## Getting Help

**Report Issues:**
- GitHub Issues: [Project Issues](https://github.com/org/alkana-dashboard/issues)
- Email: support@yourcompany.com

**Feature Requests:**
- Submit via GitHub Discussions
- Email: product@yourcompany.com

**Security Issues:**
- Email: security@yourcompany.com (do not file public issues)

---

## License

Copyright © 2025 Your Company Name. All rights reserved.

---

**Last Updated:** December 30, 2025
**Maintained By:** Development Team
