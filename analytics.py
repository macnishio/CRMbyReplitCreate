from datetime import datetime, timedelta
from flask_login import current_user
from sqlalchemy import func, or_, and_
from models import Opportunity, Lead, Task, Schedule
from extensions import db

def get_sales_pipeline_value():
    """Get total value of open opportunities with null handling"""
    open_opportunities = Opportunity.query.filter(
        and_(
            Opportunity.user_id == current_user.id,
            Opportunity.stage.in_(['Initial Contact', 'Qualification', 'Proposal', 'Negotiation']),
            Opportunity.amount != None  # Exclude null amounts
        )
    ).all()
    
    return sum(opp.amount or 0 for opp in open_opportunities)

def get_sales_pipeline_by_stage():
    """Get pipeline value broken down by stage with null handling"""
    pipeline_data = db.session.query(
        Opportunity.stage,
        func.count(Opportunity.id).label('count'),
        func.coalesce(func.sum(Opportunity.amount), 0).label('amount')
    ).filter(
        Opportunity.user_id == current_user.id
    ).group_by(Opportunity.stage).all()
    
    return pipeline_data

def get_conversion_rate():
    """Get lead conversion rate with null handling"""
    total_leads = Lead.query.filter_by(user_id=current_user.id).count()
    converted_leads = Opportunity.query.filter(
        and_(
            Opportunity.user_id == current_user.id,
            Opportunity.stage == 'Closed Won'
        )
    ).count()
    
    if total_leads > 0:
        return (converted_leads / total_leads) * 100
    return 0

def get_average_deal_size():
    """Get average deal size with null handling"""
    result = db.session.query(
        func.coalesce(func.avg(Opportunity.amount), 0.0)
    ).filter(
        and_(
            Opportunity.user_id == current_user.id,
            Opportunity.stage == 'Closed Won',
            Opportunity.amount != None
        )
    ).scalar()
    
    return float(result or 0)

def get_lead_score_distribution():
    """Get distribution of lead scores"""
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    score_ranges = {
        'Low (0-30)': len([l for l in leads if l.score is not None and 0 <= l.score <= 30]),
        'Medium (31-70)': len([l for l in leads if l.score is not None and 31 <= l.score <= 70]),
        'High (71-100)': len([l for l in leads if l.score is not None and 71 <= l.score <= 100])
    }
    return score_ranges

def get_monthly_revenue(date=None):
    """Get revenue for a specific month with null handling"""
    if date is None:
        date = datetime.utcnow()
        
    start_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if date.month == 12:
        end_date = date.replace(year=date.year + 1, month=1, day=1) - timedelta(microseconds=1)
    else:
        end_date = date.replace(month=date.month + 1, day=1) - timedelta(microseconds=1)
    
    revenue = db.session.query(
        func.coalesce(func.sum(Opportunity.amount), 0.0)
    ).filter(
        Opportunity.user_id == current_user.id,
        Opportunity.stage == 'Closed Won',
        Opportunity.close_date >= start_date,
        Opportunity.close_date <= end_date,
        Opportunity.amount != None  # Exclude null amounts
    ).scalar() or 0.0
    
    return float(revenue)

def get_task_status_distribution():
    """Get distribution of task statuses"""
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    status_counts = {
        'New': len([t for t in tasks if t.status == 'New']),
        'In Progress': len([t for t in tasks if t.status == 'In Progress']),
        'Completed': len([t for t in tasks if t.status == 'Completed'])
    }
    return status_counts

def get_upcoming_schedules(days=7):
    """Get upcoming schedules for the next N days"""
    today = datetime.utcnow()
    end_date = today + timedelta(days=days)
    
    schedules = Schedule.query.filter(
        Schedule.user_id == current_user.id,
        Schedule.start_time >= today,
        Schedule.start_time <= end_date
    ).order_by(Schedule.start_time).all()
    
    return schedules

def get_revenue_trend(months=6):
    """Get revenue trend for the last N months with null handling"""
    today = datetime.utcnow()
    trend = []
    
    for i in range(months-1, -1, -1):
        date = today - timedelta(days=i*30)
        revenue = get_monthly_revenue(date)
        trend.append({
            'month': date.strftime('%Y-%m'),
            'revenue': float(revenue)
        })
    
    return trend
