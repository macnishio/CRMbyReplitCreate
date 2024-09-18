from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Lead, Opportunity, Account

bp = Blueprint('mobile', __name__, url_prefix='/mobile')

@bp.route('/')
@login_required
def mobile_dashboard():
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    opportunities = Opportunity.query.filter_by(user_id=current_user.id).all()
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('mobile/dashboard.html', leads=leads, opportunities=opportunities, accounts=accounts)
