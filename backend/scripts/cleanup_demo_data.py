#!/usr/bin/env python3
"""
Explicit Demo Data Cleanup Utility
AI Study Planner Agent

Usage:
    python scripts/cleanup_demo_data.py --dry-run   (inspect demo records without deleting)
    python scripts/cleanup_demo_data.py --confirm   (explicitly delete demo records)

Safety guarantees:
    - Only deletes records matching the exact initial demo IDs (task-1..6, session-1..8, exam-1..3).
    - Preserves any user-created tasks, sessions, and exams with custom or UUID identifiers.
    - Preserves foreign key integrity in SQLite.
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.task import Task
from app.models.session import StudySession
from app.models.exam import Exam
from app.models.agent_log import AgentActivityLog
from app.models.user import User

DEMO_TASK_IDS = ["task-1", "task-2", "task-3", "task-4", "task-5", "task-6"]
DEMO_SESSION_IDS = [
    "session-1", "session-2", "session-3", "session-4",
    "session-5", "session-6", "session-7", "session-8"
]
DEMO_EXAM_IDS = ["exam-1", "exam-2", "exam-3"]


def cleanup_demo_data(dry_run: bool = True, confirm: bool = False):
    print("=" * 70)
    print("AI STUDY PLANNER AGENT — EXPLICIT DEMO DATA CLEANUP")
    print("=" * 70)

    db: Session = SessionLocal()
    try:
        # 1. Identify Demo Records
        demo_tasks = db.query(Task).filter(Task.id.in_(DEMO_TASK_IDS)).all()
        demo_sessions = db.query(StudySession).filter(StudySession.id.in_(DEMO_SESSION_IDS)).all()
        demo_exams = db.query(Exam).filter(Exam.id.in_(DEMO_EXAM_IDS)).all()

        # Count total records vs demo records
        total_tasks = db.query(Task).count()
        total_sessions = db.query(StudySession).count()
        total_exams = db.query(Exam).count()

        print("\n[INSPECTION RESULT]")
        print(f"  Tasks:    {len(demo_tasks)} demo record(s) found out of {total_tasks} total.")
        for t in demo_tasks:
            print(f"    - [{t.id}] {t.subject}: {t.title}")

        print(f"\n  Sessions: {len(demo_sessions)} demo record(s) found out of {total_sessions} total.")
        for s in demo_sessions:
            print(f"    - [{s.id}] {s.subject}: {s.title} ({s.date} {s.start_time}-{s.end_time})")

        print(f"\n  Exams:    {len(demo_exams)} demo record(s) found out of {total_exams} total.")
        for e in demo_exams:
            print(f"    - [{e.id}] {e.subject}: {e.title} ({e.exam_date})")

        demo_user = db.query(User).filter(User.id == "demo-user-id").first()
        if demo_user and demo_user.name == "Aditya Sharma":
            print(f"\n  Demo User Profile: [{demo_user.id}] name='{demo_user.name}', email='{demo_user.email}'")

        if dry_run and not confirm:
            print("\n" + "-" * 70)
            print("[DRY-RUN MODE] No changes were made to your database.")
            print("To delete the verified demo records above, run:")
            print("    python scripts/cleanup_demo_data.py --confirm")
            print("-" * 70)
            return

        if not confirm:
            user_input = input("\nAre you sure you want to permanently delete these demo records? (yes/no): ")
            if user_input.strip().lower() not in ["y", "yes"]:
                print("[ABORTED] Cleanup cancelled by user. No records were modified.")
                return

        # Execute Deletions
        print("\n[EXECUTING CLEANUP] Deleting verified demo records...")

        deleted_tasks = 0
        for t in demo_tasks:
            db.delete(t)
            deleted_tasks += 1

        deleted_sessions = 0
        for s in demo_sessions:
            db.delete(s)
            deleted_sessions += 1

        deleted_exams = 0
        for e in demo_exams:
            db.delete(e)
            deleted_exams += 1

        # Reset demo user profile to clean generic student account
        if demo_user and demo_user.name == "Aditya Sharma":
            demo_user.name = "Student"
            demo_user.email = None

        db.commit()

        print(f"[SUCCESS] Cleaned {deleted_tasks} demo task(s), {deleted_sessions} demo session(s), {deleted_exams} demo exam(s).")
        print("[SUCCESS] Preserved all user-created records and reset user profile to a clean state.")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean verified demo coursework from SQLite database.")
    parser.add_argument("--dry-run", action="store_true", help="Inspect demo records without modifying database.")
    parser.add_argument("--confirm", action="store_true", help="Confirm deletion of verified demo records.")
    args = parser.parse_args()

    cleanup_demo_data(dry_run=args.dry_run, confirm=args.confirm)
