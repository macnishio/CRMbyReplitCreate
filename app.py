import os
from flask import Flask, current_app
from flask_login import LoginManager
from extensions import db, mail, scheduler
from models import User
from config import Config
import logging
from logging.handlers import RotatingFileHandler
from flask_migrate import Migrate
from email_utils import send_automated_follow_ups

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    mail.init_app(app)
    scheduler.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.main import bp as main_bp
    from routes.auth import bp as auth_bp
    from routes.leads import bp as leads_bp
    from routes.opportunities import bp as opportunities_bp
    from routes.accounts import bp as accounts_bp
    from routes.reports import bp as reports_bp
    from routes.tracking import bp as tracking_bp
    from routes.mobile import bp as mobile_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(leads_bp)
    app.register_blueprint(opportunities_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(tracking_bp)
    app.register_blueprint(mobile_bp)

    with app.app_context():
        migrate = Migrate(app, db)
        migrate.init_app(app, db)
        db.create_all()

    # Set up the scheduler job for automated follow-ups
    scheduler.add_job(id='send_automated_follow_ups', func=send_automated_follow_ups, trigger='interval', hours=24)
    app.logger.info("Scheduled automated follow-ups job")

    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/crm.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('CRM startup')

    return app

app = create_app()

if __name__ == '__main__':
    app.logger.info('Starting scheduler')
    scheduler.start()
    app.logger.info('Scheduler started')
    app.run(host='0.0.0.0', port=5000)
