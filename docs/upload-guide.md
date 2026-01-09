# Upload Guide

This guide explains how to upload SAP Excel files, how the system detects file types, and how deduplication works to keep data consistent.

## Supported Reports
- COOISPI (Production Orders)
- MB51 (Material Movements)
- ZRMM024 (MRP Controller)
- ZRSD002 (Sales Orders / Billing)
- ZRSD004 (Delivery)
- ZRSD006 (Distribution Channel)
- ZRFI005 (AR Aging, requires snapshot date)
- TARGET (Sales Targets)

## Upload Flow
1. Validation: File extension, size, and basic structure are checked.
2. Detection: Headers are scanned and matched to known patterns.
3. Loading: Excel rows are mapped into raw tables with correct column names.
4. Upsert: Existing business records are updated; identical rows are skipped.
5. Transform: Raw data is processed into fact tables.

## File Detection Notes
- ZRSD006: Accepts `Material Code` and `PH 1` / `PH 2` headers.
- ZRSD002: Uses actual headers like `Name of Bill to`, `Description`, and `Volum`.

## Deduplication Strategy (ZRSD002)
- Business key: `(billing_document, billing_item)` is unique.
- `row_hash` excludes `source_file` to avoid false differences across files.
- Uploading overlapping files results in updates for existing records and inserts for new records.

### Example
- File A: Jan–Dec 2025 (21,072 rows)
- File B: Dec 2025–Jan 2026 (2,514 rows)
- Result: 396 new inserts (Jan 2026), 2,118 updates (Dec 2025 overlap), 0 duplicates.

## Troubleshooting
- 400 errors: Ensure headers match expected patterns; see detection notes above.
- All rows skipped: Data already exists and is identical; this is expected for re-uploads.
- Wrong totals (e.g., 0 kg): Ensure MB51 transform is run and UOM conversion data exists.

## Best Practices
- Prefer full-month files; avoid partial overlaps where possible.
- Keep header names consistent; small differences (spaces, periods) matter.
- Run transforms after uploads to refresh dashboards.

## Related Docs
- Date Defaults: Dashboards use first day of month → today.
- ETL Fixes Report: See `docs/ETL_FIXES_2026-01-07.md` for detailed changes.
