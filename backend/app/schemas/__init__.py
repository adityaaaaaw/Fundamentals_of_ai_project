from app.schemas.user import UserBase, UserCreate, UserResponse
from app.schemas.task import TaskBase, TaskCreate, TaskUpdate, TaskStatusUpdate, TaskResponse
from app.schemas.session import SessionBase, SessionCreate, SessionUpdate, SessionStatusUpdate, SessionResponse
from app.schemas.exam import ExamBase, ExamCreate, ExamUpdate, ExamResponse
from app.schemas.dashboard import DashboardSummary, DayStudyMetric, WeeklyProgressResponse
from app.schemas.ai import (
    StudyBlock,
    GeneratePlanRequest,
    GeneratePlanResponse,
    AskRequest,
    AskResponse,
    OptimizeScheduleRequest,
    OptimizeScheduleResponse,
)

__all__ = [
    "UserBase", "UserCreate", "UserResponse",
    "TaskBase", "TaskCreate", "TaskUpdate", "TaskStatusUpdate", "TaskResponse",
    "SessionBase", "SessionCreate", "SessionUpdate", "SessionStatusUpdate", "SessionResponse",
    "ExamBase", "ExamCreate", "ExamUpdate", "ExamResponse",
    "DashboardSummary", "DayStudyMetric", "WeeklyProgressResponse",
    "StudyBlock", "GeneratePlanRequest", "GeneratePlanResponse",
    "AskRequest", "AskResponse", "OptimizeScheduleRequest", "OptimizeScheduleResponse",
]
