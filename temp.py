"""add message_id to emails

Revision ID: xxxxxxxxxxxxx
Revises: xxxxxxxxxxxxx
Create Date: 2024-XX-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('emails', sa.Column('message_id', sa.String(length=255), nullable=True))
    op.create_unique_constraint('uq_emails_message_id', 'emails', ['message_id'])
    # ### end Alembic commands ###

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('uq_emails_message_id', 'emails', type_='unique')
    op.drop_column('emails', 'message_id')
    # ### end Alembic commands ###