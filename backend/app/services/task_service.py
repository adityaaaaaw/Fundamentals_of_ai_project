from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate
from app.services.user_service import ensure_user_exists


def get_tasks(
    db: Session,
    user_id: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    subject: Optional[str] = None,
    due_date: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Task]:
    query = db.query(Task).filter(Task.user_id == user_id)

    if status and status != "all":
        query = query.filter(Task.status == status)
    if priority and priority != "all":
        query = query.filter(Task.priority == priority)
    if subject and subject != "all":
        query = query.filter(Task.subject == subject)
    if due_date:
        query = query.filter(Task.due_date == due_date)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Task.title.ilike(pattern),
                Task.subject.ilike(pattern),
                Task.description.ilike(pattern),
            )
        )

    # Sort: pending first, then by due_date ascending
    return query.order_by(Task.due_date.asc(), Task.created_at.desc()).offset(skip).limit(limit).all()


def get_task_by_id(db: Session, task_id: str, user_id: str) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()


def create_task(db: Session, task_in: TaskCreate, user_id: str) -> Task:
    ensure_user_exists(db, user_id)
    task_data = task_in.model_dump(exclude={"notes"})
    db_task = Task(**task_data, user_id=user_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(db: Session, task_id: str, task_in: TaskUpdate, user_id: str) -> Optional[Task]:
    db_task = get_task_by_id(db, task_id, user_id)
    if not db_task:
        return None

    update_data = task_in.model_dump(exclude_unset=True, exclude={"notes"})
    for field, value in update_data.items():
        setattr(db_task, field, value)

    db.commit()
    db.refresh(db_task)
    return db_task


def update_task_status(db: Session, task_id: str, status_in: TaskStatusUpdate, user_id: str) -> Optional[Task]:
    db_task = get_task_by_id(db, task_id, user_id)
    if not db_task:
        return None

    db_task.status = status_in.status
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: str, user_id: str) -> bool:
    db_task = get_task_by_id(db, task_id, user_id)
    if not db_task:
        return False

    db.delete(db_task)
    db.commit()
    return True
