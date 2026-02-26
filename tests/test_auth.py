from app.auth import get_current_user
from app.models import User


def test_get_current_user_returns_user(db_session):
    user = get_current_user(db_session)
    assert user is not None
    assert isinstance(user, User)
    assert user.email == "testuser@example.com"


def test_get_current_user_is_idempotent(db_session):
    user1 = get_current_user(db_session)
    user2 = get_current_user(db_session)
    assert user1.id == user2.id
