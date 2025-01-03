from datetime import datetime
from extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, text
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .behavior_pattern import BehaviorPattern
    from .opportunity import Opportunity
    from .schedule import Schedule
    from .task import Task
    from .email import Email
    from .user import User

class Lead(db.Model):
    __tablename__ = 'leads'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='New')
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text('CURRENT_TIMESTAMP')
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=text('CURRENT_TIMESTAMP')
    )
    last_contact: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_followup_email: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_followup_tracking_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_email_opened: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # リレーションシップ
    user: Mapped["User"] = relationship("User", back_populates="leads")
    opportunities: Mapped[List["Opportunity"]] = relationship("Opportunity", back_populates="lead", cascade="all, delete-orphan")
    schedules: Mapped[List["Schedule"]] = relationship("Schedule", back_populates="lead", cascade="all, delete-orphan")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="lead", cascade="all, delete-orphan")
    emails: Mapped[List["Email"]] = relationship("Email", back_populates="lead", lazy="dynamic")
    behavior_patterns: Mapped[List["BehaviorPattern"]] = relationship("BehaviorPattern", back_populates="lead", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Lead {self.name}>'
