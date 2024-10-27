from datetime import datetime
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import base64
from cryptography.fernet import Fernet
from flask import current_app

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    leads = db.relationship('Lead', backref='user', lazy=True)
    opportunities = db.relationship('Opportunity', backref='user', lazy=True)
    accounts = db.relationship('Account', backref='user', lazy=True)
    schedules = db.relationship('Schedule', backref='user', lazy=True)
    tasks = db.relationship('Task', backref='user', lazy=True)
    emails = db.relationship('Email', backref='user', lazy=True)
    settings = db.relationship('UserSettings', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    mail_server = db.Column(db.String(120))
    mail_port = db.Column(db.Integer)
    mail_use_tls = db.Column(db.Boolean, default=True)
    mail_username = db.Column(db.String(120))
    _mail_password = db.Column('mail_password', db.String(255))
    _claude_api_key = db.Column('claude_api_key', db.String(255), nullable=True)
    _clearbit_api_key = db.Column('clearbit_api_key', db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
        return self._decrypt(self._mail_password)

    @mail_password.setter
    def mail_password(self, value):
        self._mail_password = self._encrypt(value)

    @property
    def claude_api_key(self):
        return self._decrypt(self._claude_api_key)

    @claude_api_key.setter
    def claude_api_key(self, value):
        self._claude_api_key = self._encrypt(value)

    @property
    def clearbit_api_key(self):
        return self._decrypt(self._clearbit_api_key)

    @clearbit_api_key.setter
    def clearbit_api_key(self, value):
        self._clearbit_api_key = self._encrypt(value)

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    status = db.Column(db.String(20))
    score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_contact = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    opportunities = db.relationship('Opportunity', backref='lead', lazy=True)
    schedules = db.relationship('Schedule', backref='lead', lazy=True)
    tasks = db.relationship('Task', backref='lead', lazy=True)
    emails = db.relationship('Email', backref='lead', lazy=True)

class Opportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float)
    stage = db.Column(db.String(20))
    close_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    schedules = db.relationship('Schedule', backref='opportunity', lazy=True)
    tasks = db.relationship('Task', backref='opportunity', lazy=True)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(50))
    website = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    opportunities = db.relationship('Opportunity', backref='account', lazy=True)
    schedules = db.relationship('Schedule', backref='account', lazy=True)
    tasks = db.relationship('Task', backref='account', lazy=True)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunity.id'))
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunity.id'))
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(200), unique=True, nullable=False)
    sender = db.Column(db.String(120), nullable=False)
    sender_name = db.Column(db.String(100))
    subject = db.Column(db.String(200))
    content = db.Column(db.Text)
    received_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class EmailFetchTracker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_fetch_time = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
