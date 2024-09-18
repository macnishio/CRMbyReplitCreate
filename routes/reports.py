from flask import Blueprint, render_template
from flask_login import login_required, current_user
from extensions import db
from models import Lead, Opportunity, Account
from sqlalchemy import func
from analytics import get_conversion_rate, get_average_deal_size, get_sales_pipeline_value

bp = Blueprint('reports', __name__, url_prefix='/reports')


@bp.route('/')
@login_required
def index():
    # Lead status report
    lead_status = db.session.query(Lead.status, func.count(Lead.id)).filter_by(
        user_id=current_user.id).group_by(Lead.status).all()

    # Opportunity stage report
    opportunity_stage = db.session.query(
        Opportunity.stage, func.count(Opportunity.id),
        func.sum(Opportunity.amount)).filter_by(
            user_id=current_user.id).group_by(Opportunity.stage).all()

    # Account industry report
    account_industry = db.session.query(Account.industry, func.count(
        Account.id)).filter_by(user_id=current_user.id).group_by(
            Account.industry).all()

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

    return render_template('reports/index.html',
                           lead_status=lead_status,
                           opportunity_stage=opportunity_stage,
                           account_industry=account_industry,
                           conversion_rate=conversion_rate,
                           average_deal_size=average_deal_size,
                           sales_pipeline_value=sales_pipeline_value,
                           lead_score_labels=lead_score_labels,
                           lead_score_data=lead_score_data)
