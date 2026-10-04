import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    subject = Column(String(100), nullable=False, index=True)
    priority = Column(String(20), nullable=False, default="medium", index=True)  # low, medium, high
    status = Column(String(20), nullable=False, default="pending", index=True)   # pending, completed, missed, in_progress
    due_date = Column(String(20), nullable=False, index=True)  # ISO YYYY-MM-DD
    estimated_minutes = Column(Integer, nullable=True, default=60)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="tasks")
    study_sessions = relationship("StudySession", back_populates="task")
