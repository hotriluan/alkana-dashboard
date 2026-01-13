-- =====================================================================
-- Migration: Drop Legacy Yield Tables
-- Date: 2026-01-12
-- Author: Deep Clean Operation
-- Reference: plans/20260112-deep-clean-legacy-yield.md
-- 
-- Purpose: Remove legacy genealogy tracking tables (fact_production_chain,
--          fact_p02_p01_yield) while preserving V3 production performance.
-- 
-- CRITICAL: DO NOT DROP:
--   - fact_production_performance_v2 (used by V3)
--   - dim_product_hierarchy (dimension table)
--   - raw_zrpp062 (source data for V3)
-- =====================================================================

BEGIN;

-- =====================================================================
-- BACKUP VERIFICATION (Run this first before executing drops)
-- =====================================================================

-- Check row counts before deletion
-- COPY TO FILE: backups/yield_legacy_row_counts_20260112.txt
SELECT 
    'fact_production_chain' as table_name,
    COUNT(*) as row_count,
    MIN(created_at) as earliest_record,
    MAX(created_at) as latest_record
FROM fact_production_chain
UNION ALL
SELECT 
    'fact_p02_p01_yield' as table_name,
    COUNT(*) as row_count,
    MIN(created_at) as earliest_record,
    MAX(created_at) as latest_record
FROM fact_p02_p01_yield;

-- Export schemas before drop
-- Run: pg_dump --schema-only -t fact_production_chain -t fact_p02_p01_yield > backups/yield_legacy_schemas_20260112.sql

-- =====================================================================
-- DROP VIEWS THAT DEPEND ON LEGACY TABLES
-- =====================================================================

-- Drop view_yield_dashboard if it references fact_production_chain
DROP VIEW IF EXISTS view_yield_dashboard CASCADE;

-- Drop executive KPIs view and recreate without yield reference
DROP VIEW IF EXISTS view_executive_kpis CASCADE;

-- =====================================================================
-- DROP LEGACY TABLES
-- =====================================================================

-- Drop P02->P01 Yield Tracking Table (decommissioned)
DROP TABLE IF EXISTS fact_p02_p01_yield CASCADE;

-- Drop Production Chain Genealogy Table (decommissioned)
DROP TABLE IF EXISTS fact_production_chain CASCADE;

-- =====================================================================
-- RECREATE EXECUTIVE KPIs VIEW (WITHOUT YIELD REFERENCE)
-- =====================================================================

CREATE OR REPLACE VIEW view_executive_kpis AS
SELECT 
    (SELECT COALESCE(SUM(net_value), 0) FROM fact_billing) as total_revenue,
    (SELECT COUNT(*) FROM fact_production WHERE is_mto = TRUE) as total_mto_orders,
    (SELECT COUNT(*) FROM fact_production WHERE is_mto = FALSE) as total_mts_orders,
    0::numeric as avg_yield_pct,  -- Removed: was referencing fact_production_chain
    (SELECT COUNT(*) FROM fact_alert WHERE status = 'ACTIVE') as active_alerts,
    (SELECT COUNT(*) FROM fact_inventory) as total_inventory_movements,
    (SELECT COUNT(*) FROM fact_purchase_order) as total_purchase_orders;

COMMENT ON VIEW view_executive_kpis IS 'Executive KPIs - updated 2026-01-12 to remove legacy yield reference';

-- =====================================================================
-- VERIFICATION QUERIES
-- =====================================================================

-- Verify tables are dropped
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('fact_production_chain', 'fact_p02_p01_yield');
-- Expected: 0 rows

-- Verify V3 tables still exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('fact_production_performance_v2', 'dim_product_hierarchy', 'raw_zrpp062');
-- Expected: 3 rows

-- Check for any remaining FK dependencies
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND (ccu.table_name IN ('fact_production_chain', 'fact_p02_p01_yield')
       OR tc.table_name IN ('fact_production_chain', 'fact_p02_p01_yield'));
-- Expected: 0 rows (all dependencies should be dropped with CASCADE)

COMMIT;

-- =====================================================================
-- ROLLBACK PLAN (if needed)
-- =====================================================================
-- 1. Restore schemas: psql -d alkana_db < backups/yield_legacy_schemas_20260112.sql
-- 2. Restore data if backup was taken
-- 3. Recreate views: run src/db/views.py original view definitions
-- =====================================================================
