"""Add sender_name to Email and UnknownEmail models

Revision ID: 7eebfe037d4a
Revises: c5dace7740a7
Create Date: 2024-09-25 17:25:16.936623

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7eebfe037d4a'
down_revision = 'c5dace7740a7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('emails', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sender_name', sa.String(length=255), nullable=True))

    with op.batch_alter_table('unknown_emails', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sender_name', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('unknown_emails', schema=None) as batch_op:
        batch_op.drop_column('sender_name')

    with op.batch_alter_table('emails', schema=None) as batch_op:
        batch_op.drop_column('sender_name')

    # ### end Alembic commands ###