from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from email_receiver import check_emails
from models import Lead, Opportunity, Task
from sqlalchemy import func
from datetime import datetime, timedelta
from extensions import db

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    return redirect(url_for('main.dashboard'))

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

    return render_template('index.html',
                         new_leads_count=new_leads_count,
                         ongoing_opportunities_count=ongoing_opportunities_count,
                         this_month_revenue=this_month_revenue,
                         completed_tasks_count=completed_tasks_count)

@bp.route('/check_emails')
@login_required
def trigger_email_check():
    check_emails(current_app)
    return redirect(url_for('main.dashboard'))
