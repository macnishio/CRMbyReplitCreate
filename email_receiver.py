import imaplib
import email
from email.header import decode_header
from flask import current_app
from models import Email, Lead
from extensions import db
from flask_apscheduler import APScheduler


def connect_to_email_server():
    mail = imaplib.IMAP4_SSL(current_app.config['MAIL_SERVER'])
    mail.login(current_app.config['MAIL_USERNAME'],
               current_app.config['MAIL_PASSWORD'])
    return mail


def fetch_emails():
    mail = connect_to_email_server()
    mail.select('inbox')
    _, search_data = mail.search(None, 'UNSEEN')

    for num in search_data[0].split():
        _, data = mail.fetch(num, '(RFC822)')
        _, bytes_data = data[0]

        email_message = email.message_from_bytes(bytes_data)
        subject, encoding = decode_header(email_message["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or 'utf-8')

        sender = email_message["From"]

        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = email_message.get_payload(decode=True).decode()

        process_email(sender, subject, body)

    mail.close()
    mail.logout()


def process_email(sender, subject, content):
    lead = Lead.query.filter_by(email=sender).first()
    if lead:
        new_email = Email(sender=sender,
                          subject=subject,
                          content=content,
                          lead=lead)
        db.session.add(new_email)
        db.session.commit()
        current_app.logger.info(f"New email processed for lead: {lead.name}")
    else:
        current_app.logger.warning(
            f"Received email from unknown sender: {sender}")


def setup_email_scheduler(app):
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    @scheduler.task('interval',
                    id='check_emails',
                    minutes=5,
                    misfire_grace_time=900)
    def check_emails_task():
        with app.app_context():
            app.logger.info("Checking for new emails")
            fetch_emails()

    with app.app_context():
        app.logger.info("Email scheduler set up")
