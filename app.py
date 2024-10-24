import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import config
from extensions import db, migrate, login_manager, mail, limiter
from email_receiver import fetch_emails, connect_to_email_server, setup_email_scheduler
import logging
from sqlalchemy import inspect

def init_database(app):
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            if not inspector.get_table_names():
                db.create_all()
                create_initial_admin(app)
                app.logger.info("Database initialized successfully")
            else:
                app.logger.info("Database tables already exist")
        except Exception as e:
            app.logger.error(f"Database initialization error: {str(e)}")
            raise

def create_initial_admin(app):
    from models import User, UserSettings
    try:
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com')
            admin.set_password('admin')
            db.session.add(admin)
            db.session.flush()

            # Create user settings
            settings = UserSettings(
                user_id=admin.id,
                mail_server=os.environ.get('MAIL_SERVER', 'smtp.example.com'),
                mail_port=int(os.environ.get('MAIL_PORT', 587)),
                mail_use_tls=os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true',
                mail_username=os.environ.get('MAIL_USERNAME', 'test@example.com'),
                mail_password=os.environ.get('MAIL_PASSWORD', 'password123')
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

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Set up logging
    logging.basicConfig(level=app.config['LOG_LEVEL'])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    # Debug logging for database URL
    app.logger.debug(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[0]}@[REDACTED]")

    # Initialize database
    init_database(app)

    # Set CLAUDE_API_KEY in app.config
    app.config['CLAUDE_API_KEY'] = os.environ.get('CLAUDE_API_KEY')
    if app.config['CLAUDE_API_KEY']:
        app.logger.info("CLAUDE_API_KEY is set in app.config")
    else:
        app.logger.error("CLAUDE_API_KEY is missing from environment variables")

    # Register blueprints
    from routes import main, auth, leads, opportunities, accounts, reports, tracking, mobile, schedules, tasks, settings
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(leads.bp)
    app.register_blueprint(opportunities.bp)
    app.register_blueprint(accounts.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(tracking.bp)
    app.register_blueprint(mobile.bp)
    app.register_blueprint(schedules.bp)
    app.register_blueprint(tasks.tasks_bp, url_prefix='/tasks')
    app.register_blueprint(settings.bp)

    # Set up email scheduler
    setup_email_scheduler(app)

    return app

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return db.session.get(User, int(user_id))

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
