from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import User, SubscriptionPlan, Subscription
from extensions import db, limiter
from functools import wraps
from werkzeug.security import check_password_hash
from urllib.parse import urlparse, urljoin
from forms import RegistrationForm
import stripe
from stripe.error import (
   StripeError,
   CardError,
   InvalidRequestError,
   AuthenticationError,
   APIConnectionError,
   RateLimitError
)
from datetime import datetime, timedelta
import logging

# Blueprint設定
bp = Blueprint('auth', __name__)

# ログ設定
logger = logging.getLogger(__name__)

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
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    stripe_publishable_key = current_app.config.get('STRIPE_PUBLISHABLE_KEY')
    if not stripe_publishable_key:
        current_app.logger.error('Stripe publishable key is missing')
        flash('決済システムの設定エラーが発生しました。管理者に連絡してください。', 'error')
        return redirect(url_for('auth.login'))

    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            # Check for existing user
            if User.query.filter_by(email=form.email.data).first():
                flash('このメールアドレスは既に登録されています。', 'error')
                return render_template('register.html', 
                    form=form,
                    stripe_publishable_key=stripe_publishable_key)

            if User.query.filter_by(username=form.username.data).first():
                flash('このユーザー名は既に使用されています。', 'error')
                return render_template('register.html', 
                    form=form,
                    stripe_publishable_key=stripe_publishable_key)

            # Set Stripe API key
            stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
            if not stripe.api_key:
                current_app.logger.error('Stripe secret key not found')
                flash('決済システムの設定エラーが発生しました。', 'error')
                return redirect(url_for('auth.login'))

            # Validate and get payment method
            payment_methods = request.form.getlist('stripe_payment_method')
            valid_payment_method = next((pm for pm in reversed(payment_methods) if pm), None)

            if not valid_payment_method:
                current_app.logger.error("Payment method is missing")
                flash('カード情報が正しく入力されていません。', 'error')
                return render_template('register.html', 
                    form=form,
                    stripe_publishable_key=stripe_publishable_key)

            try:
                # Create Stripe customer
                customer = stripe.Customer.create(
                    email=form.email.data,
                    payment_method=valid_payment_method,
                    invoice_settings={
                        'default_payment_method': valid_payment_method
                    },
                    metadata={
                        'username': form.username.data,
                        'registration_date': datetime.utcnow().isoformat()
                    }
                )
            except CardError as e:
                current_app.logger.error(f"Stripe card error: {str(e)}")
                flash(f'カード情報に問題があります: {e.user_message}', 'error')
                return render_template('register.html', 
                    form=form,
                    stripe_publishable_key=stripe_publishable_key)
            except StripeError as e:
                current_app.logger.error(f"Stripe customer creation error: {str(e)}")
                flash('決済システムでエラーが発生しました。', 'error')
                return render_template('register.html', 
                    form=form,
                    stripe_publishable_key=stripe_publishable_key)

            # Get and validate plan
            plan = SubscriptionPlan.query.get(form.plan_id.data)
            if not plan or not plan.stripe_price_id:
                current_app.logger.error(f'Invalid plan or missing Stripe price ID: {form.plan_id.data}')
                flash('選択されたプランが無効です。', 'error')
                return render_template('register.html', 
                    form=form,
                    stripe_publishable_key=stripe_publishable_key)

            # Create subscription
            try:
                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{'price': plan.stripe_price_id}],
                    expand=['latest_invoice.payment_intent'],
                    payment_behavior='default_incomplete',
                    payment_settings={'save_default_payment_method': 'on_subscription'}
                )

                if subscription.status == 'incomplete':
                    # 支払いの確認が必要な場合
                    payment_intent = subscription.latest_invoice.payment_intent

                    try:
                        # 支払いの確認を実行
                        payment_intent = stripe.PaymentIntent.confirm(payment_intent.id)

                        # 支払い状態を確認
                        if payment_intent.status not in ['succeeded', 'requires_capture']:
                            current_app.logger.error(f"Payment confirmation failed: {payment_intent.status}")
                            flash('支払いの確認に失敗しました。もう一度お試しください。', 'error')
                            return render_template('register.html', 
                                form=form,
                                stripe_publishable_key=stripe_publishable_key)

                    except StripeError as e:
                        current_app.logger.error(f"Payment confirmation error: {str(e)}")
                        flash('支払いの確認中にエラーが発生しました。', 'error')
                        return render_template('register.html', 
                            form=form,
                            stripe_publishable_key=stripe_publishable_key)

            except StripeError as e:
                current_app.logger.error(f"Subscription creation error: {str(e)}")
                flash('サブスクリプション作成中にエラーが発生しました。', 'error')
                return render_template('register.html', 
                    form=form,
                    stripe_publishable_key=stripe_publishable_key)

            # Create user and subscription records
            try:
                user = User()
                user.username = form.username.data
                user.email = form.email.data
                user.role = 'user'
                user.set_password(form.password.data)

                db.session.add(user)
                db.session.flush()

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

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Database error: {str(e)}")
                flash('ユーザー情報の保存中にエラーが発生しました。', 'error')
                return render_template('register.html', 
                    form=form,
                    stripe_publishable_key=stripe_publishable_key)

        except Exception as e:
            current_app.logger.error(f"Registration error: {str(e)}")
            flash('登録処理中にエラーが発生しました。', 'error')
            return render_template('register.html', 
                form=form,
                stripe_publishable_key=stripe_publishable_key)

    return render_template('register.html',
        form=form,
        stripe_publishable_key=stripe_publishable_key
    )