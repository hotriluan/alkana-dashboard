# Development Scripts Reference

Catalog of ad-hoc development and debugging scripts in the project root.

## Overview

The project root contains **80+ ad-hoc scripts** used during development for debugging, testing, and data analysis. These are **not part of the production codebase** and serve as investigation tools.

**Purpose:**
- Debug specific issues
- Validate data transformations
- Investigate production incidents
- Test hypotheses
- Analyze patterns

**Not for:**
- Automated testing (use `tests/` instead)
- Production deployment
- CI/CD pipelines

---

## Script Categories

### Check Scripts (36 files)

**Prefix:** `check_*.py`

**Purpose:** Validate data, table structure, and business logic

| Script | Purpose |
|--------|---------|
| `check_alert.py` | Verify alert detection logic |
| `check_all_movements.py` | Review all material movements |
| `check_alternative_link.py` | Test alternative batch linking approaches |
| `check_ar_overdue.py` | Validate AR aging calculations |
| `check_ar_table.py` | Inspect AR table structure |
| `check_batch_classification.py` | Verify batch type classification (P01/P02/P03) |
| `check_channel_data.py` | Review distribution channel data |
| `check_channel_simple.py` | Simplified channel validation |
| `check_column.py` | Check table column existence |
| `check_cooispi_structure.py` | Validate COOISPI table structure |
| `check_dist_channel.py` | Distribution channel data inspection |
| `check_final_alerts.py` | Review final alert implementation |
| `check_leadtime_records.py` | Validate lead time calculations |
| `check_mb51_columns.py` | Verify MB51 table columns |
| `check_mb51_mrp.py` | Check MRP-related MB51 data |
| `check_mb51.py` | General MB51 data validation |
| `check_mts_channel.py` | MTS distribution channel check |
| `check_mts_sources.py` | Validate MTS data sources |
| `check_mvt_261.py` | Movement type 261 validation |
| `check_p01_different_batch.py` | Check P01 batch variations |
| `check_p01_uom_conversion.py` | Validate UOM conversions for P01 |
| `check_production_chain.py` | Verify production chain linking |
| `check_raw_data_json.py` | JSON data structure validation |
| `check_raw_zrsd002.py` | ZRSD002 raw data check |
| `check_so_210033967.py` | Specific sales order investigation |
| `check_uom_schema.py` | UOM schema validation |
| `check_yield_data_structure.py` | Yield data structure check |
| `check_yield_view.py` | Materialized view validation |
| `check_zrsd006_channel.py` | ZRSD006 channel data |
| `check_zrsd006_file.py` | ZRSD006 file validation |
| `check_zrsd006_loader.py` | ZRSD006 ETL loader test |
| `check_zrsd006.py` | General ZRSD006 validation |

**Usage Example:**
```bash
python check_mb51.py
# Output: Shows sample MB51 records, column types, null counts
```

---

### Debug Scripts (15 files)

**Prefix:** `debug_*.py`

**Purpose:** Investigate specific batches, issues, or anomalies

| Script | Purpose |
|--------|---------|
| `debug_25L2502310_output.txt` | Output from batch 25L2502310 debug |
| `debug_alert_monitor.py` | Debug alert detection system |
| `debug_batch_25L2460910.py` | Investigate batch 25L2460910 |
| `debug_batch_25L2502310.py` | Investigate batch 25L2502310 |
| `debug_batch_25L2535110.py` | Investigate batch 25L2535110 |
| `debug_batch.py` | General batch debugging utility |
| `debug_empty_tables.py` | Check for empty tables after ETL |
| `debug_excel_read.py` | Test Excel file reading |
| `debug_mto_fact.py` | Debug MTO fact table |
| `debug_mvt_261_data.py` | MVT 261 data debugging |
| `debug_mvt_type.py` | Movement type classification debug |
| `debug_output.json` | JSON output from debugging |
| `debug_p02_finding.py` | P02 batch finding logic |
| `debug_production_record.py` | Production record debugging |
| `debug_prod_json.py` | Production JSON data debug |
| `debug_stuck_calculation.py` | Stuck-in-transit calculation debug |
| `debug_yield_tracker.py` | Yield tracking algorithm debug |

**Usage Example:**
```bash
python debug_batch_25L2502310.py
# Output: Full trace of batch movements, yield calculations, alerts
```

---

### Test Scripts (35 files)

**Prefix:** `test_*.py`

**Purpose:** Manual API testing, integration testing, hypothesis testing

| Script | Purpose |
|--------|---------|
| `test_alert_detection_direct.py` | Direct alert detection test |
| `test_api.py` | General API endpoint testing |
| `test_ar_fix.py` | AR calculation fix testing |
| `test_batch_linking.py` | Batch linking logic test |
| `test_batch_reference_search.py` | Batch reference search test |
| `test_batch_yield_sample.py` | Sample yield calculation test |
| `test_by_channel_api.py` | Sales by channel API test |
| `test_channel_direct.py` | Direct channel data test |
| `test_channel_endpoint.py` | Channel API endpoint test |
| `test_channel_mapping.py` | Channel mapping logic test |
| `test_channel_query.py` | Channel query test |
| `test_correct_yield_path.py` | Yield calculation path test |
| `test_dim_material.py` | Material dimension test |
| `test_dual_validation.py` | Dual validation logic test |
| `test_executive_api.py` | Executive dashboard API test |
| `test_fixed_query.py` | Fixed query validation |
| `test_lead_time_api.py` | Lead time API test |
| `test_material_date_linking.py` | Material-date linking test |
| `test_mto_trace.py` | MTO order tracing test |
| `test_netting_25L2502310.py` | Netting for specific batch |
| `test_queries.py` | SQL query testing |
| `test_query.py` | Single query test |
| `test_result.txt` | Test results output |
| `test_sequential_batch_pattern.py` | Sequential batch pattern test |
| `test_stuck_hours_integration.py` | Stuck hours integration test |
| `test_trace_api.py` | Trace API endpoint test |
| `test_trace_with_desc.py` | Trace with description test |
| `test_transform_leadtime.py` | Lead time transformation test |
| `test_yield_api.py` | Yield API test |
| `test_yield_endpoints.py` | Yield endpoints test |

**Note:** These are NOT formal tests for CI/CD. See `tests/` directory for automated test suite.

**Usage Example:**
```bash
python test_executive_api.py
# Output: Calls executive API endpoints, prints responses
```

---

### Verify Scripts (10 files)

**Prefix:** `verify_*.py`

**Purpose:** Data verification, validation of fixes, regression checking

| Script | Purpose |
|--------|---------|
| `verify_alerts.py` | Verify alerts are firing correctly |
| `verify_alert_system.py` | Alert system end-to-end verification |
| `verify_ar_fix.py` | Verify AR aging fix |
| `verify_channel_data.py` | Channel data verification |
| `verify_channel_implementation.py` | Channel implementation verification |
| `verify_lead_time_logic.py` | Lead time calculation verification |
| `verify_output.txt` | Verification output |
| `verify_p02_p01_yield.py` | P02→P01 yield verification |
| `verify_results.txt` | Verification results |
| `verify_simple.py` | Simple verification utility |
| `verify_transit_alerts.py` | Transit alert verification |
| `verify_zrsd006_data.py` | ZRSD006 data verification |

**Usage Example:**
```bash
python verify_alerts.py
# Output: Lists all alerts, verifies thresholds, checks for false positives
```

---

### Analyze Scripts (10 files)

**Prefix:** `analyze_*.py`

**Purpose:** Pattern analysis, data exploration, root cause investigation

| Script | Purpose |
|--------|---------|
| `analyze_backtracking.py` | Batch backtracking analysis |
| `analyze_dist_channel.py` | Distribution channel analysis |
| `analyze_material_doc_linking.py` | Material document linking analysis |
| `analyze_material_patterns.py` | Material usage patterns |
| `analyze_mvt_261_ref.py` | MVT 261 reference analysis |
| `analyze_p02_to_multiple_p01.py` | P02 splitting analysis |
| `analyze_prep_time.py` | Preparation time analysis |
| `analyze_source_duplicates.py` | Duplicate source detection |
| `analyze_storage_movements.py` | Storage movement patterns |
| `analyze_stuck_batch_25L2492010.py` | Specific stuck batch analysis |

**Usage Example:**
```bash
python analyze_material_patterns.py
# Output: Statistical analysis of material consumption patterns
```

---

### Utility Scripts (10+ files)

**Purpose:** Miscellaneous utilities, data manipulation, investigation

| Script | Purpose |
|--------|---------|
| `add_channel_column.py` | Add channel column to tables |
| `add_p02_p01_yield_table.py` | Create P02-P01 yield table |
| `audit_database.py` | Database integrity audit |
| `audit_duplication.py` | Find duplicate records |
| `auto_patch_table.py` | Auto-patch table structure |
| `combine_plans.py` | Combine planning data |
| `copy_next_steps.py` | Copy next steps content |
| `deep_check_dates.py` | Deep date validation |
| `deep_debug_25L2502310.py` | Deep batch investigation |
| `deep_investigation.py` | Deep data investigation |
| `examine_mvt_261_sample.py` | MVT 261 sample examination |
| `explain_stuck_logic.py` | Explain stuck-in-transit logic |
| `extract_plans.py` | Extract planning data |
| `extract_with_commit.py` | Extract with database commit |
| `extract_zrsd006_from_json.py` | Extract ZRSD006 from JSON |
| `final_check_zrsd006.py` | Final ZRSD006 validation |
| `final_stuck_analysis.py` | Final stuck batch analysis |
| `find_mto_batch.py` | Find MTO batches |
| `find_p02_p01_batches.py` | Find P02-P01 batch links |
| `find_real_mto.py` | Identify real MTO orders |
| `find_true_p02_batches.py` | Find true P02 batches |
| `import_zrsd006.py` | Import ZRSD006 data |
| `inspect_ar_table.py` | Inspect AR table |
| `investigate_p02_p01_linking.py` | Investigate P02-P01 linking |
| `quick_check.py` | Quick data check |
| `read_next_steps.py` | Read next steps content |
| `read_plans_safe.py` | Safely read plans |
| `simple_check.py` | Simple validation check |
| `simple_test.py` | Simple test utility |

---

## Output Files

**Purpose:** Captured outputs from script runs

| File | Source | Purpose |
|------|--------|---------|
| `debug_25L2502310_output.txt` | `debug_batch_25L2502310.py` | Batch debug output |
| `debug_output.json` | Various debug scripts | JSON debug data |
| `dist_channel_result.txt` | `analyze_dist_channel.py` | Channel analysis results |
| `extract_result.txt` | `extract_plans.py` | Extraction results |
| `stuck_analysis_output.txt` | `final_stuck_analysis.py` | Stuck batch analysis |
| `test_result.txt` | Various test scripts | Test execution results |
| `transit_verification_output.txt` | `verify_transit_alerts.py` | Transit verification |
| `verification_results.txt` | Various verify scripts | Verification results |
| `verify_output.txt` | Various verify scripts | Verification output |

---

## Using Scripts Effectively

### Investigation Workflow

**Scenario: Customer reports incorrect inventory count**

1. **Check raw data:**
   ```bash
   python check_mb51.py
   # Verify raw MB51 data loaded correctly
   ```

2. **Verify transformations:**
   ```bash
   python verify_simple.py
   # Check fact tables populated
   ```

3. **Debug specific material:**
   ```bash
   # Edit simple_test.py to filter by material code
   python simple_test.py
   # Trace all movements for material
   ```

4. **Test API response:**
   ```bash
   python test_api.py
   # Call inventory API, check response
   ```

5. **Document findings:**
   - Create issue with reproduction steps
   - Attach relevant script outputs
   - Propose fix in formal test + code

### Creating New Scripts

**When to create ad-hoc script:**
- Investigating production issue
- One-time data analysis
- Hypothesis testing
- Manual testing before automation

**Template:**
```python
#!/usr/bin/env python
"""
Quick description of what this script does and why it exists.

Created: 2025-12-30
Issue: #123
Purpose: Debug batch 25L9999999 stuck-in-transit alert
"""

from src.db.database import SessionLocal
from src.db.models import RawMB51

def main():
    db = SessionLocal()
    
    # Your investigation code here
    batch = "25L9999999"
    movements = db.query(RawMB51).filter(
        RawMB51.batch_number == batch
    ).all()
    
    print(f"Found {len(movements)} movements for batch {batch}")
    for m in movements:
        print(f"{m.posting_date}: {m.movement_type} {m.quantity}")
    
    db.close()

if __name__ == "__main__":
    main()
```

**Naming Convention:**
- `check_` - Data validation
- `debug_` - Issue investigation  
- `test_` - Manual testing
- `verify_` - Verification
- `analyze_` - Pattern analysis

---

## Should These Be Cleaned Up?

**Options:**

### Option 1: Keep As-Is
- **Pros:** Historical reference, quick copy-paste for new issues
- **Cons:** Clutters root directory, unclear which are still relevant

### Option 2: Move to `dev-tools/` folder
```
dev-tools/
├── check/
├── debug/
├── test/
├── verify/
├── analyze/
└── README.md  (this file)
```
- **Pros:** Organized, still accessible
- **Cons:** Requires reorganization effort

### Option 3: Delete Obsolete, Keep Essential
- **Keep:** Generic utilities (`simple_check.py`, `quick_check.py`)
- **Delete:** Batch-specific debugs for resolved issues
- **Archive:** Move old scripts to `archive/` or Git history

### Option 4: Convert to Formal Tools
- Move useful logic into `scripts/` folder
- Create `scripts/investigate.py` with subcommands
- Example:
  ```bash
  python -m scripts.investigate batch 25L2502310
  python -m scripts.investigate material P01-12345
  python -m scripts.investigate stuck-alerts
  ```

**Recommendation:** Option 2 (Move to `dev-tools/`) + Option 4 (Convert useful ones)

---

## FAQ

**Q: Should I use these scripts in production?**
A: No. These are development tools only.

**Q: Can I commit new ad-hoc scripts?**
A: Yes, but add descriptive header comment explaining purpose and context.

**Q: How do I know which script to use?**
A: Start with this README, then check script headers for descriptions.

**Q: Can I delete these scripts?**
A: Check with team first. Some may still be useful references.

**Q: Should I write tests this way?**
A: No. Use formal test framework in `tests/` directory. These are for quick investigation only.

---

## Related Documentation

- [TESTING.md](./TESTING.md) - Formal testing guide
- [CONTRIBUTING.md](./CONTRIBUTING.md) - Development workflow
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues

---

**Last Updated:** December 30, 2025
**Maintainer:** Development Team
