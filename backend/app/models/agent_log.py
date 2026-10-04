import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base


class AgentActivityLog(Base):
    __tablename__ = "agent_activity_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False)
    summary = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="completed", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
