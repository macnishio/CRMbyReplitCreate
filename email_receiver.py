import os
import email
from email.header import decode_header
from datetime import datetime, timedelta, timezone
from flask import current_app
from models import Lead, Email, UnknownEmail, EmailFetchTracker, Opportunity, Schedule, Task, User, UserSettings
from extensions import db
from sqlalchemy.exc import SQLAlchemyError
import imaplib
import ssl
import re
import chardet
from ai_analysis import analyze_email, parse_ai_response
from flask_apscheduler import APScheduler
import smtplib
from utils import decode_mime_words

def get_user_settings(user_id):
    return UserSettings.query.filter_by(user_id=user_id).first()

def connect_to_email_server(user_settings):
    if not user_settings:
        raise ValueError("User settings are required to connect to the email server.")

    mail_server = user_settings.mail_server
    mail_port = user_settings.mail_port
    mail_username = user_settings.mail_username
    mail_password = user_settings.mail_password

    if not all([mail_server, mail_port, mail_username, mail_password]):
        raise ValueError("One or more email connection settings are missing.")

    try:
        mail = imaplib.IMAP4_SSL(mail_server, mail_port)
        mail.login(mail_username, mail_password)
        current_app.logger.info(f"Successfully connected to email server: {mail_server}:{mail_port}")
        return mail
    except Exception as e:
        current_app.logger.error(f"Error connecting to email server: {str(e)}")
        raise

def setup_email_scheduler(app):
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    @scheduler.task('interval', id='check_emails', minutes=5, misfire_grace_time=300, max_instances=1)
    def check_emails_task():
        with app.app_context():
            app.logger.info("Checking for new emails")
            user_ids = [user.id for user in User.query.all()]
            for user_id in user_ids:
                try:
                    fetch_emails(time_range=30, max_emails=100, user_id=user_id)
                except Exception as e:
                    current_app.logger.error(f"Error fetching emails for user_id {user_id}: {str(e)}")

def fetch_emails(time_range=30, max_emails=100, user_id=None):
    current_app.logger.info(f"Fetching emails for user_id: {user_id}")
    mail = None
    try:
        user_settings = get_user_settings(user_id)
        if not user_settings:
            raise ValueError(f"No user settings found for user_id: {user_id}")

        mail = connect_to_email_server(user_settings)
        mail.select('INBOX')

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(minutes=time_range)
        date_str = start_date.strftime("%d-%b-%Y")

        _, message_numbers = mail.search(None, f'(SINCE "{date_str}")')
        email_ids = message_numbers[0].split()[-max_emails:]

        total_emails = len(email_ids)
        processed_emails = 0
        known_lead_emails = 0
        unknown_sender_emails = 0

        current_app.logger.info(f"Total emails found: {total_emails}")

        for num in reversed(email_ids):
            try:
                _, msg_data = mail.fetch(num, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        email_message = email.message_from_bytes(response_part[1])
                        subject = decode_mime_words(email_message["Subject"])
                        sender = email.utils.parseaddr(email_message["From"])[1]
                        date_tuple = email.utils.parsedate_tz(email_message["Date"])
                        local_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple)) if date_tuple else datetime.now()

                        current_app.logger.info(f"Processing email - Sender: {sender}, Subject: {subject}")

                        lead = Lead.query.filter_by(email=sender).first()
                        if lead:
                            known_lead_emails += 1
                            process_lead_email(lead, email_message, subject, local_date)
                        else:
                            unknown_sender_emails += 1
                            store_unknown_email(sender, email_message, subject, local_date, user_id)

                        processed_emails += 1
            except Exception as e:
                current_app.logger.error(f"Error processing email ID {num}: {str(e)}")

        current_app.logger.info(f"Processed {processed_emails} out of {total_emails} emails")
        current_app.logger.info(f"Emails from known leads: {known_lead_emails}")
        current_app.logger.info(f"Emails from unknown senders: {unknown_sender_emails}")

    except Exception as e:
        current_app.logger.error(f"Error fetching emails: {str(e)}")
    finally:
        if mail:
            try:
                mail.logout()
            except Exception as e:
                current_app.logger.error(f"Error logging out from email server: {str(e)}")

def get_email_content(email_message):
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode(errors='ignore')
    else:
        return email_message.get_payload(decode=True).decode(errors='ignore')
    return ""

def process_lead_email(lead, email_message, subject, date):
    try:
        content = get_email_content(email_message)
        new_email = Email(
            sender=lead.email,
            sender_name=lead.name,
            subject=subject,
            content=content,
            received_at=date,
            lead_id=lead.id
        )
        db.session.add(new_email)
        lead.last_contact = date

        ai_response = analyze_email(subject, content, lead.user_id)
        opportunities, schedules, tasks = parse_ai_response(ai_response)

        create_opportunities(opportunities, lead)
        create_schedules(schedules, lead)
        create_tasks(tasks, lead)

        db.session.commit()
        current_app.logger.info(f"Processed email for lead: {lead.email}")
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error processing lead email: {str(e)}")
        db.session.rollback()
    except Exception as e:
        current_app.logger.error(f"Error processing lead email: {str(e)}")
        db.session.rollback()

def store_unknown_email(sender, email_message, subject, date, user_id):
    try:
        content = get_email_content(email_message)
        sender_name, sender_email = email.utils.parseaddr(sender)

        new_lead = Lead(
            name=decode_mime_words(sender_name),
            email=sender_email,
            user_id=user_id,
            status='New'
        )
        db.session.add(new_lead)
        db.session.flush()  # To get the new lead's ID

        new_email = Email(
            sender=sender_email,
            sender_name=sender_name,
            subject=subject,
            content=content,
            received_at=date,
            lead_id=new_lead.id
        )
        db.session.add(new_email)

        ai_response = analyze_email(subject, content, user_id)
        opportunities, schedules, tasks = parse_ai_response(ai_response)

        create_opportunities(opportunities, new_lead)
        create_schedules(schedules, new_lead)
        create_tasks(tasks, new_lead)

        db.session.commit()
        current_app.logger.info(f"Stored email from new lead: {sender_email}")
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error storing unknown email: {str(e)}")
        db.session.rollback()
    except Exception as e:
        current_app.logger.error(f"Error storing unknown email: {str(e)}")
        db.session.rollback()

def create_opportunities(opportunities, lead):
    for opp in opportunities:
        new_opp = Opportunity(
            name=opp,
            stage="New",
            amount=0,
            close_date=datetime.utcnow() + timedelta(days=30),
            user_id=lead.user_id,
            lead_id=lead.id
        )
        db.session.add(new_opp)

def create_schedules(schedules, lead):
    for sched in schedules:
        new_sched = Schedule(
            title=sched,
            description="AI生成されたスケジュール",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            user_id=lead.user_id,
            lead_id=lead.id
        )
        db.session.add(new_sched)

def create_tasks(tasks, lead):
    for task in tasks:
        new_task = Task(
            title=task,
            description="AI生成されたタスク",
            status="New",
            due_date=datetime.now() + timedelta(days=7),
            user_id=lead.user_id,
            lead_id=lead.id
        )
        db.session.add(new_task)