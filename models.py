from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from datetime import datetime
from sqlalchemy.sql import func

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(80), nullable=False, default='user')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    status = db.Column(db.String(20))
    score = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_contact = db.Column(db.DateTime)
    last_followup_email = db.Column(db.DateTime)
    
    opportunities = db.relationship('Opportunity', backref='lead', lazy=True)
    tasks = db.relationship('Task', backref='lead', lazy=True)
    schedules = db.relationship('Schedule', backref='lead', lazy=True)

class Opportunity(db.Model):
    __tablename__ = 'opportunities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    stage = db.Column(db.String(20))
    close_date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    industry = db.Column(db.String(50))
    website = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    opportunities = db.relationship('Opportunity', backref='account', lazy=True)

class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'))
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'))
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Email(db.Model):
    __tablename__ = 'emails'
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(200))
    sender = db.Column(db.String(120))
    sender_name = db.Column(db.String(100))
    subject = db.Column(db.String(200))
    content = db.Column(db.Text)
    received_date = db.Column(db.DateTime)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UnknownEmail(db.Model):
    __tablename__ = 'unknown_emails'
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(120))
    sender_name = db.Column(db.String(100))
    subject = db.Column(db.String(200))
    content = db.Column(db.Text)
    received_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EmailFetchTracker(db.Model):
    __tablename__ = 'email_fetch_tracker'
    id = db.Column(db.Integer, primary_key=True)
    last_fetch_time = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class UserSettings(db.Model):
    __tablename__ = 'user_settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    claude_api_key = db.Column(db.String(200))
    mail_server = db.Column(db.String(200))
    mail_port = db.Column(db.String(10))
    mail_use_tls = db.Column(db.Boolean, default=True)
    mail_username = db.Column(db.String(200))
    mail_password = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
