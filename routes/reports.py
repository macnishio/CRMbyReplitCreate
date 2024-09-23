from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Lead, Opportunity, Account, Task
from sqlalchemy import func
from analytics import get_conversion_rate, get_average_deal_size, get_sales_pipeline_value
from datetime import datetime, timedelta

bp = Blueprint('reports', __name__, url_prefix='/reports')

@bp.route('/')
@login_required
def index():
    # Lead status report
    lead_status = db.session.query(Lead.status, func.count(Lead.id)).filter_by(
        user_id=current_user.id).group_by(Lead.status).all()
    current_app.logger.debug(f"Lead status data: {lead_status}")

    # Opportunity stage report
    opportunity_stage = db.session.query(
        Opportunity.stage, func.count(Opportunity.id),
        func.sum(Opportunity.amount)).filter_by(
            user_id=current_user.id).group_by(Opportunity.stage).all()
    current_app.logger.debug(f"Opportunity stage data: {opportunity_stage}")

    # Account industry report
    account_industry = db.session.query(Account.industry, func.count(
        Account.id)).filter_by(user_id=current_user.id).group_by(
            Account.industry).all()
    current_app.logger.debug(f"Account industry data: {account_industry}")

    # Advanced analytics
    conversion_rate = get_conversion_rate()
    average_deal_size = get_average_deal_size()
    sales_pipeline_value = get_sales_pipeline_value()

    # Lead scoring distribution
    lead_scores = db.session.query(
        func.floor(Lead.score / 10) * 10,
        func.count(Lead.id)).filter_by(user_id=current_user.id).group_by(
            func.floor(Lead.score / 10) * 10).all()
    lead_score_labels = [
        f"{int(score)}-{int(score)+9}" for score, _ in lead_scores
    ]
    lead_score_data = [count for _, count in lead_scores]
    current_app.logger.debug(f"Lead score distribution: {lead_scores}")

    # Task status report
    task_status = db.session.query(
        Task.completed, func.count(Task.id)
    ).filter_by(user_id=current_user.id).group_by(Task.completed).all()
    current_app.logger.debug(f"Task status data: {task_status}")

    # Task due date report
    today = datetime.utcnow().date()
    task_due_date = db.session.query(
        func.case(
            (Task.due_date.cast(db.Date) < today, 'Overdue'),
            (Task.due_date.cast(db.Date) == today, 'Due Today'),
            else_='Upcoming'
        ).label('due_status'),
        func.count(Task.id)
    ).filter_by(user_id=current_user.id).group_by('due_status').all()
    current_app.logger.debug(f"Task due date data: {task_due_date}")

    current_app.logger.debug(f"Conversion rate: {conversion_rate}")
    current_app.logger.debug(f"Average deal size: {average_deal_size}")
    current_app.logger.debug(f"Sales pipeline value: {sales_pipeline_value}")

    # Add more detailed logging
    current_app.logger.info("Data being passed to the reports template:")
    current_app.logger.info(f"Lead status: {lead_status}")
    current_app.logger.info(f"Opportunity stage: {opportunity_stage}")
    current_app.logger.info(f"Account industry: {account_industry}")
    current_app.logger.info(f"Lead score labels: {lead_score_labels}")
    current_app.logger.info(f"Lead score data: {lead_score_data}")
    current_app.logger.info(f"Task status: {task_status}")
    current_app.logger.info(f"Task due date: {task_due_date}")

    return render_template('reports/index.html',
                           lead_status=lead_status,
                           opportunity_stage=opportunity_stage,
                           account_industry=account_industry,
                           conversion_rate=conversion_rate,
                           average_deal_size=average_deal_size,
                           sales_pipeline_value=sales_pipeline_value,
                           lead_score_labels=lead_score_labels,
                           lead_score_data=lead_score_data,
                           task_status=task_status,
                           task_due_date=task_due_date)