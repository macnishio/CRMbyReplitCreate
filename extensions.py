from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_apscheduler import APScheduler
from flask_caching import Cache
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
mail = Mail()
scheduler = APScheduler()
cache = Cache()
migrate = Migrate()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)

def init_app(app):
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    scheduler.init_app(app)
    cache.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
