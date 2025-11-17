"""Add property table templates

Revision ID: ed72e886423d
Revises: 94a2212c4c76
Create Date: 2025-11-17 20:30:35.047629

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed72e886423d'
down_revision: Union[str, None] = '94a2212c4c76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums if they don't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE tabletype AS ENUM ('single_var_lookup', 'range_based_lookup', 'multi_var_lookup', 'reference_only');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE interpolationtype AS ENUM ('linear', 'logarithmic', 'polynomial', 'range_lookup', 'none');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE importmethod AS ENUM ('document_import', 'api_import', 'manual_entry', 'copied');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE verificationstatus AS ENUM ('verified', 'cited', 'unverified');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE sourcetype AS ENUM ('standard', 'paper', 'handbook', 'report', 'experimental', 'other');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create property_table_templates table
    op.create_table('property_table_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('table_type', sa.Enum('single_var_lookup', 'range_based_lookup', 'multi_var_lookup', 'reference_only', name='tabletype', create_type=False), nullable=False),
        sa.Column('independent_vars', sa.JSON(), nullable=False),
        sa.Column('dependent_vars', sa.JSON(), nullable=False),
        sa.Column('interpolation_type', sa.Enum('linear', 'logarithmic', 'polynomial', 'range_lookup', 'none', name='interpolationtype', create_type=False), nullable=False),
        sa.Column('extrapolation_allowed', sa.Boolean(), nullable=False),
        sa.Column('require_monotonic', sa.Boolean(), nullable=False),
        sa.Column('created_from_document', sa.Boolean(), nullable=False),
        sa.Column('source_document_example', sa.String(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_property_table_templates_created_by'), 'property_table_templates', ['created_by'], unique=False)
    op.create_index(op.f('ix_property_table_templates_id'), 'property_table_templates', ['id'], unique=False)
    op.create_index(op.f('ix_property_table_templates_is_public'), 'property_table_templates', ['is_public'], unique=False)
    op.create_index(op.f('ix_property_table_templates_name'), 'property_table_templates', ['name'], unique=False)
    op.create_index(op.f('ix_property_table_templates_table_type'), 'property_table_templates', ['table_type'], unique=False)

    # Check if property_tables table exists first
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'property_tables') THEN
                -- Add template_id column to property_tables if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'property_tables' AND column_name = 'template_id') THEN
                    ALTER TABLE property_tables ADD COLUMN template_id INTEGER REFERENCES property_table_templates(id);
                END IF;
                
                -- Add other columns
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'property_tables' AND column_name = 'import_method') THEN
                    ALTER TABLE property_tables ADD COLUMN import_method importmethod NOT NULL DEFAULT 'manual_entry';
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'property_tables' AND column_name = 'source_document_path') THEN
                    ALTER TABLE property_tables ADD COLUMN source_document_path VARCHAR;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'property_tables' AND column_name = 'source_document_hash') THEN
                    ALTER TABLE property_tables ADD COLUMN source_document_hash VARCHAR;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'property_tables' AND column_name = 'source_url') THEN
                    ALTER TABLE property_tables ADD COLUMN source_url VARCHAR;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'property_tables' AND column_name = 'source_citation') THEN
                    ALTER TABLE property_tables ADD COLUMN source_citation VARCHAR;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'property_tables' AND column_name = 'source_type') THEN
                    ALTER TABLE property_tables ADD COLUMN source_type sourcetype;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'property_tables' AND column_name = 'source_authority') THEN
                    ALTER TABLE property_tables ADD COLUMN source_authority VARCHAR;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'property_tables' AND column_name = 'verification_status') THEN
                    ALTER TABLE property_tables ADD COLUMN verification_status verificationstatus NOT NULL DEFAULT 'unverified';
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'property_tables' AND column_name = 'verification_method') THEN
                    ALTER TABLE property_tables ADD COLUMN verification_method VARCHAR;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'property_tables' AND column_name = 'last_verified') THEN
                    ALTER TABLE property_tables ADD COLUMN last_verified TIMESTAMP;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'property_tables' AND column_name = 'extracted_via_ocr') THEN
                    ALTER TABLE property_tables ADD COLUMN extracted_via_ocr BOOLEAN DEFAULT FALSE;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'property_tables' AND column_name = 'manual_corrections') THEN
                    ALTER TABLE property_tables ADD COLUMN manual_corrections INTEGER DEFAULT 0;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'property_tables' AND column_name = 'data_quality') THEN
                    ALTER TABLE property_tables ADD COLUMN data_quality VARCHAR;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'property_tables' AND column_name = 'applicable_conditions') THEN
                    ALTER TABLE property_tables ADD COLUMN applicable_conditions TEXT;
                END IF;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Drop columns from property_tables if table exists
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'property_tables') THEN
                ALTER TABLE property_tables DROP COLUMN IF EXISTS template_id;
                ALTER TABLE property_tables DROP COLUMN IF EXISTS import_method;
                ALTER TABLE property_tables DROP COLUMN IF EXISTS source_document_path;
                ALTER TABLE property_tables DROP COLUMN IF EXISTS source_document_hash;
                ALTER TABLE property_tables DROP COLUMN IF EXISTS source_url;
                ALTER TABLE property_tables DROP COLUMN IF EXISTS source_citation;
                ALTER TABLE property_tables DROP COLUMN IF EXISTS source_type;
                ALTER TABLE property_tables DROP COLUMN IF EXISTS source_authority;
                ALTER TABLE property_tables DROP COLUMN IF EXISTS verification_status;
                ALTER TABLE property_tables DROP COLUMN IF EXISTS verification_method;
                ALTER TABLE property_tables DROP COLUMN IF EXISTS last_verified;
                ALTER TABLE property_tables DROP COLUMN IF EXISTS extracted_via_ocr;
                ALTER TABLE property_tables DROP COLUMN IF EXISTS manual_corrections;
                ALTER TABLE property_tables DROP COLUMN IF EXISTS data_quality;
                ALTER TABLE property_tables DROP COLUMN IF EXISTS applicable_conditions;
            END IF;
        END $$;
    """)
    
    # Drop property_table_templates table
    op.drop_index(op.f('ix_property_table_templates_table_type'), table_name='property_table_templates')
    op.drop_index(op.f('ix_property_table_templates_name'), table_name='property_table_templates')
    op.drop_index(op.f('ix_property_table_templates_is_public'), table_name='property_table_templates')
    op.drop_index(op.f('ix_property_table_templates_id'), table_name='property_table_templates')
    op.drop_index(op.f('ix_property_table_templates_created_by'), table_name='property_table_templates')
    op.drop_table('property_table_templates')