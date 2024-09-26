import os
import email
from email.header import decode_header
from datetime import datetime, timedelta
from flask import current_app
from models import Lead, Email, UnknownEmail
from extensions import db
from imap_tools import MailBox, AND
from sqlalchemy.exc import DataError
import imaplib

def connect_to_email_server():
    mail_server = os.environ.get('MAIL_SERVER')
    mail_port = int(os.environ.get('MAIL_PORT', 993))
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')

    try:
        mail = imaplib.IMAP4_SSL(mail_server, mail_port)
        mail.login(mail_username, mail_password)
        return mail
    except Exception as e:
        current_app.logger.error(f"Error connecting to email server: {str(e)}")
        raise

def process_email(sender, subject, body, received_at):
    sender_name, sender_email = email.utils.parseaddr(sender)
    lead = Lead.query.filter_by(email=sender_email).first()

    if lead:
        email_obj = Email(
            sender=sender_email,
            sender_name=sender_name,
            subject=subject,
            content=body,
            received_at=received_at,
            lead=lead
        )
        db.session.add(email_obj)
    else:
        current_app.logger.warning(f"Received email from unknown sender: {sender}")
        unknown_email = UnknownEmail(
            sender=sender_email,
            sender_name=sender_name,
            subject=subject,
            content=body,
            received_at=received_at
        )
        db.session.add(unknown_email)

    try:
        db.session.commit()
        if lead:
            current_app.logger.info(f"Stored email for lead: {lead.id}")
        else:
            current_app.logger.info(f"Stored email from unknown sender: {sender}")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error storing email: {str(e)}")

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
            local_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
        else:
            local_date = datetime.utcnow()  # Fallback to current time if date parsing fails

        current_app.logger.info(
            f"Processing email - Sender: {sender}, Subject: {subject}, Original Date: {email_message['Date']}, Parsed Date: {local_date.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode(
                            encoding or 'utf-8', errors='ignore')
                        body = body.replace('\x00', '')  # Remove NUL characters
                    except Exception as e:
                        current_app.logger.error(
                            f"Error decoding email body: {str(e)}")
                        body = "Error: Unable to decode email content"
                    break
        else:
            try:
                body = email_message.get_payload(decode=True).decode(
                    encoding or 'utf-8', errors='ignore')
                body = body.replace('\x00', '')  # Remove NUL characters
            except Exception as e:
                current_app.logger.error(
                    f"Error decoding email body: {str(e)}")
                body = "Error: Unable to decode email content"

        try:
            process_email(sender, subject, body, local_date)
        except DataError as e:
            current_app.logger.error(f"DataError processing email: {str(e)}")
        except Exception as e:
            current_app.logger.error(
                f"Unexpected error processing email: {str(e)}")

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
