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
from contextlib import contextmanager
from threading import Thread

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = db.session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

def process_emails_for_user(settings, parent_session, app):
    """Process emails for a single user with exponential backoff"""
    # Get or create tracker
    tracker = parent_session.query(EmailFetchTracker)\
        .filter_by(user_id=settings.user_id)\
        .order_by(EmailFetchTracker.last_fetch_time.desc())\
        .first()
    
    if not tracker:
        tracker = EmailFetchTracker(
            user_id=settings.user_id,
            last_fetch_time=datetime.utcnow() - timedelta(minutes=5)
        )
        parent_session.add(tracker)
        parent_session.flush()

    # Connect to email server with exponential backoff
    mail = None
    retry_delays = [5, 10, 20]  # Exponential backoff delays in seconds
    
    for attempt, delay in enumerate(retry_delays):
        try:
            mail = connect_to_email_server(app, settings)
            if mail:
                break
            app.logger.warning(f"Failed to connect on attempt {attempt + 1}, waiting {delay}s before retry...")
            time.sleep(delay)
        except imaplib.IMAP4.error as e:
            error_str = str(e)
            if '[UNAVAILABLE]' in error_str:
                app.logger.error(f"Server temporarily unavailable (attempt {attempt + 1}): {error_str}")
                if attempt < len(retry_delays) - 1:
                    time.sleep(delay)
                    continue
                app.logger.error("Server still unavailable after all retries")
                return
            app.logger.error(f"IMAP error on attempt {attempt + 1}: {error_str}")
            if attempt < len(retry_delays) - 1:
                time.sleep(delay)
                continue
        except Exception as e:
            app.logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
            if attempt < len(retry_delays) - 1:
                time.sleep(delay)
                continue
            app.logger.error("Failed all connection attempts")
            return

    if not mail:
        app.logger.error(f"Failed to connect to email server for user {settings.user_id} after all retries")
        return

    try:
        # Search for new emails
        date_str = tracker.last_fetch_time.strftime("%d-%b-%Y")
        try:
            _, message_numbers = mail.search(None, f'(SINCE "{date_str}")')
        except imaplib.IMAP4.error as e:
            app.logger.error(f"IMAP search error: {str(e)}")
            return

        # Process each email
        processed_count = 0
        for num in message_numbers[0].split():
            try:
                _, msg_data = mail.fetch(num, '(RFC822)')
                if msg_data and msg_data[0] and msg_data[0][1]:
                    email_body = msg_data[0][1]
                    msg = email.message_from_bytes(email_body)
                    
                    # メールの重複チェックのために必要な情報を取得
                    message_id = msg.get('Message-ID', '')
                    
                    # 既に処理済みのメールかチェック
                    if message_id:
                        existing_email = parent_session.query(Email)\
                            .filter_by(
                                message_id=message_id,
                                user_id=settings.user_id
                            ).first()
                        
                        if existing_email:
                            app.logger.info(f"Skipping already processed email: {message_id}")
                            continue
                    
                    subject = decode_email_header(msg['subject'])
                    sender = decode_email_header(msg['from'])
                    sender_name = extract_sender_name(sender)
                    sender_email = extract_email_address(sender)
                    content = get_email_content(msg)
                    received_date = parse_email_date(msg.get('date'))
                    
                    lead = parent_session.query(Lead).filter_by(email=sender_email, user_id=settings.user_id).first()
                    if not lead:
                        lead = Lead(
                            name=sender_name,
                            email=sender_email,
                            status='New',
                            score=0.0,
                            user_id=settings.user_id,
                            last_contact=received_date or datetime.utcnow()
                        )
                        parent_session.add(lead)
                        parent_session.flush()

                    # Analyze email if not spam
                    if lead.status != 'Spam':
                        try:
                            ai_response = analyze_email(subject, content, lead.user_id)
                            process_ai_response(ai_response, lead, app)
                        except Exception as e:
                            app.logger.error(f"AI analysis error: {str(e)}")
                    
                    email_record = Email(
                        message_id=message_id,  # メールIDを保存
                        sender=sender_email,
                        sender_name=sender_name,
                        subject=subject,
                        content=content,
                        lead_id=lead.id,
                        user_id=settings.user_id,
                        received_date=received_date
                    )
                    parent_session.add(email_record)
                    processed_count += 1
                    
                    # 処理済みメールのログを残す
                    app.logger.info(f"Processed email: {message_id} from {sender_email}")
            
            except Exception as e:
                app.logger.error(f"Error processing email {num}: {str(e)}")
                continue

        # Update tracker
        try:
            tracker.last_fetch_time = datetime.utcnow()
            parent_session.commit()
        except Exception as e:
            app.logger.error(f"Error updating tracker: {str(e)}")
            parent_session.rollback()
            raise
        
        app.logger.info(f"Processed {processed_count} emails for user {settings.user_id}")

    except Exception as e:
        app.logger.error(f"Error checking emails for user {settings.user_id}: {str(e)}")
        raise
    finally:
        try:
            mail.close()
            mail.logout()
        except:
            pass

def check_emails_task(app):
    """Task to check for new emails"""
    with app.app_context():
        try:
            with session_scope() as session:
                settings_list = session.query(UserSettings).all()
                processed_count = 0
                
                for settings in settings_list:
                    try:
                        process_emails_for_user(settings, session, app)
                        processed_count += 1
                    except Exception as e:
                        app.logger.error(f"Error processing emails for user {settings.user_id}: {str(e)}")
                        continue
                        
                app.logger.info(f"Processed emails for {processed_count} users")
        except Exception as e:
            app.logger.error(f"Error in check_emails_task: {str(e)}")

def setup_email_scheduler(app):
    """Setup scheduler for periodic email checking with immediate first run"""
    scheduler = BackgroundScheduler()
    
    def run_initial_check():
        with app.app_context():
            app.logger.info("Running initial email check on startup")
            check_emails_task(app)
    
    # Run initial check in a background thread
    Thread(target=run_initial_check).start()
    
    # Schedule email checking every 5 minutes
    scheduler.add_job(lambda: check_emails_task(app), 'interval', minutes=5)
    scheduler.start()
    app.logger.info("Email scheduler started")

def connect_to_email_server(app, settings):
    """Connect to email server with improved error handling"""
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = True
        
        mail = imaplib.IMAP4_SSL(
            host=settings.mail_server,
            ssl_context=ssl_context
        )
        
        try:
            mail.login(settings.mail_username, settings.mail_password)
            status, messages = mail.select('inbox')
            if status != 'OK':
                app.logger.error(f"Failed to select inbox: {messages}")
                return None
            return mail
            
        except imaplib.IMAP4.error as e:
            error_str = str(e)
            if '[UNAVAILABLE]' in error_str:
                app.logger.error(f"Server temporarily unavailable during login: {error_str}")
            else:
                app.logger.error(f"IMAP login error: {error_str}")
            return None
        
    except ssl.SSLError as e:
        app.logger.error(f"SSL error connecting to mail server: {str(e)}")
        return None
    except imaplib.IMAP4.error as e:
        error_str = str(e)
        if '[UNAVAILABLE]' in error_str:
            app.logger.error(f"Server temporarily unavailable: {error_str}")
        else:
            app.logger.error(f"IMAP error connecting to mail server: {error_str}")
        return None
    except Exception as e:
        app.logger.error(f"Unexpected error connecting to mail server: {str(e)}")
        return None

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
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str)
    except Exception as e:
        current_app.logger.warning(f"Error parsing email date: {str(e)}")
        return None
