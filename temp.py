"""Add google calendar columns

Revision ID: 9c91270c5bb1
Create Date: 2024-10-27 14:21:36.032880
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add google_calendar_id column to users table
    op.add_column('users', sa.Column('google_calendar_id', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('google_service_account_file', sa.String(length=255), nullable=True))

def downgrade():
    # Remove the columns if needed to rollback
    op.drop_column('users', 'google_calendar_id')
    op.drop_column('users', 'google_service_account_file')