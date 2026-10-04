import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from app.utils.date_utils import (
    get_timezone,
    get_current_datetime,
    resolve_target_date,
    check_time_overlap,
)
from app.schemas.agent import ProposedSessionBlock
from app.services.agent_tools import (
    validate_schedule_constraints,
    parse_schedule_constraints_from_text,
    execute_optimize_study_schedule_tool,
)
from app.services.agent_service import approve_schedule_proposal, reject_schedule_proposal
from app.models.session import StudySession
from app.models.exam import Exam
from app.core.config import settings


# ---------------------------------------------------------------------------
# 1. Date Resolution & Leap/Month Boundary Tests
# ---------------------------------------------------------------------------

def test_resolve_target_date_relative_expressions():
    # Base date: Wednesday, 2026-10-07
    base = date(2026, 10, 7)

    today_iso, today_wd = resolve_target_date("today", base_date=base)
    assert today_iso == "2026-10-07"
    assert today_wd == "Wednesday"

    tom_iso, tom_wd = resolve_target_date("tomorrow", base_date=base)
    assert tom_iso == "2026-10-08"
    assert tom_wd == "Thursday"

    dat_iso, dat_wd = resolve_target_date("day after tomorrow", base_date=base)
    assert dat_iso == "2026-10-09"
    assert dat_wd == "Friday"

    # "this Friday" from Wednesday -> 2 days ahead (2026-10-09)
    fri_iso, fri_wd = resolve_target_date("this friday", base_date=base)
    assert fri_iso == "2026-10-09"
    assert fri_wd == "Friday"

    # "next Monday" from Wednesday -> next week's Monday (2026-10-19)
    next_mon_iso, next_mon_wd = resolve_target_date("next monday", base_date=base)
    assert next_mon_iso == "2026-10-19"
    assert next_mon_wd == "Monday"


def test_resolve_target_date_month_and_year_rollovers():
    # Month-end rollover: Oct 31 -> Nov 01
    oct_end = date(2026, 10, 31)
    res_iso, res_wd = resolve_target_date("tomorrow", base_date=oct_end)
    assert res_iso == "2026-11-01"
    assert res_wd == "Sunday"

    # Year-end rollover: Dec 31 -> Jan 01
    dec_end = date(2026, 12, 31)
    res_iso, res_wd = resolve_target_date("tomorrow", base_date=dec_end)
    assert res_iso == "2027-01-01"
    assert res_wd == "Friday"


def test_resolve_target_date_leap_year_handling():
    # Leap year (2024): Feb 28 + 1 day -> Feb 29
    leap_base = date(2024, 2, 28)
    res_iso, res_wd = resolve_target_date("tomorrow", base_date=leap_base)
    assert res_iso == "2024-02-29"
    assert res_wd == "Thursday"

    # Non-leap year (2023): Feb 28 + 1 day -> Mar 01
    non_leap = date(2023, 2, 28)
    res_iso, res_wd = resolve_target_date("tomorrow", base_date=non_leap)
    assert res_iso == "2023-03-01"
    assert res_wd == "Wednesday"


def test_timezone_resolution_and_safe_fallback():
    # Valid IANA timezone
    tz = get_timezone("Asia/Kolkata")
    assert tz is not None

    # Invalid timezone must fall back safely without raising an exception
    fallback_tz = get_timezone("Invalid/Fictional_Zone")
    assert fallback_tz is not None

    # None falls back to local/UTC
    none_tz = get_timezone(None)
    assert none_tz is not None

    # Runtime timestamp retrieval
    now_dt = get_current_datetime("Asia/Kolkata")
    assert now_dt.year >= 2026


# ---------------------------------------------------------------------------
# 2. Scheduling Capacity and Constraint Validation Tests
# ---------------------------------------------------------------------------

def test_daily_24_hour_capacity_infeasible_detected():
    # 10h sleep + 8h job + 4h meals/gym + 6h study = 28 hours (> 24 hours)
    commitments = {
        "Sleep": 10.0,
        "Job": 8.0,
        "Meals & Gym": 4.0,
        "Study": 6.0,
    }
    is_valid, errors = validate_schedule_constraints(
        blocks=[],
        requested_commitments=commitments
    )
    assert is_valid is False
    assert any("24-hour" in err for err in errors)


def test_optimize_tool_returns_infeasible_explanation_with_alternatives(db_session):
    # Prompt requiring 28 hours
    raw_args = {
        "available_hours": 6.0,
        "preferences": "10 hours sleep, 8 hours at my job, 4 hours for meals and gym, and 6 hours of study",
        "target_date": "2026-10-08",
    }
    res = execute_optimize_study_schedule_tool(
        db=db_session,
        user_id="test_user",
        raw_args=raw_args,
        prompt_context="Plan my day tomorrow with 10 hours sleep, 8 hours at my job, 4 hours for meals and gym, and 6 hours of study."
    )
    assert res["requires_approval"] is False
    assert len(res["proposed_sessions"]) == 0
    assert "Infeasible" in res["summary"]
    assert "Feasible Alternatives" in res["explanation"]
    assert len(res["constraint_errors"]) > 0


def test_overlap_detection_across_different_event_types():
    target_d = "2026-10-08"
    # Sleep block overlaps with morning study block
    sleep_block = ProposedSessionBlock(
        subject="Routine",
        topic="Sleep",
        date=target_d,
        start_time="00:00",
        end_time="08:00",
        duration_minutes=480,
        reason="Sleep",
        event_type="sleep"
    )
    overlapping_study = ProposedSessionBlock(
        subject="AI",
        topic="Morning Cram",
        date=target_d,
        start_time="07:30",
        end_time="09:00",
        duration_minutes=90,
        reason="Study",
        event_type="study"
    )
    is_valid, errors = validate_schedule_constraints([sleep_block, overlapping_study])
    assert is_valid is False
    assert any("conflict" in err.lower() or "overlap" in err.lower() for err in errors)


def test_existing_database_study_and_exam_conflicts(db_session):
    target_d = "2026-10-08"
    user_id = settings.DEMO_USER_ID

    # Seed existing study session: 10:00 - 11:30
    sess = StudySession(
        user_id=user_id,
        subject="Math",
        title="Calculus Session",
        date=target_d,
        day_of_week="Thursday",
        start_time="10:00",
        end_time="11:30",
        duration_minutes=90,
        status="upcoming"
    )
    db_session.add(sess)

    # Seed existing exam: 14:00 - 16:00
    exam = Exam(
        user_id=user_id,
        subject="Physics",
        title="Physics Midterm",
        exam_date=target_d,
        exam_time="14:00"
    )
    db_session.add(exam)
    db_session.commit()

    # Propose session conflicting with study session (11:00 - 12:30)
    conflict_block1 = ProposedSessionBlock(
        subject="AI",
        topic="AI Session",
        date=target_d,
        start_time="11:00",
        end_time="12:30",
        duration_minutes=90,
        reason="AI Study",
        event_type="study"
    )
    is_valid, errors = validate_schedule_constraints(
        blocks=[conflict_block1], db=db_session, user_id=user_id, target_date=target_d
    )
    assert is_valid is False
    assert any("Calculus Session" in err for err in errors)

    # Propose session conflicting with exam (14:30 - 15:30)
    conflict_block2 = ProposedSessionBlock(
        subject="AI",
        topic="AI Prep",
        date=target_d,
        start_time="14:30",
        end_time="15:30",
        duration_minutes=60,
        reason="AI Prep",
        event_type="study"
    )
    is_valid, errors = validate_schedule_constraints(
        blocks=[conflict_block2], db=db_session, user_id=user_id, target_date=target_d
    )
    assert is_valid is False
    assert any("Physics Midterm" in err for err in errors)


# ---------------------------------------------------------------------------
# 3. Empty Database & General Schedule Recommendation Tests
# ---------------------------------------------------------------------------

def test_empty_database_general_schedule_recommendation(db_session):
    user_id = "clean_student_id"
    prompt = "I want to study 4 hours, sleep 8 hours, have lunch at 1pm, and have an AI exam tomorrow from 2pm to 4pm."

    res = execute_optimize_study_schedule_tool(
        db=db_session,
        user_id=user_id,
        raw_args={"target_date": "2026-10-08"},
        prompt_context=prompt
    )

    assert res["is_general_recommendation"] is True
    assert res["requires_approval"] is True
    assert len(res["proposed_sessions"]) >= 4

    blocks = [ProposedSessionBlock.model_validate(b) for b in res["proposed_sessions"]]

    # Verify event types present
    event_types = [b.event_type for b in blocks]
    assert "sleep" in event_types
    assert "meal" in event_types
    assert "exam" in event_types
    assert "study" in event_types

    # Verify exam duration is NOT counted as study preparation
    exam_block = next(b for b in blocks if b.event_type == "exam")
    assert exam_block.start_time == "14:00"
    assert exam_block.end_time == "16:00"
    assert exam_block.subject == "AI"

    # Verify zero overlaps among all generated blocks
    is_valid, errors = validate_schedule_constraints(blocks)
    assert is_valid is True
    assert len(errors) == 0


def test_approval_persists_only_study_sessions_not_routine(db_session):
    user_id = "persistence_test_student"
    target_d = "2026-10-09"

    blocks = [
        ProposedSessionBlock(
            subject="Routine",
            topic="Sleep Window",
            date=target_d,
            start_time="00:00",
            end_time="08:00",
            duration_minutes=480,
            reason="Night sleep",
            event_type="sleep"
        ),
        ProposedSessionBlock(
            subject="Routine",
            topic="Lunch",
            date=target_d,
            start_time="13:00",
            end_time="14:00",
            duration_minutes=60,
            reason="Meal",
            event_type="meal"
        ),
        ProposedSessionBlock(
            subject="Fundamentals of AI",
            topic="Neural Networks Revision",
            date=target_d,
            start_time="09:30",
            end_time="11:30",
            duration_minutes=120,
            reason="Course study",
            event_type="study"
        ),
    ]

    res = approve_schedule_proposal(
        db=db_session,
        user_id=user_id,
        proposed_sessions=blocks
    )

    assert res.approved is True
    assert res.saved_count == 1  # ONLY the 1 study session was persisted!

    # Verify in SQLite database
    saved_sessions = db_session.query(StudySession).filter(
        StudySession.user_id == user_id,
        StudySession.date == target_d
    ).all()

    assert len(saved_sessions) == 1
    assert saved_sessions[0].subject == "Fundamentals of AI"
    assert saved_sessions[0].title == "Neural Networks Revision"

    # Ensure Sleep and Lunch were NOT inserted into StudySession table
    assert not any(s.subject == "Routine" for s in saved_sessions)


def test_rejection_leaves_database_completely_unmodified(db_session):
    user_id = "rejection_test_student"
    res = reject_schedule_proposal(
        db=db_session,
        user_id=user_id,
        reason="Not suitable"
    )
    assert res.approved is False
    assert "rejected" in res.message.lower()

    count = db_session.query(StudySession).filter(StudySession.user_id == user_id).count()
    assert count == 0
