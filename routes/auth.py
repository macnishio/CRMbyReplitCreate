from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import User, SubscriptionPlan, Subscription
from extensions import db
from functools import wraps
from werkzeug.security import check_password_hash
from urllib.parse import urlparse, urljoin
from forms import RegistrationForm
import stripe
from datetime import datetime, timedelta

bp = Blueprint('auth', __name__)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember = 'remember' in request.form
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('main.dashboard')
            return redirect(next_page)
            
        flash('メールアドレスまたはパスワードが正しくありません。', 'error')
    
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました。', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('このメールアドレスは既に登録されています。', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(username=form.username.data).first():
            flash('このユーザー名は既に使用されています。', 'error')
            return redirect(url_for('auth.register'))

        try:
            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
            
            # Create Stripe customer
            customer = stripe.Customer.create(
                email=form.email.data,
                payment_method=form.stripe_payment_method.data,
                invoice_settings={
                    'default_payment_method': form.stripe_payment_method.data
                }
            )

            # Get selected plan
            plan = SubscriptionPlan.query.get(form.plan_id.data)
            if not plan:
                flash('選択されたプランが見つかりません。', 'error')
                return redirect(url_for('auth.register'))

            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': plan.stripe_price_id}],
                expand=['latest_invoice.payment_intent']
            )

            # Create user
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.flush()  # Get user.id without committing

            # Create local subscription record
            user_subscription = Subscription(
                user_id=user.id,
                plan_id=plan.id,
                stripe_subscription_id=subscription.id,
                stripe_customer_id=customer.id,
                status=subscription.status,
                current_period_start=datetime.fromtimestamp(subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(subscription.current_period_end)
            )
            
            db.session.add(user_subscription)
            db.session.commit()
            
            flash('登録が完了しました。ログインしてください。', 'success')
            return redirect(url_for('auth.login'))
            
        except stripe.error.StripeError as e:
            db.session.rollback()
            flash(f'支払い処理中にエラーが発生しました: {str(e)}', 'error')
            current_app.logger.error(f"Stripe error during registration: {str(e)}")
            return redirect(url_for('auth.register'))
        except Exception as e:
            db.session.rollback()
            flash('登録処理中にエラーが発生しました。', 'error')
            current_app.logger.error(f"Error during registration: {str(e)}")
            return redirect(url_for('auth.register'))
    
    return render_template(
        'register.html',
        form=form,
        stripe_publishable_key=current_app.config['STRIPE_PUBLISHABLE_KEY']
    )
