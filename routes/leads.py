from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Lead
from forms import LeadForm
from analytics import calculate_lead_score, train_lead_scoring_model, predict_lead_score
from email_utils import send_follow_up_email, send_automated_follow_ups, needs_follow_up
from datetime import datetime

bp = Blueprint('leads', __name__, url_prefix='/leads')

@bp.route('/')
@login_required
def list_leads():
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    for lead in leads:
        lead.needs_follow_up = needs_follow_up(lead)
    return render_template('leads/list.html', leads=leads)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_lead():
    form = LeadForm()
    if form.validate_on_submit():
        lead = Lead(name=form.name.data,
                    email=form.email.data,
                    phone=form.phone.data,
                    status=form.status.data,
                    score=form.score.data or 0,
                    user_id=current_user.id)
        lead.score = calculate_lead_score(lead)
        lead.last_contact = datetime.utcnow()
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
        lead.score = calculate_lead_score(lead)
        lead.last_contact = datetime.utcnow()
        db.session.commit()
        flash('Lead updated successfully')
        return redirect(url_for('leads.lead_detail', id=lead.id))
    return render_template('leads/edit.html', form=form, lead=lead)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_lead(id):
    lead = Lead.query.get_or_404(id)
    db.session.delete(lead)
    db.session.commit()
    flash('Lead deleted successfully')
    return redirect(url_for('leads.list_leads'))

@bp.route('/update-scores')
@login_required
def update_lead_scores():
    leads = Lead.query.filter_by(user_id=current_user.id).all()
    model, scaler = train_lead_scoring_model(leads)
    for lead in leads:
        lead.score = predict_lead_score(model, scaler, lead)
    db.session.commit()
    flash('Lead scores updated successfully')
    return redirect(url_for('leads.list_leads'))

@bp.route('/send-follow-ups')
@login_required
def send_follow_ups():
    send_automated_follow_ups()
    flash('Follow-up emails sent successfully')
    return redirect(url_for('leads.list_leads'))

@bp.route('/<int:id>/send-follow-up')
@login_required
def send_individual_follow_up(id):
    lead = Lead.query.get_or_404(id)
    send_follow_up_email(lead)
    lead.last_contact = datetime.utcnow()
    db.session.commit()
    flash(f'Follow-up email sent to {lead.name}')
    return redirect(url_for('leads.lead_detail', id=lead.id))

@bp.route('/trigger-followups')
@login_required
def trigger_followups():
    send_automated_follow_ups()
    flash('Automated follow-ups triggered successfully')
    return redirect(url_for('leads.list_leads'))
