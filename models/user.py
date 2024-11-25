from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, ForeignKey
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(20), default='user')
    google_calendar_id: Mapped[str] = mapped_column(String(255), nullable=True)
    google_service_account_file: Mapped[str] = mapped_column(String(255), nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
