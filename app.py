import os
import socket
from flask import Flask, render_template, current_app
from config import config
from extensions import db, migrate, login_manager, mail, limiter
from email_receiver import setup_email_scheduler
import logging
from sqlalchemy import text
from db_utils import init_database
from sqlalchemy.exc import SQLAlchemyError
from commands import reset_db_command
from datetime import datetime

# モデルのインポート
from models import (
    User, Lead, Task, Email, Schedule, 
    Opportunity, Account, SubscriptionPlan, 
    Subscription, UserSettings
)

def create_app(config_name: str = 'default') -> Flask:
    """アプリケーションファクトリ関数"""
    app = Flask(__name__, 
        static_url_path='/static',
        static_folder='static'
    )
    
    # 基本設定とロギングの初期化
    _initialize_config(app, config_name)
    _initialize_logging()
    
    # 各コンポーネントの初期化
    _initialize_components(app)
    
    # エラーハンドラとコンテキストプロセッサの設定
    _setup_error_handlers(app)
    _setup_context_processors(app)
    
    return app

def _initialize_config(app: Flask, config_name: str) -> None:
    """設定の初期化"""
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

def _initialize_logging() -> None:
    """ロギングの初期化"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )

def _initialize_components(app: Flask) -> None:
    """各コンポーネントの初期化"""
    # 拡張機能の初期化を最初に行う
    _initialize_extensions(app)
    
    # データベースコンポーネントの初期化
    _initialize_database_components(app)
    
    # ブループリントの登録
    _register_blueprints(app)
    
    # メールスケジューラーの設定
    setup_email_scheduler(app)

def _initialize_database_components(app: Flask) -> None:
    """データベース関連コンポーネントの初期化"""
    with app.app_context():
        try:
            # セッションのクリーンアップ
            if db.session:
                db.session.remove()
                db.session.close_all()
            
            # データベースの初期化
            db.init_app(app)
            db.create_all()
            init_database(app)
            
        except SQLAlchemyError as e:
            app.logger.error(f"Database initialization error: {str(e)}")
            raise

def _initialize_extensions(app: Flask) -> None:
    """Flaskの拡張機能の初期化"""
    # データベース関連の初期化を最初に行う
    db.init_app(app)
    
    # その他の拡張機能の初期化
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    app.cli.add_command(reset_db_command)

def _register_blueprints(app: Flask) -> None:
    """ブループリントの登録"""
    from routes import (
        main, auth, leads, opportunities, accounts, reports,
        tracking, mobile, schedules, tasks, settings, system_management
    )
    from routes.history import bp as history_bp

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
        settings.bp: '/settings',
        system_management.bp: '/system',
        history_bp: '/history'
    }

    for blueprint, url_prefix in blueprints.items():
        app.register_blueprint(blueprint, url_prefix=url_prefix)

def _setup_error_handlers(app: Flask) -> None:
    """エラーハンドラーの設定"""
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

def _setup_context_processors(app: Flask) -> None:
    """コンテキストプロセッサの設定"""
    @app.context_processor
    def utility_processor():
        return {
            'now': datetime.utcnow,
            'format_date': lambda x: x.strftime('%Y-%m-%d %H:%M') if x else ''
        }

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5002))
    app.logger.info(f"Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port)