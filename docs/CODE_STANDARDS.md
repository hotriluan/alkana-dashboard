# Code Standards & Best Practices

**Last Updated:** January 13, 2026 | **Version:** 1.0 | **Audience:** Development Team

## Table of Contents
- [Backend Standards (Python)](#backend-standards-python)
- [Frontend Standards (TypeScript/React)](#frontend-standards-typescriptreact)
- [Database Standards (PostgreSQL)](#database-standards-postgresql)
- [ETL Standards](#etl-standards)
- [Testing Standards](#testing-standards)
- [Documentation Standards](#documentation-standards)
- [Git Workflow](#git-workflow)

---

## Backend Standards (Python)

### Code Style & Organization

#### File Organization
```python
# src/<module>/<file>.py structure:

# 1. Imports (standard library → third-party → local)
import os
import sys
from typing import Optional, List, Dict
from datetime import datetime, timedelta

import pandas as pd
import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.db.models import RawMB51, FactInventory
from src.core.alerts import AlertDetector
from src.config import settings
```

#### Naming Conventions
- **Modules**: `lowercase_with_underscores.py` (e.g., `leadtime_calculator.py`)
- **Classes**: `PascalCase` (e.g., `LeadTimeCalculator`, `BaseLoader`)
- **Functions**: `snake_case` (e.g., `calculate_lead_time()`, `get_user_by_id()`)
- **Constants**: `UPPER_CASE_WITH_UNDERSCORES` (e.g., `MAX_RETRY_COUNT = 3`)
- **Private**: Prefix with `_` (e.g., `_internal_helper()`)
- **Database tables**: `snake_case_plural` (e.g., `fact_inventory`, `dim_material`)

#### File Size Limits
- **Target**: <200 lines per file (Python best practice)
- **Rationale**: Improved code review, testing, maintenance
- **Exception**: ORM models allowed up to 500 lines (models.py = 27KB is acceptable for central schema)

**Example: Breaking apart large modules**
```python
# ❌ BEFORE: 450 lines in single file
src/core/business_logic.py

# ✅ AFTER: Split into focused modules
src/core/
├── revenue_calculator.py
├── inventory_turnover.py
├── customer_segmentation.py
└── product_performance.py
```

### Backend Patterns

#### 1. API Endpoint Pattern

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api.deps import get_current_user
from src.db.models import User

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])

# 1. Define response model
class InventoryLevelResponse(BaseModel):
    material_id: str
    location: str
    qty_kg: float
    net_value: float
    
    class Config:
        from_attributes = True  # SQLAlchemy compat

# 2. Define endpoint
@router.get("/levels", response_model=List[InventoryLevelResponse])
async def get_inventory_levels(
    current_user: User = Depends(get_current_user),
    material_id: Optional[str] = None,
    limit: int = 100
):
    """Get current inventory levels, optionally filtered by material."""
    # 3. Validate inputs
    if limit > 1000:
        raise HTTPException(status_code=400, detail="Limit max 1000")
    
    # 4. Query database
    db = get_db()  # From dependency injection
    query = db.query(FactInventory)
    
    if material_id:
        query = query.filter(FactInventory.material_id == material_id)
    
    results = query.limit(limit).all()
    
    # 5. Return response
    return results
```

#### 2. Business Logic Pattern

```python
class LeadTimeCalculator:
    """Calculate lead time for materials from production to delivery."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_end_to_end(self, so_id: str) -> Dict[str, float]:
        """
        Calculate total lead time from SO create to GI.
        
        Args:
            so_id: Sales order ID
            
        Returns:
            {
                'total_days': 15,
                'production_days': 10,
                'transit_days': 5
            }
            
        Raises:
            ValueError: If SO not found
        """
        # 1. Validate input
        if not so_id:
            raise ValueError("SO ID required")
        
        # 2. Query data
        production = self.db.query(FactProduction)\
            .filter(FactProduction.so_id == so_id)\
            .first()
        
        if not production:
            raise ValueError(f"SO {so_id} not found")
        
        # 3. Calculate metrics
        production_days = (production.gr_date - production.po_create_date).days
        transit_days = (production.gi_date - production.gr_date).days
        total_days = production_days + transit_days
        
        # 4. Return result
        return {
            'total_days': total_days,
            'production_days': production_days,
            'transit_days': transit_days
        }
```

#### 3. Data Loader Pattern

```python
class BaseLoader:
    """Base class for all SAP data loaders."""
    
    def __init__(self, db: Session, mode: str = 'upsert', batch_size: int = 1000):
        self.db = db
        self.mode = mode  # 'insert' or 'upsert'
        self.batch_size = batch_size
    
    def load(self, file_path: Path) -> Dict[str, int]:
        """
        Load Excel file into database.
        
        Returns: {'loaded': 100, 'updated': 50, 'skipped': 5, 'errors': 0}
        """
        # 1. Read file
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            raise
        
        # 2. Validate columns
        columns = self.get_column_mapping(df.columns.tolist())
        if not columns:
            raise ValueError(f"File format not recognized: {file_path}")
        
        # 3. Process records
        stats = {'loaded': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        records = []
        
        for idx, row in df.iterrows():
            try:
                record = self._process_row(row, columns)
                records.append(record)
                
                # Batch insert
                if len(records) >= self.batch_size:
                    count = self._insert_batch(records)
                    stats['loaded'] += count
                    records = []
            except Exception as e:
                logger.warning(f"Row {idx} error: {e}")
                stats['errors'] += 1
        
        # Final batch
        if records:
            stats['loaded'] += self._insert_batch(records)
        
        return stats
    
    def _process_row(self, row: pd.Series, columns: Dict) -> Dict:
        """Convert Excel row to database record."""
        return {
            'material_code': safe_str(row.get(columns['material'])),
            'quantity': safe_float(row.get(columns['quantity'])),
            'posting_date': safe_datetime(row.get(columns['date'])),
        }
    
    def _insert_batch(self, records: List[Dict]) -> int:
        """Insert batch of records with dedup."""
        count = 0
        for record in records:
            try:
                if self.mode == 'upsert':
                    # Upsert: Update if exists, insert if new
                    stmt = sa.insert(RawMB51).values(**record)\
                        .on_conflict_do_update(
                            index_elements=['document_number'],
                            set_=record
                        )
                else:
                    # Insert: Fail if exists
                    stmt = sa.insert(RawMB51).values(**record)
                
                self.db.execute(stmt)
                count += 1
            except sa.exc.IntegrityError:
                self.db.rollback()
        
        self.db.commit()
        return count
```

#### 4. Type Conversion Pattern

```python
# src/etl/loaders.py - Safe type conversion functions

def safe_str(value: Any, default: str = None) -> Optional[str]:
    """Safely convert value to string, handling None and special values."""
    if value is None or pd.isna(value):
        return default
    return str(value).strip()

def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    if value is None or pd.isna(value):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_datetime(value: Any, default: datetime = None) -> Optional[datetime]:
    """Safely convert value to datetime, handling Excel serial dates."""
    if value is None or pd.isna(value):
        return default
    if isinstance(value, datetime):
        return value
    try:
        # Pandas handles Excel serial date conversion
        return pd.to_datetime(value).to_pydatetime()
    except (ValueError, TypeError):
        logger.warning(f"Could not parse date: {value}")
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to integer."""
    if value is None or pd.isna(value):
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
```

#### 5. Error Handling Pattern

```python
# Always use try/catch with specific exceptions
try:
    result = perform_complex_operation()
except ValueError as e:
    # Handle validation errors
    logger.warning(f"Invalid input: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except DatabaseError as e:
    # Handle database errors
    logger.error(f"Database error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Database error")
except Exception as e:
    # Catch-all for unexpected errors
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Database Access Pattern

```python
# ✅ GOOD: Use dependency injection
@router.get("/items")
async def get_items(db: Session = Depends(get_db)):
    return db.query(Item).limit(100).all()

# ❌ AVOID: Global database access
# GLOBAL_DB = get_connection()  # Don't do this!

# ✅ GOOD: Use context manager for transactions
with db.begin():
    new_item = Item(name="Test")
    db.add(new_item)
    # Auto-rollback if exception, auto-commit if successful

# ❌ AVOID: Manual transaction handling
# db.execute("BEGIN")
# db.execute("INSERT INTO ...")
# db.commit()
```

---

## Frontend Standards (TypeScript/React)

### Code Style & Organization

#### File Organization
```typescript
// src/components/dashboard/<module>/ComponentName.tsx structure:

// 1. Imports (React → third-party → local)
import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis } from 'recharts'

import { api } from '@/services/api'
import { DateRangePicker } from '@/components/common/DateRangePicker'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import type { SalesMetrics } from '@/types/sales'

// 2. Constants
const REFRESH_INTERVAL = 30000  // 30 seconds
const DEFAULT_LIMIT = 100

// 3. Types
interface SalesChartProps {
  startDate: Date
  endDate: Date
  onFilterChange?: (filters: FilterState) => void
}

interface FilterState {
  channel?: string
  customer?: string
  product?: string
}

// 4. Component
export function SalesChart({ startDate, endDate, onFilterChange }: SalesChartProps) {
  const [filters, setFilters] = useState<FilterState>({})
  
  // 5. Hooks
  const { data, isLoading, error } = useQuery({
    queryKey: ['sales-metrics', startDate, endDate, filters],
    queryFn: () => api.get('/api/v1/sales/metrics', { startDate, endDate, ...filters }),
    staleTime: 5 * 60 * 1000,  // 5 minutes
  })
  
  // 6. Side effects
  useEffect(() => {
    onFilterChange?.(filters)
  }, [filters])
  
  // 7. Render
  if (isLoading) return <LoadingSpinner />
  if (error) return <div className="text-red-600">Error loading data</div>
  
  return (
    <div className="p-4">
      <LineChart data={data} width={800} height={300}>
        <XAxis dataKey="month" />
        <YAxis />
        <Line type="monotone" dataKey="revenue" stroke="#8884d8" />
      </LineChart>
    </div>
  )
}
```

#### Naming Conventions
- **Components**: `PascalCase` (e.g., `SalesChart.tsx`, `InventoryTable.tsx`)
- **Hooks**: Prefix with `use` (e.g., `useAuth.ts`, `useInventory.ts`)
- **Types**: `PascalCase` interfaces (e.g., `InventoryLevel`, `SalesMetrics`)
- **Constants**: `UPPER_CASE_WITH_UNDERSCORES` (e.g., `API_BASE_URL`)
- **Functions**: `camelCase` (e.g., `formatCurrency()`, `calculateDays()`)
- **Utilities**: `camelCase` (e.g., `formatDate.ts`, `validateEmail.ts`)

#### File Size Limits
- **Target**: <300 lines per component
- **Rationale**: Easier testing, reusability, code review
- **Example: Breaking apart large components**

```typescript
// ❌ BEFORE: 450 lines
src/pages/LeadTimeDashboard.tsx

// ✅ AFTER: Split into smaller components
src/components/dashboard/leadtime/
├── LeadTimeSummary.tsx      (150 lines)
├── BottleneckAnalysis.tsx   (120 lines)
├── OTIFRecentOrders.tsx     (100 lines)
└── LeadTimeTrends.tsx       (80 lines)

// Then compose in page
src/pages/LeadTimeDashboard.tsx  (50 lines - just composition)
```

### Frontend Patterns

#### 1. Custom Hook Pattern

```typescript
// src/hooks/useInventory.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import type { InventoryLevel } from '@/types/inventory'

export function useInventory(materialId?: string) {
  return useQuery({
    queryKey: ['inventory', materialId],
    queryFn: () => 
      api.get('/api/v1/inventory/levels', { material_id: materialId }),
    staleTime: 5 * 60 * 1000,
  })
}

export function useUpdateInventory() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: UpdateInventoryPayload) =>
      api.put('/api/v1/inventory/levels', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] })
    },
  })
}
```

#### 2. API Service Pattern

```typescript
// src/services/api.ts

import axios, { AxiosInstance, AxiosError } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add request interceptor for auth token
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response.data,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Clear token and redirect to login
          localStorage.removeItem('auth_token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    return this.client.get(endpoint, { params })
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.client.post(endpoint, data)
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.client.put(endpoint, data)
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.client.delete(endpoint)
  }
}

export const api = new ApiClient()
```

#### 3. Date Handling Pattern (Timezone-Safe)

```typescript
// src/utils/dateHelpers.ts - CRITICAL for avoiding UTC midnight bug

import { startOfMonth, endOfDay, format, differenceInDays, addDays } from 'date-fns'

/**
 * Get first day of current month in local timezone.
 * IMPORTANT: Avoids UTC midnight bug when using .toISOString()
 */
export function getFirstDayOfMonth(date = new Date()): Date {
  return startOfMonth(date)
}

/**
 * Get today's date in local timezone.
 * IMPORTANT: Avoids UTC midnight bug
 */
export function getToday(): Date {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), now.getDate())
}

/**
 * Get default date range: 1st of month → today
 */
export function getDefaultDateRange(): [Date, Date] {
  return [getFirstDayOfMonth(), getToday()]
}

/**
 * Format date as YYYY-MM-DD (safe for API calls)
 * IMPORTANT: Uses local date, not UTC
 */
export function formatDateForApi(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Calculate days between two dates
 */
export function getDaysBetween(start: Date, end: Date): number {
  return differenceInDays(end, start)
}

/**
 * Add days to date
 */
export function addDaysToDate(date: Date, days: number): Date {
  return addDays(date, days)
}

// ✅ USAGE in components
const [dateRange, setDateRange] = useState(getDefaultDateRange())

// ✅ When sending to API
const apiPayload = {
  start_date: formatDateForApi(dateRange[0]),
  end_date: formatDateForApi(dateRange[1]),
}

// ❌ AVOID (UTC midnight bug)
// const isoString = dateRange[0].toISOString()  // Can shift to previous day in UTC!
```

#### 4. Component Composition Pattern

```typescript
// ✅ GOOD: Compose smaller components
export function InventoryDashboard() {
  const [dateRange, setDateRange] = useState(getDefaultDateRange())

  return (
    <div className="space-y-4">
      <DateRangePicker
        value={dateRange}
        onChange={setDateRange}
      />
      <div className="grid grid-cols-2 gap-4">
        <InventorySummary dateRange={dateRange} />
        <InventoryTrends dateRange={dateRange} />
      </div>
      <InventoryMovementTable dateRange={dateRange} />
    </div>
  )
}

// ✅ GOOD: Each sub-component is self-contained
function InventorySummary({ dateRange }: { dateRange: [Date, Date] }) {
  const { data } = useInventory(dateRange)
  return <div>{/* render data */}</div>
}

// ❌ AVOID: One massive component with all logic
function InventoryDashboard_Old() {
  // 300+ lines of complex logic...
}
```

#### 5. Error Boundary Pattern

```typescript
// src/components/common/ErrorBoundary.tsx

import React, { ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-4 bg-red-50 text-red-700">
          Something went wrong: {this.state.error?.message}
        </div>
      )
    }

    return this.props.children
  }
}
```

#### 6. Responsive Design Pattern (TailwindCSS)

```typescript
// ✅ GOOD: Mobile-first responsive design
export function DataTable({ data }: { data: any[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse">
        <thead className="bg-gray-100 hidden md:table-header-group">
          <tr>
            <th className="px-4 py-2 text-left">Material</th>
            <th className="px-4 py-2 text-right">Quantity</th>
            <th className="px-4 py-2 text-right">Value</th>
          </tr>
        </thead>
        <tbody className="block md:table-row-group">
          {data.map((row) => (
            <tr
              key={row.id}
              className="block border-b md:table-row mb-4 md:mb-0"
            >
              <td className="block md:table-cell px-4 py-2 before:content-['Material:'] before:font-bold before:mr-2 md:before:content-none">
                {row.material}
              </td>
              <td className="block md:table-cell px-4 py-2 text-right before:content-['Qty:'] before:font-bold before:mr-2 md:before:content-none">
                {row.quantity}
              </td>
              <td className="block md:table-cell px-4 py-2 text-right before:content-['Value:'] before:font-bold before:mr-2 md:before:content-none">
                ${row.value.toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

---

## Database Standards (PostgreSQL)

### Schema Design Principles

#### 1. Naming Convention
```sql
-- Tables: lowercase_plural
CREATE TABLE fact_inventory (...)
CREATE TABLE dim_material (...)

-- Columns: lowercase_with_underscores
CREATE TABLE fact_sales (
  id SERIAL PRIMARY KEY,
  material_id VARCHAR(50) NOT NULL,
  customer_id VARCHAR(50) NOT NULL,
  billing_date DATE NOT NULL,
  net_value NUMERIC(18,4)
)

-- Indexes: idx_<table>_<columns>
CREATE INDEX idx_fact_sales_billing_date ON fact_sales(billing_date)
CREATE INDEX idx_fact_sales_material_customer ON fact_sales(material_id, customer_id)

-- Foreign keys: fk_<table>_<referenced_table>
ALTER TABLE fact_sales
ADD CONSTRAINT fk_fact_sales_dim_material
FOREIGN KEY (material_id) REFERENCES dim_material(material_id)
```

#### 2. Data Type Standards
```sql
-- Use appropriate types
-- ✅ GOOD
material_code VARCHAR(50)           -- Fixed-width identifiers
quantity NUMERIC(15,3)              -- Business calculations (not FLOAT)
net_value NUMERIC(18,4)             -- Money (not FLOAT)
posting_date DATE                   -- Dates without time
created_at TIMESTAMP NOT NULL       -- Timestamps with time
description TEXT                    -- Long text
is_active BOOLEAN DEFAULT true      -- Flags

-- ❌ AVOID
material_code TEXT                  -- Should be VARCHAR(50)
quantity FLOAT                      -- Should be NUMERIC (precision loss)
created_at BIGINT                   -- Should be TIMESTAMP
```

#### 3. Constraint Standards
```sql
-- Primary Keys
CREATE TABLE fact_sales (
  id SERIAL PRIMARY KEY,  -- Always include explicit PK
  ...
)

-- Unique Constraints (Business Keys)
CREATE TABLE raw_zrsd002 (
  id SERIAL PRIMARY KEY,
  billing_document VARCHAR(50),
  billing_item INTEGER,
  UNIQUE(billing_document, billing_item),  -- Composite unique key
  ...
)

-- Foreign Keys
CREATE TABLE fact_sales (
  material_id VARCHAR(50) REFERENCES dim_material(material_id),
  ...
)

-- NOT NULL
CREATE TABLE fact_inventory (
  material_id VARCHAR(50) NOT NULL,  -- Required fields
  quantity NUMERIC(15,3) NOT NULL,
  ...
)

-- CHECK Constraints
CREATE TABLE fact_sales (
  quantity NUMERIC(18,4) CHECK (quantity > 0),
  net_value NUMERIC(18,4) CHECK (net_value >= 0),
  ...
)

-- DEFAULT Values
CREATE TABLE fact_alert (
  status VARCHAR(20) DEFAULT 'open',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ...
)
```

#### 4. Indexing Standards
```sql
-- Primary indexes on frequently queried columns
CREATE INDEX idx_fact_sales_billing_date ON fact_sales(billing_date)
CREATE INDEX idx_fact_sales_material_id ON fact_sales(material_id)
CREATE INDEX idx_fact_sales_customer_id ON fact_sales(customer_id)

-- Composite indexes for common filter combinations
CREATE INDEX idx_fact_sales_material_customer_date 
  ON fact_sales(material_id, customer_id, billing_date)

-- Indexes on foreign keys (auto-referenced)
CREATE INDEX idx_fact_sales_fk_material 
  ON fact_sales(material_id)

-- Index on date ranges (common in dashboards)
CREATE INDEX idx_fact_inventory_snapshot_date_material
  ON fact_inventory(snapshot_date DESC, material_id)

-- ❌ AVOID: Indexing low-cardinality columns
-- CREATE INDEX idx_fact_sales_is_active ON fact_sales(is_active)
-- (Only 2 values: true/false - not efficient)
```

#### 5. View Standards
```sql
-- Materialized views for pre-aggregated metrics
CREATE MATERIALIZED VIEW v_inventory_summary AS
SELECT
  m.material_id,
  m.description,
  SUM(fi.qty_kg) as total_qty_kg,
  SUM(fi.net_value) as total_value,
  MAX(fi.snapshot_date) as last_update
FROM fact_inventory fi
  JOIN dim_material m ON fi.material_id = m.material_id
GROUP BY m.material_id, m.description
WITH DATA;

-- Refresh strategy (after data loads)
REFRESH MATERIALIZED VIEW v_inventory_summary;

-- Create index on materialized view for faster queries
CREATE INDEX idx_v_inventory_summary_material
  ON v_inventory_summary(material_id);
```

### Query Standards

#### 1. SELECT Pattern
```sql
-- ✅ GOOD: Explicit columns, clear joins, readable formatting
SELECT
  m.material_id,
  m.description,
  fi.qty_kg,
  fi.net_value,
  fi.snapshot_date
FROM fact_inventory fi
  INNER JOIN dim_material m ON fi.material_id = m.material_id
WHERE fi.snapshot_date >= DATE '2026-01-01'
  AND fi.qty_kg > 0
  AND m.active = true
ORDER BY fi.snapshot_date DESC, m.material_id
LIMIT 100;

-- ❌ AVOID: SELECT *, unclear joins, poor formatting
SELECT * FROM fact_inventory, dim_material
WHERE fact_inventory.material_id = dim_material.material_id;
```

#### 2. INSERT/UPDATE Pattern
```sql
-- ✅ GOOD: UPSERT with business keys
INSERT INTO raw_zrsd002 (
  billing_document, billing_item, customer_name, material_code, 
  quantity, net_value, billing_date, row_hash, created_at
) VALUES (
  'BD-123456', 1, 'Customer A', 'MAT-001', 100.00, 5000.00, 
  '2026-01-13', 'abc123...', NOW()
)
ON CONFLICT (billing_document, billing_item) DO UPDATE SET
  customer_name = EXCLUDED.customer_name,
  quantity = EXCLUDED.quantity,
  net_value = EXCLUDED.net_value,
  updated_at = NOW()
WHERE raw_zrsd002.row_hash IS DISTINCT FROM EXCLUDED.row_hash;

-- ❌ AVOID: Duplicate inserts without upsert
INSERT INTO raw_zrsd002 (...) VALUES (...)  -- Will fail if duplicate!
```

#### 3. Aggregation Pattern
```sql
-- ✅ GOOD: Clear grouping with NULL handling
SELECT
  c.customer_id,
  c.name,
  DATE_TRUNC('month', fs.billing_date) as period,
  COUNT(*) as order_count,
  SUM(COALESCE(fs.quantity, 0)) as total_qty,
  SUM(COALESCE(fs.net_value, 0)) as total_revenue,
  AVG(COALESCE(fs.net_value, 0)) as avg_order_value
FROM fact_sales fs
  INNER JOIN dim_customer c ON fs.customer_id = c.customer_id
WHERE fs.billing_date >= DATE '2025-01-01'
GROUP BY c.customer_id, c.name, DATE_TRUNC('month', fs.billing_date)
HAVING SUM(fs.net_value) > 10000
ORDER BY period DESC, total_revenue DESC;

-- ❌ AVOID: Group without handling NULLs
SELECT customer_id, SUM(net_value) FROM fact_sales GROUP BY customer_id;
```

---

## ETL Standards

### Loader Standards

#### 1. File Type Detection
```python
# ✅ GOOD: Flexible header pattern matching
def detect_file_type(headers: List[str]) -> Optional[str]:
    headers_lower = [h.lower() for h in headers]
    headers_str = ' '.join(headers_lower)
    
    if 'material code' in headers_str and 'movement type' in headers_str:
        return 'MB51'
    elif 'billing document' in headers_str and 'customer' in headers_str:
        return 'ZRSD002'
    elif 'material' in headers_str and 'ph 1' in headers_str:
        return 'ZRSD006'
    else:
        return None

# ❌ AVOID: Brittle exact column position matching
def detect_file_type_bad(row: List[str]) -> Optional[str]:
    if row[0] == 'Material Code' and row[1] == 'Movement Type':
        return 'MB51'  # Breaks if columns reordered!
```

#### 2. Record Validation
```python
# ✅ GOOD: Validate each field with clear rules
def validate_record(record: Dict) -> Tuple[bool, Optional[str]]:
    # Required fields
    if not record.get('material_code'):
        return False, "material_code is required"
    
    if not record.get('posting_date'):
        return False, "posting_date is required"
    
    # Business rules
    if record.get('quantity', 0) == 0:
        return False, "quantity must be non-zero"
    
    if record.get('posting_date') > datetime.now():
        return False, "posting_date cannot be in future"
    
    return True, None

# ❌ AVOID: Loose validation
def validate_record_bad(record: Dict) -> bool:
    return record.get('material_code') is not None
```

#### 3. Deduplication Strategy
```python
# ✅ GOOD: Row-hash based dedup (excludes source_file)
def compute_row_hash(record: Dict) -> str:
    # Exclude fields that change between uploads
    dedup_dict = {k: v for k, v in record.items() if k != 'source_file'}
    record_str = json.dumps(dedup_dict, sort_keys=True, default=str)
    return hashlib.md5(record_str.encode()).hexdigest()

# Usage in loader
if mode == 'upsert':
    existing = db.query(RawZRSD002).filter_by(
        billing_document=record['billing_document'],
        billing_item=record['billing_item']
    ).first()
    
    if existing and existing.row_hash == compute_row_hash(record):
        # Skip: identical record
        return 'skipped'
    else:
        # Update or insert
        return 'upserted'

# ❌ AVOID: Including source_file in hash
# def compute_row_hash_bad(record: Dict) -> str:
#     record_str = json.dumps(record, sort_keys=True)  # Includes source_file!
```

---

## Testing Standards

### Unit Test Pattern (Backend)

```python
# tests/test_leadtime_calculator.py

import pytest
from datetime import datetime, timedelta
from src.core.leadtime_calculator import LeadTimeCalculator
from src.db.models import FactProduction

class TestLeadTimeCalculator:
    
    @pytest.fixture
    def calculator(self, db_session):
        return LeadTimeCalculator(db_session)
    
    @pytest.fixture
    def sample_production(self, db_session):
        prod = FactProduction(
            so_id='SO-001',
            po_create_date=datetime(2026, 1, 1),
            gr_date=datetime(2026, 1, 11),  # 10 days
            gi_date=datetime(2026, 1, 16)   # 5 more days
        )
        db_session.add(prod)
        db_session.commit()
        return prod
    
    def test_calculate_end_to_end_success(self, calculator, sample_production):
        """Test normal lead time calculation."""
        result = calculator.calculate_end_to_end('SO-001')
        
        assert result['total_days'] == 15
        assert result['production_days'] == 10
        assert result['transit_days'] == 5
    
    def test_calculate_end_to_end_not_found(self, calculator):
        """Test with non-existent SO."""
        with pytest.raises(ValueError) as exc_info:
            calculator.calculate_end_to_end('SO-NONEXISTENT')
        
        assert "not found" in str(exc_info.value)
    
    def test_calculate_end_to_end_invalid_input(self, calculator):
        """Test with invalid input."""
        with pytest.raises(ValueError) as exc_info:
            calculator.calculate_end_to_end('')
        
        assert "required" in str(exc_info.value)
```

### Component Test Pattern (Frontend)

```typescript
// src/components/__tests__/SalesChart.test.tsx

import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SalesChart } from '../SalesChart'

const queryClient = new QueryClient()

describe('SalesChart', () => {
  it('renders loading state initially', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <SalesChart
          startDate={new Date('2026-01-01')}
          endDate={new Date('2026-01-31')}
        />
      </QueryClientProvider>
    )

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('renders chart with data', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <SalesChart
          startDate={new Date('2026-01-01')}
          endDate={new Date('2026-01-31')}
        />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument()
    })

    expect(screen.getByRole('presentation')).toBeInTheDocument()
  })
})
```

---

## Documentation Standards

### Code Comments

```python
# ✅ GOOD: Clear, concise comments
def calculate_lead_time(so_id: str) -> int:
    """Calculate total lead time in days from SO creation to GI.
    
    Args:
        so_id: Sales order identifier
        
    Returns:
        Total lead time in days
        
    Raises:
        ValueError: If SO not found or invalid
        
    Example:
        >>> calculate_lead_time('SO-123456')
        15
    """
    # Retrieve production data for this SO
    production = db.query(FactProduction).filter_by(so_id=so_id).first()
    if not production:
        raise ValueError(f"SO {so_id} not found")
    
    # Calculate days between creation and issue
    lead_time = (production.gi_date - production.po_create_date).days
    return lead_time

# ❌ AVOID: Redundant or unclear comments
# Get production data
production = db.query(FactProduction).filter_by(so_id=so_id).first()
# Set x to result
x = production.gi_date - production.po_create_date
```

### Docstring Standards

```python
# ✅ GOOD: Complete docstring (Google style)
def process_upload(file_path: Path, file_type: str, mode: str = 'upsert') -> Dict[str, int]:
    """
    Process uploaded Excel file and load into database.
    
    Supports auto-detection of SAP file types (MB51, ZRSD002, etc.)
    with deduplication and business key validation.
    
    Args:
        file_path: Path to Excel file
        file_type: Detected type ('MB51', 'ZRSD002', etc.)
        mode: Loading mode - 'insert' (fail on duplicate) or 'upsert' (update if exists)
        
    Returns:
        Dictionary with statistics:
        {
            'loaded': 1000,      # New records inserted
            'updated': 500,      # Existing records updated (upsert mode)
            'skipped': 100,      # Duplicates skipped
            'errors': 5          # Failed records
        }
        
    Raises:
        FileNotFoundError: If file_path does not exist
        ValueError: If file format is invalid
        IntegrityError: If mode='insert' and duplicate key exists
        
    Example:
        >>> process_upload(
        ...     Path('data/zrsd002.xlsx'),
        ...     'ZRSD002',
        ...     mode='upsert'
        ... )
        {'loaded': 1000, 'updated': 500, 'skipped': 100, 'errors': 0}
    """
```

---

## Git Workflow

### Commit Message Standards

```bash
# Format: <type>(<scope>): <subject>
#         <blank line>
#         <body>
#         <blank line>
#         <footer>

# ✅ GOOD examples
git commit -m "feat(api): Add OTIF delivery tracking endpoint

Add GET /api/v1/leadtime/recent-orders endpoint for displaying
recent deliveries with OTIF status. Includes:
- delivery_date column to FactDelivery model
- OTIF status calculation (On Time/Late/Pending)
- Frontend OTIFRecentOrdersTable component
- Materialized view for performance

Closes #123"

git commit -m "fix(loader): Fix ZRSD002 column mapping for customer name

Customer name was reading from wrong Excel column. Changed:
- 'Customer Name' → 'Name of Bill to'
- 'Material Description' → 'Description'
- 'Volume' → 'Volum' (with typo match)

Impact: All ZRSD002 uploads now capture customer information correctly"

git commit -m "docs: Update codebase summary with OTIF implementation"

# ❌ AVOID
git commit -m "fixes"
git commit -m "Updated files"
git commit -m "work in progress"
```

### Branch Naming

```bash
# Format: <type>/<issue-number>-<short-description>

# ✅ GOOD
git checkout -b feature/123-otif-delivery-tracking
git checkout -b fix/456-zrsd002-column-mapping
git checkout -b docs/update-architecture

# ❌ AVOID
git checkout -b feature
git checkout -b fix_stuff
git checkout -b mychanges
```

---

## Code Review Checklist

Before submitting PR, verify:

- [ ] Code follows naming conventions (files, classes, functions, vars)
- [ ] Functions have docstrings (for public API)
- [ ] Error handling with try/catch (specific exceptions)
- [ ] No console.log/print statements in production code
- [ ] Database changes include migration file
- [ ] API endpoints have request/response validation (Pydantic)
- [ ] Frontend components under 300 lines
- [ ] Backend modules under 200 lines (except models.py)
- [ ] Tests included for new functionality
- [ ] No hardcoded secrets/credentials
- [ ] No unused imports
- [ ] Commit messages follow standards

---

## Summary

| Aspect | Standard |
|--------|----------|
| **Files** | <200 LOC (backend), <300 LOC (frontend), except models/schema |
| **Naming** | snake_case (functions), PascalCase (classes), UPPER_CASE (constants) |
| **Functions** | Clear docstrings, specific error handling, type hints |
| **Database** | Proper constraints, indexes, materialized views for performance |
| **API** | Pydantic validation, JWT auth, standardized error responses |
| **Frontend** | Custom hooks, TanStack Query, timezone-safe dates |
| **Testing** | Unit + integration tests, clear test names and fixtures |
| **Docs** | Docstrings, clear comments, README for new modules |
| **Git** | Conventional commits, descriptive branch names, clean history |
