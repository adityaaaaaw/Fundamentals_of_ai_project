from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.utils.date_utils import calculate_days_remaining


class ExamBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    subject: str = Field(..., min_length=1, max_length=100)
    exam_date: str = Field(..., description="YYYY-MM-DD")
    exam_time: str = Field(..., description="e.g. 10:00 AM - 12:00 PM")
    date: Optional[str] = None
    time: Optional[str] = None
    room: Optional[str] = None
    weight: Optional[str] = None
    total_marks: Optional[int] = None
    notes: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, data: dict):
        if isinstance(data, dict):
            # Sync date and exam_date
            if "date" in data and ("exam_date" not in data or not data["exam_date"]):
                data["exam_date"] = data["date"]
            elif "exam_date" in data and ("date" not in data or not data["date"]):
                data["date"] = data["exam_date"]

            # Sync time and exam_time
            if "time" in data and ("exam_time" not in data or not data["exam_time"]):
                data["exam_time"] = data["time"]
            elif "exam_time" in data and ("time" not in data or not data["time"]):
                data["time"] = data["exam_time"]
        return data


class ExamCreate(ExamBase):
    pass


class ExamUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    subject: Optional[str] = Field(None, min_length=1, max_length=100)
    exam_date: Optional[str] = None
    exam_time: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    room: Optional[str] = None
    weight: Optional[str] = None
    total_marks: Optional[int] = None
    notes: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, data: dict):
        if isinstance(data, dict):
            if "date" in data and ("exam_date" not in data or not data["exam_date"]):
                data["exam_date"] = data["date"]
            elif "exam_date" in data and ("date" not in data or not data["date"]):
                data["date"] = data["exam_date"]

            if "time" in data and ("exam_time" not in data or not data["exam_time"]):
                data["exam_time"] = data["time"]
            elif "exam_time" in data and ("time" not in data or not data["time"]):
                data["time"] = data["exam_time"]
        return data


class ExamResponse(ExamBase):
    id: str
    user_id: str
    days_remaining: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def compute_days_remaining(self):
        if self.exam_date and self.days_remaining is None:
            try:
                self.days_remaining = calculate_days_remaining(self.exam_date)
            except Exception:
                self.days_remaining = 0
        return self
