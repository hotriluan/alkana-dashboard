# 03. Logic and Algorithms

## A. Implemented Algorithms (Active)

### 1. Stack-Based MVT Netting Engine
**Problem:** A simple sum of movements is wrong because it doesn't account for reversals (e.g., MVT 602 cancelling MVT 601).
**Solution:** `StackNettingEngine` uses a LIFO (Last-In-First-Out) stack.
*   **Logic:** Push every "Forward" movement (e.g., 601) onto a stack. When a "Reverse" movement (e.g., 602) is encountered, pop the matching Forward movement off the stack.
*   **Implementation:** `src/core/netting.py`

### 2. Yield Tracking (Genealogy)
**Problem:** Yield loss happens at 3 stages (Mixing P03 -> Intermediate P02 -> Filling P01).
**Solution:** Recursive "Genealogy" tracing.
*   **Logic:** Start at P01. Find the input batch (MVT 261). Identify that input as a P02 output. Repeat upstream to P03.
*   **Formula:** $$ Yield \% = \frac{\text{Output Weight (KG)}}{\text{Total Input Weight (KG)}} \times 100 $$
*   **Implementation:** `src/core/yield_tracker.py`

### 3. Lead Time Calculation (MTO/MTS)
**Objective:** Calculate "Order to Delivery" time.
**Logic:**
*   **MTS (Make-to-Stock):**
    $$ T_{mts} = T_{prod} + T_{transit} + T_{storage} $$
*   **MTO (Make-to-Order):**
    $$ T_{mto} = T_{prep} + T_{prod} + T_{transit} + T_{storage} + T_{delivery} $$
    *   $T_{prep}$: PO Date (from Sales PO '44*') -> Release Date
    *   $T_{prod}$: Release -> Finish
    *   $T_{storage}$: Finish -> Valid Issue (MVT 601)
*   **Implementation:** `src/core/business_logic.py`, `src/etl/transform.py`

### 4. Auto-Learning UOM Conversion
**Problem:** Sales in PC, Production in KG. No standard conversion table.
**Solution:** Learn from historical Billing data.
*   **Logic:** $$ \text{Factor} = \frac{\sum \text{Net Weight}}{\sum \text{Billing Qty}} $$
*   **Implementation:** `src/core/uom_converter.py`

### 5. Alert Detection
**Logic:**
*   **Stuck in Transit:** > 48 hours between MVT 601 (Issue from Factory) and MVT 101 (Receipt at DC).
*   **Low Yield:** Yield < 95% or Loss > 100kg.
*   **Implementation:** `src/core/alerts.py`
