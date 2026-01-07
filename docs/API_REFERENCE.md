# API Reference

Complete reference for the Alkana Dashboard REST API.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.dashboard.yourcompany.com`

All endpoints are prefixed with `/api`

## Authentication

### JWT Token Authentication

The API uses JWT (JSON Web Token) bearer authentication.

#### Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin"
  }
}
```

#### Using Token

Include token in `Authorization` header for all protected endpoints:

```http
GET /api/executive/summary
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Token Refresh

Tokens expire after 24 hours (configurable). Re-authenticate to get new token.

---

## Executive Dashboard

### Get Executive Summary

Retrieve high-level KPIs across all business areas.

```http
GET /api/executive/summary
Authorization: Bearer <token>
```

**Query Parameters:**
- `start_date` (optional): Filter start date (YYYY-MM-DD)
- `end_date` (optional): Filter end date (YYYY-MM-DD)

**Response:**
```json
{
  "total_revenue": 15750000.50,
  "revenue_growth_pct": 12.5,
  "total_customers": 145,
  "active_customers": 128,
  "total_orders": 1250,
  "completed_orders": 1180,
  "completion_rate": 94.4,
  "total_inventory_value": 2500000.00,
  "inventory_items": 8500,
  "total_ar": 3200000.00,
  "overdue_ar": 450000.00,
  "overdue_pct": 14.06
}
```

### Get Revenue by Division

```http
GET /api/executive/revenue-by-division
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "division_code": "DIV01",
    "revenue": 8500000.00,
    "customer_count": 75,
    "order_count": 680
  },
  {
    "division_code": "DIV02",
    "revenue": 7250000.50,
    "customer_count": 70,
    "order_count": 570
  }
]
```

### Get Top Customers

```http
GET /api/executive/top-customers
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit` (optional): Number of top customers (default: 10)

**Response:**
```json
[
  {
    "customer_name": "ABC Trading Co.",
    "revenue": 1250000.00,
    "order_count": 45
  },
  {
    "customer_name": "XYZ Industries",
    "revenue": 980000.50,
    "order_count": 38
  }
]
```

---

## Inventory Management

### Get Current Inventory

```http
GET /api/inventory/current
Authorization: Bearer <token>
```

**Query Parameters:**
- `material_code` (optional): Filter by material code
- `plant` (optional): Filter by plant
- `storage_location` (optional): Filter by storage location
- `min_qty` (optional): Minimum quantity threshold

**Response:**
```json
[
  {
    "material_code": "P01-12345",
    "material_description": "Premium Paint - White 5L",
    "plant": "1000",
    "storage_location": "FG01",
    "quantity": 2500.0,
    "unit": "PC",
    "value": 125000.00,
    "last_movement_date": "2025-12-29"
  }
]
```

### Get Inventory Movements

```http
GET /api/inventory/movements
Authorization: Bearer <token>
```

**Query Parameters:**
- `material_code` (optional): Filter by material
- `start_date` (optional): Movement start date
- `end_date` (optional): Movement end date
- `movement_type` (optional): Filter by MVT type (e.g., "101", "261", "601")
- `limit` (optional): Number of records (default: 100)

**Response:**
```json
[
  {
    "document_number": "5000123456",
    "material_code": "P01-12345",
    "movement_type": "601",
    "movement_type_text": "Goods Issue to Customer",
    "quantity": -50.0,
    "unit": "PC",
    "plant": "1000",
    "storage_location": "FG01",
    "posting_date": "2025-12-29",
    "reference_document": "210045678",
    "batch_number": "25L2535110"
  }
]
```

### Get Slow-Moving Items

```http
GET /api/inventory/slow-moving
Authorization: Bearer <token>
```

**Query Parameters:**
- `days_threshold` (optional): Days without movement (default: 90)

**Response:**
```json
[
  {
    "material_code": "P02-98765",
    "material_description": "Semi-Finished Product",
    "quantity": 150.0,
    "value": 45000.00,
    "last_movement_date": "2025-09-15",
    "days_no_movement": 106
  }
]
```

---

## Lead Time Analytics

### Get Lead Time Summary

```http
GET /api/lead-time/summary
Authorization: Bearer <token>
```

**Response:**
```json
{
  "avg_total_leadtime_days": 15.3,
  "avg_procurement_days": 5.2,
  "avg_production_days": 7.8,
  "avg_distribution_days": 2.3,
  "orders_analyzed": 1250,
  "mto_orders": 450,
  "mts_orders": 800
}
```

### Get Lead Time Details

```http
GET /api/lead-time/details
Authorization: Bearer <token>
```

**Query Parameters:**
- `order_type` (optional): "MTO" or "MTS"
- `material_code` (optional): Filter by material
- `start_date` (optional): Order start date
- `end_date` (optional): Order end date

**Response:**
```json
[
  {
    "sales_order": "210045678",
    "material_code": "P01-12345",
    "customer_name": "ABC Trading",
    "order_date": "2025-12-01",
    "delivery_date": "2025-12-15",
    "total_leadtime_days": 14,
    "procurement_days": 4,
    "production_days": 8,
    "distribution_days": 2,
    "order_type": "MTO",
    "bottleneck_stage": "Production"
  }
]
```

### Get Bottleneck Analysis

```http
GET /api/lead-time/bottlenecks
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "stage": "Production",
    "avg_days": 7.8,
    "max_days": 25,
    "orders_affected": 350,
    "pct_of_total": 35.0
  },
  {
    "stage": "Procurement",
    "avg_days": 5.2,
    "max_days": 18,
    "orders_affected": 280,
    "pct_of_total": 28.0
  }
]
```

---

## Sales Performance

### Get Sales Summary

```http
GET /api/sales-performance/summary
Authorization: Bearer <token>
```

**Query Parameters:**
- `period` (optional): "daily", "weekly", "monthly" (default: "monthly")
- `start_date` (optional): Period start date
- `end_date` (optional): Period end date

**Response:**
```json
{
  "total_sales": 15750000.50,
  "total_orders": 1250,
  "avg_order_value": 12600.00,
  "top_channel": "Direct Sales",
  "growth_vs_previous": 8.5
}
```

### Get Sales by Channel

```http
GET /api/sales-performance/by-channel
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "distribution_channel": "10",
    "channel_name": "Direct Sales",
    "sales_amount": 8500000.00,
    "order_count": 680,
    "customer_count": 75,
    "pct_of_total": 54.0
  },
  {
    "distribution_channel": "20",
    "channel_name": "Distributor",
    "sales_amount": 7250000.50,
    "order_count": 570,
    "customer_count": 70,
    "pct_of_total": 46.0
  }
]
```

### Get Sales by Customer

```http
GET /api/sales-performance/by-customer
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit` (optional): Top N customers (default: 20)
- `min_amount` (optional): Minimum sales amount

**Response:**
```json
[
  {
    "customer_name": "ABC Trading Co.",
    "sales_amount": 1250000.00,
    "order_count": 45,
    "avg_order_value": 27777.78,
    "first_order_date": "2023-01-15",
    "last_order_date": "2025-12-28"
  }
]
```

### Get Sales Trends

```http
GET /api/sales-performance/trends
Authorization: Bearer <token>
```

**Query Parameters:**
- `period` (required): "daily", "weekly", "monthly"
- `months` (optional): Number of months back (default: 12)

**Response:**
```json
[
  {
    "period": "2025-12",
    "sales_amount": 1450000.00,
    "order_count": 115,
    "avg_order_value": 12608.70
  },
  {
    "period": "2025-11",
    "sales_amount": 1380000.50,
    "order_count": 108,
    "avg_order_value": 12777.78
  }
]
```

---

## Production Yield

### Get Yield Summary

```http
GET /api/yield-dashboard/summary
Authorization: Bearer <token>
```

**Response:**
```json
{
  "avg_yield_pct": 92.5,
  "total_batches": 850,
  "low_yield_batches": 45,
  "p03_to_p02_yield": 94.2,
  "p02_to_p01_yield": 96.8,
  "total_waste_kg": 2500.0
}
```

### Get Batch Yield Details

```http
GET /api/yield-dashboard/batch-details
Authorization: Bearer <token>
```

**Query Parameters:**
- `batch_number` (optional): Specific batch
- `material_code` (optional): Filter by output material
- `min_yield` (optional): Minimum yield percentage
- `max_yield` (optional): Maximum yield percentage
- `start_date` (optional): Production start date
- `end_date` (optional): Production end date

**Response:**
```json
[
  {
    "batch_number": "25L2535110",
    "output_material": "P01-12345",
    "input_material": "P02-67890",
    "planned_qty": 1000.0,
    "actual_qty": 945.0,
    "yield_pct": 94.5,
    "waste_qty": 55.0,
    "production_date": "2025-12-15",
    "plant": "1000"
  }
]
```

### Get P02-P01 Yield Tracking

```http
GET /api/yield-dashboard/p02-p01-yield
Authorization: Bearer <token>
```

**Query Parameters:**
- `p02_batch` (optional): P02 batch number
- `p01_material` (optional): P01 material code

**Response:**
```json
[
  {
    "p02_batch": "25L2530110",
    "p02_material": "P02-67890",
    "p02_qty": 500.0,
    "p01_batches": ["25L2535110", "25L2535210"],
    "total_p01_qty": 475.0,
    "yield_pct": 95.0,
    "production_date": "2025-12-15"
  }
]
```

### Get Material Genealogy

Trace material flow from P03 → P02 → P01.

```http
GET /api/yield-dashboard/genealogy
Authorization: Bearer <token>
```

**Query Parameters:**
- `batch_number` (required): Starting batch number
- `direction` (optional): "forward" or "backward" (default: "forward")

**Response:**
```json
{
  "root_batch": "25L2520110",
  "root_material": "P03-11111",
  "genealogy_tree": [
    {
      "level": "P03",
      "batch": "25L2520110",
      "material": "P03-11111",
      "qty": 1000.0,
      "children": [
        {
          "level": "P02",
          "batch": "25L2530110",
          "material": "P02-67890",
          "qty": 950.0,
          "yield_from_parent": 95.0,
          "children": [
            {
              "level": "P01",
              "batch": "25L2535110",
              "material": "P01-12345",
              "qty": 920.0,
              "yield_from_parent": 96.8
            }
          ]
        }
      ]
    }
  ]
}
```

---

## MTO Orders

### Get MTO Order List

```http
GET /api/mto-orders/list
Authorization: Bearer <token>
```

**Query Parameters:**
- `status` (optional): Filter by status ("Open", "In Progress", "Completed")
- `customer` (optional): Filter by customer name
- `start_date` (optional): Order start date
- `end_date` (optional): Order end date

**Response:**
```json
[
  {
    "sales_order": "210045678",
    "customer_name": "ABC Trading",
    "material_code": "P01-12345",
    "order_qty": 500,
    "delivered_qty": 500,
    "order_date": "2025-12-01",
    "requested_delivery": "2025-12-15",
    "actual_delivery": "2025-12-14",
    "status": "Completed",
    "leadtime_days": 13,
    "on_time": true
  }
]
```

### Get MTO Order Details

```http
GET /api/mto-orders/{order_number}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "sales_order": "210045678",
  "customer_name": "ABC Trading",
  "material_code": "P01-12345",
  "material_description": "Premium Paint - White 5L",
  "order_qty": 500,
  "delivered_qty": 500,
  "unit": "PC",
  "order_date": "2025-12-01",
  "requested_delivery": "2025-12-15",
  "actual_delivery": "2025-12-14",
  "production_batches": ["25L2535110"],
  "status": "Completed",
  "timeline": {
    "order_placed": "2025-12-01",
    "procurement_start": "2025-12-02",
    "production_start": "2025-12-06",
    "production_end": "2025-12-12",
    "goods_issued": "2025-12-14"
  },
  "leadtime_breakdown": {
    "procurement_days": 4,
    "production_days": 6,
    "distribution_days": 2,
    "total_days": 13
  }
}
```

---

## AR Aging

### Get AR Aging Summary

```http
GET /api/ar-aging/summary
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_ar": 3200000.00,
  "current": 2100000.00,
  "days_1_30": 650000.00,
  "days_31_60": 280000.00,
  "days_61_90": 120000.00,
  "days_over_90": 50000.00,
  "overdue_total": 450000.00,
  "overdue_pct": 14.06
}
```

### Get AR Aging Details

```http
GET /api/ar-aging/details
Authorization: Bearer <token>
```

**Query Parameters:**
- `bucket` (optional): "current", "1-30", "31-60", "61-90", "90+"
- `customer` (optional): Filter by customer name
- `min_amount` (optional): Minimum AR amount

**Response:**
```json
[
  {
    "customer_name": "ABC Trading",
    "invoice_number": "INV-2025-001234",
    "invoice_date": "2025-11-15",
    "due_date": "2025-12-15",
    "amount": 125000.00,
    "outstanding": 125000.00,
    "days_outstanding": 45,
    "aging_bucket": "31-60",
    "status": "Overdue"
  }
]
```

### Get Customer AR Summary

```http
GET /api/ar-aging/by-customer
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "customer_name": "ABC Trading",
    "total_ar": 450000.00,
    "current": 250000.00,
    "overdue": 200000.00,
    "oldest_invoice_days": 65,
    "invoice_count": 8
  }
]
```

---

## Alert Monitoring

### Get Active Alerts

```http
GET /api/alerts/active
Authorization: Bearer <token>
```

**Query Parameters:**
- `severity` (optional): "critical", "warning", "info"
- `alert_type` (optional): "stuck_in_transit", "low_yield", "overdue_ar", "low_stock"

**Response:**
```json
[
  {
    "alert_id": "ALT-2025-001234",
    "alert_type": "stuck_in_transit",
    "severity": "critical",
    "title": "Batch 25L2535110 stuck in transit for 72 hours",
    "description": "Material P01-12345 has been in transit from Plant 1000 to FG01 for 72 hours (threshold: 48h)",
    "created_at": "2025-12-27T10:30:00Z",
    "related_entity": "25L2535110",
    "recommended_action": "Investigate material document 5000123456"
  },
  {
    "alert_id": "ALT-2025-001235",
    "alert_type": "low_yield",
    "severity": "warning",
    "title": "Batch 25L2530210 low yield: 78.5%",
    "description": "P02 to P01 conversion yield below threshold (85%)",
    "created_at": "2025-12-28T14:15:00Z",
    "related_entity": "25L2530210",
    "recommended_action": "Review production process and material quality"
  }
]
```

### Get Alert History

```http
GET /api/alerts/history
Authorization: Bearer <token>
```

**Query Parameters:**
- `start_date` (optional): Alert start date
- `end_date` (optional): Alert end date
- `status` (optional): "active", "resolved", "dismissed"
- `limit` (optional): Number of records (default: 100)

**Response:**
```json
[
  {
    "alert_id": "ALT-2025-001200",
    "alert_type": "overdue_ar",
    "severity": "warning",
    "title": "Customer ABC Trading has $200k overdue AR",
    "created_at": "2025-12-20T09:00:00Z",
    "resolved_at": "2025-12-22T16:30:00Z",
    "status": "resolved",
    "resolution_note": "Payment received"
  }
]
```

### Acknowledge Alert

```http
POST /api/alerts/{alert_id}/acknowledge
Authorization: Bearer <token>
Content-Type: application/json

{
  "note": "Investigating with production team"
}
```

**Response:**
```json
{
  "alert_id": "ALT-2025-001234",
  "status": "acknowledged",
  "acknowledged_by": "admin",
  "acknowledged_at": "2025-12-29T10:00:00Z"
}
```

---

## Health & Status

### API Health Check

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0",
  "timestamp": "2025-12-29T10:00:00Z"
}
```

### Database Status

```http
GET /api/health/db
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "connected",
  "tables": 45,
  "last_etl_run": "2025-12-29T06:00:00Z",
  "raw_records": 125000,
  "fact_records": 85000,
  "dimension_records": 2500
}
```

---

## Error Responses

All endpoints return standard error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid date format. Use YYYY-MM-DD"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error. Please contact support."
}
```

---

## Rate Limiting

- **Limit**: 1000 requests per hour per user
- **Headers**: 
  - `X-RateLimit-Limit`: Total requests allowed
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Timestamp when limit resets

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded. Try again in 3600 seconds."
}
```

---

## OpenAPI/Swagger Documentation

Interactive API documentation available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

---

## Code Examples

### Python

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"username": "admin", "password": "password"}
)
token = response.json()["access_token"]

# Get executive summary
headers = {"Authorization": f"Bearer {token}"}
summary = requests.get(
    "http://localhost:8000/api/executive/summary",
    headers=headers
).json()

print(f"Total Revenue: ${summary['total_revenue']:,.2f}")
```

### JavaScript/TypeScript

```typescript
// Login
const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'password' })
});
const { access_token } = await loginResponse.json();

// Get inventory
const inventoryResponse = await fetch('http://localhost:8000/api/inventory/current', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const inventory = await inventoryResponse.json();

console.log(`Inventory items: ${inventory.length}`);
```

### cURL

```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.access_token')

# Get sales performance
curl http://localhost:8000/api/sales-performance/summary \
  -H "Authorization: Bearer $TOKEN" \
  | jq .
```

---

## Pagination

Endpoints returning large datasets support pagination:

```http
GET /api/inventory/movements?page=2&page_size=50
```

**Parameters:**
- `page`: Page number (1-indexed, default: 1)
- `page_size`: Items per page (default: 100, max: 1000)

**Response includes pagination metadata:**
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "page_size": 50,
    "total_items": 5000,
    "total_pages": 100,
    "has_next": true,
    "has_previous": true
  }
}
```

---

## Filtering & Sorting

### Filtering

Most list endpoints support filtering via query parameters:

```http
GET /api/inventory/current?plant=1000&min_qty=100
```

### Sorting

```http
GET /api/sales-performance/by-customer?sort_by=sales_amount&sort_order=desc
```

**Parameters:**
- `sort_by`: Field name to sort by
- `sort_order`: "asc" or "desc" (default: "asc")

---

## Webhooks (Future Feature)

Webhook support for alert notifications is planned for v2.0.

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-30 | Initial API release |

---

## Support

For API support:
- Email: api-support@yourcompany.com
- Documentation: https://docs.dashboard.yourcompany.com
