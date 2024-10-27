from datetime import datetime, timedelta
from anthropic import Anthropic
from flask import current_app
import os
from sqlalchemy import func, or_, and_
from flask_login import current_user
from models import Opportunity, Lead, Task, Schedule
from extensions import db

def get_lead_score_distribution():
    """Get distribution of lead scores"""
    try:
        distribution = {}
        leads = Lead.query.filter_by(user_id=current_user.id).all()
        
        for lead in leads:
            score_range = int(lead.score // 10) * 10
            range_key = f"{score_range}-{score_range + 9}"
            distribution[range_key] = distribution.get(range_key, 0) + 1
            
        return distribution
    except Exception as e:
        current_app.logger.error(f"Error getting lead score distribution: {str(e)}")
        return None

def get_task_status_distribution():
    """Get distribution of task statuses"""
    try:
        return {
            'completed': Task.query.filter_by(user_id=current_user.id, completed=True).count(),
            'pending': Task.query.filter_by(user_id=current_user.id, completed=False).count()
        }
    except Exception as e:
        current_app.logger.error(f"Error getting task status distribution: {str(e)}")
        return None

def get_sales_pipeline_value():
    """Get total value of open opportunities with null handling"""
    pipeline_value = db.session.query(
        func.coalesce(func.sum(Opportunity.amount), 0.0)
    ).filter(
        and_(
            Opportunity.user_id == current_user.id,
            Opportunity.stage.in_(['Initial Contact', 'Qualification', 'Proposal', 'Negotiation'])
        )
    ).scalar()
    
    return float(pipeline_value or 0.0)

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
        Opportunity.close_date <= end_date
    ).scalar()
    
    return float(revenue or 0.0)

def get_conversion_rate():
    """Calculate lead to opportunity conversion rate"""
    total_leads = Lead.query.filter_by(user_id=current_user.id).count()
    converted_leads = Lead.query.filter(
        Lead.user_id == current_user.id,
        Lead.opportunities.any()
    ).count()
    
    if total_leads == 0:
        return 0.0
        
    return (converted_leads / total_leads) * 100

def get_average_deal_size():
    """Calculate average deal size for won opportunities"""
    result = db.session.query(
        func.avg(Opportunity.amount)
    ).filter(
        Opportunity.user_id == current_user.id,
        Opportunity.stage == 'Closed Won',
        Opportunity.amount.isnot(None)
    ).scalar()
    
    return float(result or 0.0)

def get_revenue_trend(months=6):
    """Get revenue trend for the past n months"""
    end_date = datetime.utcnow().replace(day=1)
    revenues = []
    
    for i in range(months):
        date = end_date - timedelta(days=30*i)
        revenue = get_monthly_revenue(date)
        revenues.insert(0, {
            'month': date.strftime('%Y-%m'),
            'revenue': revenue
        })
        
    return revenues

def analyze_schedule(schedule):
    """Analyze a schedule using Claude AI"""
    try:
        client = Anthropic(api_key=os.environ.get('CLAUDE_API_KEY'))
        
        # Format schedule data
        schedule_data = f"""
        - タイトル: {schedule.title}, 開始: {schedule.start_time}, 終了: {schedule.end_time}
        """
        
        # Create analysis prompt
        prompt = f"""今は日本時間の{datetime.now().strftime('%Y-%m-%d')}です。以下のスケジュールデータを分析してください:
        {schedule_data}

        以下の項目について簡潔に分析してください:
        1. スケジュールの密度と時間配分
        2. 重要な予定の特定
        3. スケジュール管理の効率化
        4. バランス改善のための提案
        回答は日本語でお願いします。HTMLの段落タグ（<p>）を使用してフォーマットしてください。"""

        # Get AI response
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        return response.content[0].text
        
    except Exception as e:
        current_app.logger.error(f"Error analyzing schedule: {str(e)}")
        return None

def analyze_lead_scores(leads):
    """Analyze lead scoring patterns"""
    try:
        score_ranges = {
            '0-25': 0,
            '26-50': 0,
            '51-75': 0,
            '76-100': 0
        }
        
        for lead in leads:
            score = lead.score
            if score <= 25:
                score_ranges['0-25'] += 1
            elif score <= 50:
                score_ranges['26-50'] += 1
            elif score <= 75:
                score_ranges['51-75'] += 1
            else:
                score_ranges['76-100'] += 1
                
        return score_ranges
    except Exception as e:
        current_app.logger.error(f"Error analyzing lead scores: {str(e)}")
        return None

def get_sales_pipeline_stats():
    """Get statistics about the sales pipeline"""
    try:
        pipeline = {
            'Initial Contact': {'count': 0, 'value': 0},
            'Qualification': {'count': 0, 'value': 0},
            'Proposal': {'count': 0, 'value': 0},
            'Negotiation': {'count': 0, 'value': 0},
            'Closed Won': {'count': 0, 'value': 0},
            'Closed Lost': {'count': 0, 'value': 0}
        }
        
        opportunities = Opportunity.query.filter_by(user_id=current_user.id).all()
        
        for opp in opportunities:
            if opp.stage in pipeline:
                pipeline[opp.stage]['count'] += 1
                pipeline[opp.stage]['value'] += opp.amount if opp.amount else 0
                
        return pipeline
    except Exception as e:
        current_app.logger.error(f"Error getting pipeline stats: {str(e)}")
        return None

def get_task_completion_stats():
    """Get statistics about task completion"""
    try:
        tasks = Task.query.filter_by(user_id=current_user.id).all()
        stats = {
            'total': len(tasks),
            'completed': sum(1 for task in tasks if task.completed),
            'pending': sum(1 for task in tasks if not task.completed),
            'overdue': sum(1 for task in tasks if not task.completed and task.due_date < datetime.utcnow())
        }
        return stats
    except Exception as e:
        current_app.logger.error(f"Error getting task stats: {str(e)}")
        return None
