# routes/auth.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import User, UserSettings
from extensions import db
from forms import LoginForm, RegistrationForm
from werkzeug.urls import url_parse
from datetime import datetime

bp = Blueprint('auth', __name__)

def is_safe_url(target):
    ref_url = url_parse(request.host_url)
    test_url = url_parse(url_for(target) if target.startswith('.')
                        else target)
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """ログイン処理"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.check_password(form.password.data):
                flash('ユーザー名またはパスワードが正しくありません', 'error')
                return redirect(url_for('auth.login'))

            login_user(user, remember=True)
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('main.dashboard')

            return redirect(next_page)
        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}")
            flash('ログイン処理中にエラーが発生しました', 'error')

    return render_template('auth/login.html', title='ログイン', form=form)

@bp.route('/logout')
@login_required
def logout():
    """ログアウト処理"""
    try:
        user_email = current_user.email
        logout_user()
        flash('ログアウトしました', 'success')
        current_app.logger.info(f"User logged out: {user_email}")
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        flash('ログアウト処理中にエラーが発生しました', 'error')

    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = RegistrationForm()  # フォームのインスタンスを作成
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                role='user'
            )
            user.set_password(form.password.data)

            settings = UserSettings(
                user=user,
                mail_server='smtp.gmail.com',
                mail_port=587,
                mail_use_tls=True,
                mail_username='',
                mail_password='',
                created_at=datetime.utcnow()
            )

            db.session.add(user)
            db.session.add(settings)
            db.session.commit()

            flash('アカウントが作成されました。ログインしてください。', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {str(e)}")
            flash('登録中にエラーが発生しました。', 'error')

    return render_template('register.html', form=form)  # formをテンプレートに渡す