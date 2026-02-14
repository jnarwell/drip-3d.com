"""add error_message to model_instances

Revision ID: k9j0a1b2c3d4
Revises: j8i9a0b1c2d3
Create Date: 2026-02-13 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'k9j0a1b2c3d4'
down_revision = 'j8i9a0b1c2d3'
branch_labels = None
depends_on = None


def upgrade():
    # Add error_message column to model_instances table
    op.add_column('model_instances', sa.Column('error_message', sa.Text(), nullable=True))


def downgrade():
    # Remove error_message column from model_instances table
    op.drop_column('model_instances', 'error_message')
