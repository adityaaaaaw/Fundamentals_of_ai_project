from sqlalchemy.orm import Session
from app.models.user import User


def ensure_user_exists(db: Session, user_id: str) -> User:
    """Ensure a student user record exists for foreign key constraints without seeding demo data."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(
            id=user_id,
            name="Student",
            email=None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
