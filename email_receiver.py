import os
import email
from email.header import decode_header
from datetime import datetime, timedelta, timezone
from flask import current_app
from models import Lead, Email, UnknownEmail, EmailFetchTracker, Opportunity, Schedule, Task, User, UserSettings
from extensions import db
from sqlalchemy.exc import DataError
import imaplib
import ssl
import re
import chardet
from ai_analysis import analyze_email, parse_ai_response
from flask_apscheduler import APScheduler

def get_user_settings(user_id):
    return UserSettings.query.filter_by(user_id=user_id).first()

def connect_to_email_server(user_settings=None):
    if user_settings:
        mail_server = user_settings.mail_server
        mail_port = user_settings.mail_port
        mail_username = user_settings.mail_username
        mail_password = user_settings.mail_password
    else:
        # Fallback to environment variables for system-wide settings
        mail_server = os.environ.get('MAIL_SERVER')
        mail_port = int(os.environ.get('MAIL_PORT', 993))
        mail_username = os.environ.get('MAIL_USERNAME')
        mail_password = os.environ.get('MAIL_PASSWORD')

    if not all([mail_server, mail_port, mail_username, mail_password]):
        error_message = "One or more email connection settings are missing."
        current_app.logger.error(error_message)
        raise EnvironmentError(error_message)

    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        ssl_versions = [ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLSv1_2, ssl.PROTOCOL_TLSv1_1, ssl.PROTOCOL_TLSv1]
        for ssl_version in ssl_versions:
            try:
                context.options |= ssl_version
                current_app.logger.info(f"Attempting to connect to {mail_server}:{mail_port} with SSL version: {ssl_version}")
                mail = imaplib.IMAP4_SSL(mail_server, mail_port, ssl_context=context)
                mail.login(mail_username, mail_password)
                current_app.logger.info(f"Successfully connected and logged in to the email server using SSL version: {ssl_version}")
                return mail
            except Exception as e:
                current_app.logger.warning(f"Error with SSL version {ssl_version}: {str(e)}")
                context.options &= ~ssl_version

        raise Exception("Unable to establish a secure connection with any SSL/TLS version")

    except Exception as e:
        current_app.logger.error(f"Unexpected error in connect_to_email_server: {str(e)}")
        raise

def setup_email_scheduler(app):
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    @scheduler.task('interval', id='check_emails', minutes=5, misfire_grace_time=300, max_instances=1)
    def check_emails_task():
        with app.app_context():
            app.logger.info("Checking for new emails")
            fetch_emails(time_range=30, max_emails=100)

    with app.app_context():
        app.logger.info("Email scheduler set up")

def fetch_emails(time_range=30, max_emails=100, user_id=None):
    try:
        user_settings = get_user_settings(user_id) if user_id else None
        mail = connect_to_email_server(user_settings)
        mail.select('INBOX')

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(minutes=time_range)
        date_str = start_date.strftime("%d-%b-%Y")

        _, message_numbers = mail.search(None, f'(SINCE "{date_str}")')
        email_ids = message_numbers[0].split()

        email_ids = email_ids[-max_emails:]

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
                        email_body = response_part[1]
                        email_message = email.message_from_bytes(email_body)
                        
                        subject = decode_header(email_message["Subject"])[0][0]
                        sender = email.utils.parseaddr(email_message["From"])[1]
                        date_tuple = email.utils.parsedate_tz(email_message["Date"])
                        if date_tuple:
                            local_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                        else:
                            local_date = datetime.now()

                        if isinstance(subject, bytes):
                            subject = subject.decode()
                        
                        current_app.logger.info(f"Processing email - Sender: {sender}, Subject: {subject}, Date: {local_date}")

                        lead = Lead.query.filter_by(email=sender).first()
                        if lead:
                            known_lead_emails += 1
                            process_lead_email(lead, email_message, subject, local_date)
                        else:
                            unknown_sender_emails += 1
                            store_unknown_email(sender, email_message, subject, local_date)

                        processed_emails += 1
            except Exception as e:
                current_app.logger.error(f"Error processing email {num}: {str(e)}")

        current_app.logger.info(f"Processed {processed_emails} out of {total_emails} emails")
        current_app.logger.info(f"Emails from known leads: {known_lead_emails}")
        current_app.logger.info(f"Emails from unknown senders: {unknown_sender_emails}")

    except Exception as e:
        current_app.logger.error(f"Error fetching emails: {str(e)}")
    finally:
        if 'mail' in locals():
            try:
                mail.logout()
            except Exception as e:
                current_app.logger.error(f"Error logging out from email server: {str(e)}")

def process_lead_email(lead, email_message, subject, date):
    content = ""
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                content = part.get_payload(decode=True).decode()
                break
    else:
        content = email_message.get_payload(decode=True).decode()

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

    try:
        db.session.commit()
    except DataError as e:
        current_app.logger.error(f"Error storing email: {str(e)}")
        db.session.rollback()

    ai_response = analyze_email(subject, content, lead.user_id)
    opportunities, schedules, tasks = parse_ai_response(ai_response)

    for opp in opportunities:
        new_opp = Opportunity(
            name=opp,
            stage="New",
            amount=0,  # Set a default amount
            close_date=datetime.utcnow() + timedelta(days=30),  # Set a default close date
            user_id=lead.user_id,
            lead_id=lead.id
        )
        db.session.add(new_opp)

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

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Error storing AI analysis results: {str(e)}")
        db.session.rollback()

def store_unknown_email(sender, email_message, subject, date):
    content = ""
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                content = part.get_payload(decode=True).decode()
                break
    else:
        content = email_message.get_payload(decode=True).decode()

    unknown_email = UnknownEmail(
        sender=sender,
        sender_name=email.utils.parseaddr(email_message["From"])[0],
        subject=subject,
        content=content,
        received_at=date
    )
    db.session.add(unknown_email)

    try:
        db.session.commit()
        current_app.logger.info(f"Stored email from unknown sender: {sender}")
    except DataError as e:
        current_app.logger.error(f"Error storing unknown email: {str(e)}")
        db.session.rollback()
