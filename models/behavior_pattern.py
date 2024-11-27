from datetime import datetime
from extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey, text
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .lead import Lead

class BehaviorPattern(db.Model):
    __tablename__ = 'behavior_patterns'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey('leads.id'), nullable=False)
    pattern_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=False,
        default=datetime.utcnow,
        server_default=text('CURRENT_TIMESTAMP')
    )
    
    # リレーションシップ
    lead = relationship("Lead", back_populates="behavior_patterns")

    def __repr__(self):
        return f'<BehaviorPattern {self.pattern_type}>'
