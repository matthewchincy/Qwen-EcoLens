from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import Base

class CarbonScore(str, enum.Enum):
    LOW = 'Low'
    MEDIUM = 'Medium'
    HIGH = 'High'

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(50), unique=True, index=True)
    username = Column(String(100))
    language = Column(String(10), default='en')
    credits = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)

    food_logs = relationship("FoodLog", back_populates="user")

class FoodLog(Base):
    __tablename__ = "food_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    food_name = Column(String(255))
    calories = Column(Integer)
    carbon_score = Column(SAEnum(CarbonScore))
    image_url = Column(Text)
    analysis_json = Column(JSON)
    credits_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="food_logs")
