import os
from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_talisman import Talisman
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from logging.handlers import RotatingFileHandler
from extensions import db, mail, scheduler, cache, init_app
from email_receiver import setup_email_scheduler
from routes.auth import bp as auth_bp

logging.basicConfig(level=logging.DEBUG)
load_dotenv()


def create_app():
    from models import User
    from config import config
    from email_utils import send_automated_follow_ups

    app = Flask(__name__)
    app.config['SQLALCHEMY_ECHO'] = True
    env = 'production' if os.environ.get('FLASK_DEBUG') != 'True' else 'development'
    app.config.from_object(config[env])
    config[env].init_app(app)

    init_app(app)  # 拡張機能の初期化を一括で行う

    app.config['SCHEDULER_API_ENABLED'] = False

    limiter = Limiter(get_remote_address,
                      app=app,
                      default_limits=["200 per day", "50 per hour"],
                      storage_uri="memory://")

    csp = {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        'style-src': "'self' 'unsafe-inline'",
        'img-src': "'self' data:",
        'font-src': "'self'",
        'form-action': "'self'",
        'frame-ancestors': "'none'",
    }
    Talisman(app, content_security_policy=csp, force_https=True)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from routes import main, leads, opportunities, accounts, reports, tracking, mobile, schedules, tasks

    app.register_blueprint(main.bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(leads.bp)
    app.register_blueprint(opportunities.bp)
    app.register_blueprint(accounts.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(tracking.bp)
    app.register_blueprint(mobile.bp)
    app.register_blueprint(schedules.bp)
    app.register_blueprint(tasks.bp)

    migrate = Migrate(app, db)  # 必要に応じてextensions.py内で初期化

    scheduler.add_job(id='send_automated_follow_ups',
                      func=send_automated_follow_ups,
                      trigger='interval',
                      hours=24)
    app.logger.info("Scheduled automated follow-ups job")

    setup_email_scheduler(app)

    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/crm.log',
                                           maxBytes=10240,
                                           backupCount=10)
        file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('CRM startup')

    @app.route('/dashboard')
    def dashboard():
        leads = 100
        opportunities = 50
        accounts = 30
        return render_template('dashboard.html',
                               leads=leads,
                               opportunities=opportunities,
                               accounts=accounts)

    return app


app = create_app()

if __name__ == '__main__':
    with app.app_context():
        app.logger.info('Starting scheduler')
        scheduler.start()
        app.logger.info('Scheduler started')

    app.run(host='0.0.0.0', port=5000)
