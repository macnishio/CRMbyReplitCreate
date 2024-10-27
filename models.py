from datetime import datetime
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    google_event_id = db.Column(db.String(100))  # Added this line
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'))
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'))
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    
    # Relationships
    user = db.relationship('User', back_populates='schedules')
    lead = db.relationship('Lead', back_populates='schedules')
    opportunity = db.relationship('Opportunity', back_populates='schedules')
    account = db.relationship('Account', back_populates='schedules')

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    role = db.Column(db.String(20), default='user')
    google_service_account_file = db.Column(db.Text)
    google_calendar_id = db.Column(db.String(200))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Relationships
    leads = db.relationship('Lead', back_populates='user', cascade='all, delete-orphan')
    opportunities = db.relationship('Opportunity', back_populates='user', cascade='all, delete-orphan')
    accounts = db.relationship('Account', back_populates='user', cascade='all, delete-orphan')
    schedules = db.relationship('Schedule', back_populates='user', cascade='all, delete-orphan')
    tasks = db.relationship('Task', back_populates='user', cascade='all, delete-orphan')
    emails = db.relationship('Email', back_populates='user', cascade='all, delete-orphan')
