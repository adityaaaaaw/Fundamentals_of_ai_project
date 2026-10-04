import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Exam(Base):
    __tablename__ = "exams"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    subject = Column(String(100), nullable=False, index=True)
    exam_date = Column(String(20), nullable=False, index=True)  # YYYY-MM-DD
    exam_time = Column(String(50), nullable=False)              # e.g. "10:00 AM - 12:00 PM"
    room = Column(String(100), nullable=True)
    weight = Column(String(50), nullable=True)                  # e.g. "25% of Grade"
    total_marks = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="exams")
