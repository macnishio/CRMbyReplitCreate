import os
import email
from email.header import decode_header
from datetime import datetime, timedelta, timezone
from flask import current_app
from models import Lead, Email, UnknownEmail, EmailFetchTracker
from extensions import db
from sqlalchemy.exc import DataError
import imaplib
import ssl
import re
import chardet

def connect_to_email_server():
    mail_server = os.environ.get('RECEIVE_MAIL_SERVER')
    mail_port = int(os.environ.get('RECEIVE_MAIL_PORT', 993))
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')

    if not all([mail_server, mail_port, mail_username, mail_password]):
        error_message = "One or more email connection environment variables are missing."
        current_app.logger.error(error_message)
        raise EnvironmentError(error_message)

    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Add more SSL options
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
        
        ssl_versions = [ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLSv1_2]
        for ssl_version in ssl_versions:
            try:
                context.options |= ssl_version
                current_app.logger.info(f"Attempting to connect to {mail_server}:{mail_port} with SSL version: {ssl_version}")
                mail = imaplib.IMAP4_SSL(mail_server, mail_port, ssl_context=context)
                current_app.logger.info(f"IMAP4_SSL connection established with SSL version: {ssl_version}")
                mail.login(mail_username, mail_password)
                current_app.logger.info("Successfully logged in to the email server")
                return mail
            except ssl.SSLError as e:
                current_app.logger.warning(f"SSL Error with version {ssl_version}: {str(e)}")
                context.options &= ~ssl_version
                continue
            except imaplib.IMAP4.error as e:
                current_app.logger.error(f"IMAP Error: {str(e)}")
                continue
    except Exception as e:
        current_app.logger.error(f"Unexpected error connecting to email server: {str(e)}")
        raise

    raise Exception("Unable to establish a secure connection with any SSL/TLS version")

def extract_email_address(sender):
    decoded_sender = email.header.decode_header(sender)
    sender_str = ''
    for part, encoding in decoded_sender:
        if isinstance(part, bytes):
            sender_str += part.decode(encoding or 'utf-8', errors='replace')
        else:
            sender_str += str(part)

    email_pattern = r'<?([\w\.-]+@[\w\.-]+)>?'
    match = re.search(email_pattern, sender_str)
    if match:
        return match.group(1)
    return sender_str

def process_email(sender, subject, body, received_at):
    sender_name, sender_email = email.utils.parseaddr(sender)
    sender_email = extract_email_address(sender)
    lead = Lead.query.filter_by(email=sender_email).first()

    if lead:
        email_obj = Email(sender=sender_email,
                          sender_name=sender_name,
                          subject=subject,
                          content=body,
                          received_at=received_at,
                          lead=lead)
        db.session.add(email_obj)
    else:
        current_app.logger.warning(
            f"Received email from unknown sender: {sender}")
        unknown_email = UnknownEmail(sender=sender_email,
                                     sender_name=sender_name,
                                     subject=subject,
                                     content=body,
                                     received_at=received_at)
        db.session.add(unknown_email)

    try:
        db.session.commit()
        if lead:
            current_app.logger.info(f"Stored email for lead: {lead.id}")
        else:
            current_app.logger.info(
                f"Stored email from unknown sender: {sender_email}")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error storing email: {str(e)}")

def fetch_emails(time_range=30, lead_id=None, max_emails=100):
    try:
        mail = connect_to_email_server()
        mail.select('inbox')

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(minutes=time_range)

        current_app.logger.info(
            f"Fetching emails for the last {time_range} minutes (from {start_date.strftime('%Y-%m-%d %H:%M:%S')} to {end_date.strftime('%Y-%m-%d %H:%M:%S')})"
        )

        try:
            search_criteria = f'(SINCE "{start_date.strftime("%d-%b-%Y")}")'
            _, search_data = mail.search(None, search_criteria)
        except imaplib.IMAP4.error as e:
            current_app.logger.error(f"Error in IMAP SEARCH command: {str(e)}")
            return

        total_emails = len(search_data[0].split())
        current_app.logger.info(f"Total emails found: {total_emails}")

        processed_emails = 0
        for num in search_data[0].split():
            if processed_emails >= max_emails:
                break
            try:
                _, msg_data = mail.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                email_date = email.utils.parsedate_to_datetime(email_message['Date'])
                if email_date.tzinfo is None:
                    email_date = email_date.replace(tzinfo=timezone.utc)
                
                if start_date <= email_date <= end_date:
                    subject = email_message["Subject"]
                    if subject:
                        subject_parts = decode_header(subject)
                        decoded_subject = ""
                        for content, charset in subject_parts:
                            if isinstance(content, bytes):
                                if charset is None:
                                    detected = chardet.detect(content)
                                    charset = detected['encoding']
                                try:
                                    decoded_subject += content.decode(
                                        charset or 'utf-8', errors='replace')
                                except (UnicodeDecodeError, LookupError):
                                    decoded_subject += content.decode(
                                        'utf-8', errors='replace')
                            else:
                                decoded_subject += content
                        subject = decoded_subject
                    else:
                        subject = "No Subject"

                    sender = email_message["From"]
                    
                    current_app.logger.info(
                        f"Processing email - Sender: {sender}, Subject: {subject}, Date: {email_date.strftime('%Y-%m-%d %H:%M:%S')}"
                    )

                    body = ""
                    if email_message.is_multipart():
                        for part in email_message.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        body = payload.decode(
                                            part.get_content_charset() or 'utf-8',
                                            errors='ignore')
                                        body = body.replace('\x00', '')
                                except Exception as e:
                                    current_app.logger.error(
                                        f"Error decoding email body: {str(e)}")
                                    body = "Error: Unable to decode email content"
                                break
                    else:
                        try:
                            payload = email_message.get_payload(decode=True)
                            if payload:
                                body = payload.decode(
                                    email_message.get_content_charset() or 'utf-8',
                                    errors='ignore')
                                body = body.replace('\x00', '')
                        except Exception as e:
                            current_app.logger.error(
                                f"Error decoding email body: {str(e)}")
                            body = "Error: Unable to decode email content"

                    process_email(sender, subject, body, email_date)
                    processed_emails += 1
            except Exception as e:
                current_app.logger.error(
                    f"Error processing email {num}: {str(e)}")

        current_app.logger.info(f"Processed {processed_emails} out of {total_emails} emails")

    except Exception as e:
        current_app.logger.error(f"Error in fetch_emails: {str(e)}")
    finally:
        try:
            mail.close()
            mail.logout()
        except Exception as e:
            current_app.logger.error(
                f"Error closing mail connection: {str(e)}")

    current_app.logger.info(
        f"Emails from known leads: {Email.query.filter(Email.received_at >= start_date).count()}"
    )
    current_app.logger.info(
        f"Emails from unknown senders: {UnknownEmail.query.filter(UnknownEmail.received_at >= start_date).count()}"
    )

def setup_email_scheduler(app):
    from flask_apscheduler import APScheduler
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    @scheduler.task('interval',
                    id='check_emails',
                    minutes=5,
                    misfire_grace_time=300,
                    max_instances=1)
    def check_emails_task():
        with app.app_context():
            app.logger.info("Checking for new emails")
            fetch_emails(time_range=30, max_emails=100)

    with app.app_context():
        app.logger.info("Email scheduler set up")