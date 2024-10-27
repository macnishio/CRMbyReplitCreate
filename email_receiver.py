import os
import imaplib
import email
from email.header import decode_header
import logging
from datetime import datetime, timedelta
import pytz
from models import Lead, Email, EmailFetchTracker, UserSettings
from extensions import db
from flask import current_app
import re
from ai_analysis import analyze_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_email_content(content):
    # Remove HTML tags
    content = re.sub(r'<[^>]+>', '', content)
    # Remove extra whitespace
    content = ' '.join(content.split())
    return content

def extract_sender_name(sender):
    # Try to extract name from format "Name <email@example.com>"
    name_match = re.match(r'^([^<]*?)\s*(?:<[^>]*>)?$', sender)
    if name_match:
        name = name_match.group(1).strip()
        if name:
            # Decode any encoded parts
            try:
                decoded_parts = []
                for part, charset in decode_header(name):
                    if isinstance(part, bytes):
                        decoded_parts.append(part.decode(charset or 'utf-8', errors='ignore'))
                    else:
                        decoded_parts.append(part)
                return ''.join(decoded_parts).strip()
            except:
                return name
    return None

def update_lead_status(lead, reason):
    if lead.status != "Spam":
        lead.status = "Spam"
        logger.info(f"Updated lead {lead.id} status from {lead.status} to Spam. Reason: {reason}")

def is_mass_email(sender, subject, received_time):
    # Common mass mail domains
    mass_mail_domains = [
        'mail.rakuten.com', 'newsletters.com', 'marketing.com',
        'campaign.com', 'mailchimp.com', 'sendgrid.net'
    ]
    
    # Check sender domain
    if any(domain in sender.lower() for domain in mass_mail_domains):
        return True, f"Sent from mass mail domain: {sender}"
    
    # Check for typical newsletter/marketing keywords in subject
    marketing_keywords = [
        'newsletter', 'subscription', 'unsubscribe', 'campaign',
        'offer', 'discount', '🎉', '📰', '🔥'
    ]
    if subject and any(keyword in subject.lower() for keyword in marketing_keywords):
        return True, f"Marketing keywords detected in subject: {subject}"
    
    # Check if sent during off-hours (between 22:00 and 6:00)
    if received_time:
        hour = received_time.hour
        if hour >= 22 or hour < 6:
            return True, f"Sent during off-hours: {hour}:00"
    
    return False, None

def connect_to_email_server(settings, attempt=1, max_attempts=3):
    """Connect to email server with retry mechanism"""
    logger.info(f"Attempt {attempt} to connect to mail server for user {settings.user_id}")
    
    try:
        mail = imaplib.IMAP4_SSL(settings.mail_server)
        mail.login(settings.mail_username, settings.mail_password)
        return mail
    except Exception as e:
        if attempt < max_attempts:
            return connect_to_email_server(settings, attempt + 1, max_attempts)
        else:
            raise Exception(f"Failed to connect to mail server after {max_attempts} attempts: {str(e)}")

def process_email(email_message, lead, user_id):
    """Process a single email message"""
    try:
        # Extract message ID
        message_id = email_message.get('Message-ID', email_message.get('Message-Id'))
        if not message_id:
            logger.warning("No Message-ID found in email")
            return
            
        # Check if email already exists
        existing_email = Email.query.filter_by(message_id=message_id).first()
        if existing_email:
            logger.info(f"Skipping already processed email: {message_id}")
            return
            
        # Get sender information
        sender = email.utils.parseaddr(email_message['From'])[1]
        sender_name = extract_sender_name(email_message['From'])
        
        # Get subject
        subject = ''
        if email_message['Subject']:
            subject_parts = decode_header(email_message['Subject'])
            subject = ''.join(
                part.decode(charset or 'utf-8') if isinstance(part, bytes) else part
                for part, charset in subject_parts
            )
            
        # Get received date
        date_str = email_message['Date']
        received_date = email.utils.parsedate_to_datetime(date_str)
        
        # Get content
        content = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        part_content = part.get_payload(decode=True).decode()
                        content += clean_email_content(part_content)
                    except:
                        continue
        else:
            try:
                content = clean_email_content(email_message.get_payload(decode=True).decode())
            except:
                content = "Content extraction failed"
                
        # Check for mass email characteristics
        is_mass, reason = is_mass_email(sender, subject, received_date)
        if is_mass:
            logger.info(f"Detected mass email from {sender}. Reason: {reason}")
            if lead:
                update_lead_status(lead, reason)
                
        # Create email record
        email_record = Email(
            message_id=message_id,
            sender=sender,
            sender_name=sender_name,
            subject=subject,
            content=content,
            received_date=received_date,
            lead_id=lead.id if lead else None,
            user_id=user_id
        )
        
        db.session.add(email_record)
        db.session.commit()
        
        return email_record
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing lead and email record: {str(e)}")
        raise

def fetch_emails(user_id):
    """Fetch emails for a user"""
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    if not settings or not settings.mail_username or not settings.mail_password:
        return
        
    try:
        # Connect to mail server
        logger.info(f"Attempting to connect to {settings.mail_server} for user {settings.mail_username}")
        mail = connect_to_email_server(settings)
        
        # Select inbox
        logger.debug("Selecting inbox")
        mail.select('inbox')
        
        # Get last fetch time
        tracker = EmailFetchTracker.query.filter_by(user_id=user_id).first()
        if not tracker:
            tracker = EmailFetchTracker(user_id=user_id)
            db.session.add(tracker)
            
        since_time = tracker.last_fetch_time - timedelta(minutes=5)
        since_date = since_time.strftime("%d-%b-%Y")
        
        logger.info(f"Successfully connected to mailbox for {settings.mail_username}")
        
        # Search for emails since last fetch
        _, message_numbers = mail.search(None, f'(SINCE "{since_date}")')
        
        email_count = 0
        for num in message_numbers[0].split():
            # Fetch email message
            _, msg_data = mail.fetch(num, '(RFC822)')
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Get sender
            sender = email.utils.parseaddr(email_message['From'])[1]
            
            # Find or create lead
            lead = Lead.query.filter_by(email=sender, user_id=user_id).first()
            
            # Process email
            process_email(email_message, lead, user_id)
            email_count += 1
            
        # Update last fetch time
        tracker.last_fetch_time = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Processed {email_count} emails for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error fetching emails: {str(e)}")
        db.session.rollback()
    finally:
        try:
            mail.close()
            mail.logout()
        except:
            pass

def setup_email_scheduler(app):
    """Set up scheduled email fetching"""
    from apscheduler.schedulers.background import BackgroundScheduler
    
    scheduler = BackgroundScheduler()
    
    def fetch_all_emails():
        with app.app_context():
            logger.info("Running scheduled email fetch")
            users = UserSettings.query.filter(
                UserSettings.mail_username.isnot(None),
                UserSettings.mail_password.isnot(None)
            ).all()
            for user_settings in users:
                try:
                    fetch_emails(user_settings.user_id)
                except Exception as e:
                    logger.error(f"Error fetching emails for user {user_settings.user_id}: {str(e)}")
            logger.info(f"Processed emails for {len(users)} users")
    
    # Run initial check on startup
    logger.info("Running initial email check on startup")
    fetch_all_emails()
    
    # Schedule regular checks every 5 minutes
    scheduler.add_job(fetch_all_emails, 'interval', minutes=5)
    scheduler.start()
    logger.info("Email scheduler started")
    
    return scheduler
