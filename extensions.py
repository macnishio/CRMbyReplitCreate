from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_apscheduler import APScheduler
from flask_caching import Cache
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

db = SQLAlchemy(model_class=Base)
mail = Mail()
scheduler = APScheduler()
cache = Cache()