import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import (
    User,
    EmailConnection,
    StreamingAccount,
    SharedAccess,
    VerificationRequest,
    VerificationEvent,
)


def _make_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def test_create_user():
    engine = _make_engine()
    with Session(engine) as session:
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"
        assert user.created_at is not None


def test_create_email_connection():
    engine = _make_engine()
    with Session(engine) as session:
        user = User(email="test@example.com", display_name="Test")
        session.add(user)
        session.flush()

        conn = EmailConnection(
            user_id=user.id,
            provider="gmail",
            email_address="test@gmail.com",
            encrypted_secret_ref="fernet-ciphertext-here",
            imap_server="imap.gmail.com",
            imap_port=993,
        )
        session.add(conn)
        session.commit()
        session.refresh(conn)

        assert conn.id is not None
        assert conn.user_id == user.id
        assert conn.is_verified is False
        assert conn.imap_port == 993


def test_create_streaming_account():
    engine = _make_engine()
    with Session(engine) as session:
        user = User(email="test@example.com", display_name="Test")
        session.add(user)
        session.flush()

        conn = EmailConnection(
            user_id=user.id,
            provider="gmail",
            email_address="test@gmail.com",
            encrypted_secret_ref="enc",
            imap_server="imap.gmail.com",
            imap_port=993,
        )
        session.add(conn)
        session.flush()

        account = StreamingAccount(
            user_id=user.id,
            email_connection_id=conn.id,
            service_name="Hulu",
            account_label="Family Hulu",
        )
        session.add(account)
        session.commit()
        session.refresh(account)

        assert account.id is not None
        assert account.service_name == "Hulu"


def test_create_shared_access():
    engine = _make_engine()
    with Session(engine) as session:
        owner = User(email="owner@example.com", display_name="Owner")
        grantee = User(email="grantee@example.com", display_name="Grantee")
        session.add_all([owner, grantee])
        session.flush()

        conn = EmailConnection(
            user_id=owner.id,
            provider="gmail",
            email_address="owner@gmail.com",
            encrypted_secret_ref="enc",
            imap_server="imap.gmail.com",
            imap_port=993,
        )
        session.add(conn)
        session.flush()

        account = StreamingAccount(
            user_id=owner.id,
            email_connection_id=conn.id,
            service_name="Hulu",
            account_label="Hulu",
        )
        session.add(account)
        session.flush()

        share = SharedAccess(
            owner_id=owner.id,
            grantee_id=grantee.id,
            streaming_account_id=account.id,
        )
        session.add(share)
        session.commit()
        session.refresh(share)

        assert share.id is not None
        assert share.revoked_at is None


def test_create_verification_request_and_event():
    engine = _make_engine()
    with Session(engine) as session:
        user = User(email="test@example.com", display_name="Test")
        session.add(user)
        session.flush()

        conn = EmailConnection(
            user_id=user.id,
            provider="gmail",
            email_address="test@gmail.com",
            encrypted_secret_ref="enc",
            imap_server="imap.gmail.com",
            imap_port=993,
        )
        session.add(conn)
        session.flush()

        account = StreamingAccount(
            user_id=user.id,
            email_connection_id=conn.id,
            service_name="Hulu",
            account_label="Hulu",
        )
        session.add(account)
        session.flush()

        req = VerificationRequest(
            requester_id=user.id,
            streaming_account_id=account.id,
            status="pending",
        )
        session.add(req)
        session.flush()

        event = VerificationEvent(
            verification_request_id=req.id,
            event_type="requested",
            detail="User initiated verification",
        )
        session.add(event)
        session.commit()
        session.refresh(req)
        session.refresh(event)

        assert req.status == "pending"
        assert req.code is None
        assert event.event_type == "requested"


def test_user_email_unique_constraint():
    engine = _make_engine()
    from sqlalchemy.exc import IntegrityError
    import pytest

    with Session(engine) as session:
        session.add(User(email="dup@example.com", display_name="A"))
        session.commit()

    with Session(engine) as session:
        session.add(User(email="dup@example.com", display_name="B"))
        with pytest.raises(IntegrityError):
            session.commit()
