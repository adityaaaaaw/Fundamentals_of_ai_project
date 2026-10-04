from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.models.task import Task
from app.models.exam import Exam
from app.models.session import StudySession
from app.schemas.ai import (
    GeneratePlanRequest,
    GeneratePlanResponse,
    AskRequest,
    AskResponse,
    OptimizeScheduleRequest,
    OptimizeScheduleResponse,
)
from app.schemas.agent import (
    AgentExecuteRequest,
    AgentExecuteResponse,
    ScheduleApprovalRequest,
    ScheduleApprovalResponse,
    ScheduleRejectRequest,
    ScheduleRejectResponse,
    AgentActivityLogResponse,
)
from app.services import gemini_service, agent_service

router = APIRouter(prefix="/ai", tags=["Gemini AI & Agent"])


def _gather_user_context(db: Session, user_id: str) -> dict:
    tasks = db.query(Task).filter(Task.user_id == user_id, Task.status == "pending").limit(8).all()
    exams = db.query(Exam).filter(Exam.user_id == user_id).limit(4).all()
    sessions = db.query(StudySession).filter(StudySession.user_id == user_id, StudySession.status == "upcoming").limit(8).all()

    return {
        "pending_tasks": [{"subject": t.subject, "title": t.title, "due_date": t.due_date, "priority": t.priority} for t in tasks],
        "upcoming_exams": [{"subject": e.subject, "title": e.title, "date": e.exam_date, "time": e.exam_time} for e in exams],
        "scheduled_sessions": [{"subject": s.subject, "topic": s.title, "date": s.date, "time": f"{s.start_time}-{s.end_time}"} for s in sessions],
    }


# Standard AI Endpoints (Phase 2 preserved)
@router.post("/generate-plan", response_model=GeneratePlanResponse)
def generate_study_plan_endpoint(request: GeneratePlanRequest, db: Session = Depends(get_db)):
    context = _gather_user_context(db, settings.DEMO_USER_ID)
    return gemini_service.generate_study_plan(request, context_data=context)


@router.post("/ask", response_model=AskResponse)
def ask_assistant_endpoint(request: AskRequest, db: Session = Depends(get_db)):
    context = _gather_user_context(db, settings.DEMO_USER_ID)
    return gemini_service.ask_study_assistant(request, context_data=context)


@router.post("/optimize-schedule", response_model=OptimizeScheduleResponse)
def optimize_schedule_endpoint(request: OptimizeScheduleRequest, db: Session = Depends(get_db)):
    context = _gather_user_context(db, settings.DEMO_USER_ID)
    return gemini_service.optimize_schedule(request, context_data=context)


# Phase 3 Agent Enhancements: Explicit Workflow, Tool Execution, Safe Schedule Approval & Logging
@router.post("/agent/execute", response_model=AgentExecuteResponse)
def execute_agent_endpoint(request: AgentExecuteRequest, db: Session = Depends(get_db)):
    """Execute the multi-step agent workflow: Intake -> Context Query -> Tool Execution -> Verification."""
    return agent_service.execute_agent_workflow(db, settings.DEMO_USER_ID, request)


@router.post("/schedule/approve", response_model=ScheduleApprovalResponse)
def approve_schedule_endpoint(request: ScheduleApprovalRequest, db: Session = Depends(get_db)):
    """Approve proposed AI schedule modifications and persist non-conflicting sessions."""
    return agent_service.approve_schedule_proposal(db, settings.DEMO_USER_ID, request.sessions, log_id=request.log_id)


@router.post("/schedule/reject", response_model=ScheduleRejectResponse)
def reject_schedule_endpoint(request: ScheduleRejectRequest, db: Session = Depends(get_db)):
    """Explicitly reject proposed AI schedule modifications. Ensures 0 modifications to SQLite."""
    return agent_service.reject_schedule_proposal(db, settings.DEMO_USER_ID, log_id=request.log_id, reason=request.reason)


@router.get("/logs", response_model=List[AgentActivityLogResponse])
def get_agent_logs_endpoint(db: Session = Depends(get_db)):
    """Retrieve audit trail of recent AI Agent tool executions and safety decisions."""
    return agent_service.get_agent_activity_logs(db, settings.DEMO_USER_ID)
