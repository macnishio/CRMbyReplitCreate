"""Add created_at to Email model

Revision ID: add_created_at_to_email
Revises: 
Create Date: 2024-11-24 00:13:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_created_at_to_email'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add created_at column with a default value for existing records
    op.add_column('emails', 
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')))

def downgrade():
    op.drop_column('emails', 'created_at')
