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

def clean_string(text):
    """Remove NUL characters and other problematic characters from string"""
    if text is None:
        return ""
    # 整数型の場合は文字列に変換
    if isinstance(text, int):
        return str(text)
    if isinstance(text, bytes):
        text = text.replace(b'\x00', b'')
        try:
            return text.decode('utf-8', errors='replace').strip()
        except (UnicodeDecodeError, AttributeError):
            return text.decode('ascii', errors='replace').strip()
    else:
        return str(text).replace('\x00', '').strip()

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
    mail = None
    try:
        # Get or create tracker within a transaction
        with parent_session.begin_nested():
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
        retry_delays = [5, 10, 20]

        for attempt, delay in enumerate(retry_delays):
            try:
                mail = connect_to_email_server(app, settings)
                if mail:
                    break
                app.logger.warning(f"Failed to connect on attempt {attempt + 1}, waiting {delay}s before retry...")
                time.sleep(delay)
            except (imaplib.IMAP4.error, Exception) as e:
                app.logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < len(retry_delays) - 1:
                    time.sleep(delay)
                    continue
                app.logger.error("Failed all connection attempts")
                return

        if not mail:
            app.logger.error(f"Failed to connect to email server for user {settings.user_id} after all retries")
            return

        # Search for new emails
        date_str = tracker.last_fetch_time.strftime("%d-%b-%Y")
        _, message_numbers = mail.search(None, f'(SINCE "{date_str}")')

        # Process each email
        processed_count = 0
        for num in message_numbers[0].split():
            try:
                with parent_session.begin_nested():  # Create savepoint for each email
                    _, msg_data = mail.fetch(num, '(RFC822)')
                    if not (msg_data and msg_data[0] and msg_data[0][1]):
                        continue

                    email_body = msg_data[0][1]
                    msg = email.message_from_bytes(email_body)
                    message_id = clean_string(msg.get('Message-ID', ''))

                    # Skip if already processed
                    if message_id:
                        existing_email = parent_session.query(Email)\
                            .filter_by(message_id=message_id, user_id=settings.user_id)\
                            .first()
                        if existing_email:
                            app.logger.info(f"Skipping already processed email: {message_id}")
                            continue

                    # Extract email data
                    subject = clean_string(decode_email_header(msg['subject']))
                    sender = clean_string(decode_email_header(msg['from']))
                    sender_name = clean_string(extract_sender_name(sender))
                    sender_email = clean_string(extract_email_address(sender))
                    content = clean_string(get_email_content(msg))
                    received_date = parse_email_date(msg.get('date'))

                    # Get or create lead
                    lead = parent_session.query(Lead)\
                        .filter_by(email=sender_email, user_id=settings.user_id)\
                        .first()

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

                    # Create email record
                    email_record = Email(
                        message_id=message_id,
                        sender=sender_email,
                        sender_name=sender_name,
                        subject=subject,
                        content=content,
                        lead_id=lead.id,
                        user_id=settings.user_id,
                        received_date=received_date
                    )
                    parent_session.add(email_record)
                    parent_session.flush()

                    # AI analysis
                    if lead.status != 'Spam':
                        try:
                            ai_response = analyze_email(subject, content, lead.user_id)
                            email_record.ai_analysis = ai_response
                            email_record.ai_analysis_date = datetime.utcnow()
                            email_record.ai_model_used = "claude-3-haiku-20240307"
                            process_ai_response(ai_response, email_record, app)
                        except Exception as e:
                            app.logger.error(f"AI analysis error: {str(e)}")

                    processed_count += 1
                    app.logger.info(f"Processed email: {message_id} from {sender_email}")

            except Exception as e:
                app.logger.error(f"Error processing email {num}: {str(e)}")
                continue

        # Update tracker
        try:
            with parent_session.begin_nested():
                tracker.last_fetch_time = datetime.utcnow()
            parent_session.commit()
            app.logger.info(f"Processed {processed_count} emails for user {settings.user_id}")
        except Exception as e:
            app.logger.error(f"Error updating tracker: {str(e)}")
            parent_session.rollback()
            raise

    except Exception as e:
        app.logger.error(f"Error checking emails for user {settings.user_id}: {str(e)}")
        raise

    finally:
        if mail:
            try:
                mail.close()
                mail.logout()
            except Exception:
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
    """
    Decode email header with improved Japanese encoding support and error handling
    """
    if not header:
        return ""
    
    try:
        decoded_parts = []
        for part, encoding in decode_header(header):
            if isinstance(part, bytes):
                try:
                    # 日本語エンコーディングの優先順位付き処理
                    if encoding and encoding.lower() in ['iso-2022-jp', 'iso2022_jp', 'iso2022jp']:
                        decoded_parts.append(part.decode('iso-2022-jp', errors='replace'))
                    elif encoding and encoding.lower() in ['shift_jis', 'shift-jis', 'sjis', 'cp932']:
                        decoded_parts.append(part.decode('cp932', errors='replace'))
                    elif encoding and encoding.lower() in ['euc_jp', 'euc-jp', 'eucjp']:
                        decoded_parts.append(part.decode('euc_jp', errors='replace'))
                    elif encoding:
                        decoded_parts.append(part.decode(encoding, errors='replace'))
                    else:
                        # エンコーディングが指定されていない場合の処理
                        for enc in ['utf-8', 'iso-2022-jp', 'cp932', 'euc_jp']:
                            try:
                                decoded_text = part.decode(enc)
                                decoded_parts.append(decoded_text)
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            # どのエンコーディングでも失敗した場合
                            decoded_parts.append(part.decode('utf-8', errors='replace'))
                except (UnicodeDecodeError, LookupError) as e:
                    current_app.logger.warning(f"Decoding error with {encoding}: {str(e)}")
                    # フォールバック: UTF-8でデコード
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(str(part))
        
        # 空白で結合する前に不要な空白を削除
        cleaned_parts = [part.strip() for part in decoded_parts if part.strip()]
        return " ".join(cleaned_parts)
        
    except Exception as e:
        current_app.logger.error(f"Header decoding error: {str(e)}")
        try:
            # 最後の手段として元のヘッダーを文字列として返す
            if isinstance(header, bytes):
                return header.decode('utf-8', errors='replace')
            return str(header)
        except Exception as e:
            current_app.logger.error(f"Final fallback error: {str(e)}")
            return "（件名を表示できません）"

def get_email_content(msg):
    """Extract email content with improved MIME handling and NUL character removal"""
    content = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    part_content = part.get_payload(decode=True)
                    if part_content:
                        # 型チェックと変換を追加
                        if isinstance(part_content, int):
                            content.append(str(part_content))
                        elif isinstance(part_content, bytes):
                            decoded = clean_string(part_content)
                            content.append(decoded)
                        else:
                            content.append(clean_string(part_content))
                except Exception as e:
                    current_app.logger.warning(f"Error decoding email part: {str(e)}")
                    continue
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                # 型チェックと変換を追加
                if isinstance(payload, int):
                    content.append(str(payload))
                elif isinstance(payload, bytes):
                    decoded = clean_string(payload)
                    content.append(decoded)
                else:
                    content.append(clean_string(payload))
        except Exception as e:
            current_app.logger.warning(f"Error decoding email payload: {str(e)}")
            content.append(clean_string(msg.get_payload()))
    result = "\n".join(content)
    return clean_string(result)

def extract_sender_name(sender):
    """Extract sender name with improved parsing"""
    if not sender:
        return ""
    try:
        # まず、エンコードされたヘッダーをデコード
        decoded_sender = decode_email_header(sender)

        # 一般的なパターンを処理
        # 1. "Name" <email@example.com>
        # 2. Name <email@example.com>
        # 3. 'Name' <email@example.com>
        # 4. name@example.com
        name_patterns = [
            r'"([^"]+)"?\s*<[^>]+>',  # "Name" <email>
            r'([^<>]+?)\s*<[^>]+>',   # Name <email>
            r"'([^']+)'\s*<[^>]+>",   # 'Name' <email>
        ]

        for pattern in name_patterns:
            match = re.match(pattern, decoded_sender)
            if match:
                name = match.group(1)
                # 余分な文字を削除
                name = name.strip().strip('"').strip("'").strip()
                if name and len(name) > 1:  # 名前が1文字以上あることを確認
                    return name

        # メールアドレスのみの場合
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', decoded_sender)
        if email_match:
            return email_match.group(0).split('@')[0]  # メールアドレスのユーザー名部分を返す

        # どのパターンにも一致しない場合は、デコードされた送信者情報をそのまま返す
        return decoded_sender.strip()

    except Exception as e:
        current_app.logger.warning(f"Error extracting sender name: {str(e)} from sender: {sender}")
        return sender or ""

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

def handle_ai_error(func_name, error):
    """Handle AI analysis errors with proper logging and localized messages"""
    error_msg = None
    if isinstance(error, AuthenticationError):
        error_msg = "APIキーが無効です。システム管理者に連絡してください。"
        current_app.logger.error(f"{func_name}: Invalid API key - {str(error)}")
    elif isinstance(error, APIConnectionError):
        error_msg = "AI分析サービスに接続できません。しばらく待ってから再試行してください。"
        current_app.logger.error(f"{func_name}: Connection error - {str(error)}")
    elif isinstance(error, APIError):
        error_msg = "AI分析中にエラーが発生しました。しばらく待ってから再試行してください。"
        current_app.logger.error(f"{func_name}: API error - {str(error)}")
    else:
        error_msg = "予期せぬエラーが発生しました。システム管理者に連絡してください。"
        current_app.logger.error(f"{func_name}: Unexpected error - {str(error)}")
    return f'<p class="error-message">{error_msg}</p>'