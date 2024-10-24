from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import Opportunity, Lead
from extensions import db

opportunities_bp = Blueprint('opportunities', __name__)

@opportunities_bp.route('/edit/<int:opportunity_id>', methods=['GET', 'POST'])
@login_required
def edit_opportunity(opportunity_id):
    opportunity = Opportunity.query.get_or_404(opportunity_id)
    
    # Ensure the opportunity belongs to the current user
    if opportunity.user_id != current_user.id:
        flash('You do not have permission to edit this opportunity.', 'danger')
        return redirect(url_for('opportunities.list_opportunities'))
    
    if request.method == 'POST':
        try:
            opportunity.title = request.form['title']
            opportunity.description = request.form['description']
            opportunity.amount = float(request.form['amount'])
            opportunity.stage = request.form['stage']
            opportunity.expected_close_date = datetime.strptime(request.form['expected_close_date'], '%Y-%m-%d')
            opportunity.lead_id = request.form['lead_id'] if request.form['lead_id'] else None
            
            db.session.commit()
            flash('Opportunity updated successfully!', 'success')
            return redirect(url_for('opportunities.list_opportunities'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating opportunity: {str(e)}', 'danger')
    
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    return render_template('opportunities/edit_opportunity.html', opportunity=opportunity, leads=leads)
