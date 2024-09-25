import imaplib
import email
from email.header import decode_header
from flask import current_app
from models import Email, Lead, UnknownEmail
from extensions import db
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.exc import DataError
import re


def connect_to_email_server():
    mail = imaplib.IMAP4_SSL(current_app.config['RECEIVE_MAIL_SERVER'])
    mail.login(current_app.config['MAIL_USERNAME'],
               current_app.config['MAIL_PASSWORD'])
    return mail


def extract_email_address(sender):
    email_pattern = r'<?([\w\.-]+@[\w\.-]+)>?'
    match = re.search(email_pattern, sender)
    if match:
        return match.group(1)
    return sender


def extract_sender_name(sender):
    name_pattern = r'^(.*?)\s*<'
    match = re.search(name_pattern, sender)
    if match:
        return match.group(1).strip()
    return None


def process_email(sender, subject, content, date):
    sender_email = extract_email_address(sender)
    sender_name = extract_sender_name(sender)

    lead = Lead.query.filter(
        func.lower(Lead.email) == func.lower(sender_email)).first()

    if not lead:
        similar_lead = Lead.query.filter(
            func.lower(
                Lead.email).like(f"%{sender_email.split('@')[0]}%")).first()
        if similar_lead:
            lead = similar_lead

    if lead:
        existing_email = Email.query.filter_by(lead_id=lead.id,
                                               subject=subject,
                                               received_at=date).first()
        if not existing_email:
            new_email = Email(sender=sender_email,
                              sender_name=sender_name,
                              subject=subject,
                              content=content,
                              received_at=date,
                              lead=lead)
            db.session.add(new_email)
            db.session.commit()
            current_app.logger.info(
                f"New email processed for lead: {lead.name}, received at {date}"
            )
        else:
            current_app.logger.info(
                f"Duplicate email skipped for lead: {lead.name}, received at {date}"
            )
    else:
        current_app.logger.warning(
            f"Received email from unknown sender: {sender}")
        unknown_email = UnknownEmail(sender=sender_email,
                                     sender_name=sender_name,
                                     subject=subject,
                                     content=content,
                                     received_at=date)
        db.session.add(unknown_email)
        db.session.commit()
        current_app.logger.info(f"Stored email from unknown sender: {sender}")


def fetch_emails(days_back=30, lead_id=None):
    mail = connect_to_email_server()
    mail.select('inbox')

    # Calculate the date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    date_criterion = f'(SINCE "{start_date.strftime("%d-%b-%Y")}")'

    if lead_id:
        lead = Lead.query.get(lead_id)
        if lead:
            date_criterion += f' (FROM "{lead.email}")'

    current_app.logger.info(
        f"Fetching emails from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )

    _, search_data = mail.search(None, date_criterion)

    total_emails = len(search_data[0].split())
    current_app.logger.info(f"Total emails fetched: {total_emails}")

    for num in search_data[0].split():
        _, data = mail.fetch(num, '(RFC822)')
        _, bytes_data = data[0]

        email_message = email.message_from_bytes(bytes_data)
        subject, encoding = decode_header(email_message["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or 'utf-8')

        sender = email_message["From"]
        date_tuple = email.utils.parsedate_tz(email_message["Date"])
        if date_tuple:
            local_date = datetime.fromtimestamp(
                email.utils.mktime_tz(date_tuple))
            current_app.logger.info(
                f"Processing email - Sender: {sender}, Subject: {subject}, Date: {local_date.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            current_app.logger.warning(
                f"Unable to parse date for email from {sender}")
            continue

        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode(encoding or 'utf-8', errors='ignore')
                        body = body.replace('\x00', '')  # Remove NUL characters
                    except Exception as e:
                        current_app.logger.error(f"Error decoding email body: {str(e)}")
                        body = "Error: Unable to decode email content"
                    break
        else:
            try:
                body = email_message.get_payload(decode=True).decode(encoding or 'utf-8', errors='ignore')
                body = body.replace('\x00', '')  # Remove NUL characters
            except Exception as e:
                current_app.logger.error(f"Error decoding email body: {str(e)}")
                body = "Error: Unable to decode email content"

        try:
            process_email(sender, subject, body, local_date)
        except DataError as e:
            current_app.logger.error(f"DataError processing email: {str(e)}")
        except Exception as e:
            current_app.logger.error(f"Unexpected error processing email: {str(e)}")

    mail.close()
    mail.logout()

    current_app.logger.info(
        f"Emails from known leads: {Email.query.filter(Email.received_at >= start_date).count()}"
    )
    current_app.logger.info(
        f"Emails from unknown senders: {UnknownEmail.query.filter(UnknownEmail.received_at >= start_date).count()}"
    )


def setup_email_scheduler(app):
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    @scheduler.task('interval',
                    id='check_emails',
                    minutes=30,
                    misfire_grace_time=900)
    def check_emails_task():
        with app.app_context():
            app.logger.info("Checking for new emails")
            fetch_emails()

    with app.app_context():
        app.logger.info("Email scheduler set up")
