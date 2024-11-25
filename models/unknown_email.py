from datetime import datetime
from extensions import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, DateTime, Boolean

class UnknownEmail(db.Model):
    __tablename__ = 'unknown_emails'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender: Mapped[str] = mapped_column(String(120), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    received_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
