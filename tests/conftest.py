import os
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ.setdefault("SECRET_ENCRYPTION_KEY", "test-key-for-unit-tests-only!!")

import bcrypt
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.auth import hash_password, create_access_token
from app.models import User

# Use fast bcrypt rounds (4) for all tests to avoid slow hashing
_original_gensalt = bcrypt.gensalt
bcrypt.gensalt = lambda rounds=4: _original_gensalt(rounds=4)


@pytest.fixture()
def db_session():
    """Create a fresh in-memory database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    """TestClient with overridden DB dependency."""
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def create_test_user(
    db_session: Session,
    email: str = "testuser@example.com",
    display_name: str = "Test User",
    password: str = "testpassword123",
) -> tuple[User, str]:
    """Create a user in the DB and return (user, access_token)."""
    user = User(
        email=email,
        display_name=display_name,
        hashed_password=hash_password(password),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token(str(user.id))
    return user, token


def auth_header(token: str) -> dict[str, str]:
    """Return Authorization header dict for a Bearer token."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def authenticated_user(db_session):
    """Create a default test user and return (user, token)."""
    return create_test_user(db_session)


@pytest.fixture()
def auth_headers(authenticated_user):
    """Return auth headers for the default test user."""
    _, token = authenticated_user
    return auth_header(token)
