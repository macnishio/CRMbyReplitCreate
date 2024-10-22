from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, current_app, request
from flask_login import login_required, current_user
from email_receiver import fetch_emails
from models import Email, Lead, Opportunity, Task
from sqlalchemy import func
from datetime import datetime, timedelta
from extensions import db  # Add this line to import the db object

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
    # Get new leads count (created in the last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_leads_count = Lead.query.filter(Lead.created_at >= thirty_days_ago).count()

    # Get ongoing opportunities count
    ongoing_opportunities_count = Opportunity.query.filter_by(user_id=current_user.id, stage='In Progress').count()

    # Get this month's revenue
    this_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_revenue = db.session.query(func.sum(Opportunity.amount)).filter(
        Opportunity.user_id == current_user.id,
        Opportunity.stage == 'Won',
        Opportunity.close_date >= this_month
    ).scalar() or 0

    # Get completed tasks count
    completed_tasks_count = Task.query.filter_by(user_id=current_user.id, completed=True).count()

    # Get recent activities
    recent_activities = []
    # Add logic to fetch recent activities (e.g., recent leads, won opportunities, completed tasks)

    return render_template('dashboard.html',
                           new_leads_count=new_leads_count,
                           ongoing_opportunities_count=ongoing_opportunities_count,
                           this_month_revenue=this_month_revenue,
                           completed_tasks_count=completed_tasks_count,
                           recent_activities=recent_activities)

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
