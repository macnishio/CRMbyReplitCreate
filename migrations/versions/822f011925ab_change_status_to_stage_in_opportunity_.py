"""Change status to stage in Opportunity model

Revision ID: 822f011925ab
Revises: 5a14c4c9f0b9
Create Date: 2024-09-27 11:51:57.360734

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection

# リビジョン識別子
revision = '822f011925ab'
down_revision = '5a14c4c9f0b9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('leads_email_key', 'leads', type_='unique')
    op.create_unique_constraint('uq_leads_email', 'leads', ['email'], condition=sa.text('email IS NOT NULL'))
    # ### end Alembic commands ###

    
    bind = op.get_bind()
    inspector = reflection.Inspector.from_engine(bind)

    # 外部キー制約を削除（存在する場合のみ）
    constraints = [
        ('schedules', 'schedules_user_id_fkey'),
        ('schedules', 'schedules_account_id_fkey'),
        ('schedules', 'schedules_lead_id_fkey'),
        ('schedules', 'schedules_opportunity_id_fkey'),
        ('tasks', 'tasks_user_id_fkey'),
        ('tasks', 'tasks_account_id_fkey'),
        ('tasks', 'tasks_lead_id_fkey'),
        ('tasks', 'tasks_opportunity_id_fkey'),
        ('emails', 'emails_lead_id_fkey'),
        ('opportunities', 'opportunities_user_id_fkey'),
        ('opportunities', 'opportunities_account_id_fkey'),
        ('opportunities', 'opportunities_lead_id_fkey'),
        ('leads', 'leads_user_id_fkey'),
        ('accounts', 'accounts_user_id_fkey'),
    ]

    for table_name, constraint_name in constraints:
        if table_name in inspector.get_table_names():
            fk_constraints = inspector.get_foreign_keys(table_name)
            for fk in fk_constraints:
                if fk['name'] == constraint_name:
                    op.drop_constraint(constraint_name, table_name, type_='foreignkey')
                    break

    # テーブルを削除（存在する場合のみ）
    tables_to_drop = [
        'schedules', 'tasks', 'unknown_emails', 'emails',
        'opportunities', 'leads', 'accounts', 'email_fetch_tracker', 'users'
    ]

    for table_name in tables_to_drop:
        if table_name in inspector.get_table_names():
            op.drop_table(table_name)

    # テーブルを再作成（存在しない場合のみ）
    if 'users' not in inspector.get_table_names():
        op.create_table('users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('username', sa.String(length=255), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('password_hash', sa.String(length=512), nullable=False),
            sa.Column('role', sa.String(length=20), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email'),
            sa.UniqueConstraint('username')
        )

    if 'accounts' not in inspector.get_table_names():
        op.create_table('accounts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('industry', sa.String(length=50), nullable=False),
            sa.Column('website', sa.String(length=120), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )

    if 'leads' not in inspector.get_table_names():
        op.create_table('leads',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('email', sa.String(length=120), nullable=False),
            sa.Column('phone', sa.String(length=20), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('last_contact', sa.DateTime(), nullable=False),
            sa.Column('last_followup_email', sa.DateTime(), nullable=True),
            sa.Column('last_followup_tracking_id', sa.String(length=36), nullable=True),
            sa.Column('last_email_opened', sa.DateTime(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('score', sa.Float(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )

    if 'opportunities' not in inspector.get_table_names():
        op.create_table('opportunities',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('stage', sa.String(length=50), nullable=False),
            sa.Column('close_date', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('account_id', sa.Integer(), nullable=False),
            sa.Column('lead_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['account_id'], ['accounts.id']),
            sa.ForeignKeyConstraint(['lead_id'], ['leads.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )

    if 'emails' not in inspector.get_table_names():
        op.create_table('emails',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('sender', sa.String(length=255), nullable=False),
            sa.Column('subject', sa.String(length=255), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('received_at', sa.DateTime(), nullable=False),
            sa.Column('lead_id', sa.Integer(), nullable=False),
            sa.Column('sender_name', sa.String(length=255), nullable=True),
            sa.ForeignKeyConstraint(['lead_id'], ['leads.id']),
            sa.PrimaryKeyConstraint('id')
        )

    if 'unknown_emails' not in inspector.get_table_names():
        op.create_table('unknown_emails',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('sender', sa.String(length=255), nullable=False),
            sa.Column('subject', sa.String(length=255), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('received_at', sa.DateTime(), nullable=False),
            sa.Column('sender_name', sa.String(length=255), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    if 'tasks' not in inspector.get_table_names():
        op.create_table('tasks',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('due_date', sa.DateTime(), nullable=False),
            sa.Column('completed', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('lead_id', sa.Integer(), nullable=True),
            sa.Column('opportunity_id', sa.Integer(), nullable=True),
            sa.Column('account_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['account_id'], ['accounts.id']),
            sa.ForeignKeyConstraint(['lead_id'], ['leads.id']),
            sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )

    if 'schedules' not in inspector.get_table_names():
        op.create_table('schedules',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('start_time', sa.DateTime(), nullable=False),
            sa.Column('end_time', sa.DateTime(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('account_id', sa.Integer(), nullable=True),
            sa.Column('lead_id', sa.Integer(), nullable=True),
            sa.Column('opportunity_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['account_id'], ['accounts.id']),
            sa.ForeignKeyConstraint(['lead_id'], ['leads.id']),
            sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )

    if 'email_fetch_tracker' not in inspector.get_table_names():
        op.create_table('email_fetch_tracker',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('last_fetch_time', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade():
    bind = op.get_bind()
    inspector = reflection.Inspector.from_engine(bind)

    # テーブルを削除（存在する場合のみ）
    tables_to_drop = [
        'schedules', 'tasks', 'unknown_emails', 'emails',
        'opportunities', 'leads', 'accounts', 'email_fetch_tracker', 'users'
    ]

    for table_name in tables_to_drop:
        if table_name in inspector.get_table_names():
            op.drop_table(table_name)

    # 元のテーブルを再作成（存在しない場合のみ）
    if 'users' not in inspector.get_table_names():
        op.create_table('users',
            sa.Column('id', sa.Integer(), server_default=sa.text("nextval('users_id_seq'::regclass)"), autoincrement=True, nullable=False),
            sa.Column('username', sa.String(length=255), autoincrement=False, nullable=False),
            sa.Column('email', sa.String(length=255), autoincrement=False, nullable=False),
            sa.Column('password_hash', sa.String(length=512), autoincrement=False, nullable=False),
            sa.Column('role', sa.String(length=20), autoincrement=False, nullable=False),
            sa.PrimaryKeyConstraint('id', name='users_pkey'),
            sa.UniqueConstraint('email', name='users_email_key'),
            sa.UniqueConstraint('username', name='users_username_key'),
            postgresql_ignore_search_path=False
        )

    if 'email_fetch_tracker' not in inspector.get_table_names():
        op.create_table('email_fetch_tracker',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('last_fetch_time', sa.TIMESTAMP(), autoincrement=False, nullable=False),
            sa.PrimaryKeyConstraint('id', name='email_fetch_tracker_pkey')
        )

    if 'accounts' not in inspector.get_table_names():
        op.create_table('accounts',
            sa.Column('id', sa.Integer(), server_default=sa.text("nextval('accounts_id_seq'::regclass)"), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(length=100), autoincrement=False, nullable=False),
            sa.Column('industry', sa.String(length=50), autoincrement=False, nullable=False),
            sa.Column('website', sa.String(length=120), autoincrement=False, nullable=False),
            sa.Column('created_at', sa.TIMESTAMP(), autoincrement=False, nullable=False),
            sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='accounts_user_id_fkey'),
            sa.PrimaryKeyConstraint('id', name='accounts_pkey'),
            postgresql_ignore_search_path=False
        )

    if 'leads' not in inspector.get_table_names():
        op.create_table('leads',
            sa.Column('id', sa.Integer(), server_default=sa.text("nextval('leads_id_seq'::regclass)"), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(length=100), autoincrement=False, nullable=False),
            sa.Column('email', sa.String(length=120), autoincrement=False, nullable=False),
            sa.Column('phone', sa.String(length=20), autoincrement=False, nullable=False),
            sa.Column('status', sa.String(length=20), autoincrement=False, nullable=False),
            sa.Column('created_at', sa.TIMESTAMP(), autoincrement=False, nullable=False),
            sa.Column('last_contact', sa.TIMESTAMP(), autoincrement=False, nullable=False),
            sa.Column('last_followup_email', sa.TIMESTAMP(), autoincrement=False, nullable=True),
            sa.Column('last_followup_tracking_id', sa.String(length=36), autoincrement=False, nullable=True),
            sa.Column('last_email_opened', sa.TIMESTAMP(), autoincrement=False, nullable=True),
            sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=False),
            sa.Column('score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='leads_user_id_fkey'),
            sa.PrimaryKeyConstraint('id', name='leads_pkey'),
            postgresql_ignore_search_path=False
        )

    if 'opportunities' not in inspector.get_table_names():
        op.create_table('opportunities',
            sa.Column('id', sa.Integer(), server_default=sa.text("nextval('opportunities_id_seq'::regclass)"), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(length=255), autoincrement=False, nullable=False),
            sa.Column('amount', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
            sa.Column('status', sa.String(length=50), autoincrement=False, nullable=False),
            sa.Column('close_date', sa.TIMESTAMP(), autoincrement=False, nullable=False),
            sa.Column('created_at', sa.TIMESTAMP(), autoincrement=False, nullable=False),
            sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=False),
            sa.Column('account_id', sa.Integer(), autoincrement=False, nullable=False),
            sa.Column('lead_id', sa.Integer(), autoincrement=False, nullable=True),
            sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name='opportunities_account_id_fkey'),
            sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], name='opportunities_lead_id_fkey'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='opportunities_user_id_fkey'),
            sa.PrimaryKeyConstraint('id', name='opportunities_pkey'),
            postgresql_ignore_search_path=False
        )

    if 'emails' not in inspector.get_table_names():
        op.create_table('emails',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('sender', sa.String(length=255), autoincrement=False, nullable=False),
            sa.Column('subject', sa.String(length=255), autoincrement=False, nullable=False),
            sa.Column('content', sa.Text(), autoincrement=False, nullable=False),
            sa.Column('received_at', sa.TIMESTAMP(), autoincrement=False, nullable=False),
            sa.Column('lead_id', sa.Integer(), autoincrement=False, nullable=False),
            sa.Column('sender_name', sa.String(length=255), autoincrement=False, nullable=True),
            sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], name='emails_lead_id_fkey'),
            sa.PrimaryKeyConstraint('id', name='emails_pkey')
        )

    if 'unknown_emails' not in inspector.get_table_names():
        op.create_table('unknown_emails',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('sender', sa.String(length=255), autoincrement=False, nullable=False),
            sa.Column('subject', sa.String(length=255), autoincrement=False, nullable=False),
            sa.Column('content', sa.Text(), autoincrement=False, nullable=False),
            sa.Column('received_at', sa.TIMESTAMP(), autoincrement=False, nullable=False),
            sa.Column('sender_name', sa.String(length=255), autoincrement=False, nullable=True),
            sa.PrimaryKeyConstraint('id', name='unknown_emails_pkey')
        )

    if 'tasks' not in inspector.get_table_names():
        op.create_table('tasks',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('title', sa.String(length=255), autoincrement=False, nullable=False),
            sa.Column('description', sa.Text(), autoincrement=False, nullable=False),
            sa.Column('due_date', sa.TIMESTAMP(), autoincrement=False, nullable=False),
            sa.Column('completed', sa.Boolean(), autoincrement=False, nullable=False),
            sa.Column('created_at', sa.TIMESTAMP(), autoincrement=False, nullable=False),
            sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=False),
            sa.Column('lead_id', sa.Integer(), autoincrement=False, nullable=True),
            sa.Column('opportunity_id', sa.Integer(), autoincrement=False, nullable=True),
            sa.Column('account_id', sa.Integer(), autoincrement=False, nullable=True),
            sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name='tasks_account_id_fkey'),
            sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], name='tasks_lead_id_fkey'),
            sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], name='tasks_opportunity_id_fkey'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='tasks_user_id_fkey'),
            sa.PrimaryKeyConstraint('id', name='tasks_pkey')
        )

    if 'schedules' not in inspector.get_table_names():
        op.create_table('schedules',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('title', sa.String(length=255), autoincrement=False, nullable=False),
            sa.Column('description', sa.Text(), autoincrement=False, nullable=False),
            sa.Column('start_time', sa.TIMESTAMP(), autoincrement=False, nullable=False),
            sa.Column('end_time', sa.TIMESTAMP(), autoincrement=False, nullable=False),
            sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=False),
            sa.Column('account_id', sa.Integer(), autoincrement=False, nullable=True),
            sa.Column('lead_id', sa.Integer(), autoincrement=False, nullable=True),
            sa.Column('opportunity_id', sa.Integer(), autoincrement=False, nullable=True),
            sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name='schedules_account_id_fkey'),
            sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], name='schedules_lead_id_fkey'),
            sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], name='schedules_opportunity_id_fkey'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='schedules_user_id_fkey'),
            sa.PrimaryKeyConstraint('id', name='schedules_pkey')
        )