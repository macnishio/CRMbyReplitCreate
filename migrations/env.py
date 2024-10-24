from __future__ import with_statement

import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context
from sqlalchemy import engine_from_config, pool, inspect

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

def get_engine():
    try:
        # this works with Flask-SQLAlchemy<3 and Alchemical
        return current_app.extensions['migrate'].db.get_engine()
    except TypeError:
        # this works with Flask-SQLAlchemy>=3
        return current_app.extensions['migrate'].db.engine

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
config.set_main_option(
    'sqlalchemy.url', str(get_engine().url).replace('%', '%%'))
target_metadata = current_app.extensions['migrate'].db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    
    # Get existing tables before migration
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            
            # Get list of existing tables
            inspector = inspect(get_engine())
            existing_tables = set(inspector.get_table_names())
            
            # Filter out operations for existing tables
            for op in script.upgrade_ops.ops[:]:
                if hasattr(op, 'table_name') and op.table_name in existing_tables:
                    script.upgrade_ops.ops.remove(op)
                    logger.info(f"Skipping table creation for existing table: {op.table_name}")

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
