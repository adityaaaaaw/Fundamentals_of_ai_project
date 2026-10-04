from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.schemas.dashboard import DashboardSummary, WeeklyProgressResponse
from app.schemas.session import SessionResponse
from app.schemas.exam import ExamResponse
from app.schemas.task import TaskResponse
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def read_dashboard_summary(db: Session = Depends(get_db)):
    return dashboard_service.get_dashboard_summary(db=db, user_id=settings.DEMO_USER_ID)


@router.get("/progress", response_model=WeeklyProgressResponse)
@router.get("/weekly-progress", response_model=WeeklyProgressResponse)
def read_weekly_progress(db: Session = Depends(get_db)):
    return dashboard_service.get_weekly_progress(db=db, user_id=settings.DEMO_USER_ID)


@router.get("/today", response_model=List[SessionResponse])
@router.get("/today-sessions", response_model=List[SessionResponse])
def read_today_sessions(db: Session = Depends(get_db)):
    return dashboard_service.get_today_sessions(db=db, user_id=settings.DEMO_USER_ID)


@router.get("/upcoming", response_model=List[ExamResponse])
@router.get("/upcoming-exams", response_model=List[ExamResponse])
def read_upcoming_exams(db: Session = Depends(get_db)):
    return dashboard_service.get_upcoming_exams(db=db, user_id=settings.DEMO_USER_ID)


@router.get("/high-priority", response_model=List[TaskResponse])
@router.get("/high-priority-tasks", response_model=List[TaskResponse])
def read_high_priority_tasks(db: Session = Depends(get_db)):
    return dashboard_service.get_high_priority_tasks(db=db, user_id=settings.DEMO_USER_ID)
