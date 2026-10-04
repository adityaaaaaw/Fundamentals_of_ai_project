import sys
sys.path.insert(0, ".")
import time
import uuid
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.models.user import User
from app.models.task import Task
from app.models.session import StudySession
from app.models.exam import Exam
from app.models.agent_log import AgentActivityLog
from app.schemas.agent import AgentExecuteRequest
from app.services import agent_service
from app.core.config import settings

def run_live_verification():
    print("=" * 60)
    print("LIVE GEMINI AGENT WORKFLOW & LATENCY VERIFICATION")
    print(f"Configured Model: {settings.GEMINI_MODEL}")
    print("=" * 60)

    # 1. Setup isolated in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()

    user_id = settings.DEMO_USER_ID

    # Seed isolated student data
    user = User(id=user_id, name="Test Student", email="student@example.edu")
    task1 = Task(
        user_id=user_id,
        title="Minimax & Alpha-Beta Assignment",
        subject="Fundamentals of AI",
        due_date="2026-10-20",
        priority="high",
        status="pending"
    )
    exam1 = Exam(
        user_id=user_id,
        title="AI Midterm Examination",
        subject="Fundamentals of AI",
        exam_date="2026-10-25",
        exam_time="10:00 - 12:00"
    )
    missed_sess = StudySession(
        user_id=user_id,
        title="Heuristic Search Lecture Catchup",
        subject="Fundamentals of AI",
        date="2026-10-02",
        start_time="14:00",
        end_time="15:30",
        duration_minutes=90,
        status="missed"
    )
    db.add_all([user, task1, exam1, missed_sess])
    db.commit()

    results = []

    # -------------------------------------------------------------
    # 1. Academic Coaching
    # -------------------------------------------------------------
    print("\n[1/6] Testing Academic Coaching Workflow...")
    t0 = time.perf_counter()
    resp1 = agent_service.execute_agent_workflow(
        db, user_id,
        AgentExecuteRequest(prompt="Explain active recall and spaced repetition for studying complex algorithms.")
    )
    dur1 = time.perf_counter() - t0
    print(f"  -> Duration: {dur1:.2f}s")
    print(f"  -> Action Type: {resp1.action_type}, Tool: {resp1.tool_name}")
    print(f"  -> Explanation preview: {resp1.explanation[:100]}...")
    assert resp1.action_type == "academic_coaching"
    assert len(resp1.explanation) > 30
    results.append(("Academic Coaching", dur1, "PASS"))

    # -------------------------------------------------------------
    # 2. Progress Query with Real Coursework
    # -------------------------------------------------------------
    print("\n[2/6] Testing Progress Query with Real Coursework...")
    t0 = time.perf_counter()
    resp2 = agent_service.execute_agent_workflow(
        db, user_id,
        AgentExecuteRequest(prompt="How am I progressing with my coursework tasks and upcoming exams?")
    )
    dur2 = time.perf_counter() - t0
    print(f"  -> Duration: {dur2:.2f}s")
    print(f"  -> Action Type: {resp2.action_type}, Tool: {resp2.tool_name}")
    print(f"  -> Grounded Explanation: {resp2.explanation[:120]}...")
    assert resp2.tool_name == "query_study_progress_tool"
    assert resp2.requires_approval is False
    results.append(("Progress Query", dur2, "PASS"))

    # -------------------------------------------------------------
    # 3. Study Plan Generation with Real Coursework
    # -------------------------------------------------------------
    print("\n[3/6] Testing Study Plan Generation with Real Coursework...")
    t0 = time.perf_counter()
    resp3 = agent_service.execute_agent_workflow(
        db, user_id,
        AgentExecuteRequest(
            prompt="Generate a focused revision plan for my AI Midterm Examination",
            preferred_hours=3.0,
            target_date="2026-10-24"
        )
    )
    dur3 = time.perf_counter() - t0
    print(f"  -> Duration: {dur3:.2f}s")
    print(f"  -> Action Type: {resp3.action_type}, Tool: {resp3.tool_name}")
    print(f"  -> Proposed Sessions Count: {len(resp3.proposed_sessions)}")
    print(f"  -> Requires Approval: {resp3.requires_approval}")
    assert resp3.tool_name == "generate_study_plan_tool"
    assert resp3.requires_approval is True
    assert len(resp3.proposed_sessions) >= 1
    results.append(("Study Plan Generation", dur3, "PASS"))

    # -------------------------------------------------------------
    # 4. Reschedule Missed Study Sessions
    # -------------------------------------------------------------
    print("\n[4/6] Testing Reschedule Missed Study Sessions...")
    t0 = time.perf_counter()
    resp4 = agent_service.execute_agent_workflow(
        db, user_id,
        AgentExecuteRequest(prompt="Please reschedule my missed study session to catch up.")
    )
    dur4 = time.perf_counter() - t0
    print(f"  -> Duration: {dur4:.2f}s")
    print(f"  -> Action Type: {resp4.action_type}, Tool: {resp4.tool_name}")
    print(f"  -> Proposed Sessions Count: {len(resp4.proposed_sessions)}")
    print(f"  -> Requires Approval: {resp4.requires_approval}")
    assert resp4.tool_name == "reschedule_missed_sessions_tool"
    assert resp4.requires_approval is True
    assert len(resp4.proposed_sessions) >= 1
    results.append(("Reschedule Missed Sessions", dur4, "PASS"))

    # -------------------------------------------------------------
    # 5. Confirm Proposals Require Approval (Safety Check)
    # -------------------------------------------------------------
    print("\n[5/6] Verifying Schedule Proposals Require Approval...")
    assert resp3.requires_approval is True, "Study plan must require approval"
    assert resp4.requires_approval is True, "Rescheduling must require approval"
    # Verify no sessions were silently inserted into DB
    current_sessions_count = db.query(StudySession).filter(StudySession.user_id == user_id).count()
    assert current_sessions_count == 1, f"Expected exactly 1 initial session, found {current_sessions_count}"
    print(f"  -> Verified zero silent mutations: exactly 1 initial session in DB.")
    results.append(("Approval Enforcement", 0.0, "PASS"))

    # -------------------------------------------------------------
    # 6. Approve Valid Proposal & Verify Persistence
    # -------------------------------------------------------------
    print("\n[6/6] Approving Proposed Sessions & Verifying Persistence...")
    t0 = time.perf_counter()
    approval_resp = agent_service.approve_schedule_proposal(
        db=db,
        user_id=user_id,
        proposed_sessions=resp3.proposed_sessions
    )
    dur6 = time.perf_counter() - t0
    print(f"  -> Approval Duration: {dur6:.4f}s")
    print(f"  -> Saved Count: {approval_resp.saved_count}")
    assert approval_resp.approved is True
    assert approval_resp.saved_count == len(resp3.proposed_sessions)

    # Verify sessions in SQLite
    new_sessions_count = db.query(StudySession).filter(StudySession.user_id == user_id).count()
    assert new_sessions_count == 1 + approval_resp.saved_count
    print(f"  -> Verified SQLite persistence: total sessions in DB now = {new_sessions_count}")

    # Verify Activity Logs in SQLite
    logs = agent_service.get_agent_activity_logs(db, user_id)
    assert len(logs) >= 3
    print(f"  -> Verified persistent audit logs: {len(logs)} log entries recorded.")
    results.append(("Approval & Persistence", dur6, "PASS"))

    # -------------------------------------------------------------
    # Summary Table
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    print("LIVE VERIFICATION SUMMARY")
    print("=" * 60)
    for name, dur, status in results:
        print(f"  {name:<32} {dur:>6.2f}s   [{status}]")
    print("=" * 60)
    print("All 6 live workflows verified successfully with real Gemini API!")

if __name__ == "__main__":
    run_live_verification()
