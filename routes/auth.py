from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user
from urllib.parse import urlparse
from extensions import db
from models import User
from forms import LoginForm, RegistrationForm
from db_utils import retry_on_exception
import traceback

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data,
                        email=form.email.data,
                        role='user')  # role を追加
            user.set_password(form.password.data)
            db.session.add(user)
            commit_with_retry()
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            flash('An error occurred during registration. Please try again.')
    return render_template('register.html', title='Register', form=form)


@retry_on_exception()
def commit_with_retry():
    db.session.commit()
