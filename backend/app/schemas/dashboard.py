from typing import List
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    missed_tasks: int
    in_progress_tasks: int
    completion_rate: int
    planned_study_time_minutes: int
    completed_study_time_minutes: int
    current_streak_days: int


class DayStudyMetric(BaseModel):
    day: str
    fullDay: str
    studiedHours: float
    targetHours: float


class WeeklyProgressResponse(BaseModel):
    metrics: List[DayStudyMetric]
    total_studied_hours: float
    total_target_hours: float
    current_streak_days: int
