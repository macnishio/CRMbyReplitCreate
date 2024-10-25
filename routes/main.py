from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import Lead, Opportunity, Task, Schedule, Email
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def dashboard():
    # Get recent leads
    recent_leads = Lead.query.filter_by(user_id=current_user.id)\
        .order_by(Lead.created_at.desc())\
        .limit(5).all()
    
    # Initialize revenue values
    this_month_revenue = 0
    previous_month_revenue = 0
    total_pipeline = 0
    
    try:
        # Calculate current month revenue with coalesce and proper error handling
        today = datetime.utcnow()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_revenue = db.session.query(
            func.coalesce(func.sum(Opportunity.amount), 0)
        ).filter(
            Opportunity.user_id == current_user.id,
            Opportunity.stage == 'Closed Won',
            Opportunity.close_date >= first_day_of_month,
            Opportunity.close_date <= today
        ).scalar() or 0

        # Calculate previous month revenue with coalesce
        first_day_prev_month = (first_day_of_month - timedelta(days=1)).replace(day=1)
        last_day_prev_month = first_day_of_month - timedelta(microseconds=1)
        previous_month_revenue = db.session.query(
            func.coalesce(func.sum(Opportunity.amount), 0)
        ).filter(
            Opportunity.user_id == current_user.id,
            Opportunity.stage == 'Closed Won',
            Opportunity.close_date >= first_day_prev_month,
            Opportunity.close_date <= last_day_prev_month
        ).scalar() or 0
        
        # Get opportunities by stage with total amounts using coalesce
        opportunities_by_stage = db.session.query(
            Opportunity.stage,
            func.count(Opportunity.id).label('count'),
            func.coalesce(func.sum(Opportunity.amount), 0).label('total_amount')
        ).filter_by(user_id=current_user.id)\
        .group_by(Opportunity.stage).all()

        # Calculate total pipeline value with coalesce
        total_pipeline = db.session.query(
            func.coalesce(func.sum(Opportunity.amount), 0)
        ).filter(
            Opportunity.user_id == current_user.id,
            Opportunity.stage.in_(['Initial Contact', 'Qualification', 'Proposal', 'Negotiation'])
        ).scalar() or 0

    except Exception as e:
        current_app.logger.error(f"Error calculating revenue: {str(e)}")
        opportunities_by_stage = []

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
                         opportunities=opportunities_by_stage or [],
                         tasks=upcoming_tasks,
                         schedules=upcoming_schedules,
                         emails=recent_emails,
                         this_month_revenue=this_month_revenue,
                         previous_month_revenue=previous_month_revenue,
                         total_pipeline=total_pipeline)
