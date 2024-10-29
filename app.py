import os
import socket
from flask import Flask,render_template
from config import config
from extensions import db, migrate, login_manager, mail, limiter
from email_receiver import setup_email_scheduler
import logging
from sqlalchemy import text
from db_utils import init_database
from sqlalchemy.exc import SQLAlchemyError
from commands import reset_db_command
from datetime import datetime

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Set up logging with more detailed configuration
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )

    # Upload folder configuration
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'UPLOAD_FOLDER')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    # Register CLI commands
    app.cli.add_command(reset_db_command)

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

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        db.session.rollback()
        app.logger.error(f"Database error: {str(error)}")
        return render_template('errors/500.html'), 500

    # Context processors
    @app.context_processor
    def utility_processor():
        return {
            'now': datetime.utcnow,
            'format_date': lambda x: x.strftime('%Y-%m-%d %H:%M') if x else ''
        }

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