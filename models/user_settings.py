from datetime import datetime
import json
from cryptography.fernet import Fernet
import base64
from flask import current_app
from extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, Boolean, Text, ForeignKey
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User

class UserSettings(db.Model):
    __tablename__ = 'user_settings'
    
    # リレーションシップ
    user: Mapped["User"] = relationship("User", back_populates="settings")
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    mail_server: Mapped[str] = mapped_column(String(120))
    mail_port: Mapped[int] = mapped_column(Integer)
    mail_use_tls: Mapped[bool] = mapped_column(Boolean, default=True)
    mail_username: Mapped[str] = mapped_column(String(120))
    _mail_password: Mapped[str] = mapped_column('mail_password', String(255))
    _claude_api_key: Mapped[Optional[str]] = mapped_column('claude_api_key', String(255), nullable=True)
    _clearbit_api_key: Mapped[Optional[str]] = mapped_column('clearbit_api_key', String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    filter_preferences: Mapped[Optional[str]] = mapped_column('filter_preferences', Text, nullable=True)

    def _get_encryption_key(self):
        key = current_app.config['SECRET_KEY']
        return base64.urlsafe_b64encode(key.ljust(32)[:32].encode())

    def _encrypt(self, data):
        if not data:
            return None
        f = Fernet(self._get_encryption_key())
        return f.encrypt(data.encode()).decode()

    def _decrypt(self, data):
        if not data:
            return None
        f = Fernet(self._get_encryption_key())
        return f.decrypt(data.encode()).decode()

    @property
    def mail_password(self):
        return self._decrypt(self._mail_password) if self._mail_password else None

    @mail_password.setter
    def mail_password(self, value):
        self._mail_password = self._encrypt(value) if value else None

    @property
    def claude_api_key(self):
        return self._decrypt(self._claude_api_key) if self._claude_api_key else None

    @claude_api_key.setter
    def claude_api_key(self, value):
        self._claude_api_key = self._encrypt(value) if value else None

    @property
    def clearbit_api_key(self):
        return self._decrypt(self._clearbit_api_key) if self._clearbit_api_key else None

    @clearbit_api_key.setter
    def clearbit_api_key(self, value):
        self._clearbit_api_key = self._encrypt(value) if value else None

    @property
    def opportunity_filters(self):
        if not self.filter_preferences:
            return {}
        try:
            all_filters = json.loads(self.filter_preferences)
            return all_filters.get('opportunities', {})
        except json.JSONDecodeError:
            return {}

    @opportunity_filters.setter
    def opportunity_filters(self, value):
        try:
            current_filters = json.loads(self.filter_preferences) if self.filter_preferences else {}
        except json.JSONDecodeError:
            current_filters = {}
        
        current_filters['opportunities'] = value
        self.filter_preferences = json.dumps(current_filters)
