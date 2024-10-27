import os
import socket
from flask import Flask
from config import config
from extensions import db, migrate, login_manager, mail, limiter
from email_receiver import setup_email_scheduler
import logging
from sqlalchemy import text
from db_utils import init_database
from sqlalchemy.exc import SQLAlchemyError

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Set up logging with more detailed configuration
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    # Initialize database with error handling
    with app.app_context():
        try:
            init_database(app)
        except SQLAlchemyError as e:
            app.logger.error(f"Database initialization error: {str(e)}")
            raise

    # Register blueprints
    from routes import main, auth, leads, opportunities, accounts, reports
    from routes import tracking, mobile, schedules, tasks, settings
    
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

    # Set up email scheduler in a non-blocking way
    setup_email_scheduler(app)

    return app

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

def cleanup_socket(port):
    """Cleanup any existing socket binding"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', port))
        s.close()
    except Exception as e:
        logging.error(f"Socket cleanup error: {str(e)}")

if __name__ == '__main__':
    app = create_app()
    port = 5000
    
    # Cleanup socket before starting
    cleanup_socket(port)
    
    try:
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logging.error(f"Failed to start Flask server: {str(e)}")
        raise
