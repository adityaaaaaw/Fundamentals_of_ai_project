from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.schemas.exam import ExamCreate, ExamUpdate, ExamResponse
from app.services import exam_service

router = APIRouter(prefix="/exams", tags=["Exams"])


@router.get("", response_model=List[ExamResponse])
def read_exams(db: Session = Depends(get_db)):
    return exam_service.get_exams(db=db, user_id=settings.DEMO_USER_ID)


@router.post("", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_new_exam(exam_in: ExamCreate, db: Session = Depends(get_db)):
    return exam_service.create_exam(db=db, exam_in=exam_in, user_id=settings.DEMO_USER_ID)


@router.get("/{exam_id}", response_model=ExamResponse)
def read_exam(exam_id: str, db: Session = Depends(get_db)):
    exam = exam_service.get_exam_by_id(db=db, exam_id=exam_id, user_id=settings.DEMO_USER_ID)
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    return exam


@router.put("/{exam_id}", response_model=ExamResponse)
def update_existing_exam(exam_id: str, exam_in: ExamUpdate, db: Session = Depends(get_db)):
    exam = exam_service.update_exam(db=db, exam_id=exam_id, exam_in=exam_in, user_id=settings.DEMO_USER_ID)
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    return exam


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_exam(exam_id: str, db: Session = Depends(get_db)):
    success = exam_service.delete_exam(db=db, exam_id=exam_id, user_id=settings.DEMO_USER_ID)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    return None
