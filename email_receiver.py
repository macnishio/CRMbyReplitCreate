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

def validate_email_settings(settings, app):
    """Validate email settings before attempting connection"""
    required_fields = ['mail_server', 'mail_username', 'mail_password']
    for field in required_fields:
        if not hasattr(settings, field) or not getattr(settings, field):
            raise ValueError(f"Missing required email setting: {field}")

    # メールサーバーの形式チェック
    if not isinstance(settings.mail_server, str) or '.' not in settings.mail_server:
        raise ValueError(f"Invalid mail server format: {settings.mail_server}")

    # ユーザー名の基本的な検証
    if '@' not in settings.mail_username:
        app.logger.warning(f"Email username might be invalid: {settings.mail_username}")
        
def clean_string(text):
    """Remove NUL characters and other problematic characters from string"""
    if text is None:
        return ""
    if isinstance(text, bytes):
        text = text.replace(b'\x00', b'')
    else:
        text = str(text).replace('\x00', '')
    return text.strip()

import re
from email.utils import parsedate_tz

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
    try:
        # 設定の検証を追加
        try:
            validate_email_settings(settings, app)
        except ValueError as e:
            app.logger.error(f"Email settings validation failed for user {settings.user_id}: {str(e)}")
            return

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
                app.logger.info(f"Attempt {attempt + 1} to connect to mail server for user {settings.user_id}")
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
                if not (msg_data and msg_data[0] and msg_data[0][1]):
                    continue

                email_body = msg_data[0][1]
                msg = email.message_from_bytes(email_body)

                # メールの重複チェックのために必要な情報を取得
                message_id = clean_string(msg.get('Message-ID', ''))

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

                subject = clean_string(decode_email_header(msg['subject']))
                sender = clean_string(decode_email_header(msg['from']))
                sender_name = clean_string(extract_sender_name(sender))
                sender_email = clean_string(extract_email_address(sender))
                content = clean_string(get_email_content(msg))
                received_date = parse_email_date(msg.get('date'))

                # リードの検索と作成をトランザクション内で行う
                try:
                    lead = parent_session.query(Lead)\
                        .filter_by(email=sender_email, user_id=settings.user_id)\
                        .with_for_update()\
                        .first()

                    if not lead:
                        app.logger.debug(f"Creating new lead - Name: {sender_name}, Email: {sender_email}, User ID: {settings.user_id}")
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
                        app.logger.debug(f"Created new lead with ID: {lead.id}")

                    # Check if email is mass mail
                    is_mass_mail, spam_reason = is_mass_email(msg, content)
                    if is_mass_mail:
                        app.logger.info(f"Detected mass email from {sender_email}. Reason: {spam_reason}")
                        update_lead_status_for_mass_email(lead, is_mass_mail, spam_reason, parent_session, app)
                    # Analyze email if not spam
                    elif lead.status != 'Spam':
                        try:
                            ai_response = analyze_email(subject, content, lead.user_id)
                            process_ai_response(ai_response, lead, app)
                        except Exception as e:
                            app.logger.error(f"AI analysis error: {str(e)}")

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

                    processed_count += 1
                    app.logger.info(f"Processed email: {message_id} from {sender_email}")

                except Exception as e:
                    app.logger.error(f"Error processing lead and email record: {str(e)}")
                    parent_session.rollback()
                    continue

            except Exception as e:
                app.logger.error(f"Error processing email {num}: {str(e)}")
                continue

        # Update tracker
        try:
            tracker.last_fetch_time = datetime.utcnow()
            parent_session.commit()
            app.logger.info(f"Processed {processed_count} emails for user {settings.user_id}")
        except Exception as e:
            app.logger.error(f"Error updating tracker: {str(e)}")
            parent_session.rollback()
            raise

    except Exception as e:
        app.logger.error(f"Error checking emails for user {settings.user_id}: {str(e)}")
        parent_session.rollback()
        raise
    finally:
        try:
            if mail:
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

        # 接続試行前にログ
        app.logger.info(f"Attempting to connect to {settings.mail_server} for user {settings.mail_username}")

        mail = imaplib.IMAP4_SSL(
            host=settings.mail_server,
            ssl_context=ssl_context
        )

        try:
            # ログイン試行
            app.logger.debug(f"Attempting login for {settings.mail_username}")
            mail.login(settings.mail_username, settings.mail_password)

            # インボックス選択試行
            app.logger.debug("Selecting inbox")
            status, messages = mail.select('inbox')

            if status != 'OK':
                app.logger.error(f"Failed to select inbox: {messages}")
                try:
                    mail.logout()
                except:
                    pass
                return None

            app.logger.info(f"Successfully connected to mailbox for {settings.mail_username}")
            return mail

        except imaplib.IMAP4.error as e:
            error_str = str(e)
            if '[UNAVAILABLE]' in error_str:
                app.logger.error(f"Server temporarily unavailable during login: {error_str}")
            else:
                app.logger.error(f"IMAP login error: {error_str}")

            # エラー詳細をログに記録
            app.logger.error(f"Full IMAP error details: {error_str}")

            try:
                mail.logout()
            except:
                pass
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
        app.logger.exception("Detailed error traceback:")  # スタックトレースを記録
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
    """Extract email content with improved MIME handling and NUL character removal"""
    content = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    part_content = part.get_payload(decode=True)
                    if isinstance(part_content, bytes):
                        # NUL文字を除去してからデコード
                        part_content = clean_string(part_content)
                        content.append(part_content.decode('utf-8', errors='replace'))
                    else:
                        content.append(clean_string(part_content))
                except Exception as e:
                    current_app.logger.warning(f"Error decoding email part: {str(e)}")
                    continue
    else:
        try:
            payload = msg.get_payload(decode=True)
            if isinstance(payload, bytes):
                # NUL文字を除去してからデコード
                payload = clean_string(payload)
                content.append(payload.decode('utf-8', errors='replace'))
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