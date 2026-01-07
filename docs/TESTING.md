# Testing Guide

Comprehensive testing strategy and guide for the Alkana Dashboard.

## Table of Contents
- [Testing Philosophy](#testing-philosophy)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Test Coverage](#test-coverage)
- [Continuous Integration](#continuous-integration)

---

## Testing Philosophy

### Testing Pyramid

```
        ┌─────────────┐
        │   E2E (5%)  │  Selenium/Playwright
        ├─────────────┤
        │ Integration │  API + Database
        │   (25%)     │
        ├─────────────┤
        │    Unit     │  Individual functions
        │   (70%)     │
        └─────────────┘
```

**Principles:**
- **Fast Feedback:** Unit tests run in <1 second
- **Isolation:** Tests don't depend on each other
- **Repeatability:** Same results every run
- **Coverage:** Aim for >80% code coverage
- **Clarity:** Test names describe what's being tested

---

## Test Structure

### Backend Tests (Python)

**Location:** `tests/`

```
tests/
├── unit/                    # Unit tests
│   ├── test_netting.py      # Business logic tests
│   ├── test_yield_tracker.py
│   ├── test_uom_converter.py
│   └── test_auth.py
├── integration/             # Integration tests
│   ├── test_api_executive.py
│   ├── test_api_inventory.py
│   ├── test_etl_pipeline.py
│   └── test_database.py
├── fixtures/                # Test data
│   ├── sample_mb51.xlsx
│   ├── sample_zrsd002.xlsx
│   └── test_data.sql
└── conftest.py              # Pytest configuration
```

### Frontend Tests (TypeScript)

**Location:** `web/src/__tests__/`

```
web/src/__tests__/
├── components/
│   ├── ExecutiveDashboard.test.tsx
│   ├── InventoryTable.test.tsx
│   └── AlertCard.test.tsx
├── services/
│   └── api.test.ts
├── utils/
│   └── formatters.test.ts
└── setup.ts
```

---

## Running Tests

### Backend Tests

**Run all tests:**
```bash
cd /path/to/alkana-dashboard
pytest
```

**Run specific test file:**
```bash
pytest tests/unit/test_netting.py
```

**Run specific test:**
```bash
pytest tests/unit/test_netting.py::test_calculate_net_stock
```

**Run with coverage:**
```bash
pytest --cov=src --cov-report=html
# View report: open htmlcov/index.html
```

**Run with verbose output:**
```bash
pytest -v
```

**Run only fast tests (skip slow integration):**
```bash
pytest -m "not slow"
```

**Run in parallel:**
```bash
pytest -n auto  # Uses all CPU cores
```

### Frontend Tests

**Run all tests:**
```bash
cd web
npm test
```

**Run in watch mode:**
```bash
npm test -- --watch
```

**Run with coverage:**
```bash
npm test -- --coverage
```

**Run specific test file:**
```bash
npm test -- ExecutiveDashboard.test.tsx
```

### Integration Tests

**Prerequisites:**
- PostgreSQL running
- Test database configured

**Setup test database:**
```bash
createdb alkana_test
psql -U postgres -d alkana_test -f tests/fixtures/test_data.sql
```

**Run integration tests:**
```bash
pytest tests/integration/ -v
```

**Teardown:**
```bash
dropdb alkana_test
```

---

## Writing Tests

### Backend Unit Tests (Python)

**Example: Testing business logic**

```python
# tests/unit/test_netting.py
import pytest
from src.core.netting import calculate_net_stock

def test_calculate_net_stock_basic():
    """Test basic stock netting with receipts and issues"""
    movements = [
        {'movement_type': '101', 'quantity': 100},  # Receipt
        {'movement_type': '261', 'quantity': -50},  # Issue
        {'movement_type': '601', 'quantity': -20},  # Issue
    ]
    
    result = calculate_net_stock(movements)
    
    assert result == 30, "Net stock should be 100 - 50 - 20 = 30"

def test_calculate_net_stock_with_reversals():
    """Test netting with reversal transactions"""
    movements = [
        {'movement_type': '101', 'quantity': 100, 'doc_number': 'MAT001'},
        {'movement_type': '102', 'quantity': -100, 'doc_number': 'MAT001', 'reference_doc': 'MAT001'},  # Reversal
        {'movement_type': '101', 'quantity': 150, 'doc_number': 'MAT002'},
    ]
    
    result = calculate_net_stock(movements)
    
    assert result == 150, "Reversal should cancel original, leaving only second receipt"

def test_calculate_net_stock_empty_movements():
    """Test with no movements"""
    result = calculate_net_stock([])
    assert result == 0

@pytest.mark.parametrize("movements,expected", [
    ([{'movement_type': '101', 'quantity': 50}], 50),
    ([{'movement_type': '261', 'quantity': -25}], -25),
    ([{'movement_type': '101', 'quantity': 100}, {'movement_type': '261', 'quantity': -30}], 70),
])
def test_calculate_net_stock_parametrized(movements, expected):
    """Test multiple scenarios with parametrize"""
    assert calculate_net_stock(movements) == expected
```

**Fixtures for test data:**

```python
# tests/conftest.py
import pytest
from src.db.database import SessionLocal, Base, engine
from src.db.models import RawMB51

@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for a test"""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_mb51_data():
    """Sample MB51 data for testing"""
    return [
        {
            'material_code': 'P01-12345',
            'movement_type': '101',
            'quantity': 100,
            'posting_date': '2025-01-15'
        },
        {
            'material_code': 'P01-12345',
            'movement_type': '261',
            'quantity': -50,
            'posting_date': '2025-01-16'
        }
    ]
```

### Backend Integration Tests

**Example: Testing API endpoints**

```python
# tests/integration/test_api_executive.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.db.database import SessionLocal

client = TestClient(app)

@pytest.fixture
def auth_token(db_session):
    """Get authentication token for tests"""
    response = client.post(
        "/api/auth/login",
        json={"username": "test_user", "password": "test_pass"}
    )
    return response.json()["access_token"]

def test_get_executive_summary(auth_token):
    """Test executive summary endpoint"""
    response = client.get(
        "/api/executive/summary",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "total_revenue" in data
    assert "total_customers" in data
    assert isinstance(data["total_revenue"], (int, float))

def test_get_executive_summary_unauthorized():
    """Test endpoint without authentication"""
    response = client.get("/api/executive/summary")
    assert response.status_code == 401

def test_get_revenue_by_division(auth_token):
    """Test revenue by division endpoint"""
    response = client.get(
        "/api/executive/revenue-by-division",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    if len(data) > 0:
        assert "division_code" in data[0]
        assert "revenue" in data[0]
```

### Frontend Unit Tests (React/TypeScript)

**Example: Testing components**

```typescript
// web/src/__tests__/components/ExecutiveDashboard.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { ExecutiveDashboard } from '../../pages/ExecutiveDashboard';
import * as api from '../../services/api';

jest.mock('../../services/api');

describe('ExecutiveDashboard', () => {
  test('renders KPI cards', async () => {
    // Mock API response
    (api.getExecutiveSummary as jest.Mock).mockResolvedValue({
      total_revenue: 15750000,
      total_customers: 145,
      total_orders: 1250,
    });

    render(<ExecutiveDashboard />);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/Total Revenue/i)).toBeInTheDocument();
    });

    // Verify KPI values displayed
    expect(screen.getByText(/15,750,000/)).toBeInTheDocument();
    expect(screen.getByText(/145/)).toBeInTheDocument();
  });

  test('shows loading state', () => {
    (api.getExecutiveSummary as jest.Mock).mockReturnValue(
      new Promise(() => {}) // Never resolves
    );

    render(<ExecutiveDashboard />);

    expect(screen.getByText(/Loading.../i)).toBeInTheDocument();
  });

  test('handles API error', async () => {
    (api.getExecutiveSummary as jest.Mock).mockRejectedValue(
      new Error('API Error')
    );

    render(<ExecutiveDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/Error loading data/i)).toBeInTheDocument();
    });
  });
});
```

**Testing API service:**

```typescript
// web/src/__tests__/services/api.test.ts
import axios from 'axios';
import { getExecutiveSummary, login } from '../../services/api';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('login returns token', async () => {
    const mockResponse = {
      data: {
        access_token: 'test-token',
        user: { username: 'test' }
      }
    };
    mockedAxios.post.mockResolvedValue(mockResponse);

    const result = await login('test', 'password');

    expect(result.access_token).toBe('test-token');
    expect(mockedAxios.post).toHaveBeenCalledWith(
      '/api/auth/login',
      { username: 'test', password: 'password' }
    );
  });

  test('getExecutiveSummary calls correct endpoint', async () => {
    const mockData = { total_revenue: 1000000 };
    mockedAxios.get.mockResolvedValue({ data: mockData });

    const result = await getExecutiveSummary();

    expect(result).toEqual(mockData);
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/executive/summary');
  });
});
```

---

## Test Coverage

### Coverage Targets

| Component | Target | Current |
|-----------|--------|---------|
| Core Business Logic | 90%+ | TBD |
| API Endpoints | 80%+ | TBD |
| ETL Pipeline | 85%+ | TBD |
| Frontend Components | 75%+ | TBD |
| Overall | 80%+ | TBD |

### Viewing Coverage Reports

**Backend:**
```bash
pytest --cov=src --cov-report=html --cov-report=term
open htmlcov/index.html
```

**Frontend:**
```bash
npm test -- --coverage
open web/coverage/lcov-report/index.html
```

### Coverage Analysis

**Uncovered Code Priorities:**
1. **Critical Path:** Business logic (netting, yield tracking)
2. **High Risk:** Authentication, data transformations
3. **Medium Risk:** API endpoints, validations
4. **Low Risk:** UI formatting, helpers

**Acceptable Gaps:**
- Configuration files
- Type definitions
- Simple getters/setters
- Third-party integrations (mock instead)

---

## Continuous Integration

### GitHub Actions Workflow

**File:** `.github/workflows/test.yml`

```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: alkana_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://test_user:test_pass@localhost/alkana_test
      run: |
        pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install dependencies
      working-directory: ./web
      run: npm ci
    
    - name: Run tests
      working-directory: ./web
      run: npm test -- --coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./web/coverage/lcov.info
```

### Pre-commit Hooks

**Install pre-commit:**
```bash
pip install pre-commit
pre-commit install
```

**File:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]
  
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest tests/unit
        language: system
        pass_filenames: false
        always_run: true
```

---

## Test Organization

### Root-Level Test Scripts

**Location:** Project root (80+ files)

These are **ad-hoc debugging/investigation scripts**, not formal tests:

**Categories:**
- `check_*.py` - Data validation scripts
- `debug_*.py` - Debugging specific issues
- `test_*.py` - Manual API/integration tests
- `verify_*.py` - Data verification scripts
- `analyze_*.py` - Pattern analysis

**Purpose:**
- Development investigation
- Data quality checks
- Manual testing
- Issue reproduction

**Not for CI/CD:** These scripts are exploratory, not automated tests.

See [DEV_SCRIPTS.md](./DEV_SCRIPTS.md) for complete catalog.

---

## Best Practices

### Writing Good Tests

**✓ Do:**
- Use descriptive test names: `test_calculate_net_stock_with_reversals`
- Test one thing per test
- Use fixtures for setup/teardown
- Mock external dependencies (APIs, databases)
- Test edge cases (empty data, None values)
- Use parametrize for similar test cases

**✗ Don't:**
- Write tests that depend on other tests
- Use hardcoded timestamps (use freezegun)
- Test implementation details (test behavior)
- Leave commented-out test code
- Skip tests without good reason

### Test Naming Convention

**Format:** `test_<function>_<scenario>_<expected_result>`

**Examples:**
- `test_calculate_yield_with_valid_data_returns_percentage`
- `test_login_with_invalid_password_returns_401`
- `test_get_inventory_when_empty_returns_empty_list`

### Debugging Failed Tests

**1. Run single test in verbose mode:**
```bash
pytest tests/unit/test_netting.py::test_calculate_net_stock -v -s
```

**2. Use pytest debugging:**
```bash
pytest --pdb  # Drop into debugger on failure
```

**3. Add print statements:**
```python
def test_something():
    result = function_under_test()
    print(f"DEBUG: result = {result}")
    assert result == expected
```

**4. Check test isolation:**
```bash
pytest --lf  # Run last failed
pytest --ff  # Run failures first
```

---

## Performance Testing

### Load Testing API

**Using Locust:**

```python
# locustfile.py
from locust import HttpUser, task, between

class DashboardUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_pass"
        })
        self.token = response.json()["access_token"]
    
    @task(3)
    def get_executive_summary(self):
        self.client.get(
            "/api/executive/summary",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(2)
    def get_inventory(self):
        self.client.get(
            "/api/inventory/current",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def get_alerts(self):
        self.client.get(
            "/api/alerts/active",
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

**Run load test:**
```bash
locust -f locustfile.py --host=http://localhost:8000
# Open http://localhost:8089 to configure and run test
```

---

## Test Data Management

### Generating Test Data

**Create fixture data:**

```python
# tests/fixtures/generate_test_data.py
import pandas as pd
from datetime import datetime, timedelta

def generate_mb51_data(num_records=100):
    """Generate sample MB51 data for testing"""
    data = []
    base_date = datetime(2025, 1, 1)
    
    for i in range(num_records):
        data.append({
            'material_code': f'P01-{10000+i}',
            'movement_type': '101' if i % 2 == 0 else '261',
            'quantity': 100 if i % 2 == 0 else -50,
            'posting_date': (base_date + timedelta(days=i)).strftime('%Y-%m-%d'),
            'plant': '1000',
            'storage_location': 'FG01',
            'document_number': f'MAT{5000000+i}'
        })
    
    df = pd.DataFrame(data)
    df.to_excel('tests/fixtures/sample_mb51.xlsx', index=False)
    return df

if __name__ == '__main__':
    generate_mb51_data()
```

### Database Fixtures

**SQL file for test data:**

```sql
-- tests/fixtures/test_data.sql
INSERT INTO dim_material (material_code, description, base_uom, material_type)
VALUES 
    ('P01-12345', 'Test Product 1', 'PC', 'FERT'),
    ('P02-67890', 'Test Semi-Finished', 'KG', 'HALB'),
    ('P03-11111', 'Test Raw Material', 'KG', 'ROH');

INSERT INTO raw_mb51 (material_code, movement_type, quantity, posting_date, plant)
VALUES
    ('P01-12345', '101', 100, '2025-01-15', '1000'),
    ('P01-12345', '261', -50, '2025-01-16', '1000');
```

---

## Troubleshooting Tests

### Common Issues

**Issue: Tests fail in CI but pass locally**

**Solution:**
- Check Python/Node versions match
- Verify environment variables set
- Ensure database accessible
- Check timezone differences

**Issue: Slow tests**

**Solution:**
```bash
# Find slowest tests
pytest --durations=10

# Run fast tests only
pytest -m "not slow"

# Parallelize
pytest -n auto
```

**Issue: Flaky tests (pass/fail intermittently)**

**Solution:**
- Check for race conditions
- Mock time-dependent code
- Ensure test isolation
- Use fixtures to reset state

---

## Resources

**Documentation:**
- [Pytest Docs](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/react)
- [Jest Docs](https://jestjs.io/)

**Books:**
- "Test-Driven Development" by Kent Beck
- "Python Testing with pytest" by Brian Okken

---

**Next Steps:**
1. Set up test database
2. Write tests for critical paths
3. Configure CI/CD
4. Reach 80% coverage
5. Add E2E tests (Phase 2)
