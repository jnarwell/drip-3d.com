-- Migration: Add Time Tracking + Resources
-- Date: 2025-12-31
-- Run with: psql $DATABASE_URL -f migrations/add_time_tracking.sql

-- ============================================================================
-- 1. Add owner_id to components table
-- ============================================================================
ALTER TABLE components ADD COLUMN IF NOT EXISTS owner_id VARCHAR;

-- ============================================================================
-- 2. Create resources table
-- ============================================================================
CREATE TABLE IF NOT EXISTS resources (
    id SERIAL PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    url VARCHAR(2000),
    added_by VARCHAR(200) NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tags JSONB,
    notes TEXT
);

-- ============================================================================
-- 3. Create time_entries table
-- ============================================================================
CREATE TABLE IF NOT EXISTS time_entries (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(200) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    stopped_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    linear_issue_id VARCHAR(50),
    linear_issue_title VARCHAR(500),
    resource_id INTEGER REFERENCES resources(id),
    description TEXT,
    is_uncategorized BOOLEAN DEFAULT FALSE,
    component_id INTEGER REFERENCES components(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for time_entries
CREATE INDEX IF NOT EXISTS ix_time_entries_user_id ON time_entries(user_id);
CREATE INDEX IF NOT EXISTS ix_time_entries_linear_issue_id ON time_entries(linear_issue_id);
CREATE INDEX IF NOT EXISTS ix_time_entries_component_id ON time_entries(component_id);
CREATE INDEX IF NOT EXISTS ix_time_entries_user_started ON time_entries(user_id, started_at);
CREATE INDEX IF NOT EXISTS ix_time_entries_active ON time_entries(user_id, stopped_at);

-- ============================================================================
-- 4. Create association tables
-- ============================================================================

-- Resources <-> Components
CREATE TABLE IF NOT EXISTS resource_components (
    resource_id INTEGER NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
    component_id INTEGER NOT NULL REFERENCES components(id) ON DELETE CASCADE,
    PRIMARY KEY (resource_id, component_id)
);

-- Resources <-> Physics Models
CREATE TABLE IF NOT EXISTS resource_physics_models (
    resource_id INTEGER NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
    physics_model_id INTEGER NOT NULL REFERENCES physics_models(id) ON DELETE CASCADE,
    PRIMARY KEY (resource_id, physics_model_id)
);

-- ============================================================================
-- Verification queries
-- ============================================================================
-- Run these to verify the migration:
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'components' AND column_name = 'owner_id';
-- SELECT * FROM information_schema.tables WHERE table_name IN ('resources', 'time_entries', 'resource_components', 'resource_physics_models');
