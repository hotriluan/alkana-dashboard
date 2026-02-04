# Alkana Dashboard

> **Supply Chain Analytics Platform** - Real-time visibility into manufacturing operations, inventory management, sales performance, and financial metrics.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-blue.svg)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

## 🚀 Quick Deploy to Production

**One-click deployment to Ubuntu server (192.168.68.166):**

```bash
# Windows PowerShell
.\deployment\one-click-deploy.ps1

# Linux/Mac/Git Bash
bash deployment/one-click-deploy.sh
```

⏱️ **15 minutes** | 🤖 **95% automated** | 📦 **Includes database**

📖 **[START HERE →](START-HERE.md)** for step-by-step guide

## 📋 Overview

Alkana Dashboard is a comprehensive supply chain analytics platform that transforms raw SAP data into actionable insights. The system processes data from SAP ERP exports and provides real-time dashboards for:

- **Executive KPIs**: Revenue trends, inventory turnover, top products/customers
- **Inventory Management**: Stock levels, movements, slow-moving alerts
- **Lead Time Analytics**: End-to-end tracking, bottleneck identification
- **Sales Performance**: Revenue by channel/customer/product, trends
- **Production Yield**: Batch-level tracking, material consumption
- **MTO Orders**: Make-to-order tracking and compliance
- **AR Aging**: Receivables analysis and collection prioritization
- **Alert Monitoring**: Proactive notifications for critical events

## 🏗️ Architecture

**Full-Stack Application**
- **Backend**: Python/FastAPI with ETL pipeline and business logic
- **Frontend**: React/TypeScript SPA with interactive dashboards
- **Database**: PostgreSQL with dimensional warehouse model

```
SAP Exports (Excel) → ETL Pipeline → PostgreSQL → REST API → React Dashboards
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

### Backend Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
python -m src.main init

# Load sample data
python -m src.main load

# Transform to warehouse
python -m src.main transform

# Start API server
cd src && uvicorn api.main:app --reload
```

Backend runs at: `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend
cd web

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs at: `http://localhost:5173`

### Default Date Range
- Dashboards default to the current month: from the first day of the month to today.
- Implemented with timezone-safe local date helpers to avoid UTC shifts.

### Upload Behavior (ZRSD002)
- Multiple files with overlapping periods can be uploaded safely.
- Deduplication keys: `(billing_document, billing_item)` with an upsert flow.
- `row_hash` excludes `source_file` so re-uploads with identical data are skipped; changes overwrite the existing business record.
- Example: Upload 2025 full year then Dec 2025–Jan 2026 → 396 inserted, 2,118 updated, 0 duplicates.

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📊 Dashboard Modules

| Module | Description | Key Features |
|--------|-------------|--------------|
| **Executive** | High-level KPIs | Revenue trends, inventory turnover, top performers |
| **Inventory** | Stock management | Current levels, movement history, alerts |
| **Lead Time** | Supply chain analytics | Production vs. transit time, bottlenecks |
| **Sales** | Revenue analysis | Channel/customer/product breakdown, trends |
| **Production** | Yield tracking | Batch-level analysis, material consumption |
| **MTO Orders** | Custom orders | Order status, lead time compliance |
| **AR Aging** | Receivables | Aging buckets, payment patterns, overdue |
| **Alerts** | Monitoring | Inventory, production, quality, financial alerts |

## 🗂️ Project Structure

```
alkana-dashboard/
├── src/                    # Python Backend
│   ├── api/               # FastAPI application
│   │   ├── routers/       # API endpoints
│   │   ├── auth.py        # Authentication
│   │   └── main.py        # App setup
│   ├── core/              # Business logic
│   │   ├── alerts.py      # Alert system
│   │   ├── leadtime_calculator.py
│   │   ├── netting.py     # Material reconciliation
│   │   ├── yield_tracker.py
│   │   └── uom_converter.py
│   ├── db/                # Database layer
│   │   ├── models.py      # SQLAlchemy models
│   │   ├── views.py       # Materialized views
│   │   └── connection.py  # DB connection
│   ├── etl/               # ETL pipeline
│   │   ├── loaders.py     # Excel data loaders
│   │   └── transform.py   # Data transformers
│   └── main.py            # CLI entry point
├── web/                   # React Frontend
│   ├── src/
│   │   ├── pages/         # Dashboard pages
│   │   ├── components/    # UI components
│   │   ├── services/      # API client
│   │   └── types/         # TypeScript types
│   └── package.json
├── docs/                  # Documentation
│   ├── project-overview-pdr.md
│   ├── codebase-summary.md
│   ├── code-standards.md
│   └── system-architecture.md
├── demodata/              # Sample Excel files
├── docker-compose.yml     # Docker orchestration
└── requirements.txt       # Python dependencies
```

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Project Overview & PDR](docs/project-overview-pdr.md)**: Business objectives, features, roadmap
- **[Codebase Summary](docs/codebase-summary.md)**: Project structure, architecture, technologies
- **[Code Standards](docs/code-standards.md)**: Coding conventions and best practices
- **[System Architecture](docs/system-architecture.md)**: Technical architecture with diagrams
- **[Upload Guide](docs/upload-guide.md)**: Upload flow, detection, dedup, troubleshooting
- **[ETL Fixes Report (2026-01-07)](docs/ETL_FIXES_2026-01-07.md)**: Recent ETL and frontend fixes

## 🔧 Technology Stack

### Backend
- **Python 3.11+**: Core language
- **FastAPI**: Modern async web framework
- **SQLAlchemy 2.0**: ORM and database toolkit
- **Pandas/Polars**: Data processing
- **Pydantic**: Data validation
- **PostgreSQL**: Relational database

### Frontend
- **React 19**: UI library
- **TypeScript**: Type-safe JavaScript
- **Vite**: Build tool and dev server
- **TailwindCSS 4**: Utility-first CSS
- **Recharts**: Data visualization
- **TanStack Query**: Server state management
- **React Router 7**: Client-side routing

## 🔐 Authentication

The system uses JWT-based authentication with role-based access control:

- **Admin**: Full access to all modules
- **Manager**: Read access, limited export
- **Analyst**: Department-specific access
- **Viewer**: Read-only executive dashboard

**Default Credentials** (Development)
- Username: `admin`
- Password: `admin123`

> ⚠️ **Change default credentials in production!**

## 📦 Data Sources

The system processes Excel exports from SAP:

- **MB51**: Material movements and transactions
- **ZRSD002**: Sales orders and deliveries
- **ZRSD006**: Customer master and sales data
- **ZRFI005**: Accounts receivable and debt
- **COOISPI**: Production orders and confirmations
- **COGS**: Cost of goods sold
- **ZRSD003**: Additional sales metrics

Place Excel files in the `demodata/` directory before running the ETL pipeline.

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_leadtime.py
```

### Frontend Tests
```bash
cd web

# Run tests
npm test

# Run with coverage
npm test -- --coverage
```

## 🛠️ Development

### CLI Commands

```bash
# Initialize database schema
python -m src.main init

# Load raw data from Excel
python -m src.main load

# Transform to warehouse
python -m src.main transform

# Truncate warehouse tables
python -m src.main truncate

# Run full ELT pipeline
python -m src.main run

# Test database connection
python -m src.main test
```

### API Documentation

FastAPI provides interactive API documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🚢 Deployment

### Quick Deployment to Ubuntu Server

**Automated deployment via GitHub Actions:**

```bash
# 1. Setup server (one-time)
./deployment/setup-server.sh

# 2. Configure GitHub secrets
# Add: SERVER_HOST, SERVER_USER, SSH_PRIVATE_KEY, DB_PASSWORD, etc.

# 3. Deploy by pushing to main branch
git push origin main
```

**Manual deployment:**

```bash
# On server
./deployment/deploy.sh

# Migrate local database to server
./deployment/migrate-database.sh YOUR_SERVER_IP
```

📖 **Complete guides:**
- [Quick Start](docs/QUICKSTART.md) - 30-minute deployment guide
- [Deployment Guide](docs/DEPLOYMENT.md) - Full production setup
- [Database Migration](docs/DATABASE-MIGRATION.md) - Migrate local DB to server

### Production Checklist

- [ ] Run server setup script
- [ ] Configure GitHub secrets
- [ ] Setup SSL certificates
- [ ] Migrate database from development
- [ ] Update `.env.production` with credentials
- [ ] Change default admin password
- [ ] Configure CORS allowed origins
- [ ] Set up automated backups
- [ ] Configure monitoring and alerts
- [ ] Review security settings
- [ ] Test all dashboards

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/alkana_db
DB_PASSWORD=SecurePassword123

# API
ALLOWED_ORIGINS=https://dashboard.alkana.com

# Frontend
VITE_API_URL=/api
```

## 📚 Documentation

### Getting Started
- **[README](README.md)** - Project overview and quick start (this file)
- **[User Guide](docs/USER_GUIDE.md)** - End-user instructions for all dashboards
- **[Glossary](docs/GLOSSARY.md)** - Business and technical terminology

### Development
- **[API Reference](docs/API_REFERENCE.md)** - Complete REST API documentation
- **[Database Documentation](docs/DATABASE.md)** - Schema, tables, and data model
- **[Development Scripts](docs/DEV_SCRIPTS.md)** - Catalog of ad-hoc utility scripts
- **[Testing Guide](docs/TESTING.md)** - Testing strategy and examples
- **[Contributing Guide](docs/CONTRIBUTING.md)** - Git workflow and code standards

### Operations
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[Monitoring Guide](docs/MONITORING.md)** - Logging, metrics, and alerting
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Security Guide](docs/SECURITY.md)** - Security best practices
- **[Performance Guide](docs/PERFORMANCE.md)** - Optimization strategies

### Reference
- **[System Architecture](docs/system-architecture.md)** - Technical architecture diagrams
- **[Changelog](CHANGELOG.md)** - Version history and release notes

## 🤝 Contributing

1. Follow the [Code Standards](docs/code-standards.md)
2. Write tests for new features
3. Update documentation as needed
4. Submit pull requests with clear descriptions

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

## 📝 License

This project is proprietary and confidential.

## 📧 Support

For questions or issues, contact the development team.

---

**Built with ❤️ for supply chain excellence**
