from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)
    audio_path = Column(String, nullable=False)
    transcript = Column(Text, nullable=True)
    acoustic_features = Column(JSON, nullable=True)
    emotion_analysis = Column(JSON, nullable=True)
    content_analysis = Column(JSON, nullable=True)
    advanced_acoustic = Column(JSON, nullable=True)
    linguistic_analysis = Column(JSON, nullable=True)
    gemini_report = Column(Text, nullable=True)
    report_pdf_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="analyses")
    participant = relationship("Participant", back_populates="analyses")


