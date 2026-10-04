import re
from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


AgentActionType = Literal[
    "generate_plan",
    "query_progress",
    "reschedule_missed",
    "optimize_schedule",
    "academic_coaching",
]

EventType = Literal["study", "exam", "meal", "sleep", "fixed"]

EVENT_TYPE_COLORS: Dict[str, str] = {
    "study": "#C5A059",   # Muted Gold
    "exam": "#DC2626",    # Crimson / Ruby
    "meal": "#10B981",    # Emerald
    "sleep": "#6366F1",   # Indigo
    "fixed": "#8B5CF6",   # Purple
}


class AgentWorkflowStep(BaseModel):
    step_id: int
    name: str
    status: Literal["processing", "retrieving_data", "executing_action", "awaiting_approval", "completed", "failed"]
    summary: str


class ProposedSessionBlock(BaseModel):
    subject: str = Field(..., min_length=1, description="Subject name or category")
    topic: str = Field(..., min_length=1, description="Topic or activity title")
    date: str = Field(..., description="Target date in YYYY-MM-DD format")
    start_time: str = Field(..., description="Start time in HH:MM (24-hour)")
    end_time: str = Field(..., description="End time in HH:MM (24-hour)")
    duration_minutes: int = Field(..., gt=0, description="Duration in minutes")
    reason: str = Field(..., min_length=2, description="Rationale for scheduling this block")
    status: str = "upcoming"
    event_type: EventType = "study"
    color: Optional[str] = None

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if not re.match(r"^20\d{2}-\d{2}-\d{2}$", v.strip()):
            raise ValueError(f"Invalid date format '{v}'. Expected YYYY-MM-DD.")
        return v.strip()

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        v_clean = v.strip()
        if not re.match(r"^([01]\d|2[0-3]):[0-5]\d$", v_clean):
            raise ValueError(f"Invalid time format '{v}'. Expected HH:MM in 24-hour format.")
        return v_clean

    def model_post_init(self, __context: Any) -> None:
        if not self.color:
            self.color = EVENT_TYPE_COLORS.get(self.event_type, "#C5A059")


class AgentExecuteRequest(BaseModel):
    prompt: str = Field(..., min_length=2, description="Natural language request from student")
    preferred_hours: Optional[float] = None
    target_date: Optional[str] = None
    timezone: Optional[str] = None


class AgentExecuteResponse(BaseModel):
    prompt: str
    action_type: str
    tool_name: str
    summary: str
    explanation: str
    steps: List[AgentWorkflowStep]
    requires_approval: bool
    proposed_sessions: List[ProposedSessionBlock] = []
    target_date: Optional[str] = None
    timezone: Optional[str] = None
    assumptions: List[str] = []
    is_general_recommendation: bool = False
    constraint_errors: List[str] = []
    data_snapshot: Optional[Dict[str, Any]] = None



class ScheduleApprovalRequest(BaseModel):
    sessions: List[ProposedSessionBlock]
    log_id: Optional[str] = None


class ScheduleApprovalResponse(BaseModel):
    approved: bool
    saved_count: int
    rejected_count: int
    message: str
    saved_session_ids: List[str] = []


class ScheduleRejectRequest(BaseModel):
    reason: Optional[str] = "Student rejected proposed changes"
    log_id: Optional[str] = None


class ScheduleRejectResponse(BaseModel):
    approved: bool = False
    message: str


class AgentActivityLogResponse(BaseModel):
    id: str
    action_type: str
    tool_name: str
    summary: str
    status: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
