from flask import Blueprint, render_template
from flask_login import login_required
from models import Lead, Opportunity, Account

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    leads = Lead.query.count()
    opportunities = Opportunity.query.count()
    accounts = Account.query.count()
    return render_template('dashboard.html', leads=leads, opportunities=opportunities, accounts=accounts)
