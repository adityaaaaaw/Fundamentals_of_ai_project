from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.exam import Exam
from app.schemas.exam import ExamCreate, ExamUpdate
from app.services.user_service import ensure_user_exists


def get_exams(db: Session, user_id: str) -> List[Exam]:
    return db.query(Exam).filter(Exam.user_id == user_id).order_by(Exam.exam_date.asc()).all()


def get_exam_by_id(db: Session, exam_id: str, user_id: str) -> Optional[Exam]:
    return db.query(Exam).filter(Exam.id == exam_id, Exam.user_id == user_id).first()


def create_exam(db: Session, exam_in: ExamCreate, user_id: str) -> Exam:
    ensure_user_exists(db, user_id)
    exam_data = exam_in.model_dump(exclude={"date", "time"})
    db_exam = Exam(**exam_data, user_id=user_id)
    db.add(db_exam)
    db.commit()
    db.refresh(db_exam)
    return db_exam


def update_exam(db: Session, exam_id: str, exam_in: ExamUpdate, user_id: str) -> Optional[Exam]:
    db_exam = get_exam_by_id(db, exam_id, user_id)
    if not db_exam:
        return None

    update_data = exam_in.model_dump(exclude_unset=True, exclude={"date", "time"})
    for field, value in update_data.items():
        setattr(db_exam, field, value)

    db.commit()
    db.refresh(db_exam)
    return db_exam


def delete_exam(db: Session, exam_id: str, user_id: str) -> bool:
    db_exam = get_exam_by_id(db, exam_id, user_id)
    if not db_exam:
        return False

    db.delete(db_exam)
    db.commit()
    return True
