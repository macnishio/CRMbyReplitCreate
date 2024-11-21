from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
import json
from datetime import datetime
import base64
from cryptography.fernet import Fernet
from flask import current_app
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, Float, ForeignKey, Text, Boolean, Numeric
from typing import List, Optional

class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    stripe_price_id: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    features: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    subscriptions = db.relationship('Subscription', back_populates='plan')

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey('subscription_plans.id'), nullable=False)
    stripe_subscription_id: Mapped[str] = mapped_column(String(100), nullable=False)
    stripe_customer_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='active')
    current_period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    user = db.relationship('User', back_populates='subscription')
    plan = db.relationship('SubscriptionPlan', back_populates='subscriptions')

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(20), default='user')
    google_calendar_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_service_account_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # リレーションシップ
    subscription = db.relationship('Subscription', back_populates='user', uselist=False)
    opportunities = db.relationship('Opportunity', backref='owner', lazy='dynamic')
    leads = db.relationship('Lead', backref='owner', lazy='dynamic')
    accounts = db.relationship('Account', backref='owner', lazy='dynamic')
    settings = db.relationship('UserSettings', backref='user', uselist=False)
    emails = db.relationship('Email', backref='user', lazy='dynamic')
    schedules = db.relationship('Schedule', backref='user', lazy='dynamic')
    tasks = db.relationship('Task', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserSettings(db.Model):
    __tablename__ = 'user_settings'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    mail_server: Mapped[str] = mapped_column(String(120))
    mail_port: Mapped[int] = mapped_column(Integer)
    mail_use_tls: Mapped[bool] = mapped_column(Boolean, default=True)
    mail_username: Mapped[str] = mapped_column(String(120))
    _mail_password: Mapped[str] = mapped_column('mail_password', String(255))
    _claude_api_key: Mapped[Optional[str]] = mapped_column('claude_api_key', String(255), nullable=True)
    _clearbit_api_key: Mapped[Optional[str]] = mapped_column('clearbit_api_key', String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    filter_preferences: Mapped[Optional[str]] = mapped_column('filter_preferences', Text, nullable=True)

    @property
    def opportunity_filters(self):
        if not self.filter_preferences:
            return {}
        try:
            all_filters = json.loads(self.filter_preferences)
            return all_filters.get('opportunities', {})
        except json.JSONDecodeError:
            return {}

    @opportunity_filters.setter
    def opportunity_filters(self, value):
        try:
            current_filters = json.loads(self.filter_preferences) if self.filter_preferences else {}
        except json.JSONDecodeError:
            current_filters = {}
        
        current_filters['opportunities'] = value
        self.filter_preferences = json.dumps(current_filters)

    def _get_encryption_key(self):
        key = current_app.config['SECRET_KEY']
        return base64.urlsafe_b64encode(key.ljust(32)[:32].encode())

    def _encrypt(self, data):
        if not data:
            return None
        f = Fernet(self._get_encryption_key())
        return f.encrypt(data.encode()).decode()

    def _decrypt(self, data):
        if not data:
            return None
        f = Fernet(self._get_encryption_key())
        return f.decrypt(data.encode()).decode()

    @property
    def mail_password(self):
        return self._decrypt(self._mail_password) if self._mail_password else None

    @mail_password.setter
    def mail_password(self, value):
        self._mail_password = self._encrypt(value) if value else None

    @property
    def claude_api_key(self):
        return self._decrypt(self._claude_api_key) if self._claude_api_key else None

    @claude_api_key.setter
    def claude_api_key(self, value):
        self._claude_api_key = self._encrypt(value) if value else None

    @property
    def clearbit_api_key(self):
        return self._decrypt(self._clearbit_api_key) if self._clearbit_api_key else None

    @clearbit_api_key.setter
    def clearbit_api_key(self, value):
        self._clearbit_api_key = self._encrypt(value) if value else None

class Lead(db.Model):
    __tablename__ = 'leads'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='New')
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_contact: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_followup_email: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    opportunities = db.relationship('Opportunity', back_populates='lead', cascade='all, delete-orphan')
    schedules = db.relationship('Schedule', back_populates='lead', cascade='all, delete-orphan')
    tasks = db.relationship('Task', back_populates='lead', cascade='all, delete-orphan')
    emails = db.relationship('Email', backref='lead', lazy='dynamic')

class Email(db.Model):
    __tablename__ = 'emails'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    sender: Mapped[str] = mapped_column(String(120), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    received_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('leads.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    ai_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_analysis_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ai_model_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tasks = db.relationship('Task', back_populates='email', lazy='dynamic')
    schedules = db.relationship('Schedule', back_populates='email', lazy='dynamic')

class UnknownEmail(db.Model):
    __tablename__ = 'unknown_emails'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender: Mapped[str] = mapped_column(String(120), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    received_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_ai_generated = db.Column(db.Boolean, default=False)

class Opportunity(db.Model):
    __tablename__ = 'opportunities'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    stage: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('leads.id'), nullable=False)
    account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounts.id'), nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # リレーションシップ
    lead = db.relationship('Lead', back_populates='opportunities')
    account = db.relationship('Account', back_populates='opportunities')

class Account(db.Model):
    __tablename__ = 'accounts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(50))
    website: Mapped[str] = mapped_column(String(200))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)

    # リレーションシップ
    opportunities = db.relationship('Opportunity', back_populates='account')

class Schedule(db.Model):
    __tablename__ = 'schedules'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='Scheduled')
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    lead_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('leads.id'), nullable=True)
    email_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('emails.id'), nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)

    # リレーションシップ
    lead = db.relationship('Lead', back_populates='schedules')
    email = db.relationship('Email', back_populates='schedules')

class Task(db.Model):
    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    due_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    lead_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('leads.id'), nullable=True)
    email_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('emails.id'), nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)

    # リレーションシップ
    lead = db.relationship('Lead', back_populates='tasks')
    email = db.relationship('Email', back_populates='tasks')

class EmailFetchTracker(db.Model):
    __tablename__ = 'email_fetch_tracker'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_fetch_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FilterPreset(db.Model):
    __tablename__ = 'filter_presets'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    filters: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of filter settings
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with User model
    user = db.relationship('User', backref=db.backref('filter_presets', lazy='dynamic'))

    @property
    def filter_data(self):
        return json.loads(self.filters)

    @filter_data.setter
    def filter_data(self, value):
        self.filters = json.dumps(value)
