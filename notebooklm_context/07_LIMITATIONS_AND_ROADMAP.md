# 07. Limitations and Roadmap

## 1. Current Limitations (Technical)
*   **Batch Data Latency:** System depends on manual Excel uploads (daily snapshost); alerts are retroactive, not real-time events.
*   **Manual Integrity:** Data quality depends on the input Excel files. If SAP data is garbage, Dashboard is garbage.
*   **Netting Integration:** Inventory values in some dashboards might not perfectly align with SAP MB52 if complex reversal chains exist (though LIFO logic is implemented).

## 2. Roadmap

### Phase 1: User Acceptance Tests (IMMEDIATE)
*   **Validation:** Compare "Lead Time" calculations against manual spreadsheet checks for 50 random production orders.
*   **Feedback:** Gather feedback from Production Manager on the "Yield" vs "Loss" visualization.

### Phase 2: User Empowerment (Q1 2026)
*   **RBAC:** Implement Role-based access (Sales vs Production views).
*   **Excel Export:** Allow users to download cleaned data sets directly from the UI.

### Phase 3: Automation (Q2 2026)
*   **RPA:** Auto-ingest Excel files from network shared folder.
*   **Direct DB:** Read-only connection to SAP HANA (remove Excel dependency).
