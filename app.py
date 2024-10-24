# app.py

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from config import config
from extensions import db, migrate, login_manager, mail, limiter, cache
from email_receiver import setup_email_scheduler
from sqlalchemy import text
from db_utils import init_database
from flask_wtf.csrf import CSRFProtect

def create_app(config_name='default'):
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Set up logging
    setup_logging(app)
    app.logger.info("Starting application...")
    app.logger.debug(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[0]}@[REDACTED]")

    # Initialize security
    csrf = CSRFProtect()
    csrf.init_app(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)

    # Initialize database
    with app.app_context():
        init_database(app)

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    register_blueprints(app)

    # Set up email scheduler
    if not app.config.get('TESTING'):
        setup_email_scheduler(app)

    # Set security headers
    setup_security_headers(app)

    return app

def setup_logging(app):
    """Set up logging configuration"""
    log_level = app.config['LOG_LEVEL']
    log_format = app.config['LOG_FORMAT']

    formatter = logging.Formatter(log_format)

    # Configure root logger
    logging.basicConfig(level=log_level)

    if not app.debug and not app.testing:
        # File handler
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)

        # Stderr handler
        stderr_handler = logging.StreamHandler()
        stderr_handler.setFormatter(formatter)
        stderr_handler.setLevel(logging.ERROR)
        app.logger.addHandler(stderr_handler)

def register_blueprints(app):
    """Register Flask blueprints"""
    from routes import (
        main, auth, leads, opportunities, accounts, reports,
        tracking, mobile, schedules, tasks, settings
    )

    blueprints = {
        main.bp: '/',
        auth.bp: '/auth',
        leads.bp: '/leads',
        opportunities.bp: '/opportunities',
        accounts.bp: '/accounts',
        reports.bp: '/reports',
        tracking.bp: '/tracking',
        mobile.bp: '/mobile',
        schedules.bp: '/schedules',
        tasks.tasks_bp: '/tasks',
        settings.bp: '/settings'
    }

    for blueprint, url_prefix in blueprints.items():
        app.register_blueprint(blueprint, url_prefix=url_prefix)
        app.logger.debug(f"Registered blueprint: {blueprint.name} at {url_prefix}")

def register_error_handlers(app):
    """Register error handlers"""

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f"Page not found: {error}")
        return {'error': 'Not Found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Server error: {error}")
        db.session.rollback()
        return {'error': 'Internal Server Error'}, 500

def setup_security_headers(app):
    """Configure security headers"""
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Content Security Policy
        csp = '; '.join(f"{key} {value}" for key, value in app.config['CONTENT_SECURITY_POLICY'].items())
        response.headers['Content-Security-Policy'] = csp

        return response

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'default'))
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)