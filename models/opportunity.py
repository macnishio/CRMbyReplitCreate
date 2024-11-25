from datetime import datetime
from extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Boolean
from typing import Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .lead import Lead
    from .account import Account
    from .user import User

class Opportunity(db.Model):
    __tablename__ = 'opportunities'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    stage: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    close_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('leads.id'), nullable=False)
    account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounts.id'), nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ
    lead: Mapped["Lead"] = relationship("Lead", back_populates="opportunities")
    account: Mapped[Optional["Account"]] = relationship("Account", back_populates="opportunities")
    user: Mapped["User"] = relationship("User", back_populates="opportunities")

    def __repr__(self):
        return f'<Opportunity {self.name}>'
