from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import Lead, Opportunity, Task, Schedule, Email
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def dashboard():
    try:
        # Get recent leads with error handling
        recent_leads = Lead.query.filter_by(user_id=current_user.id)\
            .order_by(Lead.created_at.desc())\
            .limit(5).all() or []

        # Calculate revenue metrics with proper error handling
        today = datetime.utcnow()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Current month revenue
        this_month_revenue = db.session.query(
            func.coalesce(func.sum(Opportunity.amount), 0.0)
        ).filter(
            Opportunity.user_id == current_user.id,
            Opportunity.stage == 'Closed Won',
            Opportunity.close_date >= first_day_of_month,
            Opportunity.close_date <= today
        ).scalar() or 0.0

        # Previous month revenue
        first_day_prev_month = (first_day_of_month - timedelta(days=1)).replace(day=1)
        last_day_prev_month = first_day_of_month - timedelta(microseconds=1)
        previous_month_revenue = db.session.query(
            func.coalesce(func.sum(Opportunity.amount), 0.0)
        ).filter(
            Opportunity.user_id == current_user.id,
            Opportunity.stage == 'Closed Won',
            Opportunity.close_date >= first_day_prev_month,
            Opportunity.close_date <= last_day_prev_month
        ).scalar() or 0.0

        # Get opportunities by stage with proper error handling
        opportunities_by_stage = db.session.query(
            Opportunity.stage,
            func.count(Opportunity.id).label('count'),
            func.coalesce(func.sum(Opportunity.amount), 0.0).label('total_amount')
        ).filter(
            Opportunity.user_id == current_user.id
        ).group_by(Opportunity.stage).all() or []

        # Calculate total pipeline value
        total_pipeline = db.session.query(
            func.coalesce(func.sum(Opportunity.amount), 0.0)
        ).filter(
            Opportunity.user_id == current_user.id,
            Opportunity.stage.in_(['Initial Contact', 'Qualification', 'Proposal', 'Negotiation'])
        ).scalar() or 0.0

        # Get upcoming tasks
        upcoming_tasks = Task.query.filter_by(
            user_id=current_user.id,
            completed=False
        ).filter(
            Task.due_date >= datetime.utcnow()
        ).order_by(Task.due_date).limit(5).all() or []
        
        # Get upcoming schedules
        upcoming_schedules = Schedule.query.filter_by(user_id=current_user.id)\
            .filter(Schedule.start_time >= datetime.utcnow())\
            .order_by(Schedule.start_time)\
            .limit(5).all() or []
        
        # Get recent emails
        recent_emails = Email.query.filter_by(user_id=current_user.id)\
            .order_by(Email.received_date.desc())\
            .limit(5).all() or []

        return render_template('dashboard.html',
                            leads=recent_leads,
                            opportunities=opportunities_by_stage,
                            tasks=upcoming_tasks,
                            schedules=upcoming_schedules,
                            emails=recent_emails,
                            this_month_revenue=float(this_month_revenue),
                            previous_month_revenue=float(previous_month_revenue),
                            total_pipeline=float(total_pipeline))

    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error in dashboard: {str(e)}")
        flash('データベースエラーが発生しました。', 'error')
        return render_template('dashboard.html',
                            leads=[],
                            opportunities=[],
                            tasks=[],
                            schedules=[],
                            emails=[],
                            this_month_revenue=0.0,
                            previous_month_revenue=0.0,
                            total_pipeline=0.0)
    except Exception as e:
        current_app.logger.error(f"Unexpected error in dashboard: {str(e)}")
        flash('予期せぬエラーが発生しました。', 'error')
        return render_template('dashboard.html',
                            leads=[],
                            opportunities=[],
                            tasks=[],
                            schedules=[],
                            emails=[],
                            this_month_revenue=0.0,
                            previous_month_revenue=0.0,
                            total_pipeline=0.0)
