"""Add indexes and cascade deletes for performance and data integrity

Revision ID: g5f6a7b8c9d0
Revises: f4e5a6b7c8d9
Create Date: 2025-01-02

Changes:
- Add indexes on resources.resource_type, resources.added_by
- Add index on time_entries.resource_id
- Add CASCADE delete on resource_components and resource_physics_models
- Add SET NULL on time_entries.resource_id when resource deleted
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g5f6a7b8c9d0'
down_revision = 'f4e5a6b7c8d9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add indexes for frequently queried columns
    op.create_index('ix_resources_resource_type', 'resources', ['resource_type'], unique=False)
    op.create_index('ix_resources_added_by', 'resources', ['added_by'], unique=False)
    op.create_index('ix_time_entries_resource_id', 'time_entries', ['resource_id'], unique=False)

    # Update foreign key constraints with CASCADE/SET NULL
    # Note: SQLite doesn't support ALTER CONSTRAINT, so we need to recreate tables
    # For PostgreSQL, we can use batch operations

    # resource_components: add CASCADE on both foreign keys
    with op.batch_alter_table('resource_components', schema=None) as batch_op:
        batch_op.drop_constraint('resource_components_resource_id_fkey', type_='foreignkey')
        batch_op.drop_constraint('resource_components_component_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'resource_components_resource_id_fkey',
            'resources', ['resource_id'], ['id'],
            ondelete='CASCADE'
        )
        batch_op.create_foreign_key(
            'resource_components_component_id_fkey',
            'components', ['component_id'], ['id'],
            ondelete='CASCADE'
        )

    # resource_physics_models: add CASCADE on both foreign keys
    with op.batch_alter_table('resource_physics_models', schema=None) as batch_op:
        batch_op.drop_constraint('resource_physics_models_resource_id_fkey', type_='foreignkey')
        batch_op.drop_constraint('resource_physics_models_physics_model_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'resource_physics_models_resource_id_fkey',
            'resources', ['resource_id'], ['id'],
            ondelete='CASCADE'
        )
        batch_op.create_foreign_key(
            'resource_physics_models_physics_model_id_fkey',
            'physics_models', ['physics_model_id'], ['id'],
            ondelete='CASCADE'
        )

    # time_entries: add SET NULL on resource_id foreign key
    with op.batch_alter_table('time_entries', schema=None) as batch_op:
        batch_op.drop_constraint('time_entries_resource_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'time_entries_resource_id_fkey',
            'resources', ['resource_id'], ['id'],
            ondelete='SET NULL'
        )


def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_time_entries_resource_id', table_name='time_entries')
    op.drop_index('ix_resources_added_by', table_name='resources')
    op.drop_index('ix_resources_resource_type', table_name='resources')

    # Revert foreign key constraints (remove CASCADE/SET NULL)
    with op.batch_alter_table('resource_components', schema=None) as batch_op:
        batch_op.drop_constraint('resource_components_resource_id_fkey', type_='foreignkey')
        batch_op.drop_constraint('resource_components_component_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'resource_components_resource_id_fkey',
            'resources', ['resource_id'], ['id']
        )
        batch_op.create_foreign_key(
            'resource_components_component_id_fkey',
            'components', ['component_id'], ['id']
        )

    with op.batch_alter_table('resource_physics_models', schema=None) as batch_op:
        batch_op.drop_constraint('resource_physics_models_resource_id_fkey', type_='foreignkey')
        batch_op.drop_constraint('resource_physics_models_physics_model_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'resource_physics_models_resource_id_fkey',
            'resources', ['resource_id'], ['id']
        )
        batch_op.create_foreign_key(
            'resource_physics_models_physics_model_id_fkey',
            'physics_models', ['physics_model_id'], ['id']
        )

    with op.batch_alter_table('time_entries', schema=None) as batch_op:
        batch_op.drop_constraint('time_entries_resource_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'time_entries_resource_id_fkey',
            'resources', ['resource_id'], ['id']
        )
