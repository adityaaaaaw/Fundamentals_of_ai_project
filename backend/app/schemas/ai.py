from typing import List, Optional
from pydantic import BaseModel, Field


class StudyBlock(BaseModel):
    time: str = Field(..., description="e.g. 09:00 - 10:30")
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    subject: str
    topic: str
    duration_minutes: int = 60
    strategy: str = ""
    break_recommendation: Optional[str] = "10-minute hydration & stretch break"
    priority: Optional[str] = "medium"


class GeneratePlanRequest(BaseModel):
    goal: str = Field(..., min_length=2, description="Student's study goal or prompt")
    subject: Optional[str] = None
    available_hours: Optional[float] = None
    target_date: Optional[str] = None
    preferred_duration: Optional[int] = None
    instructions: Optional[str] = None


class GeneratePlanResponse(BaseModel):
    goal: str
    summary: str
    total_hours: float
    blocks: List[StudyBlock]


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2)
    context: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    suggested_actions: List[str] = []


class OptimizeScheduleRequest(BaseModel):
    target_date: Optional[str] = None
    available_hours: Optional[float] = None
    preferences: Optional[str] = None


class OptimizeScheduleResponse(BaseModel):
    summary: str
    recommendations: List[StudyBlock]
