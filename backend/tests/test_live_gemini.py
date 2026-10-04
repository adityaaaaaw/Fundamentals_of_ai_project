import pytest
from app.core.config import settings
from app.schemas.agent import AgentExecuteRequest
from app.services import agent_service
from app.models.task import Task
from app.models.session import StudySession
from app.models.exam import Exam

has_gemini_key = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip() and settings.GEMINI_API_KEY != "your_gemini_api_key")


@pytest.mark.skipif(not has_gemini_key, reason="Live GEMINI_API_KEY not configured in backend/.env")
def test_live_gemini_intent_and_tool_execution(db_session):
    """Integration test executing a live call to Google Gemini API with function calling."""
    # Seed test data
    task = Task(
        user_id=settings.DEMO_USER_ID,
        title="Live AI Lab",
        subject="Fundamentals of AI",
        due_date="2026-10-20",
        priority="high",
        status="pending"
    )
    exam = Exam(
        user_id=settings.DEMO_USER_ID,
        subject="Fundamentals of AI",
        title="Final Exam",
        exam_date="2026-10-30",
        exam_time="09:00",
    )
    db_session.add_all([task, exam])
    db_session.commit()

    # 1. Live Query Progress
    resp_progress = agent_service.execute_agent_workflow(
        db=db_session,
        user_id=settings.DEMO_USER_ID,
        request=AgentExecuteRequest(prompt="How am I doing on my coursework tasks?")
    )
    assert resp_progress.tool_name == "query_study_progress_tool"
    assert resp_progress.requires_approval is False

    # 2. Live Study Plan
    resp_plan = agent_service.execute_agent_workflow(
        db=db_session,
        user_id=settings.DEMO_USER_ID,
        request=AgentExecuteRequest(prompt="Generate a revision plan for Fundamentals of AI Final Exam")
    )
    assert resp_plan.tool_name == "generate_study_plan_tool"
    assert resp_plan.requires_approval is True
    assert len(resp_plan.proposed_sessions) >= 1
