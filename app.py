import os
from flask import Flask, current_app
from flask_login import LoginManager, login_required, current_user
from extensions import db, mail, scheduler
from models import User, Lead
from config import Config
import logging
from logging.handlers import RotatingFileHandler
from flask_migrate import Migrate
from email_utils import send_follow_up_email

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    mail.init_app(app)
    app.config['MAIL_DEBUG'] = True
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

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(leads_bp)
    app.register_blueprint(opportunities_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(tracking_bp)

    with app.app_context():
        migrate = Migrate(app, db)
        migrate.init_app(app, db)
        db.create_all()

    # Set up the scheduler job for automated follow-ups
    from email_utils import send_automated_follow_ups
    scheduler.add_job(id='send_automated_follow_ups', func=send_automated_follow_ups, trigger='interval', hours=24)
    app.logger.info("Scheduled automated follow-ups job")

    # Add a test route for triggering automated follow-ups (without authentication)
    @app.route('/test_followups')
    def test_followups():
        current_app.logger.info("Manually triggering automated follow-ups")
        try:
            send_automated_follow_ups()
            current_app.logger.info("Automated follow-ups triggered successfully")
            return "Automated follow-ups triggered manually. Check logs for details."
        except Exception as e:
            current_app.logger.error(f"Error triggering automated follow-ups: {str(e)}")
            return f"Error triggering automated follow-ups: {str(e)}", 500

    # Add a test route for sending a single follow-up email (without authentication)
    @app.route('/test_single_email/<int:lead_id>')
    def test_single_email(lead_id):
        lead = Lead.query.get_or_404(lead_id)
        try:
            send_follow_up_email(lead)
            current_app.logger.info(f"Test email sent to {lead.email}")
            return f"Test email sent to {lead.email}. Check logs for details."
        except Exception as e:
            current_app.logger.error(f"Error sending test email: {str(e)}")
            return f"Error sending test email: {str(e)}", 500

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
