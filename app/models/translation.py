from sqlalchemy import Column, Integer, Text, String, ForeignKey, DateTime
from datetime import datetime
from app.database import Base

class Translation(Base):
    __tablename__ = "translation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_text = Column(Text, nullable=False)
    target_language = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
