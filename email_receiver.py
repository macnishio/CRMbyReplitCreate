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
from email_encoding import convert_encoding, clean_email_content, analyze_iso2022jp_text
from email.utils import parsedate_tz
from requests.exceptions import AuthenticationError, APIConnectionError, APIError

def clean_string(text):
    """Remove NUL characters and other problematic characters from string"""
    if text is None:
        return ""
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

def is_mass_email(msg, content):
    """
    Enhanced spam detection function for mass emails - supports English, Japanese, and both Simplified and Traditional Chinese.
    Returns: (bool, str) - (is_mass_email, reason)
    """
    spam_indicators = []

    # Expanded list of known spam/mass email domains and patterns, including Chinese-specific domains
    spam_domains = [
        'mailout.', 'mailchimp.', 'sendgrid.', 'marketo.', 'salesforce.', 'campaign-', 'newsletter.', 'info.',
        'noreply', 'no-reply', 'donotreply', 'notifications.', 'amazonses.com', 'bounce.', 'mailer.', 'mta', 'spark',
        'mail.rakuten.com', 'cuenote.jp', 'mpse.jp', 'itmedia.co.jp',  # Japanese
        '.qq.com', '.163.com', '.sina.com', '.sohu.com', 'edm.', 'mail.hk', '.alibaba.com', '.taobao.com', '.tmall.com',  # Chinese
        'google.com', 'outlook.com', 'hotmail.com', 'yahoo.'
    ]

    sender = msg.get('from', '').lower()
    if any(domain in sender for domain in spam_domains):
        spam_indicators.append(f'Sent from mass mail domain: {sender}')

    # Expanded list of bulk mail headers with common marketing indicators
    bulk_headers = [
        'List-Unsubscribe', 'List-Id', 'List-Post', 'List-Owner', 'List-Subscribe', 'List-Help', 
        'Bulk-Sender', 'Precedence', 'X-SES-Outgoing', 'X-Mailer', 'X-Campaign', 'X-Report-Abuse',
        'X-CSA-Complaints', 'X-Auto-Response-Suppress', 'Auto-Submitted', 'X-MC-User', 'Feedback-ID',
        'X-EDM-Key', 'X-CNDM', 'X-CN-List', 'X-Marketing', 'X-Campaign-ID', 'X-Newsletter'
    ]

    for header in bulk_headers:
        if msg.get(header):
            spam_indicators.append(f'Contains bulk mail header: {header}')

    precedence = msg.get('Precedence', '').lower()
    if precedence in ['bulk', 'list', 'junk']:
        spam_indicators.append(f'Precedence header indicates bulk mail: {precedence}')

    # Expanded unsubscribe and automated mail phrases in English, Japanese, Traditional and Simplified Chinese
    unsubscribe_phrases = [
        # English
        'unsubscribe', 'opt-out', 'opt out', 'email preferences', 'notification settings', 'manage subscriptions',
        'you received this email because', 'this is an automated message', 'do not reply to this email',
        'this is a system generated email',

        # Japanese
        '配信停止', 'メール配信を停止', '退会', 'このメールの配信を停止', '※本メールは自動送信されています',
        'この内容に関してご不明な点がございましたら', 'このメールに返信されても回答できません', 'このアドレスは送信専用です',
        'お問い合わせはこちら', 'メールの変更・停止', 'メールマガジン', 'ニュースレター', '※本メールは送信専用のため',
        'このメールは送信専用です',

        # Traditional Chinese
        '取消訂閱', '退訂', '停止訂閱', '取消電子報', '系統自動發送', '請勿直接回覆', '自動通知信', 
        '電子報', '取消接收', '停止接收', '管理訂閱', '訂閱設定', '電郵偏好', 
        '這是自動發送的郵件', '本郵件由系統自動發送', '如要取消接收', '如不想再收到',

        # Simplified Chinese
        '取消订阅', '退订', '停止订阅', '取消电子报', '系统自动发送', '请勿直接回复', '自动通知信',
        '电子报', '取消接收', '停止接收', '管理订阅', '订阅设置', '邮件偏好',
        '这是自动发送的邮件', '本邮件由系统自动发送', '如要取消接收', '如不想再收到'
    ]

    if content:
        content_lower = content.lower()
        found_phrases = [phrase for phrase in unsubscribe_phrases if phrase.lower() in content_lower]
        if found_phrases:
            spam_indicators.append(f'Contains unsubscribe phrases: {", ".join(found_phrases)}')

    # Check for multiple recipients
    recipient_count = sum(len(msg.get_all(field, [])) for field in ['to', 'cc', 'bcc'])
    if recipient_count > 2:
        spam_indicators.append(f'Multiple recipients: {recipient_count}')

    # Check for HTML content which often indicates newsletters
    if msg.get_content_type() == 'text/html':
        spam_indicators.append('HTML formatted email')

    # Expanded list of subject patterns common in newsletters in multiple languages
    subject = msg.get('subject', '').lower()
    newsletter_subject_patterns = [
        # English
        'newsletter', 'bulletin', 'update', 'digest', 'notification', 'subscription', 'campaign',
        'special offer', 'announcement', 'weekly', 'monthly', 'breaking news', 'alert',

        # Japanese
        'ニュース', 'マガジン', '配信', 'special', 'キャンペーン', 'セール', '[pr]', '(pr)',
        'お知らせ', 'ご案内', 'まとめ', 'レポート', '速報',

        # Traditional Chinese
        '電子報', '通訊', '快訊', '報導', '週報', '月報', '消息', '公告', '通知', '速報', 
        '優惠', '促銷', '特賣', '限時', '限定', '新聞', '訂閱',

        # Simplified Chinese
        '电子报', '通讯', '快讯', '报道', '周报', '月报', '消息', '公告', '通知', '速报', 
        '优惠', '促销', '特卖', '限时', '限定', '新闻', '订阅'
    ]

    if any(pattern in subject for pattern in newsletter_subject_patterns):
        spam_indicators.append(f'Newsletter-like subject: {subject}')

    # Check sending time (likely automated if sent between 0-6 am)
    try:
        date_tuple = parsedate_tz(msg.get('date'))
        if date_tuple:
            hour = date_tuple[3]
            if 0 <= hour < 6:
                spam_indicators.append(f'Sent during off-hours: {hour}:00')
    except:
        pass

    # Determine if email is spam based on detected indicators
    is_spam = len(spam_indicators) >= 1  # 1つ以上の指標でスパム判定
    reason = ' | '.join(spam_indicators) if spam_indicators else 'No spam indicators found'

    return is_spam, reason


def update_lead_status_for_mass_email(lead, is_spam, reason, session, app):
    """Update lead status if email is determined to be mass mail"""
    if is_spam and lead.status != 'Spam':
        previous_status = lead.status
        lead.status = 'Spam'
        app.logger.info(f"Updated lead {lead.id} status from {previous_status} to Spam. Reason: {reason}")
        session.add(lead)

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

        date_str = tracker.last_fetch_time.strftime("%d-%b-%Y")
        _, message_numbers = mail.search(None, f'(SINCE "{date_str}")')

        processed_count = 0
        error_count = 0
        for num in message_numbers[0].split():
            try:
                with parent_session.begin_nested():
                    _, msg_data = mail.fetch(num, '(RFC822)')
                    if not (msg_data and msg_data[0] and msg_data[0][1]):
                        continue
                    
                    # Retrieve the email body and ensure it's bytes
                    email_body = msg_data[0][1]
                    if isinstance(email_body, bytes):
                        msg = email.message_from_bytes(email_body)
                    else:
                        app.logger.error(f"Unexpected type for email_body: {type(email_body)}. Skipping email {num}.")
                        continue
                    message_id = clean_string(msg.get('Message-ID', ''))

                    if message_id:
                        existing_email = parent_session.query(Email)\
                            .filter_by(message_id=message_id, user_id=settings.user_id)\
                            .first()
                        if existing_email:
                            continue

                    subject = clean_string(decode_email_header(msg['subject']))
                    sender = clean_string(decode_email_header(msg['from']))
                    sender_name = clean_string(extract_sender_name(sender))
                    sender_email = clean_string(extract_email_address(sender))
                    content = clean_string(get_email_content(msg))
                    received_date = parse_email_date(msg.get('date'))

                    lead = parent_session.query(Lead)\
                        .filter_by(email=sender_email, user_id=settings.user_id)\
                        .first()

                    if not lead:
                        lead = Lead(
                            name=sender_name or sender_email.split('@')[0],
                            email=sender_email,
                            status='New',
                            score=0.0,
                            user_id=settings.user_id,
                            last_contact=received_date or datetime.utcnow()
                        )
                        parent_session.add(lead)
                        parent_session.flush()

                    email_record = Email(
                        message_id=message_id,
                        sender=sender_email,
                        sender_name=sender_name,
                        subject=subject,
                        content=content,
                        lead_id=lead.id,
                        user_id=settings.user_id,
                        received_date=received_date or datetime.utcnow()
                    )
                    parent_session.add(email_record)
                    parent_session.flush()

                    # Check if email is mass mail
                    is_mass_mail, spam_reason = is_mass_email(msg, content)
                    if is_mass_mail:
                        app.logger.info(f"Detected mass email from {sender_email}. Reason: {spam_reason}")
                        update_lead_status_for_mass_email(lead, is_mass_mail, spam_reason, parent_session, app)
                    # Analyze email if not spam
                    elif lead.status != 'Spam':
                        try:
                            ai_response = analyze_email(subject, content, lead.user_id)
                            if ai_response:
                                email_record.ai_analysis = ai_response
                                email_record.ai_analysis_date = datetime.utcnow()
                                email_record.ai_model_used = "claude-3-haiku-20240307"
                                process_ai_response(ai_response, email_record, app)
                        except Exception as e:
                            app.logger.error(f"AI analysis error for email {message_id}: {str(e)}")
                            error_count += 1

                    processed_count += 1
                    app.logger.info(f"Processed email: {message_id} from {sender_email}")

            except Exception as e:
                app.logger.error(f"Error processing email {num}: {str(e)}")
                error_count += 1
                continue

        try:
            with parent_session.begin_nested():
                tracker.last_fetch_time = datetime.utcnow()
            parent_session.commit()
            app.logger.info(
                f"Completed processing for user {settings.user_id}. "
                f"Processed: {processed_count}, Errors: {error_count}"
            )
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
            except Exception as e:
                app.logger.warning(f"Error closing mail connection: {str(e)}")

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
    
    Thread(target=run_initial_check).start()
    
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
    """Decode email header with improved Japanese encoding support and error handling"""
    if not header:
        return ""
    
    try:
        decoded_parts = []
        for part, encoding in decode_header(header):
            if isinstance(part, bytes):
                try:
                    if encoding and encoding.lower() in ['iso-2022-jp', 'iso2022_jp', 'iso2022jp']:
                        decoded_parts.append(part.decode('iso-2022-jp', errors='replace'))
                    elif encoding and encoding.lower() in ['shift_jis', 'shift-jis', 'sjis', 'cp932']:
                        decoded_parts.append(part.decode('cp932', errors='replace'))
                    elif encoding and encoding.lower() in ['euc_jp', 'euc-jp', 'eucjp']:
                        decoded_parts.append(part.decode('euc_jp', errors='replace'))
                    elif encoding:
                        decoded_parts.append(part.decode(encoding, errors='replace'))
                    else:
                        for enc in ['utf-8', 'iso-2022-jp', 'cp932', 'euc_jp']:
                            try:
                                decoded_text = part.decode(enc)
                                decoded_parts.append(decoded_text)
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            decoded_parts.append(part.decode('utf-8', errors='replace'))
                except (UnicodeDecodeError, LookupError) as e:
                    current_app.logger.warning(f"Decoding error with {encoding}: {str(e)}")
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
            else:
                decoded_parts.append(str(part))
        
        cleaned_parts = [part.strip() for part in decoded_parts if part.strip()]
        return " ".join(cleaned_parts)
        
    except Exception as e:
        current_app.logger.error(f"Header decoding error: {str(e)}")
        try:
            if isinstance(header, bytes):
                return header.decode('utf-8', errors='replace')
            return str(header)
        except Exception as e:
            current_app.logger.error(f"Final fallback error: {str(e)}")
            return "（件名を表示できません）"

def get_email_content(msg):
    """Extract email content with improved encoding handling"""
    content = []
    current_app.logger.debug("Processing email content")

    def process_content(raw_content):
        """Helper function to process raw content"""
        if not raw_content:
            return ""

        if not isinstance(raw_content, bytes):
            raw_content = raw_content.encode('utf-8', errors='replace')

        # 保存前に必ずバイト列として処理
        if analyze_iso2022jp_text(raw_content):
            try:
                # ISO-2022-JPの正規化とデコード
                normalized = raw_content
                if b'$B' in raw_content and b'\x1b$B' not in raw_content:
                    normalized = raw_content.replace(b'$B', b'\x1b$B')
                if b'(B' in raw_content and b'\x1b(B' not in raw_content:
                    normalized = normalized.replace(b'(B', b'\x1b(B')

                decoded = normalized.decode('iso-2022-jp', errors='strict')
                current_app.logger.debug("Successfully decoded ISO-2022-JP content")
                return decoded
            except UnicodeDecodeError as e:
                current_app.logger.warning(f"ISO-2022-JP decoding failed: {str(e)}")

        # 他のエンコーディングを試行
        encodings = [
            ('cp932', 'strict'),
            ('shift_jis', 'strict'),
            ('euc_jp', 'strict'),
            ('utf-8', 'strict'),
            ('iso-2022-jp', 'replace'),
            ('cp932', 'replace'),
            ('utf-8', 'replace')
        ]

        for encoding, error_handler in encodings:
            try:
                decoded = raw_content.decode(encoding, errors=error_handler)
                if any('\u3000' <= c <= '\u9fff' for c in decoded):  # 日本語文字の存在確認
                    current_app.logger.debug(f"Successfully decoded using {encoding}")
                    return decoded
            except UnicodeDecodeError:
                continue

        return raw_content.decode('utf-8', errors='replace')

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    part_content = part.get_payload(decode=True)
                    if part_content:
                        current_app.logger.debug(f"Processing multipart content of length {len(part_content)}")
                        decoded_content = process_content(part_content)
                        cleaned_content = clean_email_content(decoded_content)
                        content.append(cleaned_content)
                except Exception as e:
                    current_app.logger.warning(f"Error processing email part: {str(e)}")
                    continue
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                current_app.logger.debug(f"Processing single part content of length {len(payload)}")
                decoded_content = process_content(payload)
                cleaned_content = clean_email_content(decoded_content)
                content.append(cleaned_content)
        except Exception as e:
            current_app.logger.warning(f"Error processing email payload: {str(e)}")

    final_content = "\n".join(filter(None, content))
    current_app.logger.debug(f"Final content length: {len(final_content)}")

    # 保存前の最終確認
    if not final_content:
        return "（メール内容を取得できませんでした）"

    # 日本語文字が含まれているか確認
    has_japanese = any('\u3000' <= c <= '\u9fff' for c in final_content)
    if not has_japanese:
        current_app.logger.warning("No Japanese characters found in content")

    return final_content

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
