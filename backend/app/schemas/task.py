from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator

PriorityType = Literal["low", "medium", "high"]
StatusType = Literal["pending", "in_progress", "completed", "missed"]


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    subject: str = Field(..., min_length=1, max_length=100)
    priority: PriorityType = "medium"
    status: StatusType = "pending"
    due_date: str = Field(..., description="ISO date YYYY-MM-DD")
    estimated_minutes: Optional[int] = 60
    notes: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_notes_and_description(cls, data: dict):
        if isinstance(data, dict):
            # If notes is provided but description is not, set description = notes
            if "notes" in data and ("description" not in data or not data["description"]):
                data["description"] = data["notes"]
            elif "description" in data and ("notes" not in data or not data["notes"]):
                data["notes"] = data["description"]
        return data


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    notes: Optional[str] = None
    subject: Optional[str] = Field(None, min_length=1, max_length=100)
    priority: Optional[PriorityType] = None
    status: Optional[StatusType] = None
    due_date: Optional[str] = None
    estimated_minutes: Optional[int] = None

    @model_validator(mode="before")
    @classmethod
    def sync_notes(cls, data: dict):
        if isinstance(data, dict):
            if "notes" in data and ("description" not in data or not data["description"]):
                data["description"] = data["notes"]
            elif "description" in data and ("notes" not in data or not data["notes"]):
                data["notes"] = data["description"]
        return data


class TaskStatusUpdate(BaseModel):
    status: StatusType


class TaskResponse(TaskBase):
    id: str
    user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
