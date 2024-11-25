from extensions import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, ForeignKey

class Account(db.Model):
    __tablename__ = 'accounts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(50))
    website: Mapped[str] = mapped_column(String(200))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)

    # リレーションシップ
    opportunities = db.relationship('Opportunity', back_populates='account')
