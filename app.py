import os
from flask import Flask, current_app
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
from sqlalchemy import text, inspect

def init_database(app):
    """データベースの初期化（既存の場合はスキップ）"""
    with app.app_context():
        try:
            # Step 1: データベース接続の確認
            db.session.execute(text('SELECT 1'))
            app.logger.info("Database connection successful")
            
            # Step 2: テーブルの存在確認
            inspector = inspect(db.engine)
            existing_tables = set(inspector.get_table_names())
            app.logger.info(f"Found existing tables: {existing_tables}")
            
            # Step 3: 必要に応じてテーブルを作成
            if not existing_tables:
                # 新規データベースの場合
                db.create_all()
                create_initial_admin(app)
                app.logger.info("Database tables created and initialized")
            else:
                # 既存のデータベースの場合は何もしない
                app.logger.info("Database tables already exist")
            
        except Exception as e:
            app.logger.error(f"Database initialization error: {str(e)}")
            raise

def create_initial_admin(app):
    """Create initial admin user and settings if they don't exist"""
    from models import User, UserSettings
    try:
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com')
            admin.set_password('admin')
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

    # Initialize database
    init_database(app)

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
