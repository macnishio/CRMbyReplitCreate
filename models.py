from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from typing import List
from sqlalchemy import Integer, String, DateTime, Float, ForeignKey

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128))
    leads: Mapped[List["Lead"]] = db.relationship('Lead', backref='user', lazy='dynamic')
    opportunities: Mapped[List["Opportunity"]] = db.relationship('Opportunity', backref='user', lazy='dynamic')
    accounts: Mapped[List["Account"]] = db.relationship('Account', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Lead(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    score: Mapped[float] = mapped_column(Float)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_contact: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    emails: Mapped[List["Email"]] = db.relationship('Email', backref='lead', lazy='dynamic')
    opportunities: Mapped[List["Opportunity"]] = db.relationship('Opportunity', back_populates='lead', cascade='all, delete-orphan')
    schedules: Mapped[List["Schedule"]] = db.relationship('Schedule', back_populates='lead', cascade='all, delete-orphan')
    tasks: Mapped[List["Task"]] = db.relationship('Task', back_populates='lead', cascade='all, delete-orphan')

class Email(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender: Mapped[str] = mapped_column(String(120), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(100))
    subject: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(db.Text)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('lead.id'), nullable=False)

class UnknownEmail(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender: Mapped[str] = mapped_column(String(120), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(100))
    subject: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(db.Text)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Opportunity(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20))
    amount: Mapped[float] = mapped_column(Float)
    close_date: Mapped[datetime] = mapped_column(DateTime)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('lead.id'), nullable=False)
    lead: Mapped["Lead"] = db.relationship('Lead', back_populates='opportunities')

class Account(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(50))
    website: Mapped[str] = mapped_column(String(200))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)

class Schedule(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(db.Text)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('lead.id'), nullable=False)
    lead: Mapped["Lead"] = db.relationship('Lead', back_populates='schedules')

class Task(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(db.Text)
    due_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('lead.id'), nullable=False)
    lead: Mapped["Lead"] = db.relationship('Lead', back_populates='tasks')

class EmailFetchTracker(db.Model):
    __tablename__ = 'email_fetch_tracker'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_fetch_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
