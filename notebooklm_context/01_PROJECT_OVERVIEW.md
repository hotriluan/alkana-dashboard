# 01. Project Overview

## Alkana Dashboard System

### 1. Introduction
The Alkana Dashboard is a comprehensive implementation of an Enterprise Command Center for a paint manufacturing company ("Alkana"). It integrates data from four core SAP modules:
*   **PP (Production Planning):** Production orders, yields, efficiency.
*   **MM (Material Management):** Inventory, goods movements, purchasing.
*   **SD (Sales & Distribution):** Sales orders, billing, deliveries, prices.
*   **FI (Financial Accounting):** Accounts receivable, aging analysis.

### 2. Core Objective
The system is designed to provide "Single Version of Truth" visibility into the end-to-end supply chain, transforming raw, disjointed SAP exports (Excel files) into a unified, analytical Data Warehouse.

### 3. Key Business Problems Solved
*   **Fragmented Data:** SAP data exists in isolated silos (Excel exports). The system unifies them.
*   **Inventory Accuracy:** Standard reports don't account for reversals (e.g., swapping a Goods Issue 601 with a cancellation 602). This system implements a "Stack-based Netting Engine" to accurately calculate net inventory flow.
*   **Yield Visibility:** Tracking production loss across multi-stage chemical processes (Mixing P03 -> Intermediate P02 -> Filling P01) is difficult in standard SAP. This system reconstructs the production chain to calculate true yield.
*   **Unit of Measure Confusion:** Sales sells in Pieces (PC), Production produces in Kilograms (KG). The system implements an intelligent auto-learning UOM conversion layer.

### 4. Architecture High-Level
The system follows a modern **ELT (Extract-Load-Transform)** pattern:
1.  **Extract:** Users upload raw SAP Excel exports (`.xlsx`).
2.  **Load:** Data is loaded AS-IS into a "Raw Data Lake" (PostgreSQL staging tables).
3.  **Transform:** Complex Python algorithms (Pandas/NumPy) process the data, apply business rules, and load it into a Star Schema Data Warehouse.
4.  **Visualize:** A React-based Single Page Application (SPA) queries the warehouse via a FastAPI backend to render interactive dashboards.

### 5. Intended Audience
*   **Executives:** High-level revenue, top customers, and critical alerts.
*   **Sales Managers:** Performance vs Targets, customer aging.
*   **Plant Managers:** Production yield, line efficiency, stock levels.
*   **Supply Chain:** Inventory turnover, stuck-in-transit alerts.
