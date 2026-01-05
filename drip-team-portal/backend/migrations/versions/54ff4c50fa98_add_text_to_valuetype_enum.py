"""add_text_to_valuetype_enum

Revision ID: 54ff4c50fa98
Revises: 8d87d6306b62
Create Date: 2026-01-04 22:48:27.599162

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54ff4c50fa98'
down_revision: Union[str, None] = '8d87d6306b62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing values to the valuetype enum
    # PostgreSQL requires ALTER TYPE to add new enum values
    # We use IF NOT EXISTS to make this idempotent
    # Add both lowercase (enum values) and uppercase (enum names) for compatibility
    op.execute("ALTER TYPE valuetype ADD VALUE IF NOT EXISTS 'range'")
    op.execute("ALTER TYPE valuetype ADD VALUE IF NOT EXISTS 'average'")
    op.execute("ALTER TYPE valuetype ADD VALUE IF NOT EXISTS 'text'")
    op.execute("ALTER TYPE valuetype ADD VALUE IF NOT EXISTS 'TEXT'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing values from an enum
    # Would need to recreate the enum type entirely
    pass
