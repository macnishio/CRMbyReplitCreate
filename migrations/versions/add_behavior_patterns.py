"""Add behavior_patterns field to Lead model

Revision ID: add_behavior_patterns
Revises: 
Create Date: 2024-11-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'add_behavior_patterns'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('leads', sa.Column('behavior_patterns', JSONB, nullable=True))

def downgrade():
    op.drop_column('leads', 'behavior_patterns')
