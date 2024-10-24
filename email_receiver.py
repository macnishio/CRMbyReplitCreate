import os
import imaplib
import email
from email.header import decode_header
import logging
import ssl
from datetime import datetime, timedelta
from models import Lead, Email, UnknownEmail, EmailFetchTracker
from extensions import db
from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from ai_analysis import analyze_email, process_ai_response
import json
import re
import time

def setup_email_scheduler(app):
    """Setup scheduler for periodic email checking"""
    scheduler = BackgroundScheduler()
    scheduler.start()
    
    def check_emails_task():
        """Task to check for new emails"""
        with app.app_context():
            try:
                check_emails(app)
            except Exception as e:
                app.logger.error(f"Error checking emails: {str(e)}")
    
    # Schedule email checking every 5 minutes
    scheduler.add_job(check_emails_task, 'interval', minutes=5)
    app.logger.info("Email scheduler started")

def check_emails(app):
    """Check for new emails and process them"""
    try:
        # Get last fetch time or default to 5 minutes ago
        tracker = EmailFetchTracker.query.order_by(EmailFetchTracker.last_fetch_time.desc()).first()
        if tracker:
            last_fetch = tracker.last_fetch_time
        else:
            last_fetch = datetime.utcnow() - timedelta(minutes=5)
            tracker = EmailFetchTracker()
            db.session.add(tracker)

        # Connect to email server with retries
        mail = None
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                mail = connect_to_email_server(app)
                if mail:
                    break
                app.logger.warning(f"Failed to connect on attempt {attempt + 1}, retrying...")
                time.sleep(retry_delay)
            except Exception as e:
                app.logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise

        if not mail:
            app.logger.error("Failed to connect to email server after all retries")
            return

        # Search for new emails
        date_str = last_fetch.strftime("%d-%b-%Y")
        try:
            _, message_numbers = mail.search(None, f'(SINCE "{date_str}")')
        except Exception as e:
            app.logger.error(f"Error searching emails: {str(e)}")
            return

        # Update last fetch time
        tracker.last_fetch_time = datetime.utcnow()
        db.session.commit()

        # Process each email
        for num in message_numbers[0].split():
            try:
                _, msg_data = mail.fetch(num, '(RFC822)')
                if msg_data and msg_data[0] and msg_data[0][1]:
                    email_body = msg_data[0][1]
                    process_email(email_body, app)
                else:
                    app.logger.warning(f"Skipping email {num} - invalid message data")
            except Exception as e:
                app.logger.error(f"Error processing email {num}: {str(e)}")
                continue

        mail.close()
        mail.logout()

    except Exception as e:
        app.logger.error(f"Error checking emails: {str(e)}")
        raise

def connect_to_email_server(app):
    """Connect to email server with improved error handling and SSL options"""
    try:
        # Create SSL context with proper options
        ssl_context = ssl.create_default_context()
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = True
        
        # Connect using SSL context
        mail = imaplib.IMAP4_SSL(
            host=os.environ['MAIL_SERVER'],
            ssl_context=ssl_context
        )
        
        # Authenticate with proper error handling
        try:
            mail.login(os.environ['MAIL_USERNAME'], os.environ['MAIL_PASSWORD'])
        except imaplib.IMAP4.error as e:
            app.logger.error(f"IMAP login error: {str(e)}")
            return None
        
        # Select inbox
        mail.select('inbox')
        return mail
        
    except ssl.SSLError as e:
        app.logger.error(f"SSL error connecting to mail server: {str(e)}")
        return None
    except imaplib.IMAP4.error as e:
        app.logger.error(f"IMAP error connecting to mail server: {str(e)}")
        return None
    except Exception as e:
        app.logger.error(f"Unexpected error connecting to mail server: {str(e)}")
        return None

def process_email(email_body, app):
    """Process a single email with improved error handling and lead management"""
    try:
        msg = email.message_from_bytes(email_body)
        subject = decode_email_header(msg['subject'])
        sender = decode_email_header(msg['from'])
        sender_name = extract_sender_name(sender)
        sender_email = extract_email_address(sender)
        
        content = get_email_content(msg)
        received_date = parse_email_date(msg.get('date'))
        app.logger.info(f"Processing email from: {sender_name} <{sender_email}> Received at: {received_date}")

        with db.session.begin_nested():  # Create savepoint
            # Find existing lead or create new one
            lead = Lead.query.filter_by(email=sender_email).first()
            
            if not lead:
                # Find a reference user_id from existing leads
                reference_lead = Lead.query.first()
                if reference_lead:
                    lead = Lead(
                        name=sender_name,
                        email=sender_email,
                        status='New',
                        score=0.0,
                        user_id=reference_lead.user_id,
                        last_contact=received_date or datetime.utcnow()
                    )
                    db.session.add(lead)
                    db.session.flush()  # Get ID without committing
                    app.logger.info(f"Created new lead for sender: {sender_email}")

            if lead:
                # Store email and update lead
                email_record = Email(
                    sender=sender_email,
                    sender_name=sender_name,
                    subject=subject,
                    content=content,
                    lead_id=lead.id,
                    user_id=lead.user_id,
                    received_date=received_date
                )
                lead.last_contact = received_date or datetime.utcnow()
                
                # Update empty lead name if available
                if (not lead.name or lead.name.strip() == '') and sender_name:
                    lead.name = sender_name
                    app.logger.info(f"Updated empty lead name to: {sender_name}")
                
                db.session.add(email_record)
                
                # Skip AI analysis for spam leads
                if lead.status != 'Spam':
                    try:
                        ai_response = analyze_email(subject, content, lead.user_id)
                        process_ai_response(ai_response, lead, app)
                    except Exception as ai_error:
                        app.logger.error(f"AI analysis error for email {email_record.id}: {str(ai_error)}")
                else:
                    app.logger.info(f"Skipping AI analysis for spam lead: {sender_email}")
            else:
                # Store unknown email if we couldn't create a lead
                unknown_email = UnknownEmail(
                    sender=sender_email,
                    sender_name=sender_name,
                    subject=subject,
                    content=content,
                    received_date=received_date
                )
                db.session.add(unknown_email)
                app.logger.info(f"Stored email from unknown sender: {sender_email}")

            db.session.commit()

    except Exception as e:
        app.logger.error(f"Error processing email: {str(e)}")
        db.session.rollback()
        raise

def decode_email_header(header):
    """Decode email header with improved error handling"""
    if not header:
        return ""
    try:
        decoded_parts = []
        for part, encoding in decode_header(header):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(encoding or 'utf-8', errors='replace'))
                except (UnicodeDecodeError, LookupError):
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(str(part))
        return " ".join(decoded_parts)
    except Exception as e:
        current_app.logger.warning(f"Header decoding error: {str(e)}")
        return str(header)

def get_email_content(msg):
    """Extract email content with improved MIME handling"""
    content = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    part_content = part.get_payload(decode=True)
                    if isinstance(part_content, bytes):
                        content.append(part_content.decode('utf-8', errors='replace'))
                    else:
                        content.append(str(part_content))
                except Exception as e:
                    current_app.logger.warning(f"Error decoding email part: {str(e)}")
                    continue
    else:
        try:
            payload = msg.get_payload(decode=True)
            if isinstance(payload, bytes):
                content.append(payload.decode('utf-8', errors='replace'))
            else:
                content.append(str(payload))
        except Exception as e:
            current_app.logger.warning(f"Error decoding email payload: {str(e)}")
            content.append(msg.get_payload())
    
    return "\n".join(content)

def extract_sender_name(sender):
    """Extract sender name with improved parsing"""
    if not sender:
        return ""
    try:
        # Try to match "Name" <email> format
        match = re.match(r'"([^"]+)"|([^<]+?)\s*(?:<[^>]+>)?', sender)
        if match:
            name = match.group(1) or match.group(2)
            return name.strip().strip('"')
        return sender.split('@')[0]  # Fallback to email username
    except Exception:
        return sender

def extract_email_address(sender):
    """Extract email address with improved validation"""
    if not sender:
        return ""
    try:
        # Try to match <email> format
        match = re.search(r'<([^>]+)>', sender)
        if match:
            return match.group(1).strip()
        # Try to match plain email format
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sender)
        if match:
            return match.group(0).strip()
        return sender.strip()
    except Exception:
        return sender

def parse_email_date(date_str):
    """Parse email date string to datetime"""
    if not date_str:
        return None
    try:
        # Convert email date string to datetime
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str)
    except Exception as e:
        current_app.logger.warning(f"Error parsing email date: {str(e)}")
        return None
