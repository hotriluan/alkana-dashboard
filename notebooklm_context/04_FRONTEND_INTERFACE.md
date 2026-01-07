# 04. Frontend Interface

## Overview
The frontend is a **React 18** Single Page Application (SPA) built with **TypeScript** and **Vite**. It features a modern, responsive design using **Tailwind CSS v4** and **Lucide React** icons.

## 1. Executive Dashboard (`/dashboard`)
The landing page for leadership.
*   **KPI Cards:** Sticky header showing Real-time Revenue, Total Customers, Completion Rate, and Active Alerts.
*   **Revenue by Division:** Bar chart breaking down sales by business unit (Indo, Paint, Wood, etc.).
*   **Top 10 Customers:** Horizontal bar chart of top contributors.
*   **Order Status Distribution:** Pie chart of Completed vs WIP vs Cancelled orders.

## 2. Sales Performance (`/sales`)
Deep dive into sales metrics.
*   **Filters:** Date Range Picker (Default: Last 30 Days), Salesman, Customer Group.
*   **Performance Grid:** Sortable detailed table of every Sales Order with calculated margins.
*   **Seasonal Trends:** Heatmap of sales-by-day to identify peak buying times.

## 3. Production Yield (`/yield`)
Manufacturing efficiency tracking.
*   **Factory Yield Rate:** Daily trend line of P01 yield vs Target (98%).
*   **Loss Analysis:** Pareto chart of top reasons for yield loss (e.g., "Milling Loss", "Transfer Loss").
*   **Batch Traceability:** Drill-down view to see the full P01->P02->P03 genealogy tree for any selected batch.

## 4. Accounts Receivable (`/ar-aging`)
Financial health monitoring.
*   **Aging Buckets:** Visual distribution of debt (1-30 days, 31-60 days, >90 days).
*   **Risk Map:** Scatter plot of Customer Revenue vs Overdue Amount. High-risk customers appear in the top-right quadrant.

## 5. Inventory & Supply Chain (`/inventory`)
*   **Stock Levels:** Real-time stock at Factory (1201) vs DC (1401).
*   **Stock Rotation:** FAST/SLOW mover analysis based on movement frequency.
*   **Transit Monitor:** List of all shipments currently "in-flight" between plants.

## Key UX Features
*   **Dark/Light Mode:** System-preference aware.
*   **Responsive:** Fully functional on tablets and mobile devices.
*   **Vietnamese Localization:** All currency, dates, and labels adapted for the VN market (e.g., "1.200.000 VNĐ").
*   **Client-Side Caching:** React Query handles API caching for instant page loads on revisit.
