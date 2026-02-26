from sqlalchemy.orm import Session

from app.models import User


STUB_EMAIL = "testuser@example.com"
STUB_DISPLAY_NAME = "Test User"


def get_current_user(db: Session) -> User:
    """Stub auth: returns a hardcoded test user. Replace with JWT in Phase 4."""
    user = db.query(User).filter(User.email == STUB_EMAIL).first()
    if user is None:
        user = User(email=STUB_EMAIL, display_name=STUB_DISPLAY_NAME)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
