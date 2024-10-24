from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import Opportunity, Lead

opportunities = Blueprint('opportunities', __name__)

@opportunities.route('/opportunities/edit/<int:opportunity_id>', methods=['GET', 'POST'])
def edit_opportunity(opportunity_id):
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
        
    opportunity = Opportunity.query.get_or_404(opportunity_id)
    leads = Lead.query.all()
    
    if request.method == 'POST':
        opportunity.title = request.form['title']
        opportunity.description = request.form['description']
        opportunity.amount = request.form['amount']
        opportunity.stage = request.form['stage']
        opportunity.expected_close_date = request.form['expected_close_date']
        opportunity.lead_id = request.form['lead_id'] if request.form['lead_id'] else None
        
        try:
            db.session.commit()
            flash('Opportunity updated successfully!', 'success')
            return redirect(url_for('opportunities.list_opportunities'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating opportunity. Please try again.', 'error')
            
    return render_template('opportunities/edit_opportunity.html', opportunity=opportunity, leads=leads)
