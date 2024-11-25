from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, ForeignKey
from datetime import datetime

from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .lead import Lead
    from .opportunity import Opportunity
    from .email import Email
    from .subscription import Subscription
    from .user_settings import UserSettings

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(20), default='user')
    google_calendar_id: Mapped[str] = mapped_column(String(255), nullable=True)
    google_service_account_file: Mapped[str] = mapped_column(String(255), nullable=True)

    # リレーションシップ
    leads: Mapped[List["Lead"]] = relationship("Lead", back_populates="user", foreign_keys="[Lead.user_id]")
    opportunities: Mapped[List["Opportunity"]] = relationship("Opportunity", back_populates="user", foreign_keys="[Opportunity.user_id]")
    emails: Mapped[List["Email"]] = relationship("Email", back_populates="user", foreign_keys="[Email.user_id]")
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="user", uselist=False)
    settings: Mapped["UserSettings"] = relationship("UserSettings", back_populates="user", uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
