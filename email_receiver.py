import os
import email
from email.header import decode_header
from datetime import datetime, timedelta, timezone
from flask import current_app
from models import Lead, Email, UnknownEmail, EmailFetchTracker, Opportunity, Schedule, Task, User
from extensions import db
from sqlalchemy.exc import DataError
import imaplib
import ssl
import re
import chardet
from ai_analysis import analyze_email, parse_ai_response

def connect_to_email_server():
    mail_server = os.environ.get('RECEIVE_MAIL_SERVER')
    mail_port = int(os.environ.get('RECEIVE_MAIL_PORT', 993))
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')

    if not all([mail_server, mail_port, mail_username, mail_password]):
        error_message = "One or more email connection environment variables are missing."
        current_app.logger.error(error_message)
        raise EnvironmentError(error_message)

    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Try different SSL/TLS versions
        ssl_versions = [ssl.PROTOCOL_TLS, ssl.PROTOCOL_TLSv1_2, ssl.PROTOCOL_TLSv1_1, ssl.PROTOCOL_TLSv1]
        for ssl_version in ssl_versions:
            try:
                context.options |= ssl_version
                current_app.logger.info(f"Attempting to connect to {mail_server}:{mail_port} with SSL version: {ssl_version}")
                mail = imaplib.IMAP4_SSL(mail_server, mail_port, ssl_context=context)
                mail.login(mail_username, mail_password)
                current_app.logger.info(f"Successfully connected and logged in to the email server using SSL version: {ssl_version}")
                return mail
            except ssl.SSLError as e:
                current_app.logger.warning(f"SSL Error with version {ssl_version}: {str(e)}")
                context.options &= ~ssl_version
            except imaplib.IMAP4.error as e:
                current_app.logger.error(f"IMAP Error with SSL version {ssl_version}: {str(e)}")
            except Exception as e:
                current_app.logger.error(f"Unexpected error with SSL version {ssl_version}: {str(e)}")

    except Exception as e:
        current_app.logger.error(f"Unexpected error in connect_to_email_server: {str(e)}")
        raise

    raise Exception("Unable to establish a secure connection with any SSL/TLS version")

# The rest of the file remains unchanged
# ...
