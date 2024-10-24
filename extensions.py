# extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask import current_app

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)
cache = Cache(config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

# Configure login manager
login_manager.login_view = 'auth.login'
login_manager.login_message = 'このページにアクセスするにはログインが必要です。'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'
login_manager.refresh_view = 'auth.login'
login_manager.needs_refresh_message = 'セッションが期限切れです。再度ログインしてください。'
login_manager.needs_refresh_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    try:
        from models import User
        user = User.query.get(int(user_id))
        if user:
            current_app.logger.debug(f"Loaded user: {user.username}")
        else:
            current_app.logger.warning(f"No user found with ID: {user_id}")
        return user
    except Exception as e:
        current_app.logger.error(f"Error loading user {user_id}: {str(e)}")
        return None

def init_extensions(app):
    """Initialize all extensions with the app"""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)

    # Additional login manager configuration
    app.config.setdefault('LOGIN_DISABLED', False)
    app.config.setdefault('LOGIN_MESSAGE_CATEGORY', 'info')

    return app