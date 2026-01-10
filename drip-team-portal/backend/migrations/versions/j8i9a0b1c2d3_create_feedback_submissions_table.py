"""Create feedback submissions table

Revision ID: j8i9a0b1c2d3
Revises: i7h8a9b0c1d2
Create Date: 2026-01-09

New feedback submission system:
- feedback_submissions: User feedback with type, urgency, status tracking
- Supports bug reports, feature requests, and questions
- Includes browser context and resolution workflow
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'j8i9a0b1c2d3'
down_revision = '54ff4c50fa98'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the enum types if they don't exist (PostgreSQL)
    op.execute("DO $$ BEGIN CREATE TYPE feedbacktype AS ENUM ('bug', 'feature', 'question'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE feedbackurgency AS ENUM ('need_now', 'nice_to_have'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE feedbackstatus AS ENUM ('new', 'reviewed', 'in_progress', 'resolved', 'wont_fix'); EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # Create feedback_submissions table using raw SQL to reference existing enum types
    op.execute("""
        CREATE TABLE feedback_submissions (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(200) NOT NULL,
            type feedbacktype NOT NULL,
            urgency feedbackurgency NOT NULL,
            description TEXT NOT NULL,
            page_url VARCHAR(500),
            browser_info JSON,
            status feedbackstatus NOT NULL DEFAULT 'new',
            resolution_notes TEXT,
            resolved_by VARCHAR(200),
            resolved_at TIMESTAMP,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)

    # Create indexes for commonly filtered columns
    op.create_index('ix_feedback_submissions_id', 'feedback_submissions', ['id'])
    op.create_index('ix_feedback_submissions_status', 'feedback_submissions', ['status'])
    op.create_index('ix_feedback_submissions_type', 'feedback_submissions', ['type'])
    op.create_index('ix_feedback_submissions_urgency', 'feedback_submissions', ['urgency'])
    op.create_index('ix_feedback_submissions_created_at', 'feedback_submissions', ['created_at'])
    op.create_index('ix_feedback_submissions_user_id', 'feedback_submissions', ['user_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_feedback_submissions_user_id', table_name='feedback_submissions')
    op.drop_index('ix_feedback_submissions_created_at', table_name='feedback_submissions')
    op.drop_index('ix_feedback_submissions_urgency', table_name='feedback_submissions')
    op.drop_index('ix_feedback_submissions_type', table_name='feedback_submissions')
    op.drop_index('ix_feedback_submissions_status', table_name='feedback_submissions')
    op.drop_index('ix_feedback_submissions_id', table_name='feedback_submissions')

    # Drop table
    op.drop_table('feedback_submissions')

    # Drop enums (PostgreSQL only - SQLite will ignore)
    op.execute('DROP TYPE IF EXISTS feedbackstatus')
    op.execute('DROP TYPE IF EXISTS feedbackurgency')
    op.execute('DROP TYPE IF EXISTS feedbacktype')
