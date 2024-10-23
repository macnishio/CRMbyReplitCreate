from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from typing import List
from sqlalchemy import Integer, String, DateTime, Float, ForeignKey, Text, Boolean
from typing import List, Optional 
import base64
from cryptography.fernet import Fernet
from flask import current_app

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(20), nullable=False, default='user')

    # リレーションシップ
    leads: Mapped[List["Lead"]] = db.relationship('Lead', backref='user', lazy='dynamic')
    opportunities: Mapped[List["Opportunity"]] = db.relationship('Opportunity', backref='user', lazy='dynamic')
    accounts: Mapped[List["Account"]] = db.relationship('Account', backref='user', lazy='dynamic')
    settings: Mapped["UserSettings"] = db.relationship("UserSettings", backref="user", uselist=False)

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

    def _get_encryption_key(self):
        key = current_app.config['SECRET_KEY']
        # Ensure the key is 32 bytes long for Fernet
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
    last_contact: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_followup_email: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # リレーションシップ
    emails: Mapped[List["Email"]] = db.relationship('Email', backref='lead', lazy='dynamic')
    opportunities: Mapped[List["Opportunity"]] = db.relationship('Opportunity', back_populates='lead', cascade='all, delete-orphan')
    schedules: Mapped[List["Schedule"]] = db.relationship('Schedule', back_populates='lead', cascade='all, delete-orphan')
    tasks: Mapped[List["Task"]] = db.relationship('Task', back_populates='lead', cascade='all, delete-orphan')

class Email(db.Model):
    __tablename__ = 'emails'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender: Mapped[str] = mapped_column(String(120), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('leads.id'), nullable=False)

class UnknownEmail(db.Model):
    __tablename__ = 'unknown_emails'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender: Mapped[str] = mapped_column(String(120), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(100))
    subject: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Opportunity(db.Model):
    __tablename__ = 'opportunities'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    stage: Mapped[str] = mapped_column(String(20))
    amount: Mapped[float] = mapped_column(Float, nullable=True)  # Making amount nullable
    close_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)  # Making close_date nullable
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('leads.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))

    # リレーションシップ
    lead: Mapped["Lead"] = db.relationship('Lead', back_populates='opportunities')

class Account(db.Model):
    __tablename__ = 'accounts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(50))
    website: Mapped[str] = mapped_column(String(200))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)

class Schedule(db.Model):
    __tablename__ = 'schedules'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    lead_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('leads.id'), nullable=True)  # Making lead_id nullable

    # リレーションシップ
    lead: Mapped[Optional["Lead"]] = db.relationship('Lead', back_populates='schedules')

class Task(db.Model):
    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    due_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    lead_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('leads.id'), nullable=True)  # Making lead_id nullable

    # リレーションシップ
    lead: Mapped[Optional["Lead"]] = db.relationship('Lead', back_populates='tasks')

class EmailFetchTracker(db.Model):
    __tablename__ = 'email_fetch_tracker'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_fetch_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
