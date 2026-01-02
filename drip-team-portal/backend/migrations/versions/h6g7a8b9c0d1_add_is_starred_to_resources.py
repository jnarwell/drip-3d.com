"""Add is_starred column to resources table

Revision ID: h6g7a8b9c0d1
Revises: g5f6a7b8c9d0
Create Date: 2026-01-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h6g7a8b9c0d1'
down_revision = 'g5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_starred column with default False
    op.add_column('resources', sa.Column('is_starred', sa.Boolean(), nullable=False, server_default='false'))

    # Add index for efficient filtering
    op.create_index('ix_resources_is_starred', 'resources', ['is_starred'])


def downgrade() -> None:
    op.drop_index('ix_resources_is_starred', table_name='resources')
    op.drop_column('resources', 'is_starred')
