import re
import logging
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from google.genai import types

from app.models.task import Task
from app.models.session import StudySession
from app.models.exam import Exam
from app.schemas.agent import ProposedSessionBlock, EventType
from app.services import dashboard_service
from app.utils.date_utils import (
    check_time_overlap,
    calculate_days_remaining,
    time_to_minutes,
    minutes_to_time_str,
    resolve_target_date,
    get_today_str,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic Schemas for Tool Argument Validation
# ---------------------------------------------------------------------------

class GeneratePlanArgs(BaseModel):
    goal: str = Field(..., description="Target academic goal or revision topic")
    subject: Optional[str] = Field(None, description="Course subject name (e.g. 'Fundamentals of AI')")
    target_date: Optional[str] = Field(None, description="Target date in YYYY-MM-DD format")
    available_hours: Optional[float] = Field(None, description="Available study hours")


class QueryProgressArgs(BaseModel):
    query_focus: Optional[str] = Field("general", description="Focus area (e.g. 'tasks', 'exams', 'streak', or 'general')")


class RescheduleMissedArgs(BaseModel):
    reason: Optional[str] = Field(None, description="Reason or context for rescheduling missed sessions")


class OptimizeScheduleArgs(BaseModel):
    target_date: Optional[str] = Field(None, description="Target date in YYYY-MM-DD format")
    available_hours: Optional[float] = Field(None, description="Requested study hours")
    sleep_hours: Optional[float] = Field(None, description="Requested sleep hours")
    meal_hours: Optional[float] = Field(None, description="Requested meal or break hours")
    exam_time: Optional[str] = Field(None, description="Exam time window, e.g. '14:00-16:00'")
    exam_subject: Optional[str] = Field(None, description="Exam subject if an exam is occurring")
    fixed_commitments: Optional[str] = Field(None, description="Fixed commitments such as job, classes, gym")
    preferences: Optional[str] = Field(None, description="Workload preferences or constraints")


class AcademicCoachingArgs(BaseModel):
    question: str = Field(..., description="Academic question or topic to coach on")
    topic: Optional[str] = Field(None, description="Specific course or topic")


# ---------------------------------------------------------------------------
# Time & Text Parsing Helpers
# ---------------------------------------------------------------------------

def parse_clock_time(time_str: str) -> str:
    """Parse string like '1pm', '2:30pm', '14:00', '10am' into 'HH:MM' (24-hour)."""
    t = time_str.strip().lower()
    m = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$", t)
    if not m:
        return "12:00"
    h = int(m.group(1))
    mins = int(m.group(2) or 0)
    meridiem = m.group(3)
    if meridiem == "pm" and h < 12:
        h += 12
    elif meridiem == "am" and h == 12:
        h = 0
    return f"{h:02d}:{mins:02d}"


def parse_schedule_constraints_from_text(prompt: str) -> Dict[str, Any]:
    """Extract student-specified constraints (sleep, work, meals, exam, study) from prompt."""
    text = prompt.lower()
    res: Dict[str, Any] = {}

    # Sleep hours
    m_sleep = (
        re.search(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\s*(?:of\s*)?sleep", text)
        or re.search(r"sleep\s*(?:for\s*)?(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)", text)
    )
    if m_sleep:
        res["sleep_hours"] = float(m_sleep.group(1))

    # Fixed job/work hours
    m_job = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\s*(?:at|for|in)?\s*(?:my\s*)?(?:job|work|class|office)",
        text,
    )
    if m_job:
        res["fixed_hours"] = float(m_job.group(1))
        res["fixed_title"] = "Work / Job Commitment"

    # Meals and gym
    m_meal = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\s*(?:for\s*)?(?:meals?|food|eating|lunch|dinner|gym)",
        text,
    )
    if m_meal:
        res["meal_hours"] = float(m_meal.group(1))

    # Specific lunch time
    m_lunch = re.search(r"lunch\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", text)
    if m_lunch:
        lunch_start = parse_clock_time(m_lunch.group(1))
        start_m = time_to_minutes(lunch_start)
        end_m = start_m + 60
        res["lunch_interval"] = (lunch_start, minutes_to_time_str(end_m))

    # Study hours
    m_study = (
        re.search(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\s*(?:of\s*)?study", text)
        or re.search(r"study\s*(?:for\s*)?(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)", text)
    )
    if m_study:
        res["study_hours"] = float(m_study.group(1))

    # Exam time and subject
    m_exam_time = re.search(
        r"exam\s+(?:tomorrow\s+)?(?:from\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:to|-)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
        text,
    )
    if m_exam_time:
        res["exam_start"] = parse_clock_time(m_exam_time.group(1))
        res["exam_end"] = parse_clock_time(m_exam_time.group(2))

    m_exam_subj = re.search(r"(?:have\s+(?:an?\s+)?)?([a-zA-Z0-9_-]+)\s+exam\b", text)
    if m_exam_subj:
        cand = m_exam_subj.group(1).strip()
        if cand.lower() not in ["an", "a", "have", "my", "the"]:
            res["exam_subject"] = cand.upper() if len(cand) <= 3 else cand.title()

    return res


# ---------------------------------------------------------------------------
# Central Constraint Validation Engine
# ---------------------------------------------------------------------------

def validate_schedule_constraints(
    blocks: List[ProposedSessionBlock],
    requested_commitments: Optional[Dict[str, float]] = None,
    db: Optional[Session] = None,
    user_id: Optional[str] = None,
    target_date: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    """
    Central schedule constraint validator:
    1. Checks daily commitments do not exceed 24 hours.
    2. Checks available waking hours after sleep.
    3. Detects overlapping sleep, meal, exam, study, and fixed events.
    4. Checks conflicts with existing study sessions and exams from SQLite.
    Returns (is_valid, list_of_error_messages).
    """
    errors: List[str] = []

    # 1. Total Daily Commitments Check (24-hour capacity limit)
    total_minutes = sum(b.duration_minutes for b in blocks)
    if total_minutes > 24 * 60:
        errors.append(
            f"Total daily commitments ({total_minutes / 60:.1f} hours) exceed the 24-hour limit of a day."
        )

    # If explicit commitments dict passed (e.g. before block construction)
    if requested_commitments:
        req_total = sum(requested_commitments.values())
        if req_total > 24.0:
            errors.append(
                f"Requested commitments total {req_total:.1f} hours, which exceeds the 24-hour daily boundary."
            )

    # 2. Available Waking Hours Check
    sleep_blocks = [b for b in blocks if b.event_type == "sleep"]
    sleep_minutes = sum(b.duration_minutes for b in sleep_blocks)
    waking_minutes = max(0, 24 * 60 - sleep_minutes)
    non_sleep_minutes = sum(b.duration_minutes for b in blocks if b.event_type != "sleep")

    if sleep_minutes > 0 and non_sleep_minutes > waking_minutes:
        errors.append(
            f"Non-sleep activities ({non_sleep_minutes / 60:.1f}h) exceed available waking hours "
            f"({waking_minutes / 60:.1f}h, based on {sleep_minutes / 60:.1f}h of sleep)."
        )

    # 3. Mutual Overlap Detection across all proposed blocks
    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            b1 = blocks[i]
            b2 = blocks[j]
            if b1.date == b2.date and check_time_overlap(b1.start_time, b1.end_time, b2.start_time, b2.end_time):
                errors.append(
                    f"Time conflict: '{b1.topic}' [{b1.event_type}] ({b1.start_time}-{b1.end_time}) "
                    f"overlaps with '{b2.topic}' [{b2.event_type}] ({b2.start_time}-{b2.end_time})."
                )

    # 4. Check conflicts with existing SQLite records (StudySessions & Exams)
    if db and user_id and target_date:
        existing_sessions = db.query(StudySession).filter(
            StudySession.user_id == user_id,
            StudySession.date == target_date,
            StudySession.status.in_(["upcoming", "planned", "completed"]),
        ).all()

        existing_exams = db.query(Exam).filter(
            Exam.user_id == user_id,
            Exam.exam_date == target_date,
        ).all()

        for b in blocks:
            for ex in existing_sessions:
                if check_time_overlap(b.start_time, b.end_time, ex.start_time, ex.end_time):
                    errors.append(
                        f"Slot {b.start_time}-{b.end_time} conflicts with existing study session '{ex.title}' on {target_date}."
                    )
            for exm in existing_exams:
                if exm.exam_time:
                    # Assume standard 2h duration for exam if only start time known
                    exm_start = exm.exam_time
                    exm_end = minutes_to_time_str(time_to_minutes(exm_start) + 120)
                    if check_time_overlap(b.start_time, b.end_time, exm_start, exm_end):
                        errors.append(
                            f"Slot {b.start_time}-{b.end_time} conflicts with existing exam '{exm.subject} - {exm.title}' ({exm_start}-{exm_end})."
                        )

    return (len(errors) == 0, errors)


# ---------------------------------------------------------------------------
# Slot Finding Helper
# ---------------------------------------------------------------------------

def find_available_time_slot(
    db: Session,
    user_id: str,
    target_date: str,
    duration_minutes: int = 90,
    blocked_intervals: Optional[List[Tuple[str, str]]] = None,
) -> Optional[Tuple[str, str]]:
    """Find a candidate non-overlapping time slot on a given date."""
    candidate_slots = [
        ("09:30", "11:00"),
        ("11:30", "13:00"),
        ("14:00", "15:30"),
        ("16:00", "17:30"),
        ("18:30", "20:00"),
    ]

    existing = db.query(StudySession).filter(
        StudySession.user_id == user_id,
        StudySession.date == target_date,
        StudySession.status.in_(["upcoming", "planned", "completed"]),
    ).all()

    existing_exams = db.query(Exam).filter(
        Exam.user_id == user_id,
        Exam.exam_date == target_date,
    ).all()

    for start_str, end_str in candidate_slots:
        has_overlap = False
        # Check against existing DB study sessions
        for ex in existing:
            if check_time_overlap(start_str, end_str, ex.start_time, ex.end_time):
                has_overlap = True
                break
        if has_overlap:
            continue

        # Check against existing DB exams
        for exm in existing_exams:
            if exm.exam_time:
                exm_end = minutes_to_time_str(time_to_minutes(exm.exam_time) + 120)
                if check_time_overlap(start_str, end_str, exm.exam_time, exm_end):
                    has_overlap = True
                    break
        if has_overlap:
            continue

        # Check against runtime blocked intervals (e.g. sleep, meals, exams)
        if blocked_intervals:
            for b_start, b_end in blocked_intervals:
                if check_time_overlap(start_str, end_str, b_start, b_end):
                    has_overlap = True
                    break

        if not has_overlap:
            return start_str, end_str

    return None


# ---------------------------------------------------------------------------
# Real Database Tool Implementations
# ---------------------------------------------------------------------------

def execute_generate_study_plan_tool(
    db: Session,
    user_id: str,
    raw_args: Dict[str, Any],
    prompt_context: Optional[str] = None,
) -> Dict[str, Any]:
    args = GeneratePlanArgs.model_validate(raw_args)
    target_d, target_wd = resolve_target_date(args.target_date, prompt_text=prompt_context)

    # Query real pending tasks
    query = db.query(Task).filter(Task.user_id == user_id, Task.status == "pending")
    if args.subject:
        query = query.filter(Task.subject.ilike(f"%{args.subject}%"))
    pending_tasks = query.order_by(Task.due_date.asc()).limit(3).all()

    # Query upcoming exams
    exams = db.query(Exam).filter(Exam.user_id == user_id).order_by(Exam.exam_date.asc()).limit(2).all()

    proposed_sessions: List[ProposedSessionBlock] = []
    assumptions: List[str] = []
    is_general = False

    if pending_tasks:
        for idx, task in enumerate(pending_tasks[:2]):
            slot_date, _ = resolve_target_date(
                (date.fromisoformat(target_d) + timedelta(days=idx)).isoformat()
            )
            slot = find_available_time_slot(db, user_id, slot_date, 90) or ("10:00", "11:30")
            proposed_sessions.append(
                ProposedSessionBlock(
                    subject=task.subject,
                    topic=f"Focused Study: {task.title}",
                    date=slot_date,
                    start_time=slot[0],
                    end_time=slot[1],
                    duration_minutes=90,
                    reason=f"Priority coursework revision due on {task.due_date}",
                    event_type="study",
                    status="upcoming",
                )
            )
        summary = f"Generated {len(proposed_sessions)} personalized study session(s) targeting: {args.goal}"
    else:
        subject_title = args.subject or (exams[0].subject if exams else None)
        if subject_title or args.goal:
            subject_to_use = subject_title or "Self-Directed Study"
            slot = find_available_time_slot(db, user_id, target_d, 90) or ("09:30", "11:00")
            proposed_sessions.append(
                ProposedSessionBlock(
                    subject=subject_to_use,
                    topic=f"Revision & Focus Block: {args.goal}",
                    date=target_d,
                    start_time=slot[0],
                    end_time=slot[1],
                    duration_minutes=90,
                    reason="Tailored focus block aligned with student goal and available timetable slots",
                    event_type="study",
                    status="upcoming",
                )
            )
            is_general = True
            assumptions.append(
                "No active coursework tasks found in planner; plan formulated for requested goal."
            )
            summary = f"Generated general study plan for: '{args.goal}' on {target_d} ({target_wd})."
        else:
            summary = (
                "No active coursework or exam milestones found in your planner. "
                "Please specify the subject or add your coursework tasks first so I can generate an accurate study plan."
            )
            return {
                "action_type": "generate_plan",
                "tool_name": "generate_study_plan_tool",
                "summary": summary,
                "requires_approval": False,
                "proposed_sessions": [],
                "target_date": target_d,
                "is_general_recommendation": True,
                "assumptions": ["No coursework tasks found in database."],
            }

    # Validate constraints
    is_valid, errors = validate_schedule_constraints(
        blocks=proposed_sessions, db=db, user_id=user_id, target_date=target_d
    )

    return {
        "action_type": "generate_plan",
        "tool_name": "generate_study_plan_tool",
        "summary": summary,
        "requires_approval": is_valid and len(proposed_sessions) > 0,
        "proposed_sessions": [s.model_dump() for s in proposed_sessions],
        "target_date": target_d,
        "is_general_recommendation": is_general,
        "assumptions": assumptions,
        "constraint_errors": errors,
    }


def execute_query_study_progress_tool(
    db: Session,
    user_id: str,
    raw_args: Dict[str, Any],
) -> Dict[str, Any]:
    args = QueryProgressArgs.model_validate(raw_args)
    summary_data = dashboard_service.get_dashboard_summary(db, user_id)
    exams = db.query(Exam).filter(Exam.user_id == user_id).order_by(Exam.exam_date.asc()).limit(3).all()

    summary_str = f"Academic Progress: {summary_data.completion_rate}% completion rate ({summary_data.completed_tasks}/{summary_data.total_tasks} tasks done)."

    return {
        "action_type": "query_progress",
        "tool_name": "query_study_progress_tool",
        "summary": summary_str,
        "requires_approval": False,
        "proposed_sessions": [],
        "completion_rate": summary_data.completion_rate,
        "total_tasks": summary_data.total_tasks,
        "completed_tasks": summary_data.completed_tasks,
        "pending_tasks": summary_data.pending_tasks,
        "missed_tasks": summary_data.missed_tasks,
        "current_streak_days": summary_data.current_streak_days,
        "completed_study_time_hours": round(summary_data.completed_study_time_minutes / 60, 1),
        "upcoming_exams": [
            {
                "subject": e.subject,
                "title": e.title,
                "date": e.exam_date,
                "days_remaining": calculate_days_remaining(e.exam_date),
            }
            for e in exams
        ],
        "focus_area": args.query_focus,
    }


def execute_reschedule_missed_sessions_tool(
    db: Session,
    user_id: str,
    raw_args: Dict[str, Any],
) -> Dict[str, Any]:
    args = RescheduleMissedArgs.model_validate(raw_args)
    missed = db.query(StudySession).filter(
        StudySession.user_id == user_id,
        StudySession.status == "missed",
    ).all()

    proposed_sessions: List[ProposedSessionBlock] = []

    if missed:
        tomorrow, _ = resolve_target_date("tomorrow")
        day_after, _ = resolve_target_date("day after tomorrow")

        for idx, ms in enumerate(missed[:3]):
            target_d = tomorrow if idx % 2 == 0 else day_after
            slot = find_available_time_slot(db, user_id, target_d, 90) or ("16:00", "17:30")
            proposed_sessions.append(
                ProposedSessionBlock(
                    subject=ms.subject,
                    topic=f"Makeup: {ms.title}",
                    date=target_d,
                    start_time=slot[0],
                    end_time=slot[1],
                    duration_minutes=90,
                    reason=f"Catching up on missed session from {ms.date} ({ms.title})",
                    event_type="study",
                    status="upcoming",
                )
            )

        summary = f"Identified {len(missed)} missed study session(s). Found {len(proposed_sessions)} non-conflicting makeup slot(s)."
        requires_approval = True
    else:
        summary = "No missed study sessions found in your timetable."
        requires_approval = False

    return {
        "action_type": "reschedule_missed",
        "tool_name": "reschedule_missed_sessions_tool",
        "summary": summary,
        "requires_approval": requires_approval,
        "proposed_sessions": [s.model_dump() for s in proposed_sessions],
        "missed_count": len(missed),
        "reason_context": args.reason,
    }


def execute_optimize_study_schedule_tool(
    db: Session,
    user_id: str,
    raw_args: Dict[str, Any],
    prompt_context: Optional[str] = None,
) -> Dict[str, Any]:
    args = OptimizeScheduleArgs.model_validate(raw_args)
    target_d, target_wd = resolve_target_date(args.target_date, prompt_text=prompt_context)

    # Parse natural language constraints from prompt if provided
    text_constraints = parse_schedule_constraints_from_text(prompt_context or "")
    if args.preferences:
        text_constraints.update(parse_schedule_constraints_from_text(args.preferences))

    # Resolve commitments
    sleep_h = args.sleep_hours or text_constraints.get("sleep_hours")
    study_h = args.available_hours or text_constraints.get("study_hours") or 3.5
    meal_h = args.meal_hours or text_constraints.get("meal_hours")
    job_h = text_constraints.get("fixed_hours", 0.0)

    exam_start = text_constraints.get("exam_start")
    exam_end = text_constraints.get("exam_end")
    exam_subject = text_constraints.get("exam_subject")

    if args.exam_time and "-" in args.exam_time:
        parts = args.exam_time.split("-")
        exam_start = parse_clock_time(parts[0])
        exam_end = parse_clock_time(parts[1])

    exam_h = 0.0
    if exam_start and exam_end:
        exam_h = max(0.0, (time_to_minutes(exam_end) - time_to_minutes(exam_start)) / 60.0)

    # 1. Check Capacity: Total Daily Commitments vs 24 Hours
    commitments_map = {}
    if sleep_h is not None:
        commitments_map["Sleep"] = sleep_h
    if job_h > 0:
        commitments_map["Work / Fixed Commitments"] = job_h
    if meal_h is not None:
        commitments_map["Meals & Breaks"] = meal_h
    elif text_constraints.get("lunch_interval"):
        commitments_map["Meals (Lunch)"] = 1.0
        meal_h = 1.0
    if exam_h > 0:
        commitments_map["Exam Time (Fixed)"] = exam_h
    commitments_map["Study Hours"] = study_h

    total_requested_hours = sum(commitments_map.values())

    if total_requested_hours > 24.0:
        breakdown_lines = "\n".join(f"- {name}: {h:.1f}h" for name, h in commitments_map.items())
        excess = total_requested_hours - 24.0
        max_possible_study = max(0.0, 24.0 - sum(h for k, h in commitments_map.items() if k != "Study Hours"))

        explanation = (
            f"Your requested daily commitments exceed the 24-hour limit of a day:\n"
            f"{breakdown_lines}\n"
            f"Total = {total_requested_hours:.1f}h (Exceeds 24 hours by {excess:.1f}h).\n\n"
            f"Feasible Alternatives:\n"
            f"1. Reduce planned study time from {study_h:.1f}h to {max_possible_study:.1f}h.\n"
            f"2. Adjust sleep ({sleep_h or 8.0:.1f}h) or reduce non-essential fixed commitments to free up study hours."
        )
        return {
            "action_type": "optimize_schedule",
            "tool_name": "optimize_study_schedule_tool",
            "summary": f"Schedule Infeasible: Requested commitments total {total_requested_hours:.1f} hours, exceeding the 24-hour daily boundary.",
            "explanation": explanation,
            "requires_approval": False,
            "proposed_sessions": [],
            "target_date": target_d,
            "is_general_recommendation": False,
            "assumptions": ["Commitment validation enforces hard 24-hour daily ceiling."],
            "constraint_errors": [
                f"Total commitments ({total_requested_hours:.1f}h) exceed 24.0 hours daily capacity by {excess:.1f}h."
            ],
        }

    # Query existing DB state
    pending_tasks = db.query(Task).filter(Task.user_id == user_id, Task.status == "pending").all()
    db_exams = db.query(Exam).filter(Exam.user_id == user_id, Exam.exam_date == target_d).all()

    proposed_blocks: List[ProposedSessionBlock] = []
    assumptions: List[str] = []
    is_general = False

    # -----------------------------------------------------------------------
    # Case A: Empty Database (tasks=0, exams=0) -> General Daily Blueprint
    # -----------------------------------------------------------------------
    if len(pending_tasks) == 0 and len(db_exams) == 0:
        is_general = True
        assumptions.append(
            "No saved coursework or exams found in database; schedule formulated exclusively from your prompt constraints."
        )

        # 1. Sleep Block (00:00 to 00:00 + sleep_h)
        eff_sleep_h = sleep_h if sleep_h is not None else 8.0
        sleep_mins = int(eff_sleep_h * 60)
        sleep_end = minutes_to_time_str(sleep_mins)
        proposed_blocks.append(
            ProposedSessionBlock(
                subject="Routine",
                topic="Restful Sleep Window",
                date=target_d,
                start_time="00:00",
                end_time=sleep_end,
                duration_minutes=sleep_mins,
                reason=f"Dedicated sleep block for cognitive restoration ({eff_sleep_h:.1f} hours)",
                event_type="sleep",
            )
        )
        if sleep_h is None:
            assumptions.append("Assumed standard 8.0 hours sleep window (00:00 - 08:00).")

        # 2. Lunch / Meal Block
        lunch_int = text_constraints.get("lunch_interval")
        if lunch_int:
            m_start, m_end = lunch_int
        else:
            m_start, m_end = "13:00", "14:00"
        m_mins = time_to_minutes(m_end) - time_to_minutes(m_start)
        proposed_blocks.append(
            ProposedSessionBlock(
                subject="Routine",
                topic="Nutritional Meal Break",
                date=target_d,
                start_time=m_start,
                end_time=m_end,
                duration_minutes=m_mins,
                reason="Scheduled meal break to sustain focus and energy",
                event_type="meal",
            )
        )

        # 3. Scheduled Exam (Separate event type - NOT study preparation)
        if exam_start and exam_end:
            ex_dur = time_to_minutes(exam_end) - time_to_minutes(exam_start)
            subj = exam_subject or "Coursework"
            proposed_blocks.append(
                ProposedSessionBlock(
                    subject=subj,
                    topic=f"{subj} Scheduled Examination",
                    date=target_d,
                    start_time=exam_start,
                    end_time=exam_end,
                    duration_minutes=ex_dur,
                    reason="Scheduled examination milestone (distinct from study preparation time)",
                    event_type="exam",
                )
            )
            assumptions.append(
                f"Exam time {exam_start}-{exam_end} treated as fixed event; study blocks placed outside this window."
            )

        # 4. Allocate Study Blocks outside sleep, meal, exam
        study_minutes_needed = int(study_h * 60)
        study_subject = exam_subject or "Self-Directed Study"

        # Candidate waking intervals avoiding sleep (ends at sleep_end), meal, exam
        candidate_study_windows = [
            ("09:30", "11:30", 120),
            ("16:30", "18:30", 120),
            ("19:00", "21:00", 120),
            ("11:30", "13:00", 90),
        ]

        study_allocated_mins = 0
        for cand_s, cand_e, cand_dur in candidate_study_windows:
            if study_allocated_mins >= study_minutes_needed:
                break
            # Check overlap with existing proposed blocks
            has_overlap = False
            for pb in proposed_blocks:
                if check_time_overlap(cand_s, cand_e, pb.start_time, pb.end_time):
                    has_overlap = True
                    break
            if not has_overlap:
                alloc_dur = min(cand_dur, study_minutes_needed - study_allocated_mins)
                alloc_end = minutes_to_time_str(time_to_minutes(cand_s) + alloc_dur)
                proposed_blocks.append(
                    ProposedSessionBlock(
                        subject=study_subject,
                        topic=f"Focused Study Interval ({study_subject})",
                        date=target_d,
                        start_time=cand_s,
                        end_time=alloc_end,
                        duration_minutes=alloc_dur,
                        reason="Dedicated study session scheduled in non-overlapping waking hours",
                        event_type="study",
                    )
                )
                study_allocated_mins += alloc_dur

        summary = (
            f"General daily schedule recommendation formulated for {target_d} ({target_wd}) with "
            f"{study_h:.1f}h study, {eff_sleep_h:.1f}h sleep, and {len(proposed_blocks)} distinct event blocks."
        )

    # -----------------------------------------------------------------------
    # Case B: Coursework Exists in SQLite
    # -----------------------------------------------------------------------
    else:
        urgent_task = pending_tasks[0] if pending_tasks else None
        subject_to_use = urgent_task.subject if urgent_task else "Coursework Study"
        topic_to_use = f"Optimized Review: {urgent_task.title}" if urgent_task else "Coursework Focus Session"
        reason_to_use = (
            f"Priority revision interval targeting deadline {urgent_task.due_date}"
            if urgent_task
            else "Balanced revision session"
        )

        slot = find_available_time_slot(db, user_id, target_d, 90) or ("14:00", "15:30")
        proposed_blocks.append(
            ProposedSessionBlock(
                subject=subject_to_use,
                topic=topic_to_use,
                date=target_d,
                start_time=slot[0],
                end_time=slot[1],
                duration_minutes=90,
                reason=reason_to_use,
                event_type="study",
                status="upcoming",
            )
        )
        summary = f"Optimized study block created for {target_d} ({target_wd}) targeting active coursework: {subject_to_use}."

    # Validate constraint non-overlap and capacity
    is_valid, errors = validate_schedule_constraints(
        blocks=proposed_blocks, db=db, user_id=user_id, target_date=target_d
    )

    return {
        "action_type": "optimize_schedule",
        "tool_name": "optimize_study_schedule_tool",
        "summary": summary,
        "requires_approval": is_valid and len(proposed_blocks) > 0,
        "proposed_sessions": [s.model_dump() for s in proposed_blocks],
        "target_date": target_d,
        "available_hours": study_h,
        "is_general_recommendation": is_general,
        "assumptions": assumptions,
        "constraint_errors": errors,
    }


def execute_academic_coaching_tool(
    db: Session,
    user_id: str,
    raw_args: Dict[str, Any],
) -> Dict[str, Any]:
    args = AcademicCoachingArgs.model_validate(raw_args)
    tasks = db.query(Task).filter(Task.user_id == user_id, Task.status == "pending").limit(3).all()
    exams = db.query(Exam).filter(Exam.user_id == user_id).limit(2).all()

    summary = f"Academic coaching generated for: '{args.question}'"
    return {
        "action_type": "academic_coaching",
        "tool_name": "academic_coaching_tool",
        "summary": summary,
        "requires_approval": False,
        "proposed_sessions": [],
        "question": args.question,
        "topic": args.topic,
        "related_subjects": list(set([t.subject for t in tasks] + [e.subject for e in exams])),
    }


# ---------------------------------------------------------------------------
# Tool Dispatcher
# ---------------------------------------------------------------------------

TOOL_DISPATCHER = {
    "generate_study_plan_tool": execute_generate_study_plan_tool,
    "query_study_progress_tool": execute_query_study_progress_tool,
    "reschedule_missed_sessions_tool": execute_reschedule_missed_sessions_tool,
    "optimize_study_schedule_tool": execute_optimize_study_schedule_tool,
    "academic_coaching_tool": execute_academic_coaching_tool,
}


def dispatch_tool(
    tool_name: str,
    raw_args: Dict[str, Any],
    db: Session,
    user_id: str,
    prompt_context: Optional[str] = None,
) -> Dict[str, Any]:
    handler = TOOL_DISPATCHER.get(tool_name)
    if not handler:
        raise ValueError(f"Unknown agent tool requested by model: '{tool_name}'")

    if tool_name in ["optimize_study_schedule_tool", "generate_study_plan_tool"]:
        return handler(db, user_id, raw_args, prompt_context=prompt_context)
    return handler(db, user_id, raw_args)


# ---------------------------------------------------------------------------
# Gemini SDK Tool Declarations (FunctionDeclarations)
# ---------------------------------------------------------------------------

def get_gemini_tools() -> List[types.Tool]:
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="generate_study_plan_tool",
                    description="Generate a personalized study plan using actual student coursework, exam dates, task priorities, and available study hours.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "goal": types.Schema(type="STRING", description="Target academic goal or revision topic"),
                            "subject": types.Schema(type="STRING", description="Course subject name (e.g. 'Fundamentals of AI')"),
                            "target_date": types.Schema(type="STRING", description="Target date in YYYY-MM-DD format"),
                            "available_hours": types.Schema(type="NUMBER", description="Available study hours"),
                        },
                        required=["goal"],
                    ),
                ),
                types.FunctionDeclaration(
                    name="query_study_progress_tool",
                    description="Retrieve actual progress from SQLite, including completed and pending tasks, study hours, study streak, and upcoming deadlines.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "query_focus": types.Schema(type="STRING", description="Focus area: 'tasks', 'exams', 'streak', or 'general'")
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="reschedule_missed_sessions_tool",
                    description="Retrieve missed study sessions from SQLite, find suitable non-conflicting available slots, and prepare a revised schedule proposal.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "reason": types.Schema(type="STRING", description="Context or reason for rescheduling")
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="optimize_study_schedule_tool",
                    description="Analyze constraints and commitments (sleep, meals, exams, study), enforce 24-hour limits and zero overlaps, and suggest an optimized schedule.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "target_date": types.Schema(type="STRING", description="Target date to optimize in YYYY-MM-DD format"),
                            "available_hours": types.Schema(type="NUMBER", description="Requested study hours"),
                            "sleep_hours": types.Schema(type="NUMBER", description="Requested sleep hours"),
                            "meal_hours": types.Schema(type="NUMBER", description="Requested meal/break hours"),
                            "exam_time": types.Schema(type="STRING", description="Scheduled exam time range, e.g. '14:00-16:00'"),
                            "exam_subject": types.Schema(type="STRING", description="Exam subject if an exam is occurring"),
                            "fixed_commitments": types.Schema(type="STRING", description="Fixed commitments such as job, classes, gym"),
                            "preferences": types.Schema(type="STRING", description="Workload preferences or guidelines"),
                        },
                    ),
                ),
                types.FunctionDeclaration(
                    name="academic_coaching_tool",
                    description="Provide academic advice and cognitive strategies grounded in the student's real coursework and progress.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "question": types.Schema(type="STRING", description="Academic question or topic to coach on"),
                            "topic": types.Schema(type="STRING", description="Specific course or topic"),
                        },
                        required=["question"],
                    ),
                ),
            ]
        )
    ]

