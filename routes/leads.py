from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Lead
from extensions import db

leads_bp = Blueprint('leads', __name__)

@leads_bp.route('/edit/<int:lead_id>', methods=['GET', 'POST'])
@login_required
def edit_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    
    # Ensure the lead belongs to the current user
    if lead.user_id != current_user.id:
        flash('You do not have permission to edit this lead.', 'danger')
        return redirect(url_for('leads.list_leads'))
    
    if request.method == 'POST':
        try:
            lead.name = request.form['name']
            lead.email = request.form['email']
            lead.phone = request.form['phone']
            lead.company = request.form['company']
            lead.status = request.form['status']
            lead.source = request.form['source']
            lead.notes = request.form['notes']
            
            db.session.commit()
            flash('Lead updated successfully!', 'success')
            return redirect(url_for('leads.list_leads'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating lead: {str(e)}', 'danger')
    
    return render_template('leads/edit_lead.html', lead=lead)

# Other routes remain unchanged...
