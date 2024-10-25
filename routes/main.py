from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Lead, Opportunity, Task, Schedule, Email
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func, desc

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def dashboard():
    # Get recent leads (last 30 days)
    recent_leads = Lead.query.filter_by(user_id=current_user.id)\
        .order_by(Lead.created_at.desc())\
        .limit(5).all()
    
    # Get opportunities by stage
    opportunities_by_stage = db.session.query(
        Opportunity.stage,
        func.count(Opportunity.id).label('count'),
        func.sum(Opportunity.amount).label('total_amount')
    ).filter_by(user_id=current_user.id)\
    .group_by(Opportunity.stage).all()
    
    # Get upcoming tasks
    upcoming_tasks = Task.query.filter_by(
        user_id=current_user.id,
        completed=False
    ).filter(
        Task.due_date >= datetime.utcnow()
    ).order_by(Task.due_date).limit(5).all()
    
    # Get upcoming schedules
    upcoming_schedules = Schedule.query.filter_by(user_id=current_user.id)\
        .filter(Schedule.start_time >= datetime.utcnow())\
        .order_by(Schedule.start_time)\
        .limit(5).all()
    
    # Get recent emails
    recent_emails = Email.query.filter_by(user_id=current_user.id)\
        .order_by(Email.received_date.desc())\
        .limit(5).all()

    return render_template('dashboard.html',
                         leads=recent_leads,
                         opportunities=opportunities_by_stage,
                         tasks=upcoming_tasks,
                         schedules=upcoming_schedules,
                         emails=recent_emails)
