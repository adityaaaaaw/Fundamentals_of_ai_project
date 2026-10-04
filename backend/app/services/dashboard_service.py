from datetime import date, timedelta
from typing import List
from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.session import StudySession
from app.models.exam import Exam
from app.schemas.dashboard import DashboardSummary, DayStudyMetric, WeeklyProgressResponse
from app.schemas.session import SessionResponse
from app.schemas.exam import ExamResponse
from app.schemas.task import TaskResponse
from app.utils.date_utils import get_today_str


def get_dashboard_summary(db: Session, user_id: str) -> DashboardSummary:
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    sessions = db.query(StudySession).filter(StudySession.user_id == user_id).all()

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.status == "completed")
    pending_tasks = sum(1 for t in tasks if t.status == "pending")
    missed_tasks = sum(1 for t in tasks if t.status == "missed")
    in_progress_tasks = sum(1 for t in tasks if t.status == "in_progress")

    completion_rate = int(round((completed_tasks / total_tasks) * 100)) if total_tasks > 0 else 0

    planned_minutes = sum(s.duration_minutes for s in sessions if s.status in ["upcoming", "planned"])
    completed_minutes = sum(s.duration_minutes for s in sessions if s.status == "completed")

    # Simple streak calculation: Count consecutive days ending today/yesterday with completed activity
    today = date.today()
    streak = 0
    for i in range(14):
        check_date = (today - timedelta(days=i)).isoformat()
        has_completed_session = db.query(StudySession).filter(
            StudySession.user_id == user_id,
            StudySession.date == check_date,
            StudySession.status == "completed"
        ).first() is not None
        if has_completed_session:
            streak += 1
        elif i == 0:
            # Maybe today hasn't finished yet, continue checking yesterday
            continue
        else:
            break

    return DashboardSummary(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        missed_tasks=missed_tasks,
        in_progress_tasks=in_progress_tasks,
        completion_rate=completion_rate,
        planned_study_time_minutes=planned_minutes,
        completed_study_time_minutes=completed_minutes,
        current_streak_days=streak,
    )


def get_weekly_progress(db: Session, user_id: str) -> WeeklyProgressResponse:
    # Compute the current week's Monday through Sunday
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday

    day_names = [
        ("Mon", "Monday"),
        ("Tue", "Tuesday"),
        ("Wed", "Wednesday"),
        ("Thu", "Thursday"),
        ("Fri", "Friday"),
        ("Sat", "Saturday"),
        ("Sun", "Sunday"),
    ]

    target_hours_map = {
        "Monday": 4.0,
        "Tuesday": 3.5,
        "Wednesday": 4.0,
        "Thursday": 3.5,
        "Friday": 4.0,
        "Saturday": 4.5,
        "Sunday": 3.0,
    }

    metrics: List[DayStudyMetric] = []
    total_studied = 0.0
    total_target = 0.0

    for idx, (short_name, full_name) in enumerate(day_names):
        curr_date = start_of_week + timedelta(days=idx)
        curr_date_str = curr_date.isoformat()

        # Sum studied hours for completed sessions on this date or matching day_of_week
        sessions = db.query(StudySession).filter(
            StudySession.user_id == user_id,
            StudySession.date == curr_date_str,
            StudySession.status == "completed"
        ).all()

        studied_minutes = sum(s.duration_minutes for s in sessions)
        studied_hours = round(studied_minutes / 60.0, 1)

        target_h = target_hours_map[full_name]

        metrics.append(
            DayStudyMetric(
                day=short_name,
                fullDay=full_name,
                studiedHours=studied_hours,
                targetHours=target_h,
            )
        )
        total_studied += studied_hours
        total_target += target_h

    # Calculate real streak
    real_streak = 0
    for i in range(14):
        check_date = (today - timedelta(days=i)).isoformat()
        has_completed = db.query(StudySession).filter(
            StudySession.user_id == user_id,
            StudySession.date == check_date,
            StudySession.status == "completed"
        ).first() is not None
        if has_completed:
            real_streak += 1
        elif i == 0:
            continue
        else:
            break

    return WeeklyProgressResponse(
        metrics=metrics,
        total_studied_hours=round(total_studied, 1),
        total_target_hours=round(total_target, 1),
        current_streak_days=real_streak,
    )


def get_today_sessions(db: Session, user_id: str) -> List[StudySession]:
    today_str = get_today_str()
    # Check sessions for today's date
    sessions = db.query(StudySession).filter(
        StudySession.user_id == user_id,
        StudySession.date == today_str
    ).order_by(StudySession.start_time.asc()).all()

    # If no sessions on today's exact calendar date, also include sessions marked for current weekday name
    if not sessions:
        weekday_name = date.today().strftime("%A")
        sessions = db.query(StudySession).filter(
            StudySession.user_id == user_id,
            StudySession.day_of_week == weekday_name
        ).order_by(StudySession.start_time.asc()).all()

    return sessions


def get_upcoming_exams(db: Session, user_id: str) -> List[Exam]:
    today_str = get_today_str()
    # Return upcoming exams sorted by date
    exams = db.query(Exam).filter(
        Exam.user_id == user_id,
        Exam.exam_date >= today_str
    ).order_by(Exam.exam_date.asc()).all()

    # If all exams are past, return all exams so user sees their coursework
    if not exams:
        exams = db.query(Exam).filter(Exam.user_id == user_id).order_by(Exam.exam_date.asc()).all()

    return exams


def get_high_priority_tasks(db: Session, user_id: str, limit: int = 5) -> List[Task]:
    return db.query(Task).filter(
        Task.user_id == user_id,
        Task.status == "pending"
    ).order_by(
        # High priority first, then due date
        Task.priority.desc(),
        Task.due_date.asc()
    ).limit(limit).all()
