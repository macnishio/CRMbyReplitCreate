from flask import current_app, url_for
from flask_mail import Message
from extensions import db, mail
from models import Lead, Opportunity
from datetime import datetime, timedelta
import logging
import uuid

def send_follow_up_email(lead):
    subject = f"Follow-up: {lead.name}"
    tracking_id = str(uuid.uuid4())
    
    if lead.opportunities:
        latest_opportunity = max(lead.opportunities, key=lambda x: x.created_at)
        body = f"""
        Dear {lead.name},

        I hope this email finds you well. I wanted to follow up on our previous conversation about {latest_opportunity.name}. 
        We believe our solution can greatly benefit your business by addressing your specific needs in {latest_opportunity.stage}.

        Is there a good time this week for a quick call to discuss how we can move forward?

        Best regards,
        Your Sales Team

        P.S. If you'd like to schedule a meeting, please reply to this email with your preferred date and time.
        """
    else:
        body = f"""
        Dear {lead.name},

        I hope this email finds you well. I wanted to follow up on our previous conversation and see if you have any questions 
        or if there's any additional information we can provide about our products/services.

        We'd love the opportunity to show you how we can add value to your business. Would you be interested in a quick demo?

        Best regards,
        Your Sales Team

        P.S. If you'd like to schedule a meeting, please reply to this email with your preferred date and time.
        """
    
    msg = Message(subject,
                  recipients=[lead.email],
                  body=body)
    
    tracking_pixel = f'<img src="{url_for("tracking.pixel", tracking_id=tracking_id, _external=True)}" width="1" height="1" />'
    msg.html = body + tracking_pixel
    
    try:
        mail.send(msg)
        lead.last_followup_email = datetime.utcnow()
        lead.last_followup_tracking_id = tracking_id
        db.session.commit()
        current_app.logger.info(f"Follow-up email sent to {lead.email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send follow-up email to {lead.email}: {str(e)}")
        raise

def send_automated_follow_ups():
    current_app.logger.info("Starting automated follow-ups process")
    follow_up_interval = current_app.config['FOLLOW_UP_INTERVAL_DAYS']
    lead_score_threshold = current_app.config['LEAD_SCORE_THRESHOLD']
    
    cutoff_date = datetime.utcnow() - timedelta(days=follow_up_interval)
    
    leads_to_follow_up = Lead.query.filter(
        (Lead.last_contact < cutoff_date) | (Lead.last_followup_email == None),
        Lead.score >= lead_score_threshold
    ).all()

    for lead in leads_to_follow_up:
        try:
            send_follow_up_email(lead)
            lead.last_contact = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Failed to send follow-up email to {lead.email}: {str(e)}")
            db.session.rollback()
    
    current_app.logger.info(f"Successfully sent follow-up emails to {len(leads_to_follow_up)} leads.")

def needs_follow_up(lead):
    follow_up_interval = current_app.config['FOLLOW_UP_INTERVAL_DAYS']
    lead_score_threshold = current_app.config['LEAD_SCORE_THRESHOLD']
    
    cutoff_date = datetime.utcnow() - timedelta(days=follow_up_interval)
    
    return (lead.last_contact < cutoff_date or lead.last_followup_email is None) and lead.score >= lead_score_threshold

def track_email_open(tracking_id):
    lead = Lead.query.filter_by(last_followup_tracking_id=tracking_id).first()
    if lead:
        lead.last_email_opened = datetime.utcnow()
        db.session.commit()
        current_app.logger.info(f"Email opened by lead: {lead.email}")
