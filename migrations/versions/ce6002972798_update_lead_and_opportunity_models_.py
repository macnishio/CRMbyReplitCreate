"""Update Lead and Opportunity models relationships

Revision ID: ce6002972798
Revises: f66935b4237f
Create Date: 2024-11-25 20:12:07.487036

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce6002972798'
down_revision = 'f66935b4237f'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    with op.batch_alter_table('leads', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_followup_tracking_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('last_email_opened', sa.DateTime(), nullable=True))
    with op.batch_alter_table('opportunities', schema=None) as batch_op:
        existing_columns = [column['name'] for column in inspector.get_columns('opportunities')]

        if 'created_at' not in existing_columns:
            batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))
        if 'updated_at' not in existing_columns:
            batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))
def downgrade():
    with op.batch_alter_table('opportunities', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('created_at')
    with op.batch_alter_table('leads', schema=None) as batch_op:
        batch_op.drop_column('last_email_opened')
        batch_op.drop_column('last_followup_tracking_id')
        
    # ### end Alembic commands ###
