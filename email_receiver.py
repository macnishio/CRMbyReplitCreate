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
                check_emails()
            except Exception as e:
                app.logger.error(f"Error checking emails: {str(e)}")

    # Schedule email checking every 5 minutes
    scheduler.add_job(check_emails_task, 'interval', minutes=5)
    app.logger.info("Email scheduler started")

def check_emails():
    """Check for new emails and process them"""
    try:
        # Get all users with email settings
        from models import User, UserSettings
        users = User.query.join(UserSettings).all()

        for user in users:
            try:
                user_settings = UserSettings.query.filter_by(user_id=user.id).first()
                if not user_settings:
                    current_app.logger.warning(f"No email settings found for user {user.id}")
                    continue

                # Get last fetch time or default to 5 minutes ago
                tracker = EmailFetchTracker.query.filter_by(user_id=user.id)\
                    .order_by(EmailFetchTracker.last_fetch_time.desc()).first()

                if tracker:
                    last_fetch = tracker.last_fetch_time
                else:
                    last_fetch = datetime.utcnow() - timedelta(minutes=5)
                    tracker = EmailFetchTracker(user_id=user.id)
                    db.session.add(tracker)

                # Validate settings before connecting
                errors = validate_mail_settings(user_settings)
                if errors:
                    current_app.logger.error(f"Invalid mail settings for user {user.id}: {', '.join(errors)}")
                    continue

                # Connect to email server with retries
                mail = None
                max_retries = 3
                retry_delay = 5  # seconds

                for attempt in range(max_retries):
                    try:
                        mail = connect_to_email_server(user_settings)
                        if mail:
                            break
                        current_app.logger.warning(f"Failed to connect for user {user.id} on attempt {attempt + 1}, retrying...")
                        time.sleep(retry_delay)
                    except Exception as e:
                        current_app.logger.error(f"Connection attempt {attempt + 1} failed for user {user.id}: {str(e)}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        raise

                if not mail:
                    current_app.logger.error(f"Failed to connect to email server for user {user.id} after all retries")
                    continue

                # Search for new emails
                mail.select('INBOX')
                date_str = last_fetch.strftime("%d-%b-%Y")
                try:
                    _, message_numbers = mail.search(None, f'(SINCE "{date_str}")')
                except Exception as e:
                    current_app.logger.error(f"Error searching emails for user {user.id}: {str(e)}")
                    continue

                # Update last fetch time
                tracker.last_fetch_time = datetime.utcnow()
                db.session.commit()

                # Process each email
                for num in message_numbers[0].split():
                    try:
                        _, msg_data = mail.fetch(num, '(RFC822)')
                        if msg_data and msg_data[0] and msg_data[0][1]:
                            email_body = msg_data[0][1]
                            process_email(email_body, current_app)
                        else:
                            current_app.logger.warning(f"Skipping email {num} - invalid message data for user {user.id}")
                    except Exception as e:
                        current_app.logger.error(f"Error processing email {num} for user {user.id}: {str(e)}")
                        continue

                mail.close()
                mail.logout()

            except Exception as e:
                current_app.logger.error(f"Error processing emails for user {user.id}: {str(e)}")
                continue

    except Exception as e:
        current_app.logger.error(f"Error in check_emails: {str(e)}")
        raise

def get_user_settings(user_id):
    """Get user's email settings"""
    from models import UserSettings
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    return settings

def connect_to_email_server(user_settings):
    """Connect to email server with improved error handling and user settings"""
    if not user_settings:
        raise ValueError("User settings are required to connect to the email server.")

    mail_server = user_settings.mail_server
    mail_port = user_settings.mail_port
    mail_username = user_settings.mail_username
    mail_password = user_settings.mail_password

    if not all([mail_server, mail_port, mail_username, mail_password]):
        raise ValueError("One or more email connection settings are missing.")

    try:
        # Create SSL context with proper options
        ssl_context = ssl.create_default_context()
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = True

        # Remove any whitespace from credentials
        mail_username = mail_username.strip()
        mail_password = mail_password.strip()

        # Connect using SSL context
        mail = imaplib.IMAP4_SSL(
            host=mail_server,
            port=mail_port,
            ssl_context=ssl_context
        )

        current_app.logger.debug(f"Attempting connection to {mail_server}:{mail_port}")

        # Try standard login first
        try:
            mail.login(mail_username, mail_password)
            current_app.logger.info(f"Successfully connected to {mail_server}:{mail_port}")
            return mail
        except imaplib.IMAP4.error as e:
            current_app.logger.warning(f"Standard login failed: {str(e)}")

            # Try quoted credentials
            try:
                mail.login('"%s"' % mail_username, '"%s"' % mail_password)
                current_app.logger.info(f"Successfully connected using quoted credentials")
                return mail
            except imaplib.IMAP4.error as quoted_e:
                current_app.logger.error(f"Quoted login failed: {str(quoted_e)}")
                raise

    except ssl.SSLError as e:
        current_app.logger.error(f"SSL error connecting to mail server: {str(e)}")
        raise
    except imaplib.IMAP4.error as e:
        current_app.logger.error(f"IMAP error connecting to mail server: {str(e)}")
        raise
    except Exception as e:
        current_app.logger.error(f"Unexpected error connecting to mail server: {str(e)}")
        raise

def validate_mail_settings(user_settings):
    """メール設定の検証を行う補助関数"""
    if not user_settings:
        return ["User settings not found"]

    errors = []

    # 必須フィールドの確認
    required_fields = {
        'mail_server': 'Mail server',
        'mail_port': 'Mail port',
        'mail_username': 'Username',
        'mail_password': 'Password'
    }

    for field, label in required_fields.items():
        value = getattr(user_settings, field, None)
        if not value:
            errors.append(f"{label} is missing")
        elif isinstance(value, str) and not value.strip():
            errors.append(f"{label} is empty")

    # ポート番号の検証
    if user_settings.mail_port:
        try:
            port = int(user_settings.mail_port)
            if port <= 0 or port > 65535:
                errors.append("Invalid port number")
        except ValueError:
            errors.append("Port must be a number")

    return errors

def process_email(email_body, app):
    """Process a single email with improved error handling and lead management"""
    try:
        msg = email.message_from_bytes(email_body)
        subject = decode_email_header(msg['subject'])
        sender = decode_email_header(msg['from'])
        
        # Enhanced sender name extraction with better logging
        sender_name = extract_sender_name(sender)
        sender_email = extract_email_address(sender)
        
        app.logger.debug(f"Original sender: {sender}")
        app.logger.debug(f"Extracted name: {sender_name}")
        app.logger.debug(f"Extracted email: {sender_email}")
        
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
    """Extract sender name with enhanced parsing and validation"""
    if not sender:
        return ""
    
    try:
        # Log the original sender string for debugging
        current_app.logger.debug(f"Extracting name from: {sender}")
        
        # Remove any newlines and extra spaces
        sender = ' '.join(sender.strip().splitlines())
        
        # Pattern 1: "Display Name" <email@example.com>
        pattern1 = r'"([^"]+)"'
        match = re.search(pattern1, sender)
        if match:
            name = match.group(1).strip()
            current_app.logger.debug(f"Found name using pattern 1: {name}")
            return name
        
        # Pattern 2: Display Name <email@example.com>
        pattern2 = r'^([^<>]+?)\s*(?:<[^>]+>)'
        match = re.search(pattern2, sender)
        if match:
            name = match.group(1).strip().strip('"')
            if name and not re.match(r'^[^@]+@[^@]+\.[^@]+$', name):  # Ensure it's not just an email
                current_app.logger.debug(f"Found name using pattern 2: {name}")
                return name
        
        # Pattern 3: email@example.com (Display Name)
        pattern3 = r'\((.*?)\)'
        match = re.search(pattern3, sender)
        if match:
            name = match.group(1).strip()
            current_app.logger.debug(f"Found name using pattern 3: {name}")
            return name
        
        # Pattern 4: Extract email and use local part as name
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sender)
        if email_match:
            email = email_match.group(0)
            name = email.split('@')[0].replace('.', ' ').title()
            current_app.logger.debug(f"Using email local part as name: {name}")
            return name
        
        # Fallback: Use the whole string if it doesn't contain email-like patterns
        if not re.search(r'[<>@]', sender):
            current_app.logger.debug(f"Using full sender string as name: {sender}")
            return sender.strip()
        
        # Final fallback
        current_app.logger.warning(f"Could not extract name from sender: {sender}")
        return "Unknown Sender"
        
    except Exception as e:
        current_app.logger.error(f"Error extracting sender name: {str(e)}")
        return "Unknown Sender"

def extract_email_address(sender):
    """Extract email address with improved validation"""
    if not sender:
        return ""
    try:
        # Pattern 1: <email@example.com>
        match = re.search(r'<([^>]+)>', sender)
        if match:
            email = match.group(1).strip()
            if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                return email
        
        # Pattern 2: Plain email address
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sender)
        if match:
            return match.group(0).strip()
        
        return sender.strip()
    except Exception as e:
        current_app.logger.error(f"Error extracting email address: {str(e)}")
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
