import os
import imaplib
import email
from email.header import decode_header
import logging
from datetime import datetime, timedelta
from models import Lead, Email, UnknownEmail, EmailFetchTracker
from extensions import db
from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from ai_analysis import analyze_email
import json
import re

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
            _, msg_data = mail.fetch(num, '(RFC822)')
            email_body = msg_data[0][1]
            process_email(email_body, app)

        mail.close()
        mail.logout()

    except Exception as e:
        app.logger.error(f"Error checking emails: {str(e)}")
        raise

def connect_to_email_server(app):
    """Connect to email server with error handling and SSL options"""
    try:
        mail = imaplib.IMAP4_SSL(os.environ['MAIL_SERVER'])
        mail.login(os.environ['MAIL_USERNAME'], os.environ['MAIL_PASSWORD'])
        mail.select('inbox')
        return mail
    except Exception as e:
        app.logger.error(f"Failed to connect to email server: {str(e)}")
        return None

def process_email(email_body, app):
    """Process a single email"""
    try:
        msg = email.message_from_bytes(email_body)
        subject = decode_email_header(msg['subject'])
        sender = decode_email_header(msg['from'])
        sender_name = extract_sender_name(sender)
        sender_email = extract_email_address(sender)
        
        content = get_email_content(msg)
        app.logger.info(f"Email sender: {sender_name} <{sender_email}> Received at: {datetime.utcnow()}")

        lead = Lead.query.filter_by(email=sender_email).first()

        if lead:
            # Store email and update lead
            email_record = Email(
                sender=sender_email,
                sender_name=sender_name,
                subject=subject,
                content=content,
                lead_id=lead.id
            )
            lead.last_contact = datetime.utcnow()
            db.session.add(email_record)
            
            # Skip AI analysis for spam leads
            if lead.status != 'Spam':
                ai_response = analyze_email(subject, content, lead.user_id)
                process_ai_response(ai_response, lead, app)
            else:
                app.logger.info(f"Skipping AI analysis for spam lead: {sender_email}")
            
        else:
            # Store unknown email
            unknown_email = UnknownEmail(
                sender=sender_email,
                sender_name=sender_name,
                subject=subject,
                content=content
            )
            db.session.add(unknown_email)
            app.logger.info(f"Stored email from unknown sender: {sender_email}")

        db.session.commit()

    except Exception as e:
        app.logger.error(f"Error processing email: {str(e)}")
        db.session.rollback()
        raise

def process_ai_response(response, lead, app):
    """Process AI analysis response and create corresponding records"""
    try:
        if isinstance(response, str) and response.startswith('{'):
            data = json.loads(response)
            
            if 'Opportunities' in data:
                create_opportunities_from_ai(data['Opportunities'], lead)
            
            if 'Schedules' in data:
                create_schedules_from_ai(data['Schedules'], lead)
            
            if 'Tasks' in data:
                create_tasks_from_ai(data['Tasks'], lead)
            
            # Commit changes to ensure relationships are saved
            db.session.commit()
                
    except Exception as e:
        app.logger.error(f"Error processing AI response: {str(e)}")
        db.session.rollback()

def decode_email_header(header):
    """Decode email header with proper encoding"""
    if not header:
        return ""
    try:
        decoded_parts = []
        for part, encoding in decode_header(header):
            if isinstance(part, bytes):
                decoded_parts.append(part.decode(encoding or 'utf-8', errors='replace'))
            else:
                decoded_parts.append(part)
        return " ".join(decoded_parts)
    except Exception:
        return header

def get_email_content(msg):
    """Extract email content handling different content types"""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_payload(decode=True).decode()
                except:
                    continue
    else:
        try:
            return msg.get_payload(decode=True).decode()
        except:
            return msg.get_payload()
    return ""

def extract_sender_name(sender):
    """Extract sender name from email header"""
    match = re.match(r'"?([^"<]+)"?\s*(?:<[^>]+>)?', sender)
    return match.group(1).strip() if match else sender

def extract_email_address(sender):
    """Extract email address from sender header"""
    match = re.search(r'<([^>]+)>', sender)
    return match.group(1) if match else sender

def create_opportunities_from_ai(opportunities, lead):
    """Create opportunities from AI analysis"""
    from models import Opportunity
    
    for opp_desc in opportunities:
        if ':' in opp_desc:
            _, desc = opp_desc.split(':', 1)
            opportunity = Opportunity(
                name=desc.strip(),
                stage='Initial Contact',
                user_id=lead.user_id,
                lead_id=lead.id
            )
            db.session.add(opportunity)

def create_schedules_from_ai(schedules, lead):
    """Create schedules from AI analysis"""
    from models import Schedule
    
    for schedule in schedules:
        if isinstance(schedule, dict):
            if 'Description' in schedule and ':' in schedule['Description']:
                _, desc = schedule['Description'].split(':', 1)
                try:
                    start_time = datetime.strptime(schedule.get('Start Time', ''), '%Y-%m-%d %H:%M')
                    end_time = datetime.strptime(schedule.get('End Time', ''), '%Y-%m-%d %H:%M')
                except ValueError:
                    start_time = datetime.utcnow()
                    end_time = start_time + timedelta(hours=1)
                
                schedule_record = Schedule(
                    title=desc.strip(),
                    description=desc.strip(),
                    start_time=start_time,
                    end_time=end_time,
                    user_id=lead.user_id,
                    lead_id=lead.id
                )
                db.session.add(schedule_record)

def create_tasks_from_ai(tasks, lead):
    """Create tasks from AI analysis"""
    from models import Task
    
    for task in tasks:
        if isinstance(task, dict) and 'Description' in task and ':' in task['Description']:
            _, desc = task['Description'].split(':', 1)
            try:
                due_date = datetime.strptime(task.get('Due Date', ''), '%Y-%m-%d')
            except ValueError:
                due_date = datetime.utcnow() + timedelta(days=7)
            
            task_record = Task(
                title=desc.strip(),
                description=desc.strip(),
                due_date=due_date,
                status='New',
                user_id=lead.user_id,
                lead_id=lead.id
            )
            db.session.add(task_record)
