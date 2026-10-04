from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskResponse
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=List[TaskResponse])
def read_tasks(
    status: Optional[str] = Query(None, description="Filter by status: pending, in_progress, completed, missed"),
    priority: Optional[str] = Query(None, description="Filter by priority: low, medium, high"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    due_date: Optional[str] = Query(None, description="Filter by due date YYYY-MM-DD"),
    search: Optional[str] = Query(None, description="Search term in title, subject, or description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return task_service.get_tasks(
        db=db,
        user_id=settings.DEMO_USER_ID,
        status=status,
        priority=priority,
        subject=subject,
        due_date=due_date,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_new_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    return task_service.create_task(db=db, task_in=task_in, user_id=settings.DEMO_USER_ID)


@router.get("/{task_id}", response_model=TaskResponse)
def read_task(task_id: str, db: Session = Depends(get_db)):
    task = task_service.get_task_by_id(db=db, task_id=task_id, user_id=settings.DEMO_USER_ID)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_existing_task(task_id: str, task_in: TaskUpdate, db: Session = Depends(get_db)):
    task = task_service.update_task(db=db, task_id=task_id, task_in=task_in, user_id=settings.DEMO_USER_ID)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.patch("/{task_id}/status", response_model=TaskResponse)
def patch_task_status(task_id: str, status_in: TaskStatusUpdate, db: Session = Depends(get_db)):
    task = task_service.update_task_status(db=db, task_id=task_id, status_in=status_in, user_id=settings.DEMO_USER_ID)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_task(task_id: str, db: Session = Depends(get_db)):
    success = task_service.delete_task(db=db, task_id=task_id, user_id=settings.DEMO_USER_ID)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return None
