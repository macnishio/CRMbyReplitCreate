"""Add EmailFetchTracker model

Revision ID: 1b9c16acf4cb
Revises: 7eebfe037d4a
Create Date: 2024-09-26 14:47:06.412351

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1b9c16acf4cb'
down_revision = '7eebfe037d4a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('email_fetch_tracker',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('last_fetch_time', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('email_fetch_tracker')
    # ### end Alembic commands ###