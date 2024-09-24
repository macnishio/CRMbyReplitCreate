from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(20), default='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Lead(db.Model):
    __tablename__ = 'leads'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default='New')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_contact: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_followup_email: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_followup_tracking_id: Mapped[str] = mapped_column(String(36), nullable=True)
    last_email_opened: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    user: Mapped['User'] = relationship('User', backref='leads')
    score: Mapped[float] = mapped_column(Float, default=0.0)
    emails: Mapped[list['Email']] = relationship('Email', back_populates='lead')

class Email(db.Model):
    __tablename__ = 'emails'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('leads.id'))
    lead: Mapped['Lead'] = relationship('Lead', back_populates='emails')

class Opportunity(db.Model):
    __tablename__ = 'opportunities'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    close_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    user: Mapped['User'] = relationship('User', backref='opportunities')
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounts.id'), nullable=False)
    account: Mapped['Account'] = relationship('Account', backref='opportunities')
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('leads.id'), nullable=True)
    lead: Mapped['Lead'] = relationship('Lead', backref='opportunities')

class Account(db.Model):
    __tablename__ = 'accounts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(50))
    website: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    user: Mapped['User'] = relationship('User', backref='accounts')

class Schedule(db.Model):
    __tablename__ = 'schedules'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    user: Mapped['User'] = relationship('User', backref='schedules')
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounts.id'), nullable=True)
    account: Mapped['Account'] = relationship('Account', backref='schedules')
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('leads.id'), nullable=True)
    lead: Mapped['Lead'] = relationship('Lead', backref='schedules')
    opportunity_id: Mapped[int] = mapped_column(Integer, ForeignKey('opportunities.id'), nullable=True)
    opportunity: Mapped['Opportunity'] = relationship('Opportunity', backref='schedules')

class Task(db.Model):
    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    due_date: Mapped[datetime] = mapped_column(DateTime)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    user: Mapped['User'] = relationship('User', backref='tasks')
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('leads.id'), nullable=True)
    lead: Mapped['Lead'] = relationship('Lead', backref='tasks')
    opportunity_id: Mapped[int] = mapped_column(Integer, ForeignKey('opportunities.id'), nullable=True)
    opportunity: Mapped['Opportunity'] = relationship('Opportunity', backref='tasks')
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounts.id'), nullable=True)
    account: Mapped['Account'] = relationship('Account', backref='tasks')
