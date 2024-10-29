"""Add named constraints and AI fields

Revision ID: 69f071b161c1
Revises: 33b452a9bba3
Create Date: 2024-10-28 16:12:12.882284

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '69f071b161c1'
down_revision = '33b452a9bba3'
branch_labels = None
depends_on = None

def upgrade():
    # Add AI analysis fields to emails
    with op.batch_alter_table('emails', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ai_analysis', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('ai_analysis_date', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('ai_model_used', sa.String(length=50), nullable=True))

    # Add fields to tasks (2段階で実装)
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        # 1. まず nullable な列を追加
        batch_op.add_column(sa.Column('email_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_ai_generated', sa.Boolean(), nullable=True))
        
    # 既存のレコードにデフォルト値を設定
    op.execute(text("UPDATE tasks SET is_ai_generated = false WHERE is_ai_generated IS NULL"))
    
    # NOT NULL制約を追加
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.alter_column('is_ai_generated',
                            existing_type=sa.Boolean(),
                            nullable=False,
                            server_default=sa.text('false'))
        batch_op.create_foreign_key('fk_tasks_email_id', 'emails', ['email_id'], ['id'])

    # Add fields to schedules (2段階で実装)
    with op.batch_alter_table('schedules', schema=None) as batch_op:
        # 1. まず nullable な列を追加
        batch_op.add_column(sa.Column('email_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_ai_generated', sa.Boolean(), nullable=True))
        
    # 既存のレコードにデフォルト値を設定
    op.execute(text("UPDATE schedules SET is_ai_generated = false WHERE is_ai_generated IS NULL"))
    
    # NOT NULL制約を追加
    with op.batch_alter_table('schedules', schema=None) as batch_op:
        batch_op.alter_column('is_ai_generated',
                            existing_type=sa.Boolean(),
                            nullable=False,
                            server_default=sa.text('false'))
        batch_op.create_foreign_key('fk_schedules_email_id', 'emails', ['email_id'], ['id'])

def downgrade():
    # Remove constraints and columns from schedules
    with op.batch_alter_table('schedules', schema=None) as batch_op:
        batch_op.drop_constraint('fk_schedules_email_id', type_='foreignkey')
        batch_op.drop_column('is_ai_generated')
        batch_op.drop_column('email_id')

    # Remove constraints and columns from tasks
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_constraint('fk_tasks_email_id', type_='foreignkey')
        batch_op.drop_column('is_ai_generated')
        batch_op.drop_column('email_id')

    # Remove columns from emails
    with op.batch_alter_table('emails', schema=None) as batch_op:
        batch_op.drop_column('ai_model_used')
        batch_op.drop_column('ai_analysis_date')
        batch_op.drop_column('ai_analysis')