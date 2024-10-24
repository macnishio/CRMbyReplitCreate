from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)

# Configure login manager
login_manager.login_view = 'auth.login'
login_manager.login_message = 'このページにアクセスするにはログインが必要です。'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
