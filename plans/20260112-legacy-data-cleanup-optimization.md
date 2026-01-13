# Legacy Data Cleanup & Optimization Plan

**Created:** 2026-01-12  
**Status:** Draft  
**Owner:** Engineering Team  

## Objective
Systematically eliminate data quality issues, resolve duplicate records, optimize yield calculations, and consolidate redundant analysis scripts into production-grade monitoring.

## Success Criteria
- [ ] Zero duplicate records in all fact tables (fact_inventory, fact_sales, fact_ar)
- [ ] Yield calculation V3 deployed and V2 decommissioned
- [ ] All raw data tables have unique constraints enforced
- [ ] Analysis scripts consolidated into automated_data_quality_tests.py
- [ ] Database audit passes with 0 critical issues
- [ ] API duplicate check endpoint returns clean results

## Phase 1: Data Quality Assessment (Days 1-2)
- [ ] 1.1 Run audit_database.py and document all findings in AUDIT_REPORT.md
- [ ] 1.2 Execute check_all_duplicates_robust.py across all tables
- [ ] 1.3 Analyze source data duplicates using analyze_source_duplicates.py
- [ ] 1.4 Review analyze_inventory_duplicates_fixed.py results
- [ ] 1.5 Document root causes in analysis matrix

## Phase 2: Duplicate Resolution (Days 3-5)
- [ ] 2.1 Apply unique constraints using add_unique_constraint.py (start with raw tables)
- [ ] 2.2 Resolve MB51 duplicates identified in analyze_material_doc_linking.py
- [ ] 2.3 Fix ZRSD006 duplicates per check_zrsd006_duplicates.py
- [ ] 2.4 Cleanse fact_inventory using deduplication logic
- [ ] 2.5 Add row_hash to remaining tables via check_row_hash.py approach
- [ ] 2.6 Validate via check_duplicates_api.py endpoint

## Phase 3: Schema Enhancements (Days 6-7)
- [ ] 3.1 Add channel column using add_channel_column.py
- [ ] 3.2 Add snapshot_date to AR using add_snapshot_date_to_ar.py
- [ ] 3.3 Deploy performance indexes via add_performance_indexes.py
- [ ] 3.4 Update UOM schema per check_uom_schema.py findings
- [ ] 3.5 Run auto_patch_table.py for schema migrations

## Phase 4: Yield Calculation Migration (Days 8-10)
- [ ] 4.1 Finalize Yield V3 logic per BRAINSTORM_YIELD_V3.md
- [ ] 4.2 Deploy P02→P01 yield table using add_p02_p01_yield_table.py
- [ ] 4.3 Validate against analyze_p02_to_multiple_p01.py edge cases
- [ ] 4.4 Run parallel testing: V2 vs V3 comparison
- [ ] 4.5 Switch production views to V3
- [ ] 4.6 Decommission V2 per BRAINSTORM_YIELD_DECOMMISSION.md

## Phase 5: Monitoring Consolidation (Days 11-12)
- [ ] 5.1 Migrate critical checks to automated_data_quality_tests.py
- [ ] 5.2 Archive obsolete analyze_*.py scripts (move to archive/)
- [ ] 5.3 Configure check_final_alerts.py as daily job
- [ ] 5.4 Set up check_db_status.py health monitoring
- [ ] 5.5 Document in CHANGELOG.md

## Phase 6: Validation & Documentation (Day 13)
- [ ] 6.1 Complete BROWSER_TESTING_CHECKLIST.md for UI impacts
- [ ] 6.2 Run full regression via automated_data_quality_tests.py
- [ ] 6.3 Verify API endpoints functional
- [ ] 6.4 Update README with new data flow diagrams
- [ ] 6.5 Team knowledge transfer session

## Rollback Plan
1. Database snapshots before Phase 2 (duplicate resolution)
2. Keep V2 yield views active until V3 validated (Phase 4)
3. Preserve all analyze_*.py scripts until Phase 6 complete
4. Version control all schema changes with migration scripts
5. Document rollback commands in each phase checklist

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Data loss during deduplication | HIGH | Backup before Phase 2; soft delete approach |
| Yield V3 calculation errors | HIGH | Parallel run V2/V3 for 1 week; rollback ready |
| Breaking changes to API | MEDIUM | Version API; maintain backwards compatibility |
| Performance degradation from indexes | MEDIUM | Test on staging; monitor query times |
| Incomplete duplicate detection | MEDIUM | Multi-tool validation in Phase 1 |

## Open Questions
1. Which analyze_*.py scripts are still actively used vs. one-off investigations?
2. Are there downstream dependencies on current yield V2 structure?
3. What is acceptable downtime window for schema migrations?
4. Should we archive or delete resolved analysis scripts?
5. Are there external systems consuming our API that need migration notice?

## Dependencies
- Database backup strategy confirmed
- Staging environment available for testing
- ETL pipeline pause capability for schema changes
- Team availability for validation sessions

## Metrics to Track
- Duplicate record count (target: 0)
- Data quality test pass rate (target: 100%)
- Query performance (target: <5% degradation)
- ETL pipeline success rate (target: >99.5%)

---
**Next Review:** Phase 1 completion (Day 2)
