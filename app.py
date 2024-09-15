import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    with app.app_context():
        from models import User

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

        from routes import main, leads, opportunities, accounts, reports
        app.register_blueprint(main.bp)
        app.register_blueprint(leads.bp)
        app.register_blueprint(opportunities.bp)
        app.register_blueprint(accounts.bp)
        app.register_blueprint(reports.bp)

        from auth import bp as auth_bp
        app.register_blueprint(auth_bp)

        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
