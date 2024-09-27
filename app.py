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
from email_receiver import setup_email_scheduler
import logging

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

    # Debug logging for CLAUDE_API_KEY presence
    if 'CLAUDE_API_KEY' in os.environ:
        app.logger.info("CLAUDE_API_KEY is present in environment variables")
        # Log the first few characters of the key for verification (never log the full key)
        app.logger.debug(f"CLAUDE_API_KEY starts with: {os.environ['CLAUDE_API_KEY'][:5]}...")
    else:
        app.logger.error("CLAUDE_API_KEY is missing from environment variables")

    # Ensure CLAUDE_API_KEY is set in app.config
    app.config['CLAUDE_API_KEY'] = os.environ.get('CLAUDE_API_KEY')
    if app.config['CLAUDE_API_KEY']:
        app.logger.info("CLAUDE_API_KEY is set in app.config")
    else:
        app.logger.error("CLAUDE_API_KEY is not set in app.config")

    # Register blueprints
    from routes import main, auth, leads, opportunities, accounts, reports, tracking, mobile, schedules, tasks
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(leads.bp)
    app.register_blueprint(opportunities.bp)
    app.register_blueprint(accounts.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(tracking.bp)
    app.register_blueprint(mobile.bp)
    app.register_blueprint(schedules.bp)
    app.register_blueprint(tasks.bp)

    # Set up email scheduler
    with app.app_context():
        setup_email_scheduler(app)

    return app

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return db.session.get(User, int(user_id))

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
