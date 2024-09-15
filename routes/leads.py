from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from models import Lead
from forms import LeadForm

bp = Blueprint('leads', __name__, url_prefix='/leads')

@bp.route('/')
@login_required
def list_leads():
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    return render_template('leads/list.html', leads=leads)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_lead():
    form = LeadForm()
    if form.validate_on_submit():
        lead = Lead(name=form.name.data, email=form.email.data, phone=form.phone.data, status=form.status.data, user_id=current_user.id)
        db.session.add(lead)
        db.session.commit()
        flash('Lead created successfully')
        return redirect(url_for('leads.list_leads'))
    return render_template('leads/create.html', form=form)

@bp.route('/<int:id>')
@login_required
def lead_detail(id):
    lead = Lead.query.get_or_404(id)
    return render_template('leads/detail.html', lead=lead)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_lead(id):
    lead = Lead.query.get_or_404(id)
    form = LeadForm(obj=lead)
    if form.validate_on_submit():
        form.populate_obj(lead)
        db.session.commit()
        flash('Lead updated successfully')
        return redirect(url_for('leads.lead_detail', id=lead.id))
    return render_template('leads/create.html', form=form)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_lead(id):
    lead = Lead.query.get_or_404(id)
    db.session.delete(lead)
    db.session.commit()
    flash('Lead deleted successfully')
    return redirect(url_for('leads.list_leads'))
