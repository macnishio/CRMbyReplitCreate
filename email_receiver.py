import os
import imaplib
import email
from email.header import decode_header
import logging
import ssl
from datetime import datetime, timedelta
from models import Lead, Email, UnknownEmail, EmailFetchTracker, UserSettings
from extensions import db
from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from ai_analysis import analyze_email, process_ai_response
import json
import re
import time
from threading import Thread

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

        # Connect to email server
        mail = connect_to_email_server(app)
        if not mail:
            return

        # Search for new emails
        date_str = last_fetch.strftime("%d-%b-%Y")
        _, message_numbers = mail.search(None, f'(SINCE "{date_str}")')

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
        ssl_context = ssl.create_default_context()
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = True
        
        mail = imaplib.IMAP4_SSL(
            host=os.environ['MAIL_SERVER'],
            ssl_context=ssl_context
        )
        
        mail.login(os.environ['MAIL_USERNAME'], os.environ['MAIL_PASSWORD'])
        mail.select('inbox')
        return mail
        
    except Exception as e:
        app.logger.error(f"Error connecting to mail server: {str(e)}")
        return None

def extract_sender_name(sender):
    """Extract sender name with improved parsing for full names and Japanese characters"""
    if not sender:
        return ""
    try:
        # Pattern 1: "Full Name" <email@example.com>
        quoted_pattern = r'"([^"]+)".*'
        match = re.match(quoted_pattern, sender)
        if match:
            name = match.group(1).strip()
            if len(name) > 1:  # Only use if name is more than 1 character
                return name

        # Pattern 2: Full Name <email@example.com>
        name_pattern = r'([^<>]+?)\s*(?:<[^>]+>)?'
        match = re.match(name_pattern, sender)
        if match:
            name = match.group(1).strip()
            # Remove any remaining email parts and clean up
            name = re.sub(r'\S+@\S+\.\S+', '', name).strip()
            if name and len(name) > 1:  # Only use if name is more than 1 character
                # Clean any remaining special characters
                name = re.sub(r'["\']', '', name)
                return name

        # Pattern 3: Organization name from email domain
        email_pattern = r'[\w\.-]+@([\w\.-]+)'
        match = re.search(email_pattern, sender)
        if match:
            domain = match.group(1)
            if '.' in domain:
                parts = domain.split('.')
                # Try to extract organization name, avoiding common TLDs and email providers
                org_parts = [p for p in parts if p.lower() not in {'com', 'co', 'jp', 'net', 'org', 'edu', 'gov', 'gmail', 'yahoo', 'outlook', 'hotmail'}]
                if org_parts:
                    org_name = org_parts[0].title()
                    if len(org_name) > 1:  # Only use if org name is more than 1 character
                        return org_name

        # Pattern 4: Try to get full name from email username
        if '@' in sender:
            username = sender.split('@')[0]
            # Replace common separators with spaces
            clean_username = re.sub(r'[._-]', ' ', username).title()
            if len(clean_username) > 1:  # Only use if username is more than 1 character
                return clean_username

        # Pattern 5: Use the entire original sender name if no good alternative found
        original_name = sender.split('@')[0] if '@' in sender else sender
        if len(original_name.strip()) > 1:
            return original_name.strip()

        return "Unknown Sender"  # Default fallback if everything else fails
    except Exception as e:
        current_app.logger.error(f"Error extracting sender name: {str(e)}")
        return "Unknown Sender"

def process_email(email_body, app):
    """Process a single email"""
    try:
        msg = email.message_from_bytes(email_body)
        subject = decode_email_header(msg['subject'])
        sender = decode_email_header(msg['from'])
        sender_name = extract_sender_name(sender)
        sender_email = extract_email_address(sender)
        
        content = get_email_content(msg)
        received_date = parse_email_date(msg.get('date'))
        app.logger.info(f"Processing email from: {sender_name} <{sender_email}>")

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
                db.session.flush()
                app.logger.info(f"Created new lead for sender: {sender_email}")

        if lead:
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
            
            # Update lead name if current one is empty or single character
            if not lead.name or len(lead.name.strip()) <= 1:
                lead.name = sender_name
                app.logger.info(f"Updated lead name to: {sender_name}")
            
            db.session.add(email_record)
            
            if lead.status != 'Spam':
                try:
                    ai_response = analyze_email(subject, content, lead.user_id)
                    process_ai_response(ai_response, lead, app)
                except Exception as e:
                    app.logger.error(f"AI analysis error: {str(e)}")
            else:
                app.logger.info(f"Skipping AI analysis for spam lead: {sender_email}")
        else:
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
    """Decode email header with proper encoding"""
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
    except Exception:
        return str(header)

def get_email_content(msg):
    """Extract email content with proper MIME handling"""
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

def extract_email_address(sender):
    """Extract email address with proper validation"""
    if not sender:
        return ""
    try:
        match = re.search(r'<([^>]+)>', sender)
        if match:
            return match.group(1).strip()
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
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str)
    except Exception as e:
        current_app.logger.warning(f"Error parsing email date: {str(e)}")
        return None
