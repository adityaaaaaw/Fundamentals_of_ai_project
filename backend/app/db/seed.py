from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User
from app.models.task import Task
from app.models.session import StudySession
from app.models.exam import Exam


def get_formatted_date(offset_days: int = 0) -> str:
    d = date.today() + timedelta(days=offset_days)
    return d.isoformat()


def seed_demo_data(db: Session) -> None:
    # 1. Ensure Demo User exists
    user = db.query(User).filter(User.id == settings.DEMO_USER_ID).first()
    if not user:
        user = User(
            id=settings.DEMO_USER_ID,
            name="Aditya Sharma",
            email="aditya.student@example.edu"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # 2. Seed Tasks if empty
    task_count = db.query(Task).filter(Task.user_id == settings.DEMO_USER_ID).count()
    if task_count == 0:
        tasks = [
            Task(
                id="task-1",
                user_id=settings.DEMO_USER_ID,
                title="Implement A* Search Algorithm in Python",
                subject="Fundamentals of AI",
                due_date=get_formatted_date(2),
                priority="high",
                status="pending",
                description="Include Manhattan distance heuristic and test on 8-puzzle problem.",
                estimated_minutes=90,
            ),
            Task(
                id="task-2",
                user_id=settings.DEMO_USER_ID,
                title="Solve Chapter 4 Problem Set (Eigenvalues)",
                subject="Linear Algebra",
                due_date=get_formatted_date(1),
                priority="high",
                status="pending",
                description="Problems 12-25 on diagonalization and symmetric matrices.",
                estimated_minutes=60,
            ),
            Task(
                id="task-3",
                user_id=settings.DEMO_USER_ID,
                title="Read Database Normalization & BCNF Notes",
                subject="Database Systems",
                due_date=get_formatted_date(4),
                priority="medium",
                status="pending",
                description="Prepare summary for Thursday lecture discussion.",
                estimated_minutes=45,
            ),
            Task(
                id="task-4",
                user_id=settings.DEMO_USER_ID,
                title="Submit Operating Systems Process Scheduling Lab",
                subject="Operating Systems",
                due_date=get_formatted_date(-1),
                priority="medium",
                status="completed",
                description="Submitted on GitHub classroom before deadline.",
                estimated_minutes=120,
            ),
            Task(
                id="task-5",
                user_id=settings.DEMO_USER_ID,
                title="Practice Dijkstra Algorithm implementations",
                subject="Data Structures",
                due_date=get_formatted_date(-2),
                priority="low",
                status="completed",
                description="Completed LeetCode problems 743 and 787.",
                estimated_minutes=60,
            ),
            Task(
                id="task-6",
                user_id=settings.DEMO_USER_ID,
                title="Review Machine Learning Ethics Case Study",
                subject="Fundamentals of AI",
                due_date=get_formatted_date(-3),
                priority="low",
                status="missed",
                description="Quiz closed on Sunday midnight.",
                estimated_minutes=30,
            ),
        ]
        db.add_all(tasks)
        db.commit()

    # 3. Seed Study Sessions if empty
    session_count = db.query(StudySession).filter(StudySession.user_id == settings.DEMO_USER_ID).count()
    if session_count == 0:
        sessions = [
            StudySession(
                id="session-1",
                user_id=settings.DEMO_USER_ID,
                subject="Fundamentals of AI",
                date=get_formatted_date(0),
                day_of_week="Monday",
                start_time="10:00",
                end_time="11:30",
                duration_minutes=90,
                title="Heuristic Search & Adversarial Minimax",
                status="completed",
                color="#C5A059",
            ),
            StudySession(
                id="session-2",
                user_id=settings.DEMO_USER_ID,
                subject="Linear Algebra",
                date=get_formatted_date(0),
                day_of_week="Monday",
                start_time="14:00",
                end_time="15:30",
                duration_minutes=90,
                title="Vector Spaces & Inner Product Review",
                status="upcoming",
                color="#8A7B66",
            ),
            StudySession(
                id="session-3",
                user_id=settings.DEMO_USER_ID,
                subject="Database Systems",
                date=get_formatted_date(0),
                day_of_week="Monday",
                start_time="17:00",
                end_time="18:15",
                duration_minutes=75,
                title="SQL Query Optimization and Indexing",
                status="upcoming",
                color="#5B7A8C",
            ),
            StudySession(
                id="session-4",
                user_id=settings.DEMO_USER_ID,
                subject="Operating Systems",
                date=get_formatted_date(1),
                day_of_week="Tuesday",
                start_time="09:30",
                end_time="11:00",
                duration_minutes=90,
                title="Virtual Memory & Page Replacement Algorithms",
                status="upcoming",
                color="#6B8E23",
            ),
            StudySession(
                id="session-5",
                user_id=settings.DEMO_USER_ID,
                subject="Data Structures",
                date=get_formatted_date(2),
                day_of_week="Wednesday",
                start_time="11:00",
                end_time="12:30",
                duration_minutes=90,
                title="Red-Black Trees and B-Trees",
                status="upcoming",
                color="#C5A059",
            ),
            StudySession(
                id="session-6",
                user_id=settings.DEMO_USER_ID,
                subject="Fundamentals of AI",
                date=get_formatted_date(3),
                day_of_week="Thursday",
                start_time="15:00",
                end_time="17:00",
                duration_minutes=120,
                title="Constraint Satisfaction Problems (CSP)",
                status="upcoming",
                color="#C5A059",
            ),
            StudySession(
                id="session-7",
                user_id=settings.DEMO_USER_ID,
                subject="Linear Algebra",
                date=get_formatted_date(4),
                day_of_week="Friday",
                start_time="14:00",
                end_time="15:30",
                duration_minutes=90,
                title="Orthogonal Projection and Gram-Schmidt",
                status="upcoming",
                color="#8A7B66",
            ),
            StudySession(
                id="session-8",
                user_id=settings.DEMO_USER_ID,
                subject="Fundamentals of AI",
                date=get_formatted_date(-1),
                day_of_week="Sunday",
                start_time="16:00",
                end_time="17:30",
                duration_minutes=90,
                title="Linear Regression Gradient Descent in NumPy",
                status="completed",
                color="#8B5A2B",
            ),
        ]
        db.add_all(sessions)
        db.commit()

    # 4. Seed Exams if empty
    exam_count = db.query(Exam).filter(Exam.user_id == settings.DEMO_USER_ID).count()
    if exam_count == 0:
        exams = [
            Exam(
                id="exam-1",
                user_id=settings.DEMO_USER_ID,
                subject="Fundamentals of AI",
                title="Midterm Examination: Search & Logic",
                exam_date=get_formatted_date(6),
                exam_time="10:00 AM - 12:00 PM",
                room="Hall B, CS Wing",
                weight="25% of Grade",
            ),
            Exam(
                id="exam-2",
                user_id=settings.DEMO_USER_ID,
                subject="Linear Algebra",
                title="Unit Test 2: Matrix Decompositions",
                exam_date=get_formatted_date(12),
                exam_time="02:00 PM - 03:30 PM",
                room="Room 304, Math Building",
                weight="15% of Grade",
            ),
            Exam(
                id="exam-3",
                user_id=settings.DEMO_USER_ID,
                subject="Database Systems",
                title="Practical Lab Assessment: SQL & Relational Algebra",
                exam_date=get_formatted_date(18),
                exam_time="11:00 AM - 01:00 PM",
                room="Lab 2, Informatics Dept",
                weight="20% of Grade",
            ),
        ]
        db.add_all(exams)
        db.commit()
