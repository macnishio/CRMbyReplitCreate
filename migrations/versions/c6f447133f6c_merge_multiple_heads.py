"""merge multiple heads

Revision ID: c6f447133f6c
Revises: add_behavior_patterns, ce6002972798
Create Date: 2024-11-27 07:54:17.057293

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c6f447133f6c'
down_revision = ('add_behavior_patterns', 'ce6002972798')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
