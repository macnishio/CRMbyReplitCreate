from flask_login import current_user
from models import Lead, Opportunity, Account, Task, Schedule
from sqlalchemy import func
from datetime import datetime, timedelta
from extensions import db
from flask import current_app

def get_lead_stats():
    """Get lead statistics with proper handling of null values"""
    try:
        stats = db.session.query(
            Lead.status,
            func.count(Lead.id).label('count')
        ).filter(
            Lead.user_id == current_user.id
        ).group_by(Lead.status).all()
        return stats or []
    except Exception as e:
        current_app.logger.error(f"Error getting lead stats: {str(e)}")
        return []

def get_opportunity_stats():
    """Get opportunity statistics with proper handling of null values"""
    try:
        stats = db.session.query(
            Opportunity.stage,
            func.count(Opportunity.id).label('count'),
            func.coalesce(func.sum(func.coalesce(Opportunity.amount, 0.0)), 0.0).label('total_amount')
        ).filter(
            Opportunity.user_id == current_user.id
        ).group_by(Opportunity.stage).all()
        return stats or []
    except Exception as e:
        current_app.logger.error(f"Error getting opportunity stats: {str(e)}")
        return []

def get_account_industry_stats():
    """Get account industry statistics"""
    try:
        stats = db.session.query(
            Account.industry,
            func.count(Account.id).label('count')
        ).filter(
            Account.user_id == current_user.id,
            Account.industry.isnot(None)  # Exclude null industries
        ).group_by(Account.industry).all()
        return stats or []
    except Exception as e:
        current_app.logger.error(f"Error getting account stats: {str(e)}")
        return []

def get_lead_score_stats():
    """Get lead score statistics with proper score ranges"""
    try:
        ranges = [
            (0, 20, '0-20'),
            (21, 40, '21-40'),
            (41, 60, '41-60'),
            (61, 80, '61-80'),
            (81, 100, '81-100')
        ]
        
        stats = []
        for min_score, max_score, label in ranges:
            count = Lead.query.filter(
                Lead.user_id == current_user.id,
                Lead.score.isnot(None),  # Exclude null scores
                Lead.score.between(min_score, max_score)
            ).count()
            stats.append((label, count))
        return stats or []
    except Exception as e:
        current_app.logger.error(f"Error getting lead score stats: {str(e)}")
        return []

def get_sales_pipeline_value():
    """Get total sales pipeline value with proper null handling"""
    try:
        pipeline_value = db.session.query(
            func.coalesce(func.sum(func.coalesce(Opportunity.amount, 0.0)), 0.0)
        ).filter(
            Opportunity.user_id == current_user.id,
            Opportunity.stage.in_(['Initial Contact', 'Qualification', 'Proposal', 'Negotiation'])
        ).scalar()
        return float(pipeline_value or 0.0)
    except Exception as e:
        current_app.logger.error(f"Error getting sales pipeline value: {str(e)}")
        return 0.0

def get_this_month_revenue():
    """Get this month's revenue with proper null handling"""
    try:
        today = datetime.utcnow()
        first_day = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        revenue = db.session.query(
            func.coalesce(func.sum(func.coalesce(Opportunity.amount, 0.0)), 0.0)
        ).filter(
            Opportunity.user_id == current_user.id,
            Opportunity.stage == 'Closed Won',
            Opportunity.close_date >= first_day,
            Opportunity.close_date <= today
        ).scalar()
        
        return float(revenue or 0.0)
    except Exception as e:
        current_app.logger.error(f"Error getting this month revenue: {str(e)}")
        return 0.0

def get_upcoming_tasks():
    """Get upcoming tasks"""
    try:
        return Task.query.filter(
            Task.user_id == current_user.id,
            Task.due_date >= datetime.utcnow()
        ).order_by(Task.due_date).limit(5).all()
    except Exception as e:
        current_app.logger.error(f"Error getting upcoming tasks: {str(e)}")
        return []

def get_upcoming_schedules():
    """Get upcoming schedules"""
    try:
        return Schedule.query.filter(
            Schedule.user_id == current_user.id,
            Schedule.start_time >= datetime.utcnow()
        ).order_by(Schedule.start_time).limit(5).all()
    except Exception as e:
        current_app.logger.error(f"Error getting upcoming schedules: {str(e)}")
        return []
