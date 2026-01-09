-- Fix variance_pct column overflow issue
-- Change from NUMERIC(5,2) to NUMERIC(10,2) to handle larger variance values

ALTER TABLE dim_uom_conversion 
ALTER COLUMN variance_pct TYPE NUMERIC(10, 2);

-- Verify change
SELECT column_name, data_type, numeric_precision, numeric_scale 
FROM information_schema.columns 
WHERE table_name = 'dim_uom_conversion' 
AND column_name = 'variance_pct';
