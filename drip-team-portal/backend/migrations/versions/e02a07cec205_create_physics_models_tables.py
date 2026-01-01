"""create_physics_models_tables

Revision ID: e02a07cec205
Revises: 94a2212c4c76
Create Date: 2025-12-26 23:49:19.034204

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e02a07cec205'
down_revision: Union[str, None] = '94a2212c4c76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create physics_models table
    op.create_table(
        'physics_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_physics_models_category', 'physics_models', ['category'])

    # Create physics_model_versions table
    op.create_table(
        'physics_model_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('physics_model_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_current', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('changelog', sa.Text(), nullable=True),
        sa.Column('inputs', sa.JSON(), nullable=True),
        sa.Column('outputs', sa.JSON(), nullable=True),
        sa.Column('equations', sa.JSON(), nullable=True),
        sa.Column('equation_ast', sa.JSON(), nullable=True),
        sa.Column('equation_latex', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['physics_model_id'], ['physics_models.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('physics_model_id', 'version', name='uq_model_version')
    )
    op.create_index('ix_physics_model_versions_is_current', 'physics_model_versions', ['is_current'])

    # Create model_instances table
    op.create_table(
        'model_instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_version_id', sa.Integer(), nullable=False),
        sa.Column('component_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(200), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_computed', sa.DateTime(), nullable=True),
        sa.Column('computation_status', sa.Enum('VALID', 'STALE', 'ERROR', 'PENDING', 'CIRCULAR', name='computationstatus', create_type=False), nullable=True),
        sa.ForeignKeyConstraint(['model_version_id'], ['physics_model_versions.id']),
        sa.ForeignKeyConstraint(['component_id'], ['components.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_model_instances_component_id', 'model_instances', ['component_id'])

    # Create model_inputs table
    op.create_table(
        'model_inputs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_instance_id', sa.Integer(), nullable=False),
        sa.Column('input_name', sa.String(100), nullable=False),
        sa.Column('source_value_node_id', sa.Integer(), nullable=True),
        sa.Column('source_lookup', sa.JSON(), nullable=True),
        sa.Column('literal_value', sa.Float(), nullable=True),
        sa.Column('literal_unit_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['model_instance_id'], ['model_instances.id']),
        sa.ForeignKeyConstraint(['source_value_node_id'], ['value_nodes.id']),
        sa.ForeignKeyConstraint(['literal_unit_id'], ['units.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('model_inputs')
    op.drop_table('model_instances')
    op.drop_index('ix_physics_model_versions_is_current', 'physics_model_versions')
    op.drop_table('physics_model_versions')
    op.drop_index('ix_physics_models_category', 'physics_models')
    op.drop_table('physics_models')
