from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
from analytics import (
    get_lead_stats, get_opportunity_stats, get_account_industry_stats,
    get_lead_score_stats, get_sales_pipeline_value, get_this_month_revenue
)

bp = Blueprint('reports', __name__)

@bp.route('/')
@login_required
def index():
    try:
        # Get all statistics with proper error handling
        lead_status_data = get_lead_stats()
        current_app.logger.debug(f"Lead status data: {lead_status_data}")

        opportunity_stage_data = get_opportunity_stats()
        current_app.logger.debug(f"Opportunity stage data: {opportunity_stage_data}")

        account_industry_data = get_account_industry_stats()
        current_app.logger.debug(f"Account industry data: {account_industry_data}")

        lead_score_data = get_lead_score_stats()
        current_app.logger.debug(f"Lead score data: {lead_score_data}")

        # Calculate total values with null handling
        sales_pipeline_value = get_sales_pipeline_value()
        this_month_revenue = get_this_month_revenue()

        return render_template('reports/index.html',
                           lead_status_data=lead_status_data,
                           opportunity_stage_data=opportunity_stage_data,
                           account_industry_data=account_industry_data,
                           lead_score_data=lead_score_data,
                           sales_pipeline_value=sales_pipeline_value,
                           this_month_revenue=this_month_revenue)

    except Exception as e:
        current_app.logger.error(f"Error in reports index: {str(e)}")
        # Return template with empty data in case of error
        return render_template('reports/index.html',
                           lead_status_data=[],
                           opportunity_stage_data=[],
                           account_industry_data=[],
                           lead_score_data=[],
                           sales_pipeline_value=0.0,
                           this_month_revenue=0.0)
