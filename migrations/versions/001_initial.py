"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('telegram_id', sa.BigInteger(), unique=True, nullable=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('garmin_email_enc', sa.Text(), nullable=True),
        sa.Column('garmin_token_enc', sa.Text(), nullable=True),
        sa.Column('settings_json', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'habit_definitions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('label', sa.String(255), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('options_json', postgresql.JSONB(), server_default='[]'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
    )

    op.create_table(
        'habit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False, index=True),
        sa.Column('logged_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('habit_key', sa.String(100), nullable=False),
        sa.Column('value', postgresql.JSONB(), nullable=False),
    )
    op.create_index('ix_habit_logs_user_date', 'habit_logs', ['user_id', 'date'])

    op.create_table(
        'garmin_daily',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False, index=True),
        sa.Column('sleep_score', sa.Integer(), nullable=True),
        sa.Column('deep_sleep_sec', sa.Integer(), nullable=True),
        sa.Column('rem_sleep_sec', sa.Integer(), nullable=True),
        sa.Column('light_sleep_sec', sa.Integer(), nullable=True),
        sa.Column('awake_sec', sa.Integer(), nullable=True),
        sa.Column('sleep_start', sa.DateTime(), nullable=True),
        sa.Column('sleep_end', sa.DateTime(), nullable=True),
        sa.Column('hrv_status', sa.String(20), nullable=True),
        sa.Column('hrv_peak', sa.Float(), nullable=True),
        sa.Column('resting_hr', sa.Integer(), nullable=True),
        sa.Column('avg_hr', sa.Integer(), nullable=True),
        sa.Column('avg_stress', sa.Integer(), nullable=True),
        sa.Column('max_stress', sa.Integer(), nullable=True),
        sa.Column('stress_qualifier', sa.String(50), nullable=True),
        sa.Column('body_battery_charged', sa.Integer(), nullable=True),
        sa.Column('body_battery_drained', sa.Integer(), nullable=True),
        sa.Column('steps', sa.Integer(), nullable=True),
        sa.Column('active_calories', sa.Integer(), nullable=True),
        sa.Column('moderate_intensity_minutes', sa.Integer(), nullable=True),
        sa.Column('vigorous_intensity_minutes', sa.Integer(), nullable=True),
        sa.Column('avg_spo2', sa.Float(), nullable=True),
        sa.Column('min_spo2', sa.Float(), nullable=True),
        sa.Column('raw_json', postgresql.JSONB(), nullable=True),
    )
    op.create_index('ix_garmin_daily_user_date', 'garmin_daily', ['user_id', 'date'])

    op.create_table(
        'heart_rate_intraday',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False, index=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('bpm', sa.Integer(), nullable=False),
    )
    op.create_index('ix_hr_intraday_user_date', 'heart_rate_intraday', ['user_id', 'date'])

    op.create_table(
        'garmin_activities',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('garmin_activity_id', sa.BigInteger(), unique=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False, index=True),
        sa.Column('activity_type', sa.String(100), nullable=True),
        sa.Column('duration_sec', sa.Integer(), nullable=True),
        sa.Column('avg_hr', sa.Integer(), nullable=True),
        sa.Column('max_hr', sa.Integer(), nullable=True),
        sa.Column('calories', sa.Integer(), nullable=True),
        sa.Column('training_effect', sa.Float(), nullable=True),
        sa.Column('aerobic_training_effect', sa.Float(), nullable=True),
        sa.Column('distance_meters', sa.Float(), nullable=True),
        sa.Column('hr_zones_json', postgresql.JSONB(), nullable=True),
    )

    op.create_table(
        'ai_insights',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('generated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('insight_text', sa.Text(), nullable=False),
        sa.Column('trigger_type', sa.String(50), nullable=False),
        sa.Column('metrics_snapshot_json', postgresql.JSONB(), nullable=True),
    )

    op.create_table(
        'sync_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('sync_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('status', sa.String(10), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metrics_fetched', sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_table('sync_log')
    op.drop_table('ai_insights')
    op.drop_table('garmin_activities')
    op.drop_table('heart_rate_intraday')
    op.drop_table('garmin_daily')
    op.drop_table('habit_logs')
    op.drop_table('habit_definitions')
    op.drop_table('users')
