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
from ai_analysis import analyze_email
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

# Rest of the file remains the same...
