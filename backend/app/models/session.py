import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(200), nullable=False)  # Acts as topic / session title
    subject = Column(String(100), nullable=False, index=True)
    date = Column(String(20), nullable=False, index=True)  # YYYY-MM-DD
    day_of_week = Column(String(20), nullable=True)        # Monday, Tuesday, etc.
    start_time = Column(String(10), nullable=False)        # HH:MM (24-hour)
    end_time = Column(String(10), nullable=False)          # HH:MM (24-hour)
    duration_minutes = Column(Integer, nullable=False, default=60)
    status = Column(String(20), nullable=False, default="upcoming", index=True)  # upcoming/planned, completed, missed/cancelled
    notes = Column(Text, nullable=True)
    color = Column(String(30), nullable=True, default="#C5A059")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="study_sessions")
    task = relationship("Task", back_populates="study_sessions")
