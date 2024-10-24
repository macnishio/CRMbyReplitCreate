# config.py

import os
from datetime import timedelta

class Config:
    # Security settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///crm.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
    MAIL_MAX_EMAILS = int(os.environ.get('MAIL_MAX_EMAILS', 100))
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'false').lower() in ['true', 'on', '1']
    MAIL_ASCII_ATTACHMENTS = False

    # IMAP configuration for email fetching
    IMAP_SERVER = os.environ.get('IMAP_SERVER', 'imap.gmail.com')
    IMAP_PORT = int(os.environ.get('IMAP_PORT', 993))
    IMAP_USE_SSL = True
    IMAP_USERNAME = os.environ.get('IMAP_USERNAME', MAIL_USERNAME)
    IMAP_PASSWORD = os.environ.get('IMAP_PASSWORD', MAIL_PASSWORD)

    # Scheduler configuration
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "UTC"
    FOLLOW_UP_INTERVAL_DAYS = int(os.environ.get('FOLLOW_UP_INTERVAL_DAYS', 7))
    FOLLOW_UP_HOUR = int(os.environ.get('FOLLOW_UP_HOUR', 9))
    EMAIL_CHECK_INTERVAL = int(os.environ.get('EMAIL_CHECK_INTERVAL', 5))  # minutes

    # Lead scoring configuration
    LEAD_SCORE_THRESHOLD = float(os.environ.get('LEAD_SCORE_THRESHOLD', 50))
    MIN_SCORE = 0
    MAX_SCORE = 100

    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.environ.get('LOG_FILE', 'application.log')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10000000))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))

    # Session configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=int(os.environ.get('SESSION_LIFETIME_DAYS', 30)))
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # API rate limiting
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', "200 per day;50 per hour")
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    RATELIMIT_STRATEGY = 'fixed-window'

    # CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = int(os.environ.get('CSRF_TIME_LIMIT', 3600))
    WTF_CSRF_SSL_STRICT = True

    # Content Security Policy
    CONTENT_SECURITY_POLICY = {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline' 'unsafe-eval'",
        'style-src': "'self' 'unsafe-inline'",
        'img-src': "'self' data: https:",
        'font-src': "'self' data:",
        'connect-src': "'self'",
        'frame-ancestors': "'none'"
    }

    # Redis configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_KEY_PREFIX = "crm_"

    # Database configuration
    DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', 10))
    DB_POOL_TIMEOUT = int(os.environ.get('DB_POOL_TIMEOUT', 30))
    DB_POOL_RECYCLE = int(os.environ.get('DB_POOL_RECYCLE', 3600))

    # Claude AI Configuration
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')
    CLAUDE_MODEL = os.environ.get('CLAUDE_MODEL', 'claude-3-opus-20240229')
    CLAUDE_MAX_TOKENS = int(os.environ.get('CLAUDE_MAX_TOKENS', 4096))

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    WTF_CSRF_ENABLED = True
    MAIL_SUPPRESS_SEND = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ECHO = False

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # Production-specific logging
        import logging
        from logging.handlers import RotatingFileHandler

        # File Handler
        file_handler = RotatingFileHandler(
            filename=cls.LOG_FILE,
            maxBytes=cls.LOG_MAX_BYTES,
            backupCount=cls.LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(logging.Formatter(cls.LOG_FORMAT))
        file_handler.setLevel(logging.INFO)

        # Stderr Handler
        stderr_handler = logging.StreamHandler()
        stderr_handler.setFormatter(logging.Formatter(cls.LOG_FORMAT))
        stderr_handler.setLevel(logging.ERROR)

        # Add handlers
        app.logger.addHandler(file_handler)
        app.logger.addHandler(stderr_handler)

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True