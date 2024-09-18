from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

class User(UserMixin, db.Model):
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
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'))
    user: Mapped['User'] = relationship('User', backref='leads')
    score: Mapped[float] = mapped_column(Float, default=0.0)
    
    # New enriched data fields
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    job_title: Mapped[str] = mapped_column(String(255), nullable=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=True)
    company_domain: Mapped[str] = mapped_column(String(255), nullable=True)
    company_industry: Mapped[str] = mapped_column(String(255), nullable=True)
    company_employee_count: Mapped[int] = mapped_column(Integer, nullable=True)

class Opportunity(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    close_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    user: Mapped['User'] = relationship('User', backref='opportunities')
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('account.id'), nullable=False)
    account: Mapped['Account'] = relationship('Account', backref='opportunities')
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('lead.id'), nullable=True)
    lead: Mapped['Lead'] = relationship('Lead', backref='opportunities')

class Account(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(50))
    website: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'))
    user: Mapped['User'] = relationship('User', backref='accounts')
