from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Lead, Opportunity, Account
from sqlalchemy import func

bp = Blueprint('reports', __name__, url_prefix='/reports')

@bp.route('/')
@login_required
def index():
    # Lead status report
    lead_status = db.session.query(Lead.status, func.count(Lead.id)).filter_by(user_id=current_user.id).group_by(Lead.status).all()
    
    # Opportunity stage report
    opportunity_stage = db.session.query(Opportunity.stage, func.count(Opportunity.id), func.sum(Opportunity.amount)).filter_by(user_id=current_user.id).group_by(Opportunity.stage).all()
    
    # Account industry report
    account_industry = db.session.query(Account.industry, func.count(Account.id)).filter_by(user_id=current_user.id).group_by(Account.industry).all()

    return render_template('reports/index.html', lead_status=lead_status, opportunity_stage=opportunity_stage, account_industry=account_industry)
