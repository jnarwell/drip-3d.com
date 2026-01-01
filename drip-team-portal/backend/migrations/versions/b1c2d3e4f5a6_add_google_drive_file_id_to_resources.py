"""add_google_drive_file_id_to_resources

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add google_drive_file_id column to resources table
    op.add_column('resources', sa.Column('google_drive_file_id', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_resources_google_drive_file_id'), 'resources', ['google_drive_file_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resources_google_drive_file_id'), table_name='resources')
    op.drop_column('resources', 'google_drive_file_id')
