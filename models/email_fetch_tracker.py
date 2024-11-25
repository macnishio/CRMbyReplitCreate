from datetime import datetime
from extensions import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, DateTime, ForeignKey

class EmailFetchTracker(db.Model):
    __tablename__ = 'email_fetch_tracker'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_fetch_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
