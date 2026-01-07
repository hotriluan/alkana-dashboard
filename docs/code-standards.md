# Alkana Dashboard - Code Standards

## Code Organization Principles

### 1. Separation of Concerns
- **API Layer**: Handle HTTP requests/responses only
- **Business Logic**: Core calculations and algorithms in `src/core/`
- **Data Access**: Database operations in `src/db/`
- **ETL**: Data processing in `src/etl/`

### 2. Single Responsibility Principle
- Each module should have one clear purpose
- Functions should do one thing well
- Classes should represent a single concept

### 3. DRY (Don't Repeat Yourself)
- Extract common logic into reusable functions
- Use utility modules for shared functionality
- Avoid code duplication across modules

## Backend Code Standards (Python)

### File Naming Conventions
- **Modules**: `snake_case.py` (e.g., `lead_time_calculator.py`)
- **Classes**: `PascalCase` (e.g., `LeadTimeCalculator`)
- **Functions**: `snake_case` (e.g., `calculate_lead_time`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_BATCH_SIZE`)

### Code Structure

#### Module Organization
```python
"""
Module docstring explaining purpose and usage.
"""
# Standard library imports
import sys
from datetime import datetime

# Third-party imports
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Local imports
from src.db.connection import get_db
from src.core.business_logic import calculate_metric

# Constants
MAX_RESULTS = 1000

# Functions/Classes
def my_function():
    """Function docstring."""
    pass
```

#### Function Documentation
```python
def calculate_lead_time(
    order_date: datetime,
    delivery_date: datetime,
    include_weekends: bool = True
) -> float:
    """
    Calculate lead time in days between order and delivery.
    
    Args:
        order_date: Order placement date
        delivery_date: Actual delivery date
        include_weekends: Whether to count weekends (default: True)
    
    Returns:
        Lead time in days (float)
    
    Raises:
        ValueError: If delivery_date is before order_date
    """
    if delivery_date < order_date:
        raise ValueError("Delivery date cannot be before order date")
    
    delta = delivery_date - order_date
    return delta.total_seconds() / 86400
```

### Type Hints
- **Always use type hints** for function parameters and return values
- Use `Optional[T]` for nullable types
- Use `List[T]`, `Dict[K, V]` for collections
- Use Pydantic models for complex data structures

```python
from typing import Optional, List, Dict
from pydantic import BaseModel

class ProductMetrics(BaseModel):
    product_id: str
    revenue: float
    quantity: int
    margin: Optional[float] = None

def get_top_products(
    limit: int = 10,
    min_revenue: Optional[float] = None
) -> List[ProductMetrics]:
    """Get top performing products."""
    pass
```

### Error Handling
- Use specific exception types
- Provide meaningful error messages
- Log errors appropriately
- Clean up resources in `finally` blocks

```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def process_data(file_path: str):
    try:
        with open(file_path, 'r') as f:
            data = f.read()
        return parse_data(data)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail="Data file not found")
    except Exception as e:
        logger.exception(f"Unexpected error processing {file_path}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Database Patterns

#### Session Management
```python
from src.db.connection import SessionLocal

def get_data():
    db = SessionLocal()
    try:
        result = db.query(Model).all()
        return result
    finally:
        db.close()
```

#### Query Optimization
- Use `select_related` / `joinedload` for eager loading
- Add indexes on frequently queried columns
- Use pagination for large result sets
- Avoid N+1 queries

```python
from sqlalchemy.orm import joinedload

# Good: Single query with join
products = db.query(Product)\
    .options(joinedload(Product.category))\
    .limit(100)\
    .all()

# Bad: N+1 queries
products = db.query(Product).limit(100).all()
for product in products:
    category = product.category  # Triggers separate query
```

### API Endpoint Standards

#### Naming Conventions
- Use plural nouns for resources: `/api/products`, `/api/orders`
- Use hyphens for multi-word: `/api/lead-time`, `/api/ar-aging`
- Use query parameters for filtering: `/api/products?category=electronics`

#### Response Format
```python
from pydantic import BaseModel
from typing import List, Optional

class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    
class PaginatedResponse(BaseModel):
    data: List[ProductResponse]
    total: int
    page: int
    page_size: int

@router.get("/products", response_model=PaginatedResponse)
def get_products(
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None
):
    """Get paginated product list."""
    pass
```

#### HTTP Status Codes
- `200 OK`: Successful GET, PUT, PATCH
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing/invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Frontend Code Standards (TypeScript/React)

### File Naming Conventions
- **Components**: `PascalCase.tsx` (e.g., `DashboardLayout.tsx`)
- **Hooks**: `camelCase.ts` with `use` prefix (e.g., `useAuth.ts`)
- **Utilities**: `camelCase.ts` (e.g., `formatCurrency.ts`)
- **Types**: `camelCase.ts` or `types.ts`

### Component Structure

#### Functional Components
```typescript
import React from 'react';

interface ProductCardProps {
  productId: string;
  name: string;
  price: number;
  onSelect?: (id: string) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({
  productId,
  name,
  price,
  onSelect
}) => {
  const handleClick = () => {
    onSelect?.(productId);
  };

  return (
    <div className="product-card" onClick={handleClick}>
      <h3>{name}</h3>
      <p>${price.toFixed(2)}</p>
    </div>
  );
};
```

#### Custom Hooks
```typescript
import { useState, useEffect } from 'react';
import { api } from '../services/api';

interface UseProductsResult {
  products: Product[];
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

export const useProducts = (category?: string): UseProductsResult => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const data = await api.getProducts(category);
      setProducts(data);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [category]);

  return { products, loading, error, refetch: fetchProducts };
};
```

### TypeScript Standards

#### Type Definitions
```typescript
// types/product.ts
export interface Product {
  id: string;
  name: string;
  price: number;
  category: Category;
  createdAt: Date;
}

export type Category = 'electronics' | 'clothing' | 'food';

export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}
```

#### Avoid `any`
```typescript
// Bad
const processData = (data: any) => {
  return data.map((item: any) => item.value);
};

// Good
interface DataItem {
  value: number;
}

const processData = (data: DataItem[]): number[] => {
  return data.map(item => item.value);
};
```

### React Best Practices

#### State Management
- Use `useState` for local component state
- Use TanStack Query for server state
- Avoid prop drilling (use context or composition)

#### Performance Optimization
```typescript
import React, { useMemo, useCallback } from 'react';

const ExpensiveComponent: React.FC<Props> = ({ data, onUpdate }) => {
  // Memoize expensive calculations
  const processedData = useMemo(() => {
    return data.map(item => expensiveOperation(item));
  }, [data]);

  // Memoize callbacks to prevent re-renders
  const handleUpdate = useCallback((id: string) => {
    onUpdate(id);
  }, [onUpdate]);

  return <div>{/* render */}</div>;
};

// Memoize component
export default React.memo(ExpensiveComponent);
```

#### Conditional Rendering
```typescript
// Good: Early return
if (loading) return <Spinner />;
if (error) return <ErrorMessage error={error} />;
if (!data) return null;

return <DataDisplay data={data} />;

// Good: Ternary for simple cases
{isLoggedIn ? <Dashboard /> : <Login />}

// Good: Logical AND for optional rendering
{showDetails && <DetailPanel />}
```

### CSS/Styling Standards

#### TailwindCSS Usage
```typescript
// Good: Semantic class grouping
<div className="
  flex items-center justify-between
  p-4 rounded-lg
  bg-white shadow-md
  hover:shadow-lg transition-shadow
">
  {/* content */}
</div>

// Extract repeated patterns
const cardClasses = "p-4 rounded-lg bg-white shadow-md";
```

#### Responsive Design
```typescript
<div className="
  grid grid-cols-1
  md:grid-cols-2
  lg:grid-cols-3
  gap-4
">
  {/* responsive grid */}
</div>
```

## Testing Standards

### Backend Tests (pytest)
```python
import pytest
from src.core.leadtime_calculator import calculate_lead_time
from datetime import datetime

def test_calculate_lead_time_basic():
    """Test basic lead time calculation."""
    order_date = datetime(2024, 1, 1)
    delivery_date = datetime(2024, 1, 10)
    
    result = calculate_lead_time(order_date, delivery_date)
    
    assert result == 9.0

def test_calculate_lead_time_invalid_dates():
    """Test error handling for invalid dates."""
    order_date = datetime(2024, 1, 10)
    delivery_date = datetime(2024, 1, 1)
    
    with pytest.raises(ValueError):
        calculate_lead_time(order_date, delivery_date)
```

### Frontend Tests (React Testing Library)
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductCard } from './ProductCard';

describe('ProductCard', () => {
  it('renders product information', () => {
    render(
      <ProductCard
        productId="123"
        name="Test Product"
        price={99.99}
      />
    );
    
    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('$99.99')).toBeInTheDocument();
  });

  it('calls onSelect when clicked', () => {
    const handleSelect = jest.fn();
    
    render(
      <ProductCard
        productId="123"
        name="Test Product"
        price={99.99}
        onSelect={handleSelect}
      />
    );
    
    fireEvent.click(screen.getByText('Test Product'));
    expect(handleSelect).toHaveBeenCalledWith('123');
  });
});
```

## Git Commit Standards

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process, dependencies, tooling

### Examples
```
feat(api): add lead time analytics endpoint

Implement new endpoint for calculating lead time metrics
with support for filtering by date range and product category.

Closes #123

---

fix(frontend): resolve chart rendering issue on mobile

Charts were not responsive on small screens due to
fixed width container. Updated to use responsive container.

---

docs(readme): update installation instructions

Added Docker setup instructions and environment
variable configuration details.
```

## Code Review Checklist

### General
- [ ] Code follows project structure and naming conventions
- [ ] No commented-out code or debug statements
- [ ] No hardcoded values (use config/constants)
- [ ] Error handling is appropriate
- [ ] Logging is adequate

### Backend
- [ ] Type hints are present and correct
- [ ] Database sessions are properly closed
- [ ] Queries are optimized (no N+1)
- [ ] API responses follow standard format
- [ ] Input validation is implemented

### Frontend
- [ ] TypeScript types are defined
- [ ] Components are properly memoized if needed
- [ ] No prop drilling (use context/composition)
- [ ] Accessibility attributes are present
- [ ] Responsive design is implemented

### Testing
- [ ] Unit tests cover critical logic
- [ ] Edge cases are tested
- [ ] Tests are readable and maintainable
- [ ] Test names clearly describe what is being tested
