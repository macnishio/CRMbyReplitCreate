# commands.py
import click
from flask.cli import with_appcontext
from extensions import db
from models import User, UserSettings
import os

@click.command('reset-db')
@with_appcontext
def reset_db_command():
    """Reset the database."""
    if click.confirm('Are you sure you want to reset the database? This will delete all data!', abort=True):
        try:
            # Drop all tables
            db.drop_all()
            click.echo('All tables dropped.')

            # Create all tables
            db.create_all()
            click.echo('All tables created.')

            # Create initial admin user if ADMIN_PASSWORD is set
            if os.environ.get('ADMIN_PASSWORD'):
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    role='admin'
                )
                admin.set_password(os.environ.get('ADMIN_PASSWORD'))
                db.session.add(admin)
                
                # Create default settings for admin
                settings = UserSettings(user=admin)
                db.session.add(settings)
                
                db.session.commit()
                click.echo('Initial admin user created.')

            click.echo('Database has been reset successfully.')

        except Exception as e:
            db.session.rollback()
            click.echo(f'Error resetting database: {str(e)}', err=True)