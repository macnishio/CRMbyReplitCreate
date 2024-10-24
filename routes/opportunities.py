from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Opportunity, Lead
from extensions import db
from datetime import datetime

bp = Blueprint('opportunities', __name__)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_opportunity():
    leads = Lead.query.all()
    if request.method == 'POST':
        try:
            opportunity = Opportunity(
                title=request.form['title'],
                description=request.form['description'],
                amount=float(request.form['amount']),
                stage=request.form['stage'],
                expected_close_date=datetime.strptime(request.form['expected_close_date'], '%Y-%m-%d'),
                lead_id=int(request.form['lead_id']) if request.form['lead_id'] else None
            )
            db.session.add(opportunity)
            db.session.commit()
            flash('Opportunity created successfully!', 'success')
            return redirect(url_for('opportunities.list_opportunities'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating opportunity: {str(e)}', 'error')
    
    return render_template('opportunities/create.html', opportunity=None, leads=leads)

@bp.route('/edit/<int:opportunity_id>', methods=['GET', 'POST'])
@login_required
def edit_opportunity(opportunity_id):
    opportunity = Opportunity.query.get_or_404(opportunity_id)
    leads = Lead.query.all()
    
    if request.method == 'POST':
        try:
            opportunity.title = request.form['title']
            opportunity.description = request.form['description']
            opportunity.amount = float(request.form['amount'])
            opportunity.stage = request.form['stage']
            opportunity.expected_close_date = datetime.strptime(request.form['expected_close_date'], '%Y-%m-%d')
            opportunity.lead_id = int(request.form['lead_id']) if request.form['lead_id'] else None
            
            db.session.commit()
            flash('Opportunity updated successfully!', 'success')
            return redirect(url_for('opportunities.list_opportunities'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating opportunity: {str(e)}', 'error')
            
    return render_template('opportunities/edit.html', opportunity=opportunity, leads=leads)

@bp.route('/')
@bp.route('/list')
@login_required
def list_opportunities():
    opportunities = Opportunity.query.all()
    return render_template('opportunities/list_opportunities.html', opportunities=opportunities)
