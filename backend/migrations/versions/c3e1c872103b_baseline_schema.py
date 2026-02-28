"""baseline_schema

Revision ID: c3e1c872103b
Revises: 
Create Date: 2026-02-28 10:02:55.387842

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3e1c872103b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(80), unique=True, nullable=False),
        sa.Column('email', sa.String(120), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(256), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime()),
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])

    # Contests
    op.create_table(
        'contests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), server_default=''),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime()),
    )

    # Problems
    op.create_table(
        'problems',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('contest_id', sa.Integer(), sa.ForeignKey('contests.id'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('input_format', sa.Text(), server_default=''),
        sa.Column('output_format', sa.Text(), server_default=''),
        sa.Column('constraints', sa.Text(), server_default=''),
        sa.Column('sample_input', sa.Text(), server_default=''),
        sa.Column('sample_output', sa.Text(), server_default=''),
        sa.Column('time_limit', sa.Float(), server_default='2.0'),
        sa.Column('memory_limit', sa.Integer(), server_default='256'),
        sa.Column('points', sa.Integer(), server_default='100'),
    )
    op.create_index('ix_problems_contest_id', 'problems', ['contest_id'])

    # Contest Participants
    op.create_table(
        'contest_participants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('contest_id', sa.Integer(), sa.ForeignKey('contests.id'), nullable=False),
        sa.Column('score', sa.Integer(), server_default='0'),
        sa.Column('problems_solved', sa.Integer(), server_default='0'),
        sa.Column('total_time', sa.Integer(), server_default='0'),
        sa.Column('penalty_time', sa.Integer(), server_default='0'),
        sa.Column('violation_count', sa.Integer(), server_default='0'),
        sa.Column('is_flagged', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('joined_at', sa.DateTime()),
        sa.UniqueConstraint('user_id', 'contest_id', name='uq_user_contest'),
    )

    # Test Cases
    op.create_table(
        'test_cases',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('problem_id', sa.Integer(), sa.ForeignKey('problems.id'), nullable=False),
        sa.Column('input_data', sa.Text(), nullable=False),
        sa.Column('expected_output', sa.Text(), nullable=False),
        sa.Column('is_sample', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('order', sa.Integer(), server_default='0'),
    )
    op.create_index('ix_test_cases_problem_id', 'test_cases', ['problem_id'])

    # Submissions
    op.create_table(
        'submissions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('problem_id', sa.Integer(), sa.ForeignKey('problems.id'), nullable=False),
        sa.Column('contest_id', sa.Integer(), sa.ForeignKey('contests.id'), nullable=False),
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('language', sa.String(20), nullable=False, server_default='python'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('execution_time', sa.Float()),
        sa.Column('memory_used', sa.Integer()),
        sa.Column('error_message', sa.Text()),
        sa.Column('test_cases_passed', sa.Integer(), server_default='0'),
        sa.Column('total_test_cases', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime()),
    )
    op.create_index('ix_submissions_user_id', 'submissions', ['user_id'])
    op.create_index('ix_submissions_problem_id', 'submissions', ['problem_id'])
    op.create_index('ix_submissions_contest_id', 'submissions', ['contest_id'])

    # Proctoring Violations
    op.create_table(
        'proctoring_violations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('contest_id', sa.Integer(), sa.ForeignKey('contests.id'), nullable=False),
        sa.Column('violation_type', sa.String(50), nullable=False),
        sa.Column('details', sa.Text(), server_default=''),
        sa.Column('timestamp', sa.DateTime()),
    )
    op.create_index('ix_proctoring_violations_user_id', 'proctoring_violations', ['user_id'])
    op.create_index('ix_proctoring_violations_contest_id', 'proctoring_violations', ['contest_id'])


def downgrade():
    op.drop_table('proctoring_violations')
    op.drop_table('submissions')
    op.drop_table('test_cases')
    op.drop_table('contest_participants')
    op.drop_table('problems')
    op.drop_table('contests')
    op.drop_table('users')
