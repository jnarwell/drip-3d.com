"""add_text_value_to_component_properties

Revision ID: 8d87d6306b62
Revises: i7h8a9b0c1d2
Create Date: 2026-01-04 22:20:10.879990

FIXED: Original auto-generated migration incorrectly dropped contacts, google_tokens,
and other tables. This has been cleaned up to only add the text_value column.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '8d87d6306b62'
down_revision: Union[str, None] = 'i7h8a9b0c1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Only add text_value column to component_properties
    # The original auto-generated migration incorrectly dropped many tables
    op.add_column('component_properties', sa.Column('text_value', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('component_properties', 'text_value')
