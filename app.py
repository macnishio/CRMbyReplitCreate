from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from extensions import db, migrate
from datetime import datetime
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints with URL prefixes
    from routes.schedules import schedules_bp
    from routes.tasks import tasks_bp
    from routes.opportunities import opportunities_bp
    from routes.leads import leads_bp
    from routes.auth import auth_bp

    app.register_blueprint(schedules_bp, url_prefix='/schedules')
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    app.register_blueprint(opportunities_bp, url_prefix='/opportunities')
    app.register_blueprint(leads_bp, url_prefix='/leads')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    @app.route('/')
    def index():
        return redirect(url_for('schedules.list_schedules'))

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
