from datetime import datetime
from extensions import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Numeric, Text, DateTime, ForeignKey

class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    stripe_price_id: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    features: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    subscriptions = db.relationship('Subscription', back_populates='plan')

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey('subscription_plans.id'), nullable=False)
    stripe_subscription_id: Mapped[str] = mapped_column(String(100), nullable=False)
    stripe_customer_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='active')
    current_period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    user = db.relationship('User', back_populates='subscription')
    plan = db.relationship('SubscriptionPlan', back_populates='subscriptions')
