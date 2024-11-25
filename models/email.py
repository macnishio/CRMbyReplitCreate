from datetime import datetime
from extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Boolean
from typing import Optional, List

class Email(db.Model):
    __tablename__ = 'emails'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    sender: Mapped[str] = mapped_column(String(120), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    received_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('leads.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    ai_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_analysis_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ai_model_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # リレーションシップ
    lead: Mapped["Lead"] = relationship("Lead", back_populates="emails")
    user: Mapped["User"] = relationship("User", back_populates="emails")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="email", lazy="dynamic")
    schedules: Mapped[List["Schedule"]] = relationship("Schedule", back_populates="email", lazy="dynamic")

    def __repr__(self):
        return f'<Email {self.subject}>'
