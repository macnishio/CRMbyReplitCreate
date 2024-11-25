from datetime import datetime
from extensions import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Boolean
from typing import Optional

class Schedule(db.Model):
    __tablename__ = 'schedules'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='Scheduled')
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    lead_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('leads.id'), nullable=True)
    email_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('emails.id'), nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)

    # リレーションシップ
    lead = db.relationship('Lead', back_populates='schedules')
    email = db.relationship('Email', back_populates='schedules')
