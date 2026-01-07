# Glossary

Business and technical terminology used in the Alkana Dashboard.

## Business Terms

### Accounts Receivable (AR)
Money owed to the company by customers for goods or services delivered but not yet paid for.

### Aging Bucket
Time period categories for AR aging analysis:
- **Current**: Not yet due (0 days overdue)
- **1-30 Days**: Slightly overdue
- **31-60 Days**: Moderately overdue
- **61-90 Days**: Significantly overdue
- **90+ Days**: Critically overdue, high risk of bad debt

### Batch Number
Unique identifier for a production lot. Format: `25L2535110`
- `25` = Year (2025)
- `L` = Plant identifier
- `2535110` = Sequential number

### Distribution Channel
Sales channel through which products are sold:
- **10**: Direct Sales (B2B)
- **20**: Distributor (Wholesale)
- **30**: Retail (Direct to consumer)
- **40**: E-commerce

### FERT (Finished Goods)
Final products ready for sale. In material hierarchy: **P01** level.

### HALB (Semi-Finished Goods)
Intermediate products requiring further processing. In material hierarchy: **P02** level.

### Lead Time
Total time from order placement to delivery, broken down into:
- **Procurement Time**: Supplier → Receipt
- **Production Time**: Raw materials → Finished goods
- **Distribution Time**: Warehouse → Customer

### Material Document
Record of a material movement (receipt, issue, transfer). Uniquely identified by document number (e.g., `5000123456`).

### MTO (Make-to-Order)
Production strategy where manufacturing starts only after customer order is received. Characteristics:
- Longer lead time
- Custom specifications
- Lower inventory risk

### MTS (Make-to-Stock)
Production strategy based on demand forecast. Characteristics:
- Shorter lead time
- Standard products
- Higher inventory risk

### MVT (Movement Type)
SAP transaction code indicating type of material movement:
- **101**: Goods Receipt from Purchase Order
- **102**: Reversal of Goods Receipt
- **122**: Return to Vendor
- **261**: Goods Issue for Production Order
- **262**: Reversal of Goods Issue
- **311**: Transfer Posting (between storage locations)
- **561**: Initial Entry of Stock Balance
- **601**: Goods Issue to Customer (Sales)

**MVT Reversal Pairs:**
- 101 ↔ 102
- 261 ↔ 262
- 601 ↔ 602

### OTIF (On-Time In-Full)
Key performance metric measuring percentage of orders delivered:
- **On-Time**: By or before requested delivery date
- **In-Full**: Complete quantity ordered

Target: >95%

### Plant
Manufacturing or distribution facility. Common code: **1000**

### P01, P02, P03 (Material Hierarchy)
Three-level production hierarchy:
- **P03**: Raw materials (ROH) - inputs to production
- **P02**: Semi-finished goods (HALB) - intermediate products
- **P01**: Finished goods (FERT) - final sellable products

**Material Flow:**
```
P03 (Raw Material)
  ↓ Production
P02 (Semi-Finished)
  ↓ Production
P01 (Finished Goods)
  ↓ Sales
Customer
```

### ROH (Raw Materials)
Basic inputs to production process. In material hierarchy: **P03** level.

### Sales Order
Customer order for products. Format: `210045678`

### SLOC (Storage Location)
Warehouse or storage area within a plant. Examples:
- **FG01**: Finished Goods Warehouse 1
- **RM01**: Raw Materials Warehouse
- **WIP**: Work-in-Progress

### Stuck in Transit
Alert condition when material has:
- Goods issue movement (MVT 261) but
- No corresponding receipt (MVT 101) at destination
- For more than threshold (default: 48 hours)

Indicates logistics delay or lost material.

### System Status
Production order status:
- **REL**: Released (approved for production)
- **CNF**: Confirmed (production reported)
- **TECO**: Technically Complete
- **DLV**: Delivered
- **CLSD**: Closed

### UOM (Unit of Measure)
Measurement unit for materials:
- **PC**: Pieces (individual units)
- **KG**: Kilograms
- **L**: Liters
- **EA**: Each
- **M**: Meters

**UOM Conversion Example:**
- Material P01-12345
- Base UOM: KG (1 can = 5 KG)
- Sales UOM: PC (sold by piece)
- Conversion Factor: 5 (1 PC = 5 KG)

### Yield
Production efficiency metric:
```
Yield % = (Actual Output / Planned Output) × 100
```

**Targets:**
- **Excellent**: ≥95%
- **Good**: 85-94%
- **Acceptable**: 75-84%
- **Poor**: <75% (triggers alert)

---

## Technical Terms

### API (Application Programming Interface)
RESTful web service allowing frontend to communicate with backend. Base URL: `/api`

### Dimensional Model
Data warehouse schema pattern with:
- **Fact Tables**: Transactional data (measurements)
- **Dimension Tables**: Reference/context data (who, what, where, when)

### ETL (Extract, Transform, Load)
Data pipeline process:
1. **Extract**: Read from Excel files
2. **Transform**: Clean, validate, calculate
3. **Load**: Insert into database

### FastAPI
Python web framework used for backend API. Features:
- Automatic OpenAPI/Swagger docs
- Type validation with Pydantic
- High performance (async support)

### JWT (JSON Web Token)
Authentication mechanism. Token format:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Includes user info and expiration. Default expiry: 24 hours.

### Materialized View
Pre-computed database view stored as table for performance:
- Faster query performance
- Requires periodic refresh
- Examples: `view_sales_performance`, `view_inventory_summary`

### Netting
Algorithm to calculate net inventory by accounting for:
- Receipts (+)
- Issues (-)
- Reversals (cancel original transaction)

**Example:**
```
MVT 101: +100 (receipt)
MVT 261: -50  (issue)
MVT 102: -100 (reversal of receipt)
MVT 101: +150 (new receipt)
Net: 100 (150 - 50)
```

### ORM (Object-Relational Mapping)
SQLAlchemy - maps Python classes to database tables. Benefits:
- Type safety
- Database independence
- Easier maintenance

### PostgreSQL
Relational database management system. Version: 15+

### React
JavaScript library for building user interfaces. Features:
- Component-based architecture
- Virtual DOM for performance
- Hooks for state management

### REST (Representational State Transfer)
API architectural style using HTTP methods:
- **GET**: Retrieve data
- **POST**: Create data
- **PUT**: Update data
- **DELETE**: Remove data

### SQLAlchemy
Python SQL toolkit and ORM. Used for database interactions.

### TanStack Query (React Query)
Data fetching and caching library for React. Features:
- Automatic re-fetching
- Cache management
- Loading/error states

### TypeScript
Typed superset of JavaScript. Benefits:
- Type safety
- Better IDE support
- Fewer runtime errors

---

## SAP-Specific Terms

### COOISPI
SAP table for production order details. Contains:
- Order numbers
- Planned vs actual quantities
- Start/finish dates
- System status

### MB51
SAP transaction code and table for material documents. Contains all inventory movements.

### ZRFI005
Custom SAP report for AR aging data.

### ZRMM024
Custom SAP report for material master data.

### ZRSD002
Custom SAP report for sales order data.

### ZRSD004
Custom SAP report for customer master data.

### ZRSD006
Custom SAP report for billing document data.

---

## Dashboard-Specific Terms

### Alert Monitor
Dashboard module showing system-generated alerts:
- Stuck in transit
- Low yield
- Overdue AR
- Low stock

### Executive Dashboard
High-level KPI summary for management. Shows:
- Revenue trends
- Customer metrics
- Production performance
- Inventory value
- AR aging

### Genealogy Tree
Visual representation of material flow through production levels:
```
P03 Batch → P02 Batch → P01 Batch
```

Allows tracing materials forward (what was produced) or backward (what inputs were used).

### KPI (Key Performance Indicator)
Measurable metric for business performance. Examples:
- Total Revenue
- Inventory Turnover
- On-Time Delivery %
- Average Yield %

---

## Metrics & Formulas

### Completion Rate
```
Completion Rate = (Completed Orders / Total Orders) × 100
```

### Gross Margin
```
Gross Margin = Revenue - Cost of Goods Sold
```

### Inventory Turnover
```
Inventory Turnover = Cost of Goods Sold / Average Inventory Value
```

### Lead Time
```
Total Lead Time = Procurement Days + Production Days + Distribution Days
```

### Overdue AR Percentage
```
Overdue % = (Overdue AR / Total AR) × 100
```

### Revenue Growth
```
Growth % = ((Current Period - Previous Period) / Previous Period) × 100
```

### Yield Percentage
```
Yield % = (Actual Output Qty / Planned Output Qty) × 100
```

---

## Abbreviations

| Abbreviation | Full Term |
|--------------|-----------|
| AR | Accounts Receivable |
| API | Application Programming Interface |
| B2B | Business-to-Business |
| B2C | Business-to-Consumer |
| COGS | Cost of Goods Sold |
| CRUD | Create, Read, Update, Delete |
| ERP | Enterprise Resource Planning |
| ETL | Extract, Transform, Load |
| FERT | Fertigerzeugnisse (German: Finished Product) |
| FG | Finished Goods |
| FK | Foreign Key |
| HALB | Halbfabrikat (German: Semi-Finished) |
| JWT | JSON Web Token |
| KPI | Key Performance Indicator |
| MTO | Make-to-Order |
| MTS | Make-to-Stock |
| MVT | Movement Type |
| ORM | Object-Relational Mapping |
| OTIF | On-Time In-Full |
| PK | Primary Key |
| REST | Representational State Transfer |
| RM | Raw Materials |
| ROH | Rohstoff (German: Raw Material) |
| SAP | Systems, Applications & Products |
| SLOC | Storage Location |
| SO | Sales Order |
| SQL | Structured Query Language |
| UOM | Unit of Measure |
| WIP | Work-in-Progress |
| YoY | Year-over-Year |

---

## Common Questions

**Q: What's the difference between P01, P02, and P03?**
A: Production hierarchy levels - P03 (raw materials) → P02 (semi-finished) → P01 (finished goods).

**Q: Why are some inventory quantities negative?**
A: Goods issues (MVT 261, 601) are recorded as negative quantities. Net inventory is calculated by summing all movements.

**Q: What does "stuck in transit" mean?**
A: Material was issued (MVT 261) but not received at destination (MVT 101) within 48 hours.

**Q: How is yield calculated?**
A: (Actual Output / Planned Output) × 100. Example: Planned 1000 KG, produced 950 KG = 95% yield.

**Q: What's the difference between MTO and MTS?**
A: MTO = produce after customer order (custom). MTS = produce based on forecast (stock).

**Q: What is a reversal transaction?**
A: Cancellation of a previous movement. MVT 102 reverses MVT 101, MVT 262 reverses MVT 261.

**Q: How often is data updated?**
A: Raw data loaded daily at 6:00 AM. Dashboards auto-refresh every 5 minutes.

**Q: What does TECO status mean?**
A: Technically Complete - production order is finished.

---

## Related Documentation

- [USER_GUIDE.md](./USER_GUIDE.md) - How to use dashboards
- [API_REFERENCE.md](./API_REFERENCE.md) - Technical API documentation
- [DATABASE.md](./DATABASE.md) - Database schema details

---

**Last Updated:** December 30, 2025
**Feedback:** Email product@yourcompany.com with suggested additions
