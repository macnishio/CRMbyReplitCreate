from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import User, SubscriptionPlan, Subscription
from extensions import db, limiter
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
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    # Check Stripe keys before form creation
    stripe_keys_missing = False
    if not current_app.config.get('STRIPE_PUBLISHABLE_KEY'):
        stripe_keys_missing = True
        current_app.logger.error('Stripe publishable key not found')
    if not current_app.config.get('STRIPE_SECRET_KEY'):
        stripe_keys_missing = True
        current_app.logger.error('Stripe secret key not found')

    form = RegistrationForm()
    
    if stripe_keys_missing:
        flash('決済システムの設定エラーが発生しました。管理者に連絡してください。', 'error')
        return render_template('register.html', form=form)

    if form.validate_on_submit():
        try:
            # Check for existing user
            if User.query.filter_by(email=form.email.data).first():
                flash('このメールアドレスは既に登録されています。', 'error')
                return render_template('register.html', form=form, 
                    stripe_publishable_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY', ''))
            
            if User.query.filter_by(username=form.username.data).first():
                flash('このユーザー名は既に使用されています。', 'error')
                return render_template('register.html', form=form, 
                    stripe_publishable_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY', ''))

            stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
            
            # Create Stripe customer with error handling
            try:
                customer = stripe.Customer.create(
                    email=form.email.data,
                    payment_method=form.stripe_payment_method.data,
                    invoice_settings={
                        'default_payment_method': form.stripe_payment_method.data
                    }
                )
            except stripe.error.StripeError as e:
                current_app.logger.error(f"Stripe customer creation error: {str(e)}")
                flash('顧客情報の作成中にエラーが発生しました。', 'error')
                return render_template('register.html', form=form, 
                    stripe_publishable_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY', ''))

            # Get selected plan
            plan = SubscriptionPlan.query.get(form.plan_id.data)
            if not plan:
                current_app.logger.error(f'Selected plan {form.plan_id.data} not found')
                flash('選択されたプランが見つかりません。', 'error')
                return render_template('register.html', form=form, 
                    stripe_publishable_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY', ''))

            if not plan.stripe_price_id:
                current_app.logger.error(f'Stripe price ID not found for plan {plan.id}')
                flash('プランの設定エラーが発生しました。管理者に連絡してください。', 'error')
                return render_template('register.html', form=form, 
                    stripe_publishable_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY', ''))

            # Create subscription with error handling
            try:
                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{'price': plan.stripe_price_id}],
                    expand=['latest_invoice.payment_intent'],
                    payment_behavior='default_incomplete',
                    payment_settings={'save_default_payment_method': 'on_subscription'}
                )
            except stripe.error.StripeError as e:
                current_app.logger.error(f"Stripe subscription creation error: {str(e)}")
                flash('サブスクリプションの作成中にエラーが発生しました。', 'error')
                return render_template('register.html', form=form, 
                    stripe_publishable_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY', ''))

            # Create user
            user = User(
                username=form.username.data,
                email=form.email.data,
                role='user'
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            
            try:
                db.session.flush()  # Get user.id without committing
            except Exception as e:
                current_app.logger.error(f"Database error creating user: {str(e)}")
                db.session.rollback()
                flash('ユーザー情報の保存中にエラーが発生しました。', 'error')
                return render_template('register.html', form=form, 
                    stripe_publishable_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY', ''))

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

            try:
                db.session.commit()
            except Exception as e:
                current_app.logger.error(f"Database error saving subscription: {str(e)}")
                db.session.rollback()
                flash('サブスクリプション情報の保存中にエラーが発生しました。', 'error')
                return render_template('register.html', form=form, 
                    stripe_publishable_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY', ''))
            
            flash('登録が完了しました。ログインしてください。', 'success')
            return redirect(url_for('auth.login'))
            
        except stripe.error.CardError as e:
            db.session.rollback()
            error_msg = e.error.message
            current_app.logger.error(f"Stripe card error: {error_msg}")
            flash(f'カード処理中にエラーが発生しました: {error_msg}', 'error')
            return render_template('register.html', form=form, 
                stripe_publishable_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY', ''))
        except stripe.error.StripeError as e:
            db.session.rollback()
            current_app.logger.error(f"Stripe error during registration: {str(e)}")
            flash('支払い処理中にエラーが発生しました。もう一度お試しください。', 'error')
            return render_template('register.html', form=form, 
                stripe_publishable_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY', ''))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during registration: {str(e)}")
            flash('登録処理中にエラーが発生しました。', 'error')
            return render_template('register.html', form=form, 
                stripe_publishable_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY', ''))
    
    return render_template('register.html', 
        form=form,
        stripe_publishable_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY', '')
    )
