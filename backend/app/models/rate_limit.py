from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class RateLimit(Base):
    """IP ve email bazlı rate limiting için model"""
    __tablename__ = "rate_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String, nullable=False, index=True)  # IP veya email
    action_type = Column(String, nullable=False)  # login_attempt, email_send, register_attempt
    attempt_count = Column(Integer, default=1, nullable=False)
    first_attempt_at = Column(DateTime(timezone=True), server_default=func.now())
    last_attempt_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
