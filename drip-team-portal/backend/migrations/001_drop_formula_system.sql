-- Migration: Drop Formula System
-- Date: 2025-12-15
-- Description: Remove all formula-related tables and columns in preparation for new value system

-- Drop formula tables (in order to handle foreign key constraints)
DROP TABLE IF EXISTS calculation_history CASCADE;
DROP TABLE IF EXISTS formula_validation_rules CASCADE;
DROP TABLE IF EXISTS property_references CASCADE;
DROP TABLE IF EXISTS property_formulas CASCADE;
DROP TABLE IF EXISTS formula_templates CASCADE;

-- Drop formula-related columns from component_properties table
-- Note: These may not exist if database was recently created, so we use IF EXISTS
DO $$
BEGIN
    -- Drop is_calculated column
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'component_properties' AND column_name = 'is_calculated') THEN
        ALTER TABLE component_properties DROP COLUMN is_calculated;
    END IF;

    -- Drop formula_id column
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'component_properties' AND column_name = 'formula_id') THEN
        ALTER TABLE component_properties DROP COLUMN formula_id;
    END IF;

    -- Drop last_calculated column
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'component_properties' AND column_name = 'last_calculated') THEN
        ALTER TABLE component_properties DROP COLUMN last_calculated;
    END IF;

    -- Drop calculation_inputs column
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'component_properties' AND column_name = 'calculation_inputs') THEN
        ALTER TABLE component_properties DROP COLUMN calculation_inputs;
    END IF;

    -- Drop calculation_status column
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'component_properties' AND column_name = 'calculation_status') THEN
        ALTER TABLE component_properties DROP COLUMN calculation_status;
    END IF;
END $$;

-- Verify cleanup
SELECT 'Formula system removed successfully. Tables dropped and columns removed from component_properties.' as status;
