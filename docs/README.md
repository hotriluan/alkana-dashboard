# Documentation Index

Complete documentation guide for the Alkana Dashboard project.

## 📚 Documentation Structure

```
docs/
├── Getting Started
│   ├── USER_GUIDE.md         - End-user instructions
│   └── GLOSSARY.md           - Business/technical terms
│
├── Development
│   ├── API_REFERENCE.md      - REST API documentation
│   ├── DATABASE.md           - Schema and data model
│   ├── DEV_SCRIPTS.md        - Utility scripts catalog
│   ├── TESTING.md            - Testing guide
│   └── CONTRIBUTING.md       - Git workflow and standards
│
├── Operations
│   ├── DEPLOYMENT.md         - Production deployment
│   ├── MONITORING.md         - Logging and metrics
│   ├── TROUBLESHOOTING.md    - Common issues
│   ├── SECURITY.md           - Security best practices
│   └── PERFORMANCE.md        - Optimization guide
│
└── Reference
    ├── system-architecture.md - Architecture diagrams
    └── CHANGELOG.md          - Version history
```

## 🚀 Getting Started

### For End Users

Start here if you're using the dashboard to view data and generate reports:

1. **[User Guide](USER_GUIDE.md)** - Complete guide to all 9 dashboard modules
   - Executive Dashboard
   - Inventory Management
   - Lead Time Analytics
   - Sales Performance
   - Production Yield
   - MTO Orders
   - AR Aging
   - Alert Monitor

2. **[Glossary](GLOSSARY.md)** - Understand the terminology
   - Business terms (MTO, MTS, P01-P03, yield)
   - Technical terms (API, ETL, netting)
   - SAP-specific terms (COOISPI, MB51, ZRSD)

### For Developers

Start here if you're developing new features or maintaining the system:

1. **[README](../README.md)** - Project overview and quick start
2. **[API Reference](API_REFERENCE.md)** - All API endpoints and examples
3. **[Database Documentation](DATABASE.md)** - Complete schema reference
4. **[Contributing Guide](CONTRIBUTING.md)** - Development workflow

### For System Administrators

Start here if you're deploying or operating the system:

1. **[Deployment Guide](DEPLOYMENT.md)** - Production setup
2. **[Monitoring Guide](MONITORING.md)** - Set up logging and alerts
3. **[Security Guide](SECURITY.md)** - Security configuration
4. **[Troubleshooting](TROUBLESHOOTING.md)** - Fix common issues

## 📖 Documentation by Task

### "I want to..."

#### ...understand the business logic
- [User Guide](USER_GUIDE.md) - Dashboard explanations
- [Glossary](GLOSSARY.md) - Business terminology
- [Database Documentation](DATABASE.md) - Data model and business rules

#### ...build a new feature
- [API Reference](API_REFERENCE.md) - Existing endpoints
- [Database Documentation](DATABASE.md) - Available data
- [Testing Guide](TESTING.md) - Write tests
- [Contributing Guide](CONTRIBUTING.md) - Code standards

#### ...deploy to production
- [Deployment Guide](DEPLOYMENT.md) - Step-by-step deployment
- [Security Guide](SECURITY.md) - Secure configuration
- [Monitoring Guide](MONITORING.md) - Set up monitoring
- [Performance Guide](PERFORMANCE.md) - Optimize settings

#### ...troubleshoot an issue
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common problems
- [Monitoring Guide](MONITORING.md) - Check logs and metrics
- [Database Documentation](DATABASE.md) - Query data directly

#### ...optimize performance
- [Performance Guide](PERFORMANCE.md) - Database and API optimization
- [Database Documentation](DATABASE.md) - Indexes and views
- [Monitoring Guide](MONITORING.md) - Track metrics

#### ...understand the codebase
- [System Architecture](system-architecture.md) - High-level design
- [Database Documentation](DATABASE.md) - Data flow
- [Development Scripts](DEV_SCRIPTS.md) - Utility scripts
- [API Reference](API_REFERENCE.md) - API structure

## 📋 Quick Reference

### Essential Links

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [USER_GUIDE.md](USER_GUIDE.md) | Dashboard usage | Using the application |
| [API_REFERENCE.md](API_REFERENCE.md) | API endpoints | Building integrations |
| [DATABASE.md](DATABASE.md) | Schema reference | Database queries |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production setup | Deploying system |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Problem solving | Fixing issues |
| [SECURITY.md](SECURITY.md) | Security config | Securing system |
| [PERFORMANCE.md](PERFORMANCE.md) | Optimization | Improving speed |

### Key Concepts

**Data Flow:**
```
SAP Exports → ETL Pipeline → PostgreSQL Warehouse → REST API → React Dashboards
```

**Architecture:**
- Backend: Python 3.11+, FastAPI 0.109
- Frontend: React 19, TypeScript 5.9
- Database: PostgreSQL 15+
- Deployment: Docker or manual

**Core Modules:**
- 8 Raw tables (SAP imports)
- 5 Dimension tables
- 5 Fact tables
- 4 Materialized views
- 10 API routers
- 9 Dashboard pages

## 🔍 Finding Information

### Search Guide

**By Technology:**
- Python/FastAPI → [API Reference](API_REFERENCE.md), [Performance](PERFORMANCE.md)
- PostgreSQL → [Database Documentation](DATABASE.md), [Performance](PERFORMANCE.md)
- React/TypeScript → [User Guide](USER_GUIDE.md), [../web/README.md](../web/README.md)
- Docker → [Deployment Guide](DEPLOYMENT.md), [Troubleshooting](TROUBLESHOOTING.md)

**By Topic:**
- Authentication → [API Reference](API_REFERENCE.md#authentication), [Security](SECURITY.md)
- Testing → [Testing Guide](TESTING.md), [Contributing](CONTRIBUTING.md)
- Deployment → [Deployment Guide](DEPLOYMENT.md), [Security](SECURITY.md)
- Monitoring → [Monitoring Guide](MONITORING.md), [Troubleshooting](TROUBLESHOOTING.md)
- Performance → [Performance Guide](PERFORMANCE.md), [Database](DATABASE.md)

**By User Role:**
- Business User → [User Guide](USER_GUIDE.md), [Glossary](GLOSSARY.md)
- Developer → [API Reference](API_REFERENCE.md), [Database](DATABASE.md), [Testing](TESTING.md)
- DevOps → [Deployment](DEPLOYMENT.md), [Monitoring](MONITORING.md), [Security](SECURITY.md)
- DBA → [Database](DATABASE.md), [Performance](PERFORMANCE.md), [Monitoring](MONITORING.md)

## 📝 Documentation Standards

### Contributing to Documentation

When updating documentation:

1. **Keep it current** - Update docs when code changes
2. **Be specific** - Include examples and code snippets
3. **Cross-reference** - Link to related documents
4. **Test examples** - Verify all code examples work
5. **Use templates** - Follow existing document structure

### Document Templates

**Code Examples:**
```python
# ✅ GOOD: Clear example with comments
from fastapi import APIRouter

router = APIRouter()

@router.get("/endpoint")
async def example():
    """Endpoint description"""
    return {"result": "value"}
```

**Configuration Examples:**
```bash
# Production configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/db
SECRET_KEY=your-secret-key-here
```

**Command Examples:**
```bash
# Description of what this does
command --option value

# Expected output:
# Success message
```

## 🆘 Getting Help

### Support Channels

1. **Documentation** - Search this documentation first
2. **Troubleshooting Guide** - [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. **Development Team** - Contact for complex issues
4. **Issue Tracker** - Report bugs or request features

### Common Questions

**Q: Where do I start?**
A: See [Getting Started](#getting-started) section above based on your role.

**Q: How do I deploy to production?**
A: Follow the [Deployment Guide](DEPLOYMENT.md) step-by-step.

**Q: The application is slow. How do I optimize it?**
A: See [Performance Guide](PERFORMANCE.md) for optimization strategies.

**Q: Where is the API documentation?**
A: See [API Reference](API_REFERENCE.md) or visit `/docs` when running the backend.

**Q: How do I add a new dashboard?**
A: See [Contributing Guide](CONTRIBUTING.md) for development workflow.

**Q: What does "MTO" mean?**
A: See [Glossary](GLOSSARY.md) for all terminology.

## 🔄 Documentation Updates

### Version History

See [CHANGELOG.md](../CHANGELOG.md) for version history and release notes.

### Last Updated

This documentation index was last updated: **January 2025**

Individual document update dates are noted in each file.

---

**Happy reading! 📚**

For questions about this documentation, contact the development team.
