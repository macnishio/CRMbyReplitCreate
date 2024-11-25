# Standard library imports
import os
import re
import json
import ssl
import time
import uuid
import email
import hashlib
import logging
import imaplib
import codecs
import unicodedata
from email import message_from_bytes, utils
from email.header import decode_header
from email.utils import parsedate_tz, parsedate_to_datetime
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager
from threading import Thread
from typing import Tuple, Union, Optional, List, Dict

# Third-party imports
import psutil
import chardet

# Flask and extensions
from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from anthropic import APIError, APIConnectionError, AuthenticationError

# Local application imports
from models import (
    Lead,
    Email,
    User,
    UnknownEmail,
    EmailFetchTracker,
    UserSettings
)
from extensions import db
from ai_analysis import analyze_email, process_ai_response
from email_encoding import (
    convert_encoding,
    clean_email_content,
    analyze_iso2022jp_text
)

# Constants
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 5  # seconds
DEFAULT_TIMEOUT = 30  # seconds
JAPANESE_TZ = timezone(timedelta(hours=9))  # JST

# Initialize logger
logger = logging.getLogger(__name__)

def get_email_content(msg):
    """Extract email content with improved empty content handling"""
    content_parts = []
    current_app.logger.debug("Starting email content processing")

    def process_content(raw_content, charset=None):
        if not raw_content:
            current_app.logger.debug("Empty raw content received")
            return ""

        try:
            # バイト列への変換確認
            if not isinstance(raw_content, bytes):
                try:
                    raw_content = raw_content.encode('utf-8', errors='replace')
                except Exception as e:
                    current_app.logger.warning(
                        f"Error encoding content to bytes: {str(e)}"
                    )
                    return str(raw_content)

            # エンコーディング検出と変換
            detected_encoding = detect_encoding(raw_content)
            if detected_encoding:
                try:
                    decoded = raw_content.decode(detected_encoding)
                    current_app.logger.debug(
                        f"Successfully decoded using detected encoding: {detected_encoding}"
                    )
                    if decoded.strip():  # 空白文字のみのコンテンツをチェック
                        return decoded
                    else:
                        current_app.logger.debug("Decoded content is empty or whitespace only")
                        return ""
                except UnicodeDecodeError:
                    current_app.logger.warning(
                        f"Failed to decode with detected encoding: {detected_encoding}"
                    )

            # フォールバック: UTF-8でデコード試行
            try:
                decoded = raw_content.decode('utf-8', errors='replace')
                return decoded
            except Exception as e:
                current_app.logger.warning(f"Fallback decoding failed: {str(e)}")
                return str(raw_content)

        except Exception as e:
            current_app.logger.error(f"Error in process_content: {str(e)}")
            return str(raw_content)

    try:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        charset = part.get_content_charset()
                        part_content = part.get_payload(decode=True)

                        if part_content:
                            current_app.logger.debug(
                                f"Processing multipart content of length {len(part_content)}, "
                                f"charset: {charset}"
                            )
                            processed_content = process_content(part_content, charset)
                            if processed_content.strip():  # 空でない場合のみ追加
                                content_parts.append(processed_content)
                                current_app.logger.debug(
                                    f"Added content part: {len(processed_content)} chars"
                                )
                    except Exception as e:
                        current_app.logger.warning(
                            f"Error processing email part: {str(e)}", 
                            exc_info=True
                        )
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                processed_content = process_content(payload, msg.get_content_charset())
                if processed_content.strip():  # 空でない場合のみ追加
                    content_parts.append(processed_content)
                    current_app.logger.debug(
                        f"Added single part content: {len(processed_content)} chars"
                    )

        # 最終的な内容の組み立て
        final_content = "\n".join(filter(None, content_parts))

        if not final_content.strip():
            current_app.logger.warning("No valid content found in email")
            return "（メール内容が空です）"

        current_app.logger.debug(f"Final content length: {len(final_content)}")
        return final_content

    except Exception as e:
        current_app.logger.error(f"Error in get_email_content: {str(e)}", exc_info=True)
        return "（メール内容の処理中にエラーが発生しました）"

def detect_encoding(raw_content: bytes) -> Optional[str]:
    """
    Detect the encoding of content with improved accuracy and fallback mechanisms

    Args:
        raw_content: Raw bytes content to analyze

    Returns:
        Optional[str]: Detected encoding name or None if detection fails
    """
    try:
        if not isinstance(raw_content, bytes):
            current_app.logger.warning(f"Expected bytes, got {type(raw_content)}")
            return None

        # BOMによる検出を最初に試行
        if raw_content.startswith(codecs.BOM_UTF8):
            current_app.logger.debug("UTF-8 BOM detected")
            return 'utf-8-sig'
        elif raw_content.startswith(codecs.BOM_UTF16_LE):
            current_app.logger.debug("UTF-16 LE BOM detected")
            return 'utf-16-le'
        elif raw_content.startswith(codecs.BOM_UTF16_BE):
            current_app.logger.debug("UTF-16 BE BOM detected")
            return 'utf-16-be'

        # ISO-2022-JPの検出（エスケープシーケンスによる）
        iso_jp_markers = {
            b'\x1b$B': 'iso-2022-jp',  # JIS X 0208-1983
            b'\x1b$@': 'iso-2022-jp',  # JIS X 0208-1978
            b'\x1b(J': 'iso-2022-jp',  # JIS X 0201-1976 Roman
            b'\x1b(B': 'iso-2022-jp'   # ASCII
        }

        for marker, encoding in iso_jp_markers.items():
            if marker in raw_content:
                current_app.logger.debug(f"ISO-2022-JP marker detected: {marker!r}")
                return encoding

        # chardetによる検出
        result = chardet.detect(raw_content)
        if result and result['confidence'] > 0.7:
            encoding = result['encoding']
            # エンコーディング名の正規化
            normalized_encoding = normalize_encoding_name(encoding)
            if normalized_encoding:
                current_app.logger.debug(
                    f"Detected {normalized_encoding} with "
                    f"confidence {result['confidence']:.2f}"
                )
                return normalized_encoding

        # ヒューリスティック検出
        # 日本語エンコーディングの特徴的なバイトパターンをチェック
        if is_likely_japanese_encoding(raw_content):
            encodings_to_try = ['cp932', 'euc_jp', 'iso-2022-jp']
            for enc in encodings_to_try:
                try:
                    decoded = raw_content.decode(enc)
                    if contains_japanese_chars(decoded):
                        current_app.logger.debug(
                            f"Heuristically detected {enc} based on content"
                        )
                        return enc
                except UnicodeDecodeError:
                    continue

        # UTF-8の検証
        try:
            decoded = raw_content.decode('utf-8')
            if any('\u0080' <= c <= '\uffff' for c in decoded):
                current_app.logger.debug("Valid UTF-8 with non-ASCII chars detected")
                return 'utf-8'
        except UnicodeDecodeError:
            pass

        current_app.logger.warning("Failed to detect encoding")
        return None

    except Exception as e:
        current_app.logger.error(
            f"Error in detect_encoding: {str(e)}", 
            exc_info=True
        )
        return None

def normalize_encoding_name(encoding: Optional[str]) -> Optional[str]:
    """
    Normalize encoding names to standard format

    Args:
        encoding: Raw encoding name

    Returns:
        Optional[str]: Normalized encoding name or None
    """
    if not encoding:
        return None

    encoding = encoding.lower().replace('-', '_')

    # エンコーディング名のマッピング
    encoding_map = {
        'shift_jis': 'cp932',
        'sjis': 'cp932',
        'shift': 'cp932',
        'x_sjis': 'cp932',
        'japanese': 'cp932',
        'csshiftjis': 'cp932',

        'euc': 'euc_jp',
        'eucjp': 'euc_jp',
        'x_euc': 'euc_jp',
        'eucjp_linux': 'euc_jp',

        'iso2022jp': 'iso-2022-jp',
        'iso_2022_jp': 'iso-2022-jp',
        'iso2022_jp': 'iso-2022-jp',
        'jis': 'iso-2022-jp',

        'utf8': 'utf-8',
        'u8': 'utf-8',
        'utf': 'utf-8',

        'ascii': 'ascii',
        'us_ascii': 'ascii',
        'us': 'ascii'
    }

    return encoding_map.get(encoding, encoding)

def is_likely_japanese_encoding(content: bytes) -> bool:
    """
    Check if content is likely to be Japanese encoded

    Args:
        content: Bytes content to analyze

    Returns:
        bool: True if content appears to be Japanese encoded
    """
    try:
        # SJIS/CP932の特徴的なバイトパターン
        sjis_chars = len([i for i in range(len(content)-1) 
                         if 0x81 <= content[i] <= 0x9F or 0xE0 <= content[i] <= 0xFC])

        # EUC-JPの特徴的なバイトパターン
        eucjp_chars = len([i for i in range(len(content)-1) 
                          if 0x8E <= content[i] <= 0x8F or 0xA1 <= content[i] <= 0xFE])

        # ISO-2022-JPのエスケープシーケンス
        iso2022jp_sequences = (
            content.count(b'\x1b$B') +
            content.count(b'\x1b$@') +
            content.count(b'\x1b(J')
        )

        # いずれかの特徴が強く現れている場合
        threshold = len(content) * 0.1  # コンテンツの10%以上
        return (
            sjis_chars > threshold or
            eucjp_chars > threshold or
            iso2022jp_sequences > 0
        )

    except Exception:
        return False

def contains_japanese_chars(text: str) -> bool:
    """
    Check if text contains Japanese characters

    Args:
        text: String to check

    Returns:
        bool: True if text contains Japanese characters
    """
    return any(
        '\u3040' <= c <= '\u309F' or  # ひらがな
        '\u30A0' <= c <= '\u30FF' or  # カタカナ
        '\u4E00' <= c <= '\u9FFF'     # 漢字
        for c in text
    )

def is_mass_email(msg, content, app):
    """
    Enhanced spam detection with improved pattern matching and scoring system

    Args:
        msg: Email message object
        content: Processed email content
        app: Flask app for logging

    Returns:
        tuple: (is_spam: bool, reason: str)
    """
    spam_score = 0
    spam_indicators = []
    try:
        # スコアリング閾値の設定
        SPAM_THRESHOLD = 2

        # ドメインチェック（重み: 1）
        spam_domains = [
            # メール配信サービス
            'mailout.', 'mailchimp.', 'sendgrid.', 'marketo.', 'salesforce.',
            'campaign-', 'newsletter.', 'info.', 'amazonses.com', 'bounce.',
            'mailer.', 'mta.', 'spark.',

            # 日本のサービス
            'mail.rakuten.com', 'cuenote.jp', 'mpse.jp', 'itmedia.co.jp',
            'bizmkt.jp', 'hansoku.jp',

            # 中国系サービス
            '.qq.com', '.163.com', '.sina.com', '.sohu.com', 'edm.',
            'mail.hk', '.alibaba.com', '.taobao.com', '.tmall.com',

            # 一般的なメールサービス（追加の確認が必要）
            'noreply', 'no-reply', 'donotreply', 'notifications.'
        ]

        sender = msg.get('from', '').lower()
        if any(domain in sender for domain in spam_domains):
            spam_score += 1
            spam_indicators.append(f'Mass mail domain detected: {sender}')

        # ヘッダーチェック（重み: 1）
        bulk_headers = [
            # 標準的なリストメールヘッダー
            'List-Unsubscribe', 'List-Id', 'List-Post', 'List-Owner',
            'List-Subscribe', 'List-Help', 'Precedence', 'X-Campaign',

            # マーケティングメール関連
            'X-Marketing', 'X-Campaign-ID', 'X-Newsletter',
            'X-Mailer', 'Bulk-Sender', 'X-Report-Abuse',

            # 自動送信関連
            'Auto-Submitted', 'X-Auto-Response-Suppress',

            # その他の判定用ヘッダー
            'X-MC-User', 'Feedback-ID', 'X-SES-Outgoing',
            'X-CSA-Complaints', 'X-EDM-Key', 'X-CNDM', 'X-CN-List'
        ]

        for header in bulk_headers:
            if msg.get(header):
                spam_score += 1
                spam_indicators.append(f'Bulk mail header found: {header}')
                break  # 1つのヘッダーの存在で十分

        # Precedenceヘッダーの特別チェック（重み: 1）
        precedence = msg.get('Precedence', '').lower()
        if precedence in ['bulk', 'list', 'junk']:
            spam_score += 1
            spam_indicators.append(f'Bulk mail precedence: {precedence}')

        # コンテンツ内のキーフレーズチェック（重み: 1）
        unsubscribe_phrases = [
            # 英語
            'unsubscribe', 'opt-out', 'opt out', 'email preferences',
            'notification settings', 'manage subscriptions',
            'you received this email because',
            'this is an automated message',
            'do not reply to this email',

            # 日本語
            '配信停止', 'メール配信を停止', '退会',
            'このメールの配信を停止',
            '※本メールは自動送信されています',
            'このメールに返信されても回答できません',
            'このアドレスは送信専用です',
            'お問い合わせはこちら',
            'メールの変更・停止',
            'メールマガジン',
            'ニュースレター',

            # 中国語（簡体字）
            '取消订阅', '退订', '停止订阅',
            '系统自动发送', '请勿直接回复',

            # 中国語（繁体字）
            '取消訂閱', '退訂', '停止訂閱',
            '系統自動發送', '請勿直接回覆'
        ]

        if content:
            content_lower = content.lower()
            found_phrases = [
                phrase for phrase in unsubscribe_phrases 
                if phrase.lower() in content_lower
            ]
            if found_phrases:
                spam_score += 1
                spam_indicators.append(
                    f'Unsubscribe phrases found: {", ".join(found_phrases[:3])}'
                )

        # 宛先数のチェック（重み: 1）
        recipient_count = sum(
            len(msg.get_all(field, [])) 
            for field in ['to', 'cc', 'bcc']
        )
        if recipient_count > 2:
            spam_score += 1
            spam_indicators.append(f'Multiple recipients: {recipient_count}')

        # HTMLコンテンツのチェック（重み: 0.5）
        if msg.get_content_type() == 'text/html':
            spam_score += 0.5
            spam_indicators.append('HTML formatted email')

        # 件名のパターンチェック
        subject = msg.get('subject', '').lower()
        newsletter_patterns = [
            # 英語
            'newsletter', 'bulletin', 'update', 'digest',
            'notification', 'subscription', 'campaign',
            'special offer', 'announcement', 'weekly',
            'monthly', 'breaking news', 'alert',

            # 日本語
            'ニュース', 'マガジン', '配信', 'special',
            'キャンペーン', 'セール', '[pr]', '(pr)',
            'お知らせ', 'ご案内', 'まとめ', 'レポート',
            '速報',

            # 中国語
            '电子报', '通讯', '快讯', '周报', '月报',
            '公告', '通知', '优惠', '促销', '限时',
            '電子報', '通訊', '快訊', '週報', '優惠'
        ]

        if any(pattern in subject for pattern in newsletter_patterns):
            spam_score += 1
            spam_indicators.append(f'Newsletter-like subject: {subject[:50]}')

        # 送信時刻のチェック（深夜は自動送信の可能性が高い）
        try:
            date_tuple = parsedate_tz(msg.get('date'))
            if date_tuple:
                hour = date_tuple[3]
                if 0 <= hour < 6:
                    spam_score += 0.5
                    spam_indicators.append(f'Sent during off-hours: {hour}:00')
        except Exception as e:
            app.logger.debug(f"Error checking send time: {str(e)}")

        # 最終判定
        is_spam = spam_score >= SPAM_THRESHOLD
        reason = ' | '.join(spam_indicators) if spam_indicators else 'No spam indicators found'

        # 詳細なログ記録
        app.logger.debug(
            f"Spam check result - Score: {spam_score}, "
            f"Is spam: {is_spam}, Indicators: {len(spam_indicators)}"
        )

        return is_spam, reason

    except Exception as e:
        app.logger.error(f"Error in spam detection: {str(e)}", exc_info=True)
        return False, "Error in spam detection"

def connect_to_email_server(app, settings):
    """
    Connect to email server with enhanced security and error handling

    Args:
        app: Flask app object
        settings: UserSettings object containing connection details

    Returns:
        imaplib.IMAP4_SSL object or None if connection fails
    """
    mail = None
    try:
        # SSL context の設定
        ssl_context = ssl.create_default_context()
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = True

        # 一般的なセキュリティプロトコルの設定
        ssl_context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3

        # 接続タイムアウトの設定
        timeout = 30  # seconds

        app.logger.debug(f"Connecting to {settings.mail_server}")

        mail = imaplib.IMAP4_SSL(
            host=settings.mail_server,
            ssl_context=ssl_context,
            timeout=timeout
        )

        try:
            # ログイン試行
            mail.login(settings.mail_username, settings.mail_password)
            status, capabilities = mail.capability()

            if status != 'OK':
                app.logger.error(f"Failed to get server capabilities: {capabilities}")
                return None

            app.logger.debug(f"Connected successfully to {settings.mail_server}")

            # メールボックスの選択
            status, messages = mail.select('inbox')
            if status != 'OK':
                app.logger.error(f"Failed to select inbox: {messages}")
                return None

            return mail

        except imaplib.IMAP4.error as e:
            error_str = str(e)

            if '[UNAVAILABLE]' in error_str:
                app.logger.error(
                    f"Server temporarily unavailable during login: {error_str}"
                )
            elif '[AUTHENTICATIONFAILED]' in error_str:
                app.logger.error(
                    f"Authentication failed for {settings.mail_username}"
                )
            else:
                app.logger.error(f"IMAP login error: {error_str}")

            return None

    except ssl.SSLError as e:
        app.logger.error(
            f"SSL error connecting to {settings.mail_server}: {str(e)}",
            exc_info=True
        )
        return None

    except imaplib.IMAP4.error as e:
        error_str = str(e)
        if '[UNAVAILABLE]' in error_str:
            app.logger.error(f"Server temporarily unavailable: {error_str}")
        else:
            app.logger.error(
                f"IMAP error connecting to {settings.mail_server}: {error_str}"
            )
        return None

    except Exception as e:
        app.logger.error(
            f"Unexpected error connecting to {settings.mail_server}: {str(e)}",
            exc_info=True
        )
        return None


def update_lead_status_for_mass_email(lead, is_spam, reason, session, app):
    """Update lead status if email is determined to be mass mail"""
    try:
        if not lead:
            app.logger.error("Cannot update status: Lead object is None")
            return

        if is_spam and lead.status != 'Spam':
            try:
                with session.begin_nested():
                    previous_status = lead.status
                    lead.status = 'Spam'
                    lead.last_updated = datetime.utcnow()
                    session.add(lead)

                    app.logger.info(
                        f"Updated lead {lead.id} status from {previous_status} to Spam. "
                        f"Reason: {reason}"
                    )

            except Exception as e:
                app.logger.error(
                    f"Error updating lead status: {str(e)}", 
                    exc_info=True
                )
                raise

    except Exception as e:
        app.logger.error(
            f"Error in update_lead_status_for_mass_email: {str(e)}", 
            exc_info=True
        )
        raise

@contextmanager
def session_scope(app=None):
    """
    Provide a transactional scope with improved error handling and monitoring

    Args:
        app: Optional Flask app object for logging

    Yields:
        SQLAlchemy session
    """
    session = db.session()
    start_time = time.time()

    try:
        yield session

        if session.is_active:
            session.commit()
            if app:
                duration = time.time() - start_time
                app.logger.debug(f"Session committed successfully. Duration: {duration:.2f}s")

    except Exception as e:
        if session.is_active:
            session.rollback()
            if app:
                app.logger.error(
                    f"Session rolled back due to error: {str(e)}", 
                    exc_info=True
                )
        raise

    finally:
        session.close()
        if app:
            final_duration = time.time() - start_time
            app.logger.debug(f"Session closed. Total duration: {final_duration:.2f}s")

def handle_ai_error(func_name, error, app):
    """
    Handle AI analysis errors with improved error classification and localization

    Args:
        func_name: Name of the function where error occurred
        error: Exception object
        app: Flask app object

    Returns:
        str: Localized error message
    """
    try:
        error_msg = None
        error_code = None

        if isinstance(error, AuthenticationError):
            error_msg = "APIキーが無効です。システム管理者に連絡してください。"
            error_code = "AUTH_ERROR"
            app.logger.error(
                f"{func_name}: Invalid API key - {str(error)}", 
                extra={'error_code': error_code}
            )

        elif isinstance(error, APIConnectionError):
            error_msg = "AI分析サービスに接続できません。しばらく待ってから再試行してください。"
            error_code = "CONN_ERROR"
            app.logger.error(
                f"{func_name}: Connection error - {str(error)}", 
                extra={'error_code': error_code}
            )

        elif isinstance(error, APIError):
            error_msg = "AI分析中にエラーが発生しました。しばらく待ってから再試行してください。"
            error_code = "API_ERROR"
            app.logger.error(
                f"{func_name}: API error - {str(error)}", 
                extra={'error_code': error_code}
            )

        else:
            error_msg = "予期せぬエラーが発生しました。システム管理者に連絡してください。"
            error_code = "UNKNOWN_ERROR"
            app.logger.error(
                f"{func_name}: Unexpected error - {str(error)}", 
                extra={'error_code': error_code},
                exc_info=True
            )

        # エラー統計の更新
        update_error_stats(error_code, app)

        return render_error_message(error_msg, error_code)

    except Exception as e:
        app.logger.error(f"Error in handle_ai_error: {str(e)}", exc_info=True)
        return '<p class="error-message">システムエラーが発生しました。</p>'

def update_error_stats(error_code, app):
    """Update error statistics for monitoring"""
    try:
        stats_key = f"error_stats:{error_code}:{datetime.utcnow().date()}"

        # Redis or similar cache for stats
        if hasattr(app, 'cache'):
            app.cache.incr(stats_key)

    except Exception as e:
        app.logger.warning(f"Failed to update error stats: {str(e)}")

def render_error_message(message, error_code):
    """Render error message with consistent styling"""
    return f'''
    <div class="error-message" data-error-code="{error_code}">
        <p class="error-text">{message}</p>
        <p class="error-code">エラーコード: {error_code}</p>
    </div>
    '''

def generate_fallback_message_id(msg, sender_email):
    """Generate a fallback message_id when original is empty or missing"""
    # Try to get date from email header
    date = parse_email_date(msg.get('date')) or datetime.utcnow()
    date_str = date.strftime('%Y%m%d%H%M%S')

    # Create a unique identifier using timestamp, sender and random uuid
    unique_id = f"{date_str}-{sender_email}-{str(uuid.uuid4())[:8]}"
    return f"<{unique_id}@generated.local>"

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

def get_fetch_window(tracker, app):
    """Get appropriate time window for fetching emails"""
    if not tracker or not tracker.last_fetch_time:
        # 初回の場合は5分前から
        return datetime.utcnow() - timedelta(minutes=5)

    last_fetch = tracker.last_fetch_time
    now = datetime.utcnow()

    # 最後の取得から24時間以上経過している場合は24時間前からに制限
    if now - last_fetch > timedelta(hours=24):
        app.logger.warning(f"Last fetch was more than 24 hours ago. Limiting to last 24 hours.")
        return now - timedelta(hours=24)

    return last_fetch


def check_duplicate_email(message_id, sender, received_date, content, user_id, session, app):
    """
    Comprehensive duplicate check combining message_id, time-based, and content-based approaches
    """
    try:
        if message_id:
            # Message ID based check
            existing = session.query(Email.id, Email.lead_id)\
                .filter(Email.message_id == message_id)\
                .first()

            if existing:
                app.logger.info(
                    f"Found existing email with message_id: {message_id}, "
                    f"lead_id: {existing.lead_id}"
                )
                return True, None

        # Generate content hash
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:12]

        # Time-window based check with content comparison
        time_window = timedelta(minutes=5)
        existing_emails = session.query(Email)\
            .filter(
                Email.sender == sender,
                Email.user_id == user_id,
                Email.received_date.between(
                    received_date - time_window,
                    received_date + time_window
                )
            ).all()

        # Check content hash for each potential duplicate
        for email in existing_emails:
            existing_hash = hashlib.sha256(email.content.encode('utf-8')).hexdigest()[:12]
            if existing_hash == content_hash:
                app.logger.info(
                    f"Found content-based duplicate from {sender} "
                    f"around {received_date}"
                )
                return True, content_hash

        return False, content_hash

    except Exception as e:
        app.logger.error(f"Error in duplicate check: {str(e)}", exc_info=True)
        return True, None

def generate_message_id(msg, sender_email, received_date, content_hash=None, app=None):
    """
    Generate a unique message ID with improved uniqueness guarantees and error handling

    Args:
        msg: Email message object
        sender_email: Sender's email address
        received_date: Date the email was received
        content_hash: Pre-computed content hash (optional)
        app: Flask app object for logging (optional)

    Returns:
        str: A unique message ID
    """
    try:
        # まず、元のMessage-IDを確認
        message_id = clean_string(msg.get('Message-ID', ''))
        if message_id:
            return message_id

        # 必須パラメータの検証
        if not sender_email:
            raise ValueError("Sender email is required for message ID generation")

        # タイムスタンプの生成（マイクロ秒まで）
        timestamp = received_date.strftime('%Y%m%d%H%M%S%f')

        # ユニーク性を高めるための追加情報の収集
        components = [
            ('date', timestamp),
            ('from', sender_email),
            ('subject', clean_string(decode_email_header(msg.get('subject', '')))[:32]),  # 長すぎる件名を制限
        ]

        # コンテンツハッシュの生成または使用
        if content_hash is None:
            content = clean_string(get_email_content(msg))
            content_hash = hashlib.sha256(
                f"{components[2][1]}{content}".encode('utf-8')
            ).hexdigest()[:12]

        components.extend([
            ('hash', content_hash),
            ('uuid', str(uuid.uuid4())[:8])
        ])

        # ドメイン部分の決定（送信者のドメインを使用）
        try:
            domain = sender_email.split('@')[1]
        except (IndexError, AttributeError):
            domain = 'generated.local'

        # 最終的なメッセージIDの生成
        # RFC 2822に準拠したフォーマット
        id_local_part = '.'.join(f"{k}-{v}" for k, v in components)
        message_id = f"<{id_local_part}@{domain}>"

        # 生成されたIDの検証
        if not is_valid_message_id(message_id):
            # バックアップメカニズム: より単純だが確実な形式
            fallback_id = f"<{timestamp}.{uuid.uuid4()}@generated.local>"
            if app:
                app.logger.warning(
                    f"Generated message ID was invalid, using fallback. "
                    f"Original: {message_id}, Fallback: {fallback_id}"
                )
            return fallback_id

        if app:
            app.logger.debug(f"Generated message ID: {message_id}")
        return message_id

    except Exception as e:
        if app:
            app.logger.error(f"Error generating message ID: {str(e)}", exc_info=True)
        # 最終的なフォールバック: 必ず一意になる最小限の形式
        emergency_id = f"<{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}.{uuid.uuid4()}@emergency.local>"
        if app:
            app.logger.error(f"Using emergency message ID: {emergency_id}")
        return emergency_id

def is_valid_message_id(message_id):
    """
    Check if a message ID is valid according to RFC 2822

    Args:
        message_id: Message ID to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # 基本的な構造の確認
        if not message_id.startswith('<') or not message_id.endswith('>'):
            return False

        # 内容の取り出し
        content = message_id[1:-1]

        # @による分割の確認
        if '@' not in content:
            return False

        local_part, domain = content.split('@', 1)

        # 長さの制限
        if len(message_id) > 998:  # RFC 2822の制限
            return False

        # 禁止文字のチェック
        prohibited_chars = set('()<>[]\\,;:')
        if any(char in message_id for char in prohibited_chars):
            return False

        # ドメイン部分の基本的な検証
        if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', domain):
            return False

        return True

    except Exception:
        return False

def generate_content_hash(subject, content):
    """
    Generate a consistent hash from email content

    Args:
        subject: Email subject
        content: Email content

    Returns:
        str: Content hash
    """
    try:
        # 正規化
        normalized_subject = clean_string(subject or '').lower()
        normalized_content = clean_string(content or '').lower()

        # ハッシュ生成
        combined = f"{normalized_subject}\n{normalized_content}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:12]

    except Exception:
        # エラーの場合はタイムスタンプベースのハッシュを返す
        return hashlib.sha256(
            datetime.utcnow().isoformat().encode('utf-8')
        ).hexdigest()[:12]

def process_email_message(msg, user_id, session, app, processed_ids=None):
    """
    Process a single email message with enhanced duplicate detection and validation

    Args:
        msg: Email message object
        user_id: User ID from UserSettings
        session: Database session
        app: Flask application instance for logging
        processed_ids: Set of already processed message IDs (optional)

    Returns:
        tuple: (Email record, Lead record) or None if duplicate
    """
    try:
        # Basic information extraction
        message_id = clean_string(msg.get('Message-ID', ''))
        sender = clean_string(decode_email_header(msg['from']))
        sender_email = clean_string(extract_email_address(sender))
        sender_name = clean_string(extract_sender_name(sender))
        received_date = parse_email_date(msg.get('date')) or datetime.utcnow()
        subject = clean_string(decode_email_header(msg['subject']))
        content = clean_string(get_email_content(msg))

        # Skip if already processed
        if processed_ids is not None and message_id and message_id in processed_ids:
            app.logger.info(f"Skipping already processed message: {message_id}")
            return None

        # Transaction with savepoint
        with session.begin_nested():
            # Duplicate check
            is_duplicate, content_hash = check_duplicate_email(
                message_id=message_id,
                sender=sender_email,
                received_date=received_date,
                content=content,
                user_id=user_id,
                session=session,
                app=app
            )

            if is_duplicate:
                app.logger.info(f"Duplicate email detected from {sender_email}")
                return None

            # Generate message ID if needed
            if not message_id:
                message_id = generate_message_id(
                    msg=msg,
                    sender_email=sender_email,
                    received_date=received_date,
                    content_hash=content_hash,
                    app=app
                )
                app.logger.info(f"Generated new message ID: {message_id}")

            # Lead processing with row-level locking
            lead = session.query(Lead)\
                .filter_by(email=sender_email, user_id=user_id)\
                .with_for_update()\
                .first()

            if not lead:
                lead = Lead(
                    name=sender_name or sender_email.split('@')[0],
                    email=sender_email,
                    status='New',
                    score=0.0,
                    user_id=user_id,
                    last_contact=received_date
                )
                session.add(lead)
                session.flush()
                app.logger.info(f"Created new lead for {sender_email}")

            # Validate lead creation
            if not lead or not lead.id:
                error_msg = f"Failed to create/retrieve lead for {sender_email}"
                app.logger.error(error_msg)
                raise ValueError(error_msg)

            # Create email record
            email_record = Email(
                message_id=message_id,
                sender=sender_email,
                sender_name=sender_name,
                subject=subject,
                content=content,
                lead_id=lead.id,
                user_id=user_id,
                received_date=received_date
            )

            session.add(email_record)
            session.flush()

            # Final validation
            if not email_record.id:
                error_msg = f"Failed to create email record for {message_id}"
                app.logger.error(error_msg)
                raise ValueError(error_msg)

            # Add to processed IDs if tracking is enabled
            if processed_ids is not None and message_id:
                processed_ids.add(message_id)

            app.logger.debug(
                f"Successfully processed email: {message_id}, "
                f"lead_id: {lead.id}, "
                f"email_id: {email_record.id}"
            )

            return email_record, lead

    except Exception as e:
        app.logger.error(f"Error processing email: {str(e)}", exc_info=True)
        raise

def process_emails_for_user(settings, parent_session, app):
    """
    Process emails for a user with comprehensive error handling and session management.
    """
    mail = None
    processed_messages = set()
    processed_count = 0
    error_count = 0
    duplicate_count = 0
    spam_count = 0
    max_retries = RETRY_MAX_ATTEMPTS

    try:
        current_settings = parent_session.merge(settings)
        user_id = current_settings.user_id

        with session_scope(app) as tracker_session:
            # トラッカーの取得とロック
            tracker = tracker_session.query(EmailFetchTracker)\
                .filter_by(user_id=user_id)\
                .with_for_update()\
                .first()
            
            last_fetch_time = get_fetch_window(tracker, app)

            if not tracker:
                tracker = EmailFetchTracker(
                    user_id=user_id, 
                    last_fetch_time=last_fetch_time
                )
                tracker_session.add(tracker)
                tracker_session.commit()
                app.logger.info(f"Created new fetch tracker for user {user_id}")

            # メールサーバーへの接続
            mail = connect_to_email_server_with_retry(app, current_settings, max_retries)
            if not mail:
                app.logger.error(f"Failed to connect to email server for user {user_id}")
                return

            # メール検索
            try:
                message_numbers = search_emails(mail, last_fetch_time, app)
                if not message_numbers:
                    app.logger.info(f"No new messages found for user {user_id}")
                    return
            except Exception as e:
                app.logger.error(f"Error searching emails: {str(e)}")
                return

            # メール処理
            for num_bytes in message_numbers:
                try:
                    # バイト文字列をデコードし、空白で分割
                    num_str = num_bytes.decode('ascii', errors='ignore')
                    # 空白で区切られた各メッセージ番号を処理
                    for individual_num in num_str.split():
                        try:
                            num = int(individual_num)
                            
                            # メッセージの取得
                            msg = fetch_email_message(mail, str(num).encode('ascii'), app)
                            if not msg:
                                error_count += 1
                                app.logger.warning(f"Failed to fetch message {num}")
                                continue

                            # メッセージの処理
                            with session_scope(app) as processing_session:
                                result = process_email_message(
                                    msg=msg,
                                    user_id=user_id,
                                    session=processing_session,
                                    app=app,
                                    processed_ids=processed_messages
                                )

                                if not result:
                                    duplicate_count += 1
                                    continue

                                email_record, lead = result

                                # スパム分析
                                is_spam = process_email_analysis(
                                    msg, 
                                    email_record, 
                                    lead, 
                                    processing_session, 
                                    app
                                )
                                if is_spam:
                                    spam_count += 1
                                
                                processed_count += 1

                        except ValueError as e:
                            error_count += 1
                            app.logger.error(f"Invalid message number: {individual_num}", exc_info=True)
                        except Exception as e:
                            error_count += 1
                            app.logger.error(
                                f"Error processing message {individual_num}: {str(e)}", 
                                exc_info=True
                            )

                except Exception as e:
                    error_count += 1
                    app.logger.error(
                        f"Error processing message batch {num_bytes.decode('ascii', errors='ignore')}: {str(e)}", 
                        exc_info=True
                    )

            # 最終フェッチ時刻の更新
            tracker.last_fetch_time = datetime.utcnow()
            tracker_session.commit()

            app.logger.info(
                f"Completed processing for user {user_id}. "
                f"Processed: {processed_count}, "
                f"Duplicates: {duplicate_count}, "
                f"Spam: {spam_count}, "
                f"Errors: {error_count}"
            )

    except Exception as e:
        app.logger.error(f"Critical error in process_emails_for_user: {str(e)}", exc_info=True)
        raise

    finally:
        if mail:
            try:
                mail.close()
                mail.logout()
            except Exception as e:
                app.logger.warning(f"Error closing mail connection: {str(e)}")

def connect_to_email_server_with_retry(app, settings, max_retries):
    """Separate function for email server connection with retry logic"""
    retry_count = 0
    while retry_count < max_retries:
        try:
            mail = connect_to_email_server(app, settings)
            if mail:
                app.logger.debug(f"Successfully connected to email server for user {settings.id}")
                return mail
        except Exception as e:
            app.logger.error(f"Connection attempt {retry_count + 1} failed: {str(e)}")

        retry_count += 1
        if retry_count < max_retries:
            sleep_time = RETRY_BASE_DELAY * (2 ** retry_count)
            time.sleep(sleep_time)

    app.logger.error(f"Failed to connect after {max_retries} attempts")
    return None

def fetch_email_message(mail, num_bytes, app):
    """提供されたバイト文字列を使用してメールメッセージを取得します。"""
    try:
        _, msg_data = mail.fetch(num_bytes, '(RFC822)') # ここで num_bytes はバイトである必要があります
        if not (msg_data and msg_data[0] and msg_data[0][1]):
            app.logger.warning(f"Invalid message data for message {num}")
            return None

        email_body = msg_data[0][1]
        if not isinstance(email_body, bytes):
            app.logger.error(f"Unexpected type for email_body: {type(email_body)}. Skipping.")
            return None

        return message_from_bytes(email_body)

    except Exception as e:
        app.logger.error(f"Error fetching message {num}: {str(e)}", exc_info=True)
        return None

def process_email_analysis(msg, email_record, lead, session, app):
    """Separate function for handling spam check and AI analysis"""
    try:
        is_mass_mail, spam_reason = is_mass_email(msg, email_record.content, app)
        if is_mass_mail:
            update_lead_status_for_mass_email(lead, is_mass_mail, spam_reason, session, app)
            return True

        if lead.status != 'Spam':
            ai_response = analyze_email(
                email_record.subject,
                email_record.content,
                lead.user_id
            )
            if ai_response:
                email_record.ai_analysis = ai_response
                email_record.ai_analysis_date = datetime.utcnow()
                email_record.ai_model_used = "claude-3-haiku-20240307"
                process_ai_response(ai_response, email_record, app)

        return False

    except Exception as e:
        app.logger.error(f"Error in email analysis: {str(e)}", exc_info=True)
        return False

def decode_email_header(header):
    """
    Decode email header with comprehensive encoding support and error recovery
    Handles various Japanese encodings and complex MIME headers
    """
    if not header:
        return ""

    try:
        decoded_parts = []
        raw_parts = decode_header(header)

        for part, encoding in raw_parts:
            try:
                if isinstance(part, bytes):
                    # 日本語エンコーディングの優先的な処理
                    if encoding and encoding.lower() in ['iso-2022-jp', 'iso2022_jp', 'iso2022jp']:
                        try:
                            # ISO-2022-JPの特別処理
                            normalized = normalize_iso2022jp_header(part)
                            decoded = normalized.decode('iso-2022-jp', errors='strict')
                            decoded_parts.append(decoded)
                            continue
                        except UnicodeDecodeError:
                            current_app.logger.debug("ISO-2022-JP decoding failed, trying alternatives")

                    # その他の日本語エンコーディング
                    if encoding and encoding.lower() in ['shift_jis', 'shift-jis', 'sjis', 'cp932']:
                        try:
                            decoded_parts.append(part.decode('cp932', errors='strict'))
                            continue
                        except UnicodeDecodeError:
                            current_app.logger.debug("CP932 decoding failed, trying alternatives")

                    if encoding and encoding.lower() in ['euc_jp', 'euc-jp', 'eucjp']:
                        try:
                            decoded_parts.append(part.decode('euc_jp', errors='strict'))
                            continue
                        except UnicodeDecodeError:
                            current_app.logger.debug("EUC-JP decoding failed, trying alternatives")

                    # 指定されたエンコーディングでの試行
                    if encoding:
                        try:
                            decoded_parts.append(part.decode(encoding, errors='strict'))
                            continue
                        except (UnicodeDecodeError, LookupError):
                            current_app.logger.debug(f"Specified encoding {encoding} failed, trying alternatives")

                    # フォールバックエンコーディングの試行
                    for enc in ['utf-8', 'iso-2022-jp', 'cp932', 'euc_jp']:
                        try:
                            decoded = part.decode(enc, errors='strict')
                            if contains_japanese(decoded):
                                decoded_parts.append(decoded)
                                break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # すべてのエンコーディングが失敗した場合
                        decoded_parts.append(part.decode('utf-8', errors='replace'))

                else:
                    # バイト列でない場合は文字列として追加
                    decoded_parts.append(str(part))

            except Exception as e:
                current_app.logger.warning(
                    f"Error decoding header part: {str(e)}, "
                    f"encoding: {encoding}", 
                    exc_info=True
                )
                if isinstance(part, bytes):
                    decoded_parts.append(part.decode('utf-8', errors='replace'))
                else:
                    decoded_parts.append(str(part))

        # デコードされた部分を結合
        cleaned_parts = [part.strip() for part in decoded_parts if part and part.strip()]
        result = " ".join(cleaned_parts)

        # 結果の検証
        if not result:
            return "（件名を表示できません）"

        return result

    except Exception as e:
        current_app.logger.error(f"Header decoding error: {str(e)}", exc_info=True)
        try:
            if isinstance(header, bytes):
                return header.decode('utf-8', errors='replace')
            return str(header)
        except Exception as e:
            current_app.logger.error(f"Final fallback error: {str(e)}", exc_info=True)
            return "（件名を表示できません）"

def extract_sender_name(sender):
    """
    Extract sender name with improved parsing and validation
    Handles various email address formats and encodings
    """
    if not sender:
        return ""

    try:
        # エンコードされたヘッダーのデコード
        decoded_sender = decode_email_header(sender)

        # 一般的なパターンでの抽出試行
        patterns = [
            # 標準的なフォーマット
            (r'"([^"]+)"?\s*<[^>]+>', 1),  # "Name" <email>
            (r'([^<>]+?)\s*<[^>]+>', 1),   # Name <email>
            (r"'([^']+)'\s*<[^>]+>", 1),   # 'Name' <email>

            # 日本語名フォーマット
            (r'"([^"]*[\u3000-\u9fff][^"]*)"?\s*<[^>]+>', 1),  # 日本語名を含む
            (r'=\?[^?]+\?[BQ]\?([^?]+)\?=\s*<[^>]+>', 1),      # MIME encoded

            # 特殊フォーマット
            (r'\(([^)]+)\)\s*<?[^>]*>?', 1),  # (Name) email
            (r'<?[^>]*>?\s*\(([^)]+)\)', 1),  # email (Name)
        ]

        for pattern, group in patterns:
            match = re.match(pattern, decoded_sender)
            if match:
                name = match.group(group)
                # 追加のクリーニング
                name = clean_sender_name(name)
                if name and len(name) > 1:
                    return name

        # メールアドレスのみの場合、ユーザー名部分を抽出
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', decoded_sender)
        if email_match:
            local_part = email_match.group(0).split('@')[0]
            # ユーザー名の整形
            return format_username(local_part)

        # どのパターンにも一致しない場合
        cleaned = clean_sender_name(decoded_sender)
        if cleaned:
            return cleaned

        return decoded_sender.strip()

    except Exception as e:
        current_app.logger.warning(
            f"Error extracting sender name: {str(e)} from sender: {sender}", 
            exc_info=True
        )
        return sender or ""

def extract_email_address(sender):
    """
    Extract email address with improved validation and error handling
    Supports various email address formats
    """
    if not sender:
        return ""

    try:
        # 基本的なパターンでの抽出試行
        patterns = [
            r'<([\w\.-]+@[\w\.-]+\.\w+)>',              # <email>
            r'([\w\.-]+@[\w\.-]+\.\w+)',                # email
            r'"?[^"]*"?\s*<([\w\.-]+@[\w\.-]+\.\w+)>',  # "Name" <email>
            r'=\?[^?]+\?[BQ]\?[^?]+\?=\s*<([\w\.-]+@[\w\.-]+\.\w+)>'  # MIME encoded
        ]

        for pattern in patterns:
            match = re.search(pattern, sender)
            if match:
                email = match.group(1).strip()
                if validate_email_address(email):
                    return email

        # 最後の手段として、任意の文字列からメールアドレスらしき部分を抽出
        words = sender.split()
        for word in words:
            if '@' in word:
                email = re.sub(r'[<>"\'\(\)]', '', word).strip()
                if validate_email_address(email):
                    return email

        return sender.strip()

    except Exception as e:
        current_app.logger.warning(
            f"Error extracting email address: {str(e)} from sender: {sender}", 
            exc_info=True
        )
        return sender

# Helper functions

def normalize_iso2022jp_header(raw_content):
    """Normalize ISO-2022-JP encoded header content"""
    normalized = raw_content
    if b'$B' in raw_content and b'\x1b$B' not in raw_content:
        normalized = raw_content.replace(b'$B', b'\x1b$B')
    if b'(B' in raw_content and b'\x1b(B' not in raw_content:
        normalized = normalized.replace(b'(B', b'\x1b(B')
    return normalized

def clean_sender_name(name):
    """Clean and normalize sender name"""
    if not name:
        return ""

    # 特殊文字の削除
    name = re.sub(r'["\'\(\)<>]', '', name)

    # 余分な空白の削除
    name = re.sub(r'\s+', ' ', name)

    # 制御文字の削除
    name = ''.join(char for char in name if unicodedata.category(char)[0] != 'C')

    return name.strip()

def format_username(username):
    """Format username from email address"""
    # 数字やドットで区切られた部分を分割
    parts = re.split(r'[\d\._-]+', username)

    # 最も長い意味のある部分を選択
    meaningful_part = max(parts, key=len, default=username)

    # キャメルケースやスネークケースを空白で分割
    words = re.findall(r'[A-Z][a-z]*|[a-z]+', meaningful_part)

    if words:
        # 単語の先頭を大文字に
        return ' '.join(word.capitalize() for word in words)

    return username

def validate_email_address(email):
    """Validate email address format"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def contains_japanese(text):
    """Check if text contains Japanese characters"""
    return any('\u3000' <= c <= '\u9fff' for c in text)

def parse_email_date(date_str):
    """
    Parse email date string to datetime with improved timezone handling and validation

    Args:
        date_str: Date string from email header

    Returns:
        datetime: Parsed datetime object with timezone info, or None if parsing fails
    """
    if not date_str:
        return None

    try:
        try:
            # RFC 2822 形式の日付を解析
            dt = parsedate_to_datetime(date_str)

            # タイムゾーン情報の確認と修正
            if dt.tzinfo is None:
                current_app.logger.warning(f"Date without timezone info: {date_str}")
                dt = dt.replace(tzinfo=timezone.utc)

            # 未来の日付をチェック
            now = datetime.now(timezone.utc)
            if dt > now + timedelta(days=1):
                current_app.logger.warning(f"Future date detected: {dt}, using current time")
                return now

            # 古すぎる日付をチェック
            if dt < now - timedelta(days=365*5):  # 5年以上前
                current_app.logger.warning(f"Very old date detected: {dt}, using current time")
                return now

            return dt

        except (TypeError, ValueError) as e:
            current_app.logger.warning(f"Standard date parsing failed: {str(e)}")

            # 代替フォーマットでの解析を試行
            for fmt in [
                '%a, %d %b %Y %H:%M:%S %z',     # RFC 2822
                '%d %b %Y %H:%M:%S %z',         # Modified RFC 2822
                '%Y-%m-%d %H:%M:%S%z',          # ISO-like
                '%Y-%m-%d %H:%M:%S.%f%z',       # ISO with microseconds
                '%Y-%m-%d %H:%M:%S',            # Simple datetime
                '%Y-%m-%d'                      # Simple date
            ]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except ValueError:
                    continue

            raise ValueError(f"Could not parse date with any format: {date_str}")

    except Exception as e:
        current_app.logger.error(f"Error parsing email date: {str(e)}", exc_info=True)
        return datetime.now(timezone.utc)

def setup_email_scheduler(app):
    """
    Setup scheduler for periodic email checking with improved error handling and monitoring
    """
    scheduler = BackgroundScheduler()

    def run_initial_check():
        """Run initial email check with error handling"""
        try:
            with app.app_context():
                app.logger.info("Running initial email check on startup")
                check_emails_task(app)
        except Exception as e:
            app.logger.error(f"Initial email check failed: {str(e)}", exc_info=True)

    def schedule_monitor():
        """Monitor scheduler health and job execution"""
        try:
            jobs = scheduler.get_jobs()
            running_jobs = [job for job in jobs if job.next_run_time is not None]

            current_app.logger.info(
                f"Scheduler status - Running jobs: {len(running_jobs)}, "
                f"Total jobs: {len(jobs)}"
            )

            # スケジューラーの状態確認
            if not scheduler.running:
                current_app.logger.error("Scheduler is not running, attempting restart")
                try:
                    scheduler.start()
                except Exception as e:
                    current_app.logger.error(f"Failed to restart scheduler: {str(e)}")

        except Exception as e:
            current_app.logger.error(f"Error in schedule monitor: {str(e)}")

    def email_check_wrapper():
        """Wrapper for email check task with error handling"""
        try:
            with app.app_context():
                check_emails_task(app)
        except Exception as e:
            app.logger.error(f"Scheduled email check failed: {str(e)}", exc_info=True)

    try:
        # スケジューラーの設定
        scheduler.add_job(
            email_check_wrapper,
            'interval',
            minutes=5,
            id='email_check',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300  # 5分のグレースタイム
        )

        # モニタリングジョブの追加
        scheduler.add_job(
            schedule_monitor,
            'interval',
            minutes=15,
            id='scheduler_monitor'
        )

        # スケジューラーの起動
        scheduler.start()
        app.logger.info("Email scheduler started successfully")

        # 初回チェックの実行
        Thread(
            target=run_initial_check,
            name="InitialEmailCheck",
            daemon=True
        ).start()

    except Exception as e:
        app.logger.error(f"Failed to setup email scheduler: {str(e)}", exc_info=True)
        raise

def check_emails_task(app):
    """
    Task to check for new emails with improved error handling, monitoring,
    and resource management.
    """
    start_time = datetime.now()

    with app.app_context():
        try:
            # Memory usage logging
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            with session_scope(app) as session:  # Single session scope for all users
                settings_list = session.query(UserSettings).all()

                if not settings_list:
                    app.logger.info("No user settings found for email checking")
                    return

                processed_count = 0
                error_count = 0

                for settings in settings_list:
                    try:
                        process_emails_for_user(settings, session, app)  # Pass the session
                        processed_count += 1
                    except Exception as e:
                        error_count += 1
                        app.logger.error(
                            f"Error processing emails for user {settings.user_id}: {str(e)}",
                            exc_info=True
                        )
                        # Consider adding a retry mechanism here if desired.
                        continue  # Continue to the next user

            # Performance statistics logging *outside* session scope
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_diff = final_memory - initial_memory

            app.logger.info(
                f"Email check completed - "
                f"Processed users: {processed_count}, "
                f"Errors: {error_count}, "
                f"Duration: {duration:.2f}s, "
                f"Memory diff: {memory_diff:.2f}MB"
            )

        except Exception as e:
            app.logger.error(f"Critical error in check_emails_task: {str(e)}", exc_info=True)

            # Error notification (implement as needed)
            try:
                notify_admin_error("check_emails_task", str(e))
            except Exception as notify_error:
                app.logger.error(f"Failed to send error notification: {str(notify_error)}")

def notify_admin_error(task_name, error_message):
    """
    Notify administrators about critical errors.
    Implement according to your notification system (e.g., email, Slack).
    """
    try:
        # Log to separate error log
        error_logger = logging.getLogger('error_notifications')
        error_logger.error(f"Critical error in {task_name}: {error_message}")

        # Example: Send email notification (replace with your actual notification logic)
        # from your_email_module import send_email  # Import your email sending function
        # send_email(
        #     "admin@example.com",  # Recipient
        #     f"Error in {task_name}",  # Subject
        #     error_message  # Body
        # )

    except Exception as e:
        current_app.logger.error(f"Error in notify_admin_error: {str(e)}")


def search_emails(mail, last_fetch_time, app, timeout=DEFAULT_TIMEOUT):
    try:
        # Set socket timeout
        mail.socket().settimeout(timeout)

        # Create search criteria
        search_criteria = f'(SINCE "{last_fetch_time.strftime("%d-%b-%Y")}")'

        # Execute search with timeout handling
        _, data = mail.search(None, search_criteria)
        return data
    except TimeoutError:
        app.logger.error("Search operation timed out")
        return None
    except Exception as e:
        app.logger.error(f"Error searching emails: {str(e)}")
        return None

def retry_imap_operation(func):
    def wrapper(*args, **kwargs):
        for attempt in range(RETRY_MAX_ATTEMPTS):
            try:
                return func(*args, **kwargs)
            except TimeoutError:
                if attempt < RETRY_MAX_ATTEMPTS - 1:
                    time.sleep(RETRY_BASE_DELAY * (attempt + 1))
                    continue
                raise
    return wrapper

@contextmanager
def safe_session_scope(app):
    session = db.session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        app.logger.error(f"Session rolled back due to error: {str(e)}")
        raise
    finally:
        session.close()

def cleanup_mail_connection(mail, app):
    try:
        if mail:
            try:
                mail.close()
            except Exception:
                pass
            try:
                mail.logout()
            except Exception:
                pass
    except Exception as e:
        app.logger.warning(f"Error during mail cleanup: {str(e)}")


def initialize_mail_connection(settings):
    """
    Initialize IMAP connection with security settings
    
    Args:
        settings: UserSettings object containing mail configuration
        
    Returns:
        IMAP4_SSL connection object or None if connection fails
    """
    try:
        # SSL context configuration
        ssl_context = ssl.create_default_context()
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.check_hostname = True
        ssl_context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3
        
        # Initialize connection with timeout
        mail = imaplib.IMAP4_SSL(
            host=settings.mail_server,
            ssl_context=ssl_context,
            timeout=DEFAULT_TIMEOUT
        )
        
        # Login attempt
        mail.login(settings.mail_username, settings.mail_password)
        
        # Select inbox
        mail.select('INBOX')
        
        return mail
        
    except imaplib.IMAP4.error as e:
        current_app.logger.error(f"IMAP error during connection: {str(e)}")
        return None
    except ssl.SSLError as e:
        current_app.logger.error(f"SSL error during connection: {str(e)}")
        return None
    except Exception as e:
        current_app.logger.error(f"Unexpected error during connection: {str(e)}")
        return None