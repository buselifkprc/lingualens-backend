from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime
from datetime import datetime
from app.database import Base

class Review(Base):
    __tablename__ = "restaurant_reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    restaurant_name = Column(String(100), nullable=False)
    address = Column(Text)
    rating = Column(Numeric)
    review_text = Column(Text)
    visited_at = Column(DateTime, default=datetime.utcnow)
