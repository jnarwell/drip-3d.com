"""add_analysis_constraints

Adds constraints and indexes for named analysis instances:
- Unique constraint on name for analyses (where component_id IS NULL)
- Index for fast analysis queries
- Description field for analyses

Revision ID: a1b2c3d4e5f6
Revises: 4d123d0f94e9
Create Date: 2025-12-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '4d123d0f94e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add description field (optional)
    op.add_column('model_instances',
        sa.Column('description', sa.Text(), nullable=True)
    )

    # Add partial unique index on name for analyses only
    # This creates a unique constraint where component_id IS NULL
    op.execute("""
        CREATE UNIQUE INDEX uq_model_instances_name_analyses
        ON model_instances (name)
        WHERE component_id IS NULL AND name IS NOT NULL
    """)

    # Add index for fast analysis queries (name lookup)
    op.execute("""
        CREATE INDEX ix_model_instances_analyses
        ON model_instances (name)
        WHERE component_id IS NULL AND name IS NOT NULL
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_model_instances_analyses")
    op.execute("DROP INDEX IF EXISTS uq_model_instances_name_analyses")
    op.drop_column('model_instances', 'description')
