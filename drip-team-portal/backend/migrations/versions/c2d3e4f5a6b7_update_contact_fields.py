"""update_contact_fields

Replace contact_info JSON with structured email, secondary_email, phone fields.

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add new columns (email initially nullable for migration)
    op.add_column('contacts', sa.Column('email', sa.String(length=200), nullable=True))
    op.add_column('contacts', sa.Column('secondary_email', sa.String(length=200), nullable=True))
    op.add_column('contacts', sa.Column('phone', sa.String(length=50), nullable=True))

    # Step 2: Migrate data from contact_info JSON to new columns
    # Extract email from contact_info->>'email' if it exists
    op.execute("""
        UPDATE contacts
        SET email = COALESCE(contact_info->>'email', 'unknown@placeholder.com'),
            secondary_email = contact_info->>'secondary_email',
            phone = contact_info->>'phone'
        WHERE contact_info IS NOT NULL
    """)

    # Step 3: Set placeholder email for any rows without contact_info
    op.execute("""
        UPDATE contacts
        SET email = 'unknown@placeholder.com'
        WHERE email IS NULL
    """)

    # Step 4: Make email NOT NULL
    op.alter_column('contacts', 'email', nullable=False)

    # Step 5: Drop the old contact_info column
    op.drop_column('contacts', 'contact_info')


def downgrade() -> None:
    # Re-add contact_info column
    op.add_column('contacts', sa.Column('contact_info', postgresql.JSON(astext_type=sa.Text()), nullable=True))

    # Migrate data back to JSON
    op.execute("""
        UPDATE contacts
        SET contact_info = jsonb_build_object(
            'email', email,
            'secondary_email', secondary_email,
            'phone', phone
        )
    """)

    # Drop new columns
    op.drop_column('contacts', 'phone')
    op.drop_column('contacts', 'secondary_email')
    op.drop_column('contacts', 'email')
