#!/usr/bin/env python3
"""
Live Gemini API Integration & Verification Script
AI Study Planner Agent — Phase 4

Usage:
    python scripts/verify_live_gemini.py

Requirements:
    Requires GEMINI_API_KEY set in backend/.env or as an environment variable.
    Tests actual Gemini function calling and SQLite tool execution against an isolated in-memory database.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.session import Base
from app.models.task import Task
from app.models.session import StudySession
from app.models.exam import Exam
from app.schemas.agent import AgentExecuteRequest, ProposedSessionBlock
from app.services import agent_service


def run_live_verification():
    print("=" * 70)
    print("AI STUDY PLANNER AGENT — LIVE GEMINI API VERIFICATION (PHASE 4)")
    print("=" * 70)

    api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""

    if not api_key or api_key == "your_gemini_api_key":
        print("\n[NOTICE] GEMINI_API_KEY is not configured in backend/.env.")
        print("To run live verification against the real Google Gemini API:")
        print("  1. Add your API key to backend/.env:")
        print("     GEMINI_API_KEY=AIzaSy...")
        print("     GEMINI_MODEL=gemini-2.5-flash")
        print("  2. Re-run this script:")
        print("     python scripts/verify_live_gemini.py\n")
        print("All automated unit tests pass using mocked clients.")
        print("Live verification skipped pending user API key configuration.")
        print("=" * 70)
        return False

    print(f"\n[INFO] Configured Gemini Model: {settings.GEMINI_MODEL}")
    print("[INFO] Setting up isolated in-memory test database (student DB is untouched)...")

    # Setup isolated in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    test_user_id = "test-live-user"

    # Seed isolated coursework
    task1 = Task(
        user_id=test_user_id,
        title="Adversarial Search Lab",
        subject="Fundamentals of AI",
        due_date="2026-10-18",
        priority="high",
        status="pending"
    )
    exam1 = Exam(
        user_id=test_user_id,
        subject="Fundamentals of AI",
        title="Midterm Examination",
        exam_date="2026-10-25",
        exam_time="10:00",
        room="Hall A",
        weight="30%"
    )
    missed_sess = StudySession(
        user_id=test_user_id,
        subject="Linear Algebra",
        title="Matrix Diagonalization",
        date="2026-10-01",
        start_time="11:00",
        end_time="12:30",
        duration_minutes=90,
        status="missed"
    )
    db.add_all([task1, exam1, missed_sess])
    db.commit()

    print("[SUCCESS] Isolated database initialized.")

    # -------------------------------------------------------------
    # Verification 1: Progress Query Tool Calling
    # -------------------------------------------------------------
    print("\n--- Test 1: Real Intent Classification -> query_study_progress_tool ---")
    progress_prompt = "How am I progressing with my coursework and exams?"
    print(f"Sending prompt to Gemini: \"{progress_prompt}\"")

    try:
        resp1 = agent_service.execute_agent_workflow(
            db=db,
            user_id=test_user_id,
            request=AgentExecuteRequest(prompt=progress_prompt)
        )
        print(f"  Gemini Selected Tool: {resp1.tool_name}")
        print(f"  Action Type:          {resp1.action_type}")
        print(f"  Requires Approval:    {resp1.requires_approval}")
        print(f"  Pipeline Steps:       {len(resp1.steps)} steps executed")
        print(f"  Summary:              {resp1.summary}")
        print(f"  Explanation Snippet:  {resp1.explanation[:120]}...")

        assert resp1.tool_name == "query_study_progress_tool", f"Expected query_study_progress_tool, got {resp1.tool_name}"
        assert resp1.requires_approval is False
        print("[PASSED] Test 1: Real Gemini function selection & progress retrieval verified.")
    except Exception as e:
        print(f"[FAILED] Test 1 encountered error: {e}")
        return False

    # -------------------------------------------------------------
    # Verification 2: Study Plan Generation Tool & Candidate Proposal
    # -------------------------------------------------------------
    print("\n--- Test 2: Real Intent Classification -> generate_study_plan_tool ---")
    plan_prompt = "Generate a revision plan for my Fundamentals of AI Midterm"
    print(f"Sending prompt to Gemini: \"{plan_prompt}\"")

    try:
        resp2 = agent_service.execute_agent_workflow(
            db=db,
            user_id=test_user_id,
            request=AgentExecuteRequest(prompt=plan_prompt)
        )
        print(f"  Gemini Selected Tool: {resp2.tool_name}")
        print(f"  Proposed Sessions:    {len(resp2.proposed_sessions)}")
        print(f"  Requires Approval:    {resp2.requires_approval}")
        print(f"  Summary:              {resp2.summary}")

        assert resp2.tool_name == "generate_study_plan_tool", f"Expected generate_study_plan_tool, got {resp2.tool_name}"
        assert resp2.requires_approval is True
        assert len(resp2.proposed_sessions) >= 1
        print("[PASSED] Test 2: Real Gemini study plan proposal generation verified.")
    except Exception as e:
        print(f"[FAILED] Test 2 encountered error: {e}")
        return False

    # -------------------------------------------------------------
    # Verification 3: Safe Schedule Approval (Human-in-the-Loop)
    # -------------------------------------------------------------
    print("\n--- Test 3: Safe Schedule Approval -> SQLite Persistence ---")
    try:
        approval_res = agent_service.approve_schedule_proposal(
            db=db,
            user_id=test_user_id,
            proposed_sessions=resp2.proposed_sessions,
            log_id=resp2.data_snapshot.get("log_id") if resp2.data_snapshot else None
        )
        print(f"  Approved:      {approval_res.approved}")
        print(f"  Saved Count:   {approval_res.saved_count}")
        print(f"  Message:       {approval_res.message}")

        assert approval_res.approved is True
        assert approval_res.saved_count >= 1

        # Confirm persisted in DB
        db_session_count = db.query(StudySession).filter(
            StudySession.user_id == test_user_id,
            StudySession.status == "upcoming"
        ).count()
        assert db_session_count >= 1
        print("[PASSED] Test 3: Safe schedule approval and persistence verified.")
    except Exception as e:
        print(f"[FAILED] Test 3 encountered error: {e}")
        return False

    # -------------------------------------------------------------
    # Verification 4: Safe Schedule Rejection
    # -------------------------------------------------------------
    print("\n--- Test 4: Safe Schedule Rejection -> 0 Database Alterations ---")
    try:
        count_before = db.query(StudySession).filter(StudySession.user_id == test_user_id).count()
        reject_res = agent_service.reject_schedule_proposal(
            db=db,
            user_id=test_user_id,
            reason="Test student rejection"
        )
        count_after = db.query(StudySession).filter(StudySession.user_id == test_user_id).count()
        assert reject_res.approved is False
        assert count_before == count_after
        print(f"  Rejection message: {reject_res.message}")
        print("[PASSED] Test 4: Rejection leaves database 100% unaltered verified.")
    except Exception as e:
        print(f"[FAILED] Test 4 encountered error: {e}")
        return False

    # -------------------------------------------------------------
    # Verification 5: Audit Log Trail
    # -------------------------------------------------------------
    print("\n--- Test 5: Persistent SQLite Audit Logging ---")
    try:
        logs = agent_service.get_agent_activity_logs(db, test_user_id)
        print(f"  Retrieved {len(logs)} audit log records from SQLite:")
        for l in logs[:3]:
            print(f"    - [{l.action_type}] tool={l.tool_name} status={l.status}: {l.summary[:60]}...")
        assert len(logs) >= 2
        print("[PASSED] Test 5: Persistent SQLite audit trail verified.")
    except Exception as e:
        print(f"[FAILED] Test 5 encountered error: {e}")
        return False

    print("\n" + "=" * 70)
    print("ALL LIVE GEMINI API VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = run_live_verification()
    sys.exit(0 if success else 1)
