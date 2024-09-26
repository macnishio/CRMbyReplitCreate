from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, current_app, request
from flask_login import login_required
from email_receiver import fetch_emails
from models import Email

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('home.html')

@bp.route('/health')
def health_check():
    return jsonify({"status": "ok"}), 200

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@bp.route('/fetch-emails', methods=['POST'])
@login_required
def manual_fetch_emails():
    try:
        time_range = int(request.form.get('time_range', 30))
        fetch_emails(time_range=time_range)
        flash(f'過去{time_range}分間のメールを正常に取得しました', 'success')
    except Exception as e:
        current_app.logger.error(f"メール取得中にエラーが発生しました: {str(e)}")
        flash('メールの取得中にエラーが発生しました。もう一度お試しください。', 'error')
    return redirect(url_for('main.index'))

@bp.route('/recent-emails')
@login_required
def recent_emails():
    emails = Email.query.order_by(Email.received_at.desc()).limit(100).all()
    for email in emails:
        current_app.logger.info(f"Email sender: {email.sender_name} <{email.sender}>, Received at: {email.received_at}")
    return render_template('recent_emails.html', emails=emails)
