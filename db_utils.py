from extensions import db
from models import User, UserSettings
import os
import logging
from sqlalchemy import inspect, text
from functools import wraps
from sqlalchemy.exc import OperationalError
from time import sleep
from flask import current_app

__all__ = ['retry_on_exception', 'init_database']

def reset_database():
    """Reset the database"""
    with current_app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        current_app.logger.info("Database has been reset")

def retry_on_exception(retries=3, delay=1):
    """Decorator to retry database operations on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if attempt == retries - 1:
                        raise
                    sleep(delay)
        return wrapper
    return decorator

def create_initial_admin(app):
    """Create initial admin user and settings if they don't exist"""
    try:
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com')
            admin.set_password(os.environ.get('INITIAL_ADMIN_PASSWORD', 'admin'))
            db.session.add(admin)
            db.session.flush()

            # Create user settings with environment variables
            settings = UserSettings(
                user_id=admin.id,
                mail_server=os.environ.get('MAIL_SERVER'),
                mail_port=int(os.environ.get('MAIL_PORT', 587)),
                mail_use_tls=os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true',
                mail_username=os.environ.get('MAIL_USERNAME'),
                mail_password=os.environ.get('MAIL_PASSWORD'),
                claude_api_key=os.environ.get('CLAUDE_API_KEY'),
                clearbit_api_key=os.environ.get('CLEARBIT_API_KEY')
            )
            db.session.add(settings)
            db.session.commit()
            app.logger.info("Admin user and settings created successfully")
        else:
            app.logger.info("Admin user already exists")
    except Exception as e:
        app.logger.error(f"Error creating admin user: {str(e)}")
        db.session.rollback()
        raise

@retry_on_exception(retries=3, delay=1)
def init_database(app):
    """Initialize database safely without recreation if tables exist"""
    with app.app_context():
        try:
            # Check database connection
            db.session.execute(text('SELECT 1'))
            app.logger.info("Database connection successful")
            
            # Check existing tables
            inspector = inspect(db.engine)
            existing_tables = set(inspector.get_table_names())
            
            if not existing_tables:
                # Only create tables if none exist
                #db.create_all()
                create_initial_admin(app)
                app.logger.info("Database initialized with initial data")
            else:
                app.logger.info("Database tables already exist")
            return True
        except Exception as e:
            app.logger.error(f"Database initialization error: {str(e)}")
            return False
