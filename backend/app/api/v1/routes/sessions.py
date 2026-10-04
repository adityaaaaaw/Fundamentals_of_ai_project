from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.schemas.session import SessionCreate, SessionUpdate, SessionStatusUpdate, SessionResponse
from app.services import session_service

router = APIRouter(prefix="/sessions", tags=["Study Sessions"])


@router.get("", response_model=List[SessionResponse])
def read_sessions(
    date: Optional[str] = Query(None, description="Filter by YYYY-MM-DD"),
    day_of_week: Optional[str] = Query(None, description="Filter by day of week (e.g. Monday)"),
    status: Optional[str] = Query(None, description="Filter by status: upcoming, completed, missed"),
    db: Session = Depends(get_db),
):
    return session_service.get_sessions(
        db=db,
        user_id=settings.DEMO_USER_ID,
        date=date,
        day_of_week=day_of_week,
        status=status,
    )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_new_session(session_in: SessionCreate, db: Session = Depends(get_db)):
    return session_service.create_session(db=db, session_in=session_in, user_id=settings.DEMO_USER_ID)


@router.get("/{session_id}", response_model=SessionResponse)
def read_session(session_id: str, db: Session = Depends(get_db)):
    session = session_service.get_session_by_id(db=db, session_id=session_id, user_id=settings.DEMO_USER_ID)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.put("/{session_id}", response_model=SessionResponse)
def update_existing_session(session_id: str, session_in: SessionUpdate, db: Session = Depends(get_db)):
    session = session_service.update_session(
        db=db,
        session_id=session_id,
        session_in=session_in,
        user_id=settings.DEMO_USER_ID
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.patch("/{session_id}/status", response_model=SessionResponse)
def patch_session_status(session_id: str, status_in: SessionStatusUpdate, db: Session = Depends(get_db)):
    session = session_service.update_session_status(
        db=db,
        session_id=session_id,
        status_in=status_in,
        user_id=settings.DEMO_USER_ID
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_session(session_id: str, db: Session = Depends(get_db)):
    success = session_service.delete_session(db=db, session_id=session_id, user_id=settings.DEMO_USER_ID)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return None
