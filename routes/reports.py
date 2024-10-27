from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from models import Lead, Opportunity, Task, Schedule
from extensions import db, limiter
from analytics import (
    get_sales_pipeline_value,
    get_monthly_revenue,
    get_conversion_rate,
    get_average_deal_size,
    get_revenue_trend,
    get_lead_score_distribution,
    get_task_status_distribution,
    get_sales_pipeline_by_stage
)

bp = Blueprint('reports', __name__)

def prepare_calendar_events(items, title_field='title', start_field='start_time', end_field='end_time', color=None):
    """Helper function to prepare events for FullCalendar"""
    events = []
    for item in items:
        event = {
            'id': item.id,
            'title': getattr(item, title_field),
            'start': getattr(item, start_field).isoformat(),
        }
        if hasattr(item, end_field):
            end_time = getattr(item, end_field)
            if end_time:
                event['end'] = end_time.isoformat()
        if color:
            event['backgroundColor'] = color
        events.append(event)
    return events

@bp.route('/')
@login_required
@limiter.limit("30 per minute", error_message="レポート生成の制限を超過しました。しばらく時間をおいて再試行してください。")
def index():
    # Get basic metrics
    this_month_revenue = get_monthly_revenue()
    sales_pipeline_value = get_sales_pipeline_value()
    conversion_rate = get_conversion_rate()
    average_deal_size = get_average_deal_size()

    # Get revenue trend data
    revenue_trend = get_revenue_trend(months=6)
    revenue_trend_labels = [item['month'] for item in revenue_trend]
    revenue_trend_data = [item['revenue'] for item in revenue_trend]

    # Get pipeline data
    pipeline_stages = get_sales_pipeline_by_stage()
    pipeline_labels = [stage[0] for stage in pipeline_stages]
    pipeline_data = [float(stage[2]) for stage in pipeline_stages]

    # Get lead score distribution
    lead_scores = get_lead_score_distribution()
    lead_score_labels = list(lead_scores.keys())
    lead_score_data = list(lead_scores.values())

    # Get task status distribution
    task_statuses = get_task_status_distribution()
    task_status_labels = list(task_statuses.keys())
    task_status_data = list(task_statuses.values())

    # Get schedule events for calendar
    schedules = Schedule.query.filter_by(user_id=current_user.id).all()
    schedule_events = prepare_calendar_events(schedules, color='#007bff')

    # Get task events for calendar
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    task_events = prepare_calendar_events(
        tasks,
        title_field='title',
        start_field='due_date',
        end_field='due_date',
        color='#28a745'
    )

    return render_template('reports/index.html',
                         this_month_revenue=this_month_revenue,
                         sales_pipeline_value=sales_pipeline_value,
                         conversion_rate=conversion_rate,
                         average_deal_size=average_deal_size,
                         revenue_trend_labels=revenue_trend_labels,
                         revenue_trend_data=revenue_trend_data,
                         pipeline_labels=pipeline_labels,
                         pipeline_data=pipeline_data,
                         lead_score_labels=lead_score_labels,
                         lead_score_data=lead_score_data,
                         task_status_labels=task_status_labels,
                         task_status_data=task_status_data,
                         schedule_events=schedule_events,
                         task_events=task_events)
