from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.utils.date_utils import time_to_minutes, get_day_of_week

SessionStatusType = Literal["upcoming", "planned", "completed", "missed", "cancelled"]


class SessionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    topic: Optional[str] = None
    subject: str = Field(..., min_length=1, max_length=100)
    date: str = Field(..., description="YYYY-MM-DD")
    day_of_week: Optional[str] = None
    start_time: str = Field(..., pattern=r"^\d{1,2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{1,2}:\d{2}$")
    duration_minutes: Optional[int] = None
    status: SessionStatusType = "upcoming"
    notes: Optional[str] = None
    color: Optional[str] = "#C5A059"
    task_id: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_and_compute(cls, data: dict):
        if isinstance(data, dict):
            # Sync topic & title
            if "topic" in data and ("title" not in data or not data["title"]):
                data["title"] = data["topic"]
            elif "title" in data and ("topic" not in data or not data["topic"]):
                data["topic"] = data["title"]

            # Compute day of week from date if missing
            if ("day_of_week" not in data or not data["day_of_week"]) and "date" in data:
                try:
                    data["day_of_week"] = get_day_of_week(data["date"])
                except Exception:
                    pass

            # Compute duration if missing or <= 0
            if "start_time" in data and "end_time" in data:
                try:
                    s = time_to_minutes(data["start_time"])
                    e = time_to_minutes(data["end_time"])
                    if e > s:
                        computed_duration = e - s
                        if "duration_minutes" not in data or not data["duration_minutes"]:
                            data["duration_minutes"] = computed_duration
                except Exception:
                    pass

        return data


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    topic: Optional[str] = None
    subject: Optional[str] = Field(None, min_length=1, max_length=100)
    date: Optional[str] = None
    day_of_week: Optional[str] = None
    start_time: Optional[str] = Field(None, pattern=r"^\d{1,2}:\d{2}$")
    end_time: Optional[str] = Field(None, pattern=r"^\d{1,2}:\d{2}$")
    duration_minutes: Optional[int] = None
    status: Optional[SessionStatusType] = None
    notes: Optional[str] = None
    color: Optional[str] = None
    task_id: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_topic(cls, data: dict):
        if isinstance(data, dict):
            if "topic" in data and ("title" not in data or not data["title"]):
                data["title"] = data["topic"]
            elif "title" in data and ("topic" not in data or not data["topic"]):
                data["topic"] = data["title"]
        return data


class SessionStatusUpdate(BaseModel):
    status: SessionStatusType


class SessionResponse(SessionBase):
    id: str
    user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
