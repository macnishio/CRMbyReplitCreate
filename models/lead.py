from extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from typing import Optional, List

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
    last_followup_tracking_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_email_opened: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    opportunities: Mapped[List["Opportunity"]] = relationship("Opportunity", back_populates="lead", cascade="all, delete-orphan")
    schedules: Mapped[List["Schedule"]] = relationship("Schedule", back_populates="lead", cascade="all, delete-orphan")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="lead", cascade="all, delete-orphan")
    emails: Mapped[List["Email"]] = relationship("Email", back_populates="lead", lazy="dynamic")
    
    def __repr__(self):
        return f'<Lead {self.name}>'
