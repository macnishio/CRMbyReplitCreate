from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Lead, Email
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
        try:
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
            current_app.logger.info(f"Lead created successfully: {lead.id}")
            flash('Lead created successfully', 'success')
            return redirect(url_for('leads.list_leads'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating lead: {str(e)}")
            flash('An error occurred while creating the lead. Please try again.', 'error')
    return render_template('leads/create.html', form=form)

@bp.route('/<int:id>')
@login_required
def lead_detail(id):
    lead = Lead.query.get_or_404(id)
    emails = Email.query.filter_by(lead_id=lead.id).order_by(Email.received_at.desc()).all()
    return render_template('leads/detail.html', lead=lead, emails=emails)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_lead(id):
    lead = Lead.query.get_or_404(id)
    form = LeadForm(obj=lead)
    if form.validate_on_submit():
        try:
            form.populate_obj(lead)
            lead.score = calculate_lead_score(lead)
            lead.last_contact = datetime.utcnow()
            db.session.commit()
            current_app.logger.info(f"Lead updated successfully: {lead.id}")
            flash('Lead updated successfully', 'success')
            return redirect(url_for('leads.lead_detail', id=lead.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating lead: {str(e)}")
            flash('An error occurred while updating the lead. Please try again.', 'error')
    return render_template('leads/edit.html', form=form, lead=lead)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_lead(id):
    lead = Lead.query.get_or_404(id)
    try:
        db.session.delete(lead)
        db.session.commit()
        current_app.logger.info(f"Lead deleted successfully: {id}")
        flash('Lead deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting lead: {str(e)}")
        flash('An error occurred while deleting the lead. Please try again.', 'error')
    return redirect(url_for('leads.list_leads'))

@bp.route('/update-scores')
@login_required
def update_lead_scores():
    try:
        leads = Lead.query.filter_by(user_id=current_user.id).all()
        model, scaler = train_lead_scoring_model(leads)
        for lead in leads:
            lead.score = predict_lead_score(model, scaler, lead)
        db.session.commit()
        current_app.logger.info("Lead scores updated successfully")
        flash('Lead scores updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating lead scores: {str(e)}")
        flash('An error occurred while updating lead scores. Please try again.', 'error')
    return redirect(url_for('leads.list_leads'))

@bp.route('/send-follow-ups')
@login_required
def send_follow_ups():
    try:
        send_automated_follow_ups()
        current_app.logger.info("Follow-up emails sent successfully")
        flash('Follow-up emails sent successfully', 'success')
    except Exception as e:
        current_app.logger.error(f"Error sending follow-up emails: {str(e)}")
        flash('An error occurred while sending follow-up emails. Please try again.', 'error')
    return redirect(url_for('leads.list_leads'))

@bp.route('/<int:id>/send-follow-up')
@login_required
def send_individual_follow_up(id):
    lead = Lead.query.get_or_404(id)
    try:
        send_follow_up_email(lead)
        lead.last_contact = datetime.utcnow()
        db.session.commit()
        current_app.logger.info(f"Follow-up email sent to lead: {id}")
        flash(f'Follow-up email sent to {lead.name}', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error sending follow-up email to lead {id}: {str(e)}")
        flash(f'An error occurred while sending follow-up email to {lead.name}. Please try again.', 'error')
    return redirect(url_for('leads.lead_detail', id=lead.id))

@bp.route('/trigger-followups')
@login_required
def trigger_followups():
    try:
        send_automated_follow_ups()
        current_app.logger.info("Automated follow-ups triggered successfully")
        flash('Automated follow-ups triggered successfully', 'success')
    except Exception as e:
        current_app.logger.error(f"Error triggering automated follow-ups: {str(e)}")
        flash('An error occurred while triggering automated follow-ups. Please try again.', 'error')
    return redirect(url_for('leads.list_leads'))
