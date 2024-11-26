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
    
    # Stripe configuration
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
    
    # Scheduler configuration
    SCHEDULER_API_ENABLED = True
    FOLLOW_UP_INTERVAL_DAYS = int(os.environ.get('FOLLOW_UP_INTERVAL_DAYS', 7))
    FOLLOW_UP_HOUR = int(os.environ.get('FOLLOW_UP_HOUR', 9))  # 9 AM by default
    
    # Lead scoring configuration
    LEAD_SCORE_THRESHOLD = float(os.environ.get('LEAD_SCORE_THRESHOLD', 50))
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'ERROR')
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=int(os.environ.get('SESSION_LIFETIME_DAYS', 30)))
    
    # API rate limiting
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', "1000 per day;200 per hour")
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = int(os.environ.get('CSRF_TIME_LIMIT', 3600))
    
    # Content Security Policy
    CONTENT_SECURITY_POLICY = {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://cdn.jsdelivr.net https://code.jquery.com https://cdnjs.cloudflare.com",
        'style-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://cdnjs.cloudflare.com",
        'font-src': "'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com",
        'img-src': "'self' data: https://*.stripe.com",
        'frame-src': "https://js.stripe.com https://hooks.stripe.com",
        'connect-src': "'self' https://api.stripe.com",
        'form-action': "'self'",
        'frame-ancestors': "'none'",
        'object-src': "'none'"
    }
    
    # Redis configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = REDIS_URL
    
    # Claude AI Configuration
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')

    @staticmethod
    def init_app(app):
        # Set Content Security Policy headers
        @app.after_request
        def add_security_headers(response):
            csp = '; '.join(f"{key} {value}" for key, value in Config.CONTENT_SECURITY_POLICY.items())
            response.headers['Content-Security-Policy'] = csp
            return response

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # Log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
