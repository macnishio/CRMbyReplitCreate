from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from typing import List
from sqlalchemy import Integer, String, DateTime, Float, ForeignKey, Text, Boolean
from typing import List, Optional 

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(20), nullable=False, default='user')

    leads: Mapped[List["Lead"]] = db.relationship('Lead', backref='user', lazy='dynamic')
    opportunities: Mapped[List["Opportunity"]] = db.relationship('Opportunity', backref='user', lazy='dynamic')
    accounts: Mapped[List["Account"]] = db.relationship('Account', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Lead(db.Model):
    __tablename__ = 'leads'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='New')
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_contact: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_followup_email: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    emails: Mapped[List["Email"]] = db.relationship('Email', backref='lead', lazy='dynamic')
    opportunities: Mapped[List["Opportunity"]] = db.relationship('Opportunity', back_populates='lead', cascade='all, delete-orphan')
    schedules: Mapped[List["Schedule"]] = db.relationship('Schedule', back_populates='lead', cascade='all, delete-orphan')
    tasks: Mapped[List["Task"]] = db.relationship('Task', back_populates='lead', cascade='all, delete-orphan')

class Email(db.Model):
    __tablename__ = 'emails'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender: Mapped[str] = mapped_column(String(120), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(100))
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
    amount: Mapped[float] = mapped_column(Float)
    close_date: Mapped[datetime] = mapped_column(DateTime)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('leads.id'), nullable=False)

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
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('leads.id'), nullable=False)

    lead: Mapped["Lead"] = db.relationship('Lead', back_populates='schedules')

class Task(db.Model):
    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    due_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[str] = mapped_column(String(10), default='medium')
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('leads.id'), nullable=False)

    lead: Mapped["Lead"] = db.relationship('Lead', back_populates='tasks')
    subtasks: Mapped[List["Subtask"]] = db.relationship('Subtask', back_populates='task', cascade='all, delete-orphan')

    @property
    def total_subtasks(self):
        return len(self.subtasks)

    @property
    def completed_subtasks(self):
        return sum(1 for subtask in self.subtasks if subtask.completed)

class Subtask(db.Model):
    __tablename__ = 'subtasks'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey('tasks.id'), nullable=False)

    task: Mapped["Task"] = db.relationship('Task', back_populates='subtasks')

class EmailFetchTracker(db.Model):
    __tablename__ = 'email_fetch_tracker'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_fetch_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)