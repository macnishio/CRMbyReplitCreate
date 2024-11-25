from datetime import datetime
from extensions import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, Text, Boolean, JSON

class SystemChange(db.Model):
    __tablename__ = 'system_changes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'config', 'database', 'code'
    description: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    change_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)  # Store additional context
    is_risky: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_analysis: Mapped[str] = mapped_column(Text, nullable=True)
    rollback_plan: Mapped[str] = mapped_column(Text, nullable=True)
    
class RollbackHistory(db.Model):
    __tablename__ = 'rollback_history'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    system_change_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('system_changes.id'))
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    ai_recommendation: Mapped[str] = mapped_column(Text, nullable=True)
    rollback_details: Mapped[dict] = mapped_column(JSON, nullable=True)
