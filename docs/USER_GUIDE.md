# User Guide

Welcome to the Alkana Dashboard! This guide will help you navigate and use the supply chain analytics platform effectively.

## Table of Contents
- [Getting Started](#getting-started)
- [Dashboard Overview](#dashboard-overview)
- [Executive Dashboard](#executive-dashboard)
- [Inventory Management](#inventory-management)
- [Lead Time Analytics](#lead-time-analytics)
- [Sales Performance](#sales-performance)
- [Production Yield](#production-yield)
- [MTO Orders](#mto-orders)
- [AR Aging](#ar-aging)
- [Alert Monitor](#alert-monitor)
- [Tips & Best Practices](#tips--best-practices)
- [FAQ](#faq)

---

## Getting Started

### Accessing the Dashboard

1. Open your web browser
2. Navigate to: `https://dashboard.yourcompany.com`
3. Login with your credentials

### First Login

**Default Credentials:**
- Username: Your company email
- Password: Provided by your administrator

**Change Password:**
1. Click your username in top-right corner
2. Select "Profile"
3. Click "Change Password"
4. Enter current and new password
5. Click "Update"

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│  [Logo]  Alkana Dashboard          [User] [Logout]     │
├──────┬──────────────────────────────────────────────────┤
│      │                                                  │
│ Nav  │                                                  │
│ Menu │           Main Content Area                      │
│      │           (Dashboard Modules)                    │
│      │                                                  │
└──────┴──────────────────────────────────────────────────┘
```

**Navigation Menu (Left Sidebar):**
- Executive Dashboard
- Inventory
- Lead Time
- Sales Performance
- Production Yield
- MTO Orders
- AR Aging
- Alerts

---

## Dashboard Overview

### Understanding Data Freshness

**Data Update Schedule:**
- Raw data loaded: Daily at 6:00 AM
- Dashboards refresh: Every 5 minutes (automatic)
- Manual refresh: Click 🔄 icon in top-right

**Last Updated Timestamp:**
Look for "Data as of: 2025-12-29 06:00" at top of each dashboard.

### Filtering Data

Most dashboards support filtering:

1. **Date Range Filter:**
   - Click calendar icon
   - Select "Last 7 Days", "Last Month", "Custom Range"
   - Custom: Pick start and end dates

2. **Material Filter:**
   - Type material code or description
   - Auto-complete suggests matches

3. **Customer Filter:**
   - Select from dropdown
   - Or type customer name

4. **Clear Filters:**
   - Click "Clear All" button
   - Or refresh page

### Exporting Data

**Export to Excel:**
1. Click "Export" button (📊 icon)
2. Choose "Export to Excel"
3. File downloads automatically

**Export to PDF:**
1. Click "Export" button
2. Choose "Export to PDF"
3. Includes current filters and date

**Print Dashboard:**
1. Click "Print" button (🖨️ icon)
2. Use browser print dialog

---

## Executive Dashboard

### Overview

High-level KPIs for quick business insights.

### Key Metrics

**Revenue Section:**
- **Total Revenue:** Sum of all sales this period
- **Revenue Growth %:** Comparison to previous period
  - 🟢 Green: Positive growth
  - 🔴 Red: Negative growth

**Customer Section:**
- **Total Customers:** All customers with orders
- **Active Customers:** Customers with orders this period

**Production Section:**
- **Total Orders:** Production orders created
- **Completed Orders:** Orders with status "Completed"
- **Completion Rate:** % of orders finished on time

**Inventory Section:**
- **Total Inventory Value:** Current stock value
- **Inventory Items:** Number of SKUs in stock

**AR Section:**
- **Total AR:** Accounts receivable balance
- **Overdue AR:** Amount past due date
- **Overdue %:** Percentage of AR that's overdue

### Charts

**1. Revenue Trends**
- Line chart showing monthly revenue
- Hover over points to see exact values
- Click legend to show/hide lines

**2. Top 10 Customers**
- Bar chart of highest revenue customers
- Click bar to drill down into customer details

**3. Top 10 Products**
- Shows best-selling materials
- Sorted by revenue

**4. Division Performance**
- Pie chart of revenue by division
- Hover to see percentage breakdown

### Using Executive Dashboard

**Scenario: Check monthly performance**

1. Navigate to Executive Dashboard (default landing page)
2. Set date filter to "This Month"
3. Review KPI cards at top
4. Scroll down to see trends and top performers
5. Click "Export" to save monthly report

**Interpreting Results:**
- ✓ **Good:** Revenue growth >5%, Completion rate >90%, Overdue AR <10%
- ⚠ **Watch:** Revenue flat, Completion rate 80-90%, Overdue AR 10-20%
- ⚡ **Action Needed:** Revenue declining, Completion rate <80%, Overdue AR >20%

---

## Inventory Management

### Overview

Real-time stock levels, movements, and inventory alerts.

### Current Inventory Tab

**Columns:**
- **Material Code:** SKU identifier (e.g., P01-12345)
- **Description:** Product name
- **Plant:** Manufacturing location
- **Storage Location:** Warehouse/SLOC code
- **Quantity:** Current stock level
- **Unit:** Unit of measure (PC, KG, L)
- **Value:** Inventory value in local currency
- **Last Movement:** Date of last stock change

**Sorting:**
- Click column header to sort
- Click again to reverse order

**Searching:**
- Use search box: "Search by material or description"
- Filters table in real-time

**Filters:**
- **Plant:** Select specific plant (e.g., "1000")
- **Storage Location:** Filter by warehouse
- **Min Quantity:** Show only items with qty > threshold

### Inventory Movements Tab

**View stock changes over time:**

**Movement Types:**
- **101:** Goods Receipt (incoming)
- **261:** Goods Issue to Production (consumption)
- **601:** Goods Issue to Customer (sales)
- **122:** Return Delivery (return to vendor)
- **More types:** Hover over code to see description

**Understanding Movements:**
- **Positive Quantity:** Stock increase (received)
- **Negative Quantity:** Stock decrease (issued)
- **Reference Document:** Linked SO/PO number

**Common Use Cases:**

**1. Track material usage:**
   - Filter by Material Code
   - Set date range to "Last 30 Days"
   - Look at MVT 261 (production consumption)

**2. Find customer shipments:**
   - Filter by MVT 601
   - Search by customer name in reference

**3. Investigate stock discrepancy:**
   - Filter by Material and Storage Location
   - Review all movements for period
   - Sum quantities to verify net change

### Slow-Moving Items Tab

**Identifies stagnant inventory:**

- **Days No Movement:** Days since last stock change
- **Default Threshold:** 90 days
- **Adjust Threshold:** Use slider (30-180 days)

**Action Items:**
- Items >90 days: Consider discounting or promotion
- Items >180 days: Obsolescence risk

---

## Lead Time Analytics

### Overview

Analyze order fulfillment speed and identify bottlenecks.

### Lead Time Summary

**Key Metrics:**
- **Avg Total Lead Time:** Order to delivery duration
- **Avg Procurement Days:** Supplier to receipt
- **Avg Production Days:** Raw material to finished goods
- **Avg Distribution Days:** Warehouse to customer

**Benchmark Targets:**
- Total Lead Time: <15 days
- Procurement: <5 days
- Production: <8 days
- Distribution: <3 days

### Lead Time Details

**Table Columns:**
- **Sales Order:** Customer order number
- **Material:** Product ordered
- **Customer:** Buyer name
- **Order Date → Delivery Date:** Timeline
- **Total Days:** End-to-end duration
- **Stage Breakdown:** Days per phase
- **Order Type:** MTO (Make-to-Order) or MTS (Make-to-Stock)
- **Bottleneck:** Stage with longest delay

**Color Coding:**
- 🟢 **Green:** On-time or early
- 🟡 **Yellow:** Slight delay (<20% over target)
- 🔴 **Red:** Significant delay (>20% over target)

### Bottleneck Analysis

**Chart shows:**
- Which stage causes most delays
- Average days per stage
- % of orders affected

**How to Use:**
1. Identify highest bar (biggest bottleneck)
2. Click bar to see affected orders
3. Investigate root causes:
   - **Procurement:** Supplier issues, long lead items
   - **Production:** Capacity constraints, material shortages
   - **Distribution:** Logistics delays, customer scheduling

### MTO vs MTS Comparison

**Understanding Order Types:**

**MTO (Make-to-Order):**
- Production starts after customer order
- Typically longer lead time
- Customized products

**MTS (Make-to-Stock):**
- Production based on forecast
- Shorter lead time (from stock)
- Standard products

**Chart shows:**
- Lead time distribution for each type
- Target vs actual performance

---

## Sales Performance

### Overview

Revenue analysis by channel, customer, and product.

### Sales Summary

**KPIs:**
- **Total Sales:** Revenue for period
- **Total Orders:** Number of sales orders
- **Avg Order Value:** Revenue per order
- **Top Channel:** Highest revenue distribution channel
- **Growth vs Previous:** Period-over-period change

### Sales by Channel

**Distribution Channels:**
- **10:** Direct Sales (B2B customers)
- **20:** Distributor (wholesale partners)
- **30:** Retail (direct to consumer)
- **40:** E-commerce (online orders)

**Metrics per Channel:**
- Sales Amount
- Order Count
- Customer Count
- % of Total Revenue

**Pie Chart:**
- Shows revenue split by channel
- Hover for percentage and amount

**Use Case - Channel Performance:**
1. Compare channel revenue YoY
2. Identify growing/declining channels
3. Allocate sales resources accordingly

### Sales by Customer

**Top Customers Table:**
- Ranked by revenue (highest first)
- Shows order count and avg order value
- Click customer name to see order history

**Customer Segmentation:**
- **Top 10:** VIP customers (often 80% of revenue)
- **Active:** Ordered in last 90 days
- **At Risk:** No orders in 90+ days

**Actions:**
- Monitor top customers closely
- Develop retention strategies for VIPs
- Re-engage at-risk customers

### Sales Trends

**Line Chart:**
- X-axis: Time period (daily/weekly/monthly)
- Y-axis: Sales amount
- Multiple lines: Compare different periods

**How to Use:**
1. Set period: "Monthly" for high-level trends
2. Look for patterns:
   - Seasonal peaks (e.g., Q4 holidays)
   - Growth trends (upward slope)
   - Anomalies (sudden spikes/drops)
3. Correlate with business events (promotions, etc.)

---

## Production Yield

### Overview

Track production efficiency and material consumption.

### Understanding Yield

**Yield Formula:**
```
Yield % = (Actual Output / Planned Output) × 100
```

**Good Yield:** >90%
**Acceptable:** 85-90%
**Poor:** <85% (triggers alert)

### Production Hierarchy

**3-Stage Process:**
```
P03 (Raw Material)
  ↓ Production
P02 (Semi-Finished)
  ↓ Production
P01 (Finished Goods)
```

**Example:**
- P03: Base paint (1000 KG)
- → Produces P02: Tinted paint (950 KG) → **95% yield**
- → Produces P01: Packaged 5L cans (920 KG) → **96.8% yield**
- **Overall yield:** 92% (P03 to P01)

### Yield Summary

**Dashboard Metrics:**
- **Avg Yield %:** Across all batches
- **Total Batches:** Production runs
- **Low Yield Batches:** Below threshold (85%)
- **P03→P02 Yield:** First stage efficiency
- **P02→P01 Yield:** Second stage efficiency
- **Total Waste:** Material lost in production

### Batch Yield Details

**Table Columns:**
- **Batch Number:** Unique production identifier (e.g., 25L2535110)
- **Output Material:** What was produced
- **Input Material:** What was consumed
- **Planned Qty:** Target output
- **Actual Qty:** Real output
- **Yield %:** Efficiency
- **Waste Qty:** Material loss
- **Production Date:** When batch ran

**Finding Issues:**
1. Sort by "Yield %" (lowest first)
2. Identify batches <85%
3. Look for patterns:
   - Same material consistently low? → Quality issue
   - Same plant/line low? → Equipment issue
   - Recent trend down? → Process change needed

### Material Genealogy

**Trace Material Flow:**

1. Enter batch number (e.g., "25L2535110")
2. Select direction:
   - **Forward:** What this batch produced
   - **Backward:** What inputs created this batch
3. View genealogy tree

**Tree Diagram:**
```
P03-11111 (Batch: 25L2520110) - 1000 KG
  │
  ├─ P02-67890 (Batch: 25L2530110) - 950 KG [95% yield]
  │   │
  │   ├─ P01-12345 (Batch: 25L2535110) - 460 KG [96.8% yield]
  │   └─ P01-12345 (Batch: 25L2535210) - 460 KG [96.8% yield]
```

**Use Case - Root Cause Analysis:**
- Low yield in P01 batch
- Trace backward to P02
- Check if P02 yield was also low
- → Indicates issue started at P02 stage

---

## MTO Orders

### Overview

Track Make-to-Order fulfillment and on-time delivery.

### MTO vs MTS

**MTO (Make-to-Order):**
- Customer places order first
- Production scheduled after order
- Custom specifications
- Longer lead time

**MTS (Make-to-Stock):**
- Production based on forecast
- Fulfill from inventory
- Standard products
- Shorter lead time

### MTO Order List

**Table Columns:**
- **Sales Order:** Customer order number
- **Customer:** Buyer name
- **Material:** Product ordered
- **Order Qty:** Requested amount
- **Delivered Qty:** Fulfilled amount
- **Order Date:** When order placed
- **Requested Delivery:** Customer due date
- **Actual Delivery:** When shipped
- **Status:** Open / In Progress / Completed
- **Lead Time Days:** Order to delivery duration
- **On Time:** ✓ or ✗

**Status Indicators:**
- 🟢 **Completed:** Fully delivered on time
- 🟡 **In Progress:** Production ongoing
- 🔴 **Late:** Missed delivery date
- ⚪ **Open:** Not yet started

### Filtering MTO Orders

**Common Filters:**

1. **Show only late orders:**
   - Status: "Completed"
   - On Time: "No"

2. **Active MTO orders:**
   - Status: "In Progress" or "Open"
   - Sort by "Requested Delivery" (earliest first)

3. **Customer-specific:**
   - Customer: Select from dropdown
   - Shows all orders for that customer

### Order Details

Click on order number to see:

**Order Summary:**
- Full order information
- Customer contact details
- Material specifications

**Production Timeline:**
```
Dec 1: Order Placed
Dec 2: Procurement Started
Dec 6: Production Started
Dec 12: Production Completed
Dec 14: Goods Issued to Customer
```

**Lead Time Breakdown:**
- Procurement: 4 days
- Production: 6 days
- Distribution: 2 days
- **Total: 13 days** (target: 15 days) ✓

**Linked Production Batches:**
- Shows which batch(es) fulfilled this order
- Click batch to see yield details

### On-Time Delivery Metrics

**OTIF (On-Time In-Full):**
- Dashboard shows % of orders delivered on-time
- Target: >95%

**Performance Indicators:**
- 🎯 **Excellent:** >95% on-time
- ✓ **Good:** 90-95% on-time
- ⚠ **Needs Improvement:** 80-90%
- ⚡ **Critical:** <80%

---

## AR Aging

### Overview

Accounts Receivable analysis to manage cash flow and collections.

### Understanding AR Aging

**Aging Buckets:**
- **Current:** Not yet due (0 days)
- **1-30 Days:** Slightly overdue
- **31-60 Days:** Moderately overdue
- **61-90 Days:** Significantly overdue
- **90+ Days:** Critically overdue

### AR Summary

**Key Metrics:**
- **Total AR:** All outstanding receivables
- **Current:** Amount not yet due
- **Overdue Total:** Past due date
- **Overdue %:** Percentage of AR overdue

**Target:** Keep overdue <10%

### AR Aging Chart

**Waterfall/Bar Chart:**
- Each bar represents aging bucket
- Width = amount
- Color coding:
  - 🟢 Green: Current
  - 🟡 Yellow: 1-30 days
  - 🟠 Orange: 31-60 days
  - 🔴 Red: 61+ days

### AR Aging Details

**Table View:**
- **Customer:** Name of debtor
- **Invoice Number:** Invoice reference
- **Invoice Date:** When billed
- **Due Date:** Payment deadline
- **Amount:** Original invoice value
- **Outstanding:** Remaining balance
- **Days Outstanding:** Days past invoice date
- **Aging Bucket:** Which category
- **Status:** Current / Overdue

**Sorting for Collections:**
1. Sort by "Days Outstanding" (highest first)
2. Focus on 90+ days first (highest risk)
3. Contact customers with largest overdue amounts

### Customer AR Summary

**By-Customer View:**
- Total AR per customer
- Current vs overdue split
- Oldest invoice days
- Invoice count

**Identifying Problem Customers:**
- High overdue percentage (>30%)
- Oldest invoice >90 days
- Multiple overdue invoices

**Actions:**
1. **60 days overdue:** Send reminder email
2. **90 days overdue:** Phone call + payment plan
3. **120+ days overdue:** Escalate to management/legal

### Exporting for Collections

1. Click "Export" button
2. Select "Export AR Aging"
3. Excel file includes:
   - Aging buckets
   - Customer contact info
   - Invoice details
4. Use for collection calls and tracking

---

## Alert Monitor

### Overview

Proactive notifications for critical issues requiring attention.

### Alert Types

**1. Stuck in Transit**
- **What:** Material in transit >48 hours
- **Why it matters:** Inventory not available for use
- **Action:** Investigate material document, contact logistics

**2. Low Yield**
- **What:** Production yield <85%
- **Why it matters:** Waste, cost overruns
- **Action:** Review production process, check material quality

**3. Overdue AR**
- **What:** Customer invoice >90 days overdue
- **Why it matters:** Cash flow risk, bad debt risk
- **Action:** Contact customer, escalate collections

**4. Low Stock**
- **What:** Inventory below reorder point
- **Why it matters:** Stockout risk, production delay
- **Action:** Place purchase order, expedite delivery

### Alert Severity

**Critical (🔴):**
- Immediate action required
- Business impact: High
- Examples: Stuck >72 hours, Overdue >120 days

**Warning (🟡):**
- Action needed soon
- Business impact: Medium
- Examples: Low yield, 60-90 days overdue

**Info (🔵):**
- FYI / monitoring
- Business impact: Low
- Examples: Approaching threshold

### Alert List

**Table Columns:**
- **Alert ID:** Unique identifier
- **Type:** Category (see above)
- **Severity:** Critical / Warning / Info
- **Title:** Brief description
- **Created:** When alert triggered
- **Related Entity:** Batch, customer, material, etc.
- **Recommended Action:** What to do
- **Status:** Active / Acknowledged / Resolved

### Managing Alerts

**Acknowledge Alert:**
1. Click on alert row
2. Click "Acknowledge" button
3. Add note (e.g., "Investigating with production team")
4. Click "Save"

**Resolve Alert:**
1. Take corrective action
2. Click "Resolve" button
3. Add resolution note (e.g., "Payment received")
4. Alert moves to history

**Filter Alerts:**
- **Active Only:** Default view
- **By Severity:** Show only Critical
- **By Type:** Filter to specific alert type
- **Date Range:** Historical alerts

### Alert Notifications

**Email Alerts (if configured):**
- Critical alerts sent immediately
- Warning alerts in daily digest
- Configure in Profile → Notification Settings

**Dashboard Badge:**
- Red dot on Alert icon shows unread count
- Number indicates active alerts

---

## Tips & Best Practices

### Daily Routine

**Morning Check (5 minutes):**
1. Login to dashboard
2. Check **Alert Monitor** for critical issues
3. Review **Executive Dashboard** KPIs
4. Check **MTO Orders** for deliveries today

### Weekly Review (30 minutes)

**Monday:**
1. **Sales Performance:** Review last week's revenue
2. **Lead Time:** Check bottlenecks
3. **AR Aging:** Review new overdue accounts

**Friday:**
1. **Production Yield:** Review week's batches
2. **Inventory:** Check slow-moving items
3. **Executive Dashboard:** Export weekly report

### Monthly Analysis (1-2 hours)

**Month End:**
1. Export all dashboards to PDF
2. Compare to previous month:
   - Revenue trends
   - Yield performance
   - AR aging changes
3. Prepare management report
4. Set goals for next month

### Best Practices

**✓ Do:**
- Refresh data before important meetings
- Export reports for record-keeping
- Acknowledge alerts promptly
- Use filters to focus on relevant data
- Check "Last Updated" timestamp

**✗ Don't:**
- Rely on cached/old data
- Ignore critical alerts
- Make decisions without drilling down
- Share login credentials
- Export sensitive data to unsecured locations

### Keyboard Shortcuts

- **Ctrl+R** (Cmd+R): Refresh dashboard
- **Ctrl+F** (Cmd+F): Search in table
- **Ctrl+P** (Cmd+P): Print current view
- **Esc:** Close modal/dialog

---

## FAQ

### General

**Q: How often is data updated?**
A: Raw data loads daily at 6 AM. Dashboards auto-refresh every 5 minutes.

**Q: Can I schedule automatic reports?**
A: Not yet. This feature is planned for v2.0. Currently, export manually.

**Q: What browsers are supported?**
A: Chrome, Firefox, Edge, Safari (latest 2 versions).

**Q: Can I access on mobile?**
A: Dashboard is responsive but optimized for desktop. Mobile app coming in Phase 3.

### Data Questions

**Q: Why don't my numbers match SAP exactly?**
A: Dashboard uses netting algorithm to account for reversals and cancellations. SAP shows gross movements.

**Q: What's the difference between P01, P02, P03?**
- **P03:** Raw materials (inputs)
- **P02:** Semi-finished goods (intermediate)
- **P01:** Finished goods (final products for sale)

**Q: What does "stuck in transit" mean?**
A: Material has a goods issue (MVT 261) but no corresponding receipt (MVT 101) at destination within 48 hours.

**Q: Why is yield percentage sometimes >100%?**
A: Possible reasons: Measurement error, additional materials added, or data entry issue. Investigate batch.

### Technical Issues

**Q: Dashboard won't load / shows blank screen**
A: 
1. Hard refresh (Ctrl+Shift+R)
2. Clear browser cache
3. Try different browser
4. Contact IT support

**Q: "No data" message appears**
A: Check date filters. Ensure date range includes data. If persists, contact support.

**Q: Login fails with "Invalid credentials"**
A: 
1. Verify username (case-sensitive)
2. Check Caps Lock is off
3. Use "Forgot Password" link
4. Contact admin to reset

**Q: Export doesn't work**
A: Check pop-up blocker settings. Allow pop-ups for dashboard site.

### Access & Permissions

**Q: I can't see certain dashboards**
A: Access is role-based. Contact your manager or IT to request access.

**Q: Can I share my login?**
A: No. Each user should have their own account for audit purposes.

**Q: How do I request a new account?**
A: Email: support@yourcompany.com with name, department, and required access level.

---

## Glossary of Terms

See [GLOSSARY.md](./GLOSSARY.md) for complete business terminology reference.

**Quick Reference:**
- **AR:** Accounts Receivable
- **SLOC:** Storage Location
- **MVT:** Movement Type
- **MTO:** Make-to-Order
- **MTS:** Make-to-Stock
- **OTIF:** On-Time In-Full
- **KPI:** Key Performance Indicator
- **YoY:** Year-over-Year
- **EOQ:** Economic Order Quantity

---

## Getting Help

**In-App Help:**
- Click "?" icon next to any metric
- Hover over chart elements for tooltips

**Documentation:**
- [README.md](../README.md) - Quick start
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues

**Support Contacts:**
- **General Help:** support@yourcompany.com
- **Data Issues:** data-team@yourcompany.com
- **Technical Problems:** it-support@yourcompany.com
- **Feature Requests:** product@yourcompany.com

**Response Times:**
- Critical (system down): <1 hour
- High (major issue): <4 hours
- Normal (questions): <1 business day

---

## Training Resources

**Video Tutorials:** (Coming soon)
- Dashboard Overview (5 min)
- Inventory Deep Dive (15 min)
- Lead Time Analysis (10 min)
- Alert Management (8 min)

**Live Training:**
Contact training@yourcompany.com to schedule group session.

---

**Document Version:** 1.0
**Last Updated:** December 30, 2025
**Feedback:** Send suggestions to product@yourcompany.com
