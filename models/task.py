from datetime import datetime
from extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Boolean, text
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .lead import Lead
    from .email import Email

class Task(db.Model):
    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    due_date: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    lead_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('leads.id'), nullable=True)
    email_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('emails.id'), nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
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

    # リレーションシップ
    lead = relationship('Lead', back_populates='tasks')
    email = relationship('Email', back_populates='tasks')

    def __repr__(self):
        return f'<Task {self.title}>'
