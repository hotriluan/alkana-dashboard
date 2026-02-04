# Plan: Fix Inventory Top Movers Chart Bars

## TODO
1) Replace function-based `YAxis` data keys with explicit label fields to ensure Recharts category scale renders bars correctly.
2) Add a minimum bar size for visibility while keeping current styling.
3) Validate compile/build after changes.

## Files
- web/src/components/dashboard/inventory/InventoryTopMovers.tsx

## Notes
- API data already shows numeric values (velocity_score 1369–3885; stock_kg 44k–313k), so focus on chart config/dataKey stability.
