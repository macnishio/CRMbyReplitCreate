from datetime import datetime
from extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, Text, Boolean, JSON, ForeignKey
from typing import Optional, List

class SystemChange(db.Model):
    __tablename__ = 'system_changes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'config', 'database', 'code'
    description: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    change_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Store additional context
    is_risky: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rollback_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # リレーションシップ
    rollback_histories: Mapped[List["RollbackHistory"]] = relationship("RollbackHistory", back_populates="system_change", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<SystemChange {self.change_type}: {self.description[:50]}...>'
    
class RollbackHistory(db.Model):
    __tablename__ = 'rollback_history'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    system_change_id: Mapped[int] = mapped_column(Integer, ForeignKey('system_changes.id'), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rollback_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # リレーションシップ
    system_change: Mapped["SystemChange"] = relationship("SystemChange", back_populates="rollback_histories")

    def __repr__(self):
        return f'<RollbackHistory {self.id} for SystemChange {self.system_change_id}>'
