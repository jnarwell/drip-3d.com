"""Create test protocol tables

Revision ID: i7h8a9b0c1d2
Revises: h6g7a8b9c0d1
Create Date: 2026-01-02

New test system tables:
- test_protocols: Reusable test templates defining WHAT to test and HOW
- test_runs: Individual test executions
- test_measurements: Flexible key-value measurements
- test_validations: Predicted vs measured comparisons

This replaces the old tests/test_results system with a more flexible architecture.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'i7h8a9b0c1d2'
down_revision = 'h6g7a8b9c0d1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums first (for PostgreSQL compatibility)
    # SQLite will ignore these as it doesn't support native enums
    testrunstatus = sa.Enum('SETUP', 'IN_PROGRESS', 'COMPLETED', 'ABORTED', name='testrunstatus')
    testresultstatus_new = sa.Enum('PASS', 'FAIL', 'PARTIAL', name='testresultstatus_new')
    validationstatus = sa.Enum('PASS', 'FAIL', 'WARNING', name='validationstatus')

    # Create test_protocols table
    op.create_table(
        'test_protocols',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('input_schema', sa.JSON(), nullable=True),
        sa.Column('output_schema', sa.JSON(), nullable=True),
        sa.Column('procedure', sa.Text(), nullable=True),
        sa.Column('equipment', sa.JSON(), nullable=True),
        sa.Column('model_id', sa.Integer(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['model_id'], ['physics_models.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_test_protocols_category', 'test_protocols', ['category'])
    op.create_index('ix_test_protocols_is_active', 'test_protocols', ['is_active'])

    # Create test_runs table
    op.create_table(
        'test_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('protocol_id', sa.Integer(), nullable=False),
        sa.Column('component_id', sa.Integer(), nullable=True),
        sa.Column('analysis_id', sa.Integer(), nullable=True),
        sa.Column('run_number', sa.Integer(), nullable=True),
        sa.Column('status', testrunstatus, nullable=True, server_default='SETUP'),
        sa.Column('operator', sa.String(100), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('configuration', sa.JSON(), nullable=True),
        sa.Column('result', testresultstatus_new, nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['protocol_id'], ['test_protocols.id']),
        sa.ForeignKeyConstraint(['component_id'], ['components.id']),
        sa.ForeignKeyConstraint(['analysis_id'], ['model_instances.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_test_runs_protocol_id', 'test_runs', ['protocol_id'])
    op.create_index('ix_test_runs_component_id', 'test_runs', ['component_id'])
    op.create_index('ix_test_runs_status', 'test_runs', ['status'])

    # Create test_measurements table
    op.create_table(
        'test_measurements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('parameter_name', sa.String(100), nullable=False),
        sa.Column('measured_value', sa.Float(), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['test_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_test_measurements_run_id', 'test_measurements', ['run_id'])

    # Create test_validations table
    op.create_table(
        'test_validations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('run_id', sa.Integer(), nullable=False),
        sa.Column('parameter_name', sa.String(100), nullable=False),
        sa.Column('predicted_value', sa.Float(), nullable=True),
        sa.Column('measured_value', sa.Float(), nullable=True),
        sa.Column('unit_id', sa.Integer(), nullable=True),
        sa.Column('error_absolute', sa.Float(), nullable=True),
        sa.Column('error_pct', sa.Float(), nullable=True),
        sa.Column('tolerance_pct', sa.Float(), nullable=True),
        sa.Column('status', validationstatus, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['test_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_test_validations_run_id', 'test_validations', ['run_id'])


def downgrade() -> None:
    # Drop tables in reverse order (children first)
    op.drop_index('ix_test_validations_run_id', table_name='test_validations')
    op.drop_table('test_validations')

    op.drop_index('ix_test_measurements_run_id', table_name='test_measurements')
    op.drop_table('test_measurements')

    op.drop_index('ix_test_runs_status', table_name='test_runs')
    op.drop_index('ix_test_runs_component_id', table_name='test_runs')
    op.drop_index('ix_test_runs_protocol_id', table_name='test_runs')
    op.drop_table('test_runs')

    op.drop_index('ix_test_protocols_is_active', table_name='test_protocols')
    op.drop_index('ix_test_protocols_category', table_name='test_protocols')
    op.drop_table('test_protocols')

    # Drop enums (PostgreSQL only - SQLite will ignore)
    op.execute('DROP TYPE IF EXISTS validationstatus')
    op.execute('DROP TYPE IF EXISTS testresultstatus_new')
    op.execute('DROP TYPE IF EXISTS testrunstatus')