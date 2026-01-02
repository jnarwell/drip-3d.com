"""create_google_tokens_table

Store OAuth tokens for Google Drive access.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'google_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_email', sa.String(length=200), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_google_tokens_id'), 'google_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_google_tokens_user_email'), 'google_tokens', ['user_email'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_google_tokens_user_email'), table_name='google_tokens')
    op.drop_index(op.f('ix_google_tokens_id'), table_name='google_tokens')
    op.drop_table('google_tokens')
