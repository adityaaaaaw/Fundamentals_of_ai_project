from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.session import StudySession
from app.schemas.session import SessionCreate, SessionUpdate, SessionStatusUpdate
from app.utils.date_utils import check_time_overlap, time_to_minutes, get_day_of_week
from app.services.user_service import ensure_user_exists


def check_session_conflict(
    db: Session,
    user_id: str,
    session_date: str,
    start_time: str,
    end_time: str,
    exclude_session_id: Optional[str] = None
) -> Optional[StudySession]:
    """
    Check if a session overlaps with an existing session for the user on that date.
    Adjacent sessions (e.g. 10:00-11:00 and 11:00-12:00) are permitted.
    """
    s_new = time_to_minutes(start_time)
    e_new = time_to_minutes(end_time)
    if s_new >= e_new:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session end time must be after start time."
        )

    query = db.query(StudySession).filter(
        StudySession.user_id == user_id,
        StudySession.date == session_date,
        StudySession.status.in_(["upcoming", "planned", "completed"])  # Missed/cancelled do not block
    )

    if exclude_session_id:
        query = query.filter(StudySession.id != exclude_session_id)

    existing_sessions = query.all()
    for existing in existing_sessions:
        if check_time_overlap(start_time, end_time, existing.start_time, existing.end_time):
            return existing

    return None


def get_sessions(
    db: Session,
    user_id: str,
    date: Optional[str] = None,
    day_of_week: Optional[str] = None,
    status: Optional[str] = None,
) -> List[StudySession]:
    query = db.query(StudySession).filter(StudySession.user_id == user_id)

    if date:
        query = query.filter(StudySession.date == date)
    if day_of_week and day_of_week != "All":
        query = query.filter(StudySession.day_of_week == day_of_week)
    if status and status != "all":
        query = query.filter(StudySession.status == status)

    return query.order_by(StudySession.date.asc(), StudySession.start_time.asc()).all()


def get_session_by_id(db: Session, session_id: str, user_id: str) -> Optional[StudySession]:
    return db.query(StudySession).filter(StudySession.id == session_id, StudySession.user_id == user_id).first()


def create_session(db: Session, session_in: SessionCreate, user_id: str) -> StudySession:
    # 1. Overlap validation
    conflicting = check_session_conflict(
        db,
        user_id,
        session_in.date,
        session_in.start_time,
        session_in.end_time
    )
    if conflicting:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Schedule conflict! Overlaps with '{conflicting.subject}' ({conflicting.start_time} - {conflicting.end_time})."
        )

    # 2. Compute duration and day of week if needed
    start_mins = time_to_minutes(session_in.start_time)
    end_mins = time_to_minutes(session_in.end_time)
    duration = end_mins - start_mins

    day_name = session_in.day_of_week
    if not day_name:
        try:
            day_name = get_day_of_week(session_in.date)
        except Exception:
            day_name = "Monday"

    session_data = session_in.model_dump(exclude={"topic"})
    session_data["duration_minutes"] = duration
    session_data["day_of_week"] = day_name

    ensure_user_exists(db, user_id)
    db_session = StudySession(**session_data, user_id=user_id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def update_session(db: Session, session_id: str, session_in: SessionUpdate, user_id: str) -> Optional[StudySession]:
    db_session = get_session_by_id(db, session_id, user_id)
    if not db_session:
        return None

    target_date = session_in.date or db_session.date
    target_start = session_in.start_time or db_session.start_time
    target_end = session_in.end_time or db_session.end_time

    # Validate overlap excluding self
    conflicting = check_session_conflict(
        db,
        user_id,
        target_date,
        target_start,
        target_end,
        exclude_session_id=session_id
    )
    if conflicting:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Schedule conflict! Overlaps with '{conflicting.subject}' ({conflicting.start_time} - {conflicting.end_time})."
        )

    update_data = session_in.model_dump(exclude_unset=True, exclude={"topic"})
    if "start_time" in update_data or "end_time" in update_data:
        update_data["duration_minutes"] = time_to_minutes(target_end) - time_to_minutes(target_start)

    if "date" in update_data and "day_of_week" not in update_data:
        try:
            update_data["day_of_week"] = get_day_of_week(update_data["date"])
        except Exception:
            pass

    for field, value in update_data.items():
        setattr(db_session, field, value)

    db.commit()
    db.refresh(db_session)
    return db_session


def update_session_status(db: Session, session_id: str, status_in: SessionStatusUpdate, user_id: str) -> Optional[StudySession]:
    db_session = get_session_by_id(db, session_id, user_id)
    if not db_session:
        return None

    db_session.status = status_in.status
    db.commit()
    db.refresh(db_session)
    return db_session


def delete_session(db: Session, session_id: str, user_id: str) -> bool:
    db_session = get_session_by_id(db, session_id, user_id)
    if not db_session:
        return False

    db.delete(db_session)
    db.commit()
    return True
