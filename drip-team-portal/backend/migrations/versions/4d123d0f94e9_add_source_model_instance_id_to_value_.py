"""add_source_model_instance_id_to_value_nodes

Revision ID: 4d123d0f94e9
Revises: e02a07cec205
Create Date: 2025-12-26 23:50:05.483197

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d123d0f94e9'
down_revision: Union[str, None] = 'e02a07cec205'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add source_model_instance_id column to value_nodes
    op.add_column(
        'value_nodes',
        sa.Column('source_model_instance_id', sa.Integer(), nullable=True)
    )

    # Add source_output_name column to value_nodes
    op.add_column(
        'value_nodes',
        sa.Column('source_output_name', sa.String(100), nullable=True)
    )

    # Create foreign key constraint
    op.create_foreign_key(
        'fk_value_node_model_instance',
        'value_nodes', 'model_instances',
        ['source_model_instance_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_value_node_model_instance', 'value_nodes', type_='foreignkey')
    op.drop_column('value_nodes', 'source_output_name')
    op.drop_column('value_nodes', 'source_model_instance_id')
