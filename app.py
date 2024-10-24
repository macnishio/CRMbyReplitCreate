import os
from flask import Flask
from config import config
from extensions import db, migrate, login_manager, mail, limiter
from email_receiver import setup_email_scheduler
import logging
from sqlalchemy import text
from db_utils import init_database

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Set up logging
    logging.basicConfig(level=app.config['LOG_LEVEL'])
    app.logger.debug(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[0]}@[REDACTED]")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    # Initialize database
    init_database(app)

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

    # Set up email scheduler
    setup_email_scheduler(app)

    return app

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
