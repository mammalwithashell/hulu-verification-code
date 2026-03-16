# Phase 2: Data Models + Storage Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Define all SQLAlchemy ORM models, Pydantic schemas, Fernet encryption for secrets, and generate the initial Alembic migration.

**Architecture:** Six SQLAlchemy models mapping to the entities in AGENTS.md. Pydantic schemas separate request/response contracts from ORM internals. Fernet symmetric encryption protects IMAP credentials at rest. Alembic autogenerates the initial migration from the models.

**Tech Stack:** SQLAlchemy 2.0 (mapped_column), Pydantic v2, cryptography (Fernet), Alembic

---

### Task 1: Add cryptography dependency

**Files:**
- Modify: `app/requirements.txt`

**Step 1: Add cryptography to requirements.txt**

Append this line to `app/requirements.txt`:

```
cryptography==44.0.0
```

**Step 2: Install it**

Run: `cd C:/Users/james/Documents/hulu-verification-code && pip install cryptography==44.0.0`
Expected: Successfully installed

**Step 3: Commit**

```bash
git add app/requirements.txt
git commit -m "chore: add cryptography dependency for Fernet encryption"
```

---

### Task 2: Implement encryption module

**Files:**
- Create: `app/encryption.py`
- Test: `tests/test_encryption.py`

**Step 1: Write the failing tests**

Create `tests/test_encryption.py`:

```python
import os
os.environ.setdefault("SECRET_ENCRYPTION_KEY", "test-key-for-unit-tests-only!!")

from app.encryption import encrypt_secret, decrypt_secret


def test_round_trip():
    plaintext = "my-app-password-123"
    ciphertext = encrypt_secret(plaintext)
    assert ciphertext != plaintext
    assert decrypt_secret(ciphertext) == plaintext


def test_different_plaintexts_produce_different_ciphertexts():
    a = encrypt_secret("password-a")
    b = encrypt_secret("password-b")
    assert a != b


def test_ciphertext_is_string():
    ct = encrypt_secret("hello")
    assert isinstance(ct, str)


def test_empty_string_round_trip():
    ct = encrypt_secret("")
    assert decrypt_secret(ct) == ""
```

**Step 2: Run test to verify it fails**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_encryption.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.encryption'`

**Step 3: Write app/encryption.py**

```python
import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import settings


def _get_fernet() -> Fernet:
    """Derive a valid 32-byte Fernet key from the configured secret."""
    key_bytes = hashlib.sha256(settings.secret_encryption_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a plaintext string, return base64-encoded ciphertext."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt a ciphertext string back to plaintext."""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()
```

**Step 4: Run tests to verify they pass**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_encryption.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add app/encryption.py tests/test_encryption.py
git commit -m "feat: add Fernet encryption module for secrets at rest"
```

---

### Task 3: Define SQLAlchemy ORM models

**Files:**
- Rewrite: `app/models.py`
- Test: `tests/test_models.py`

**Step 1: Write the failing tests**

Create `tests/test_models.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_models.py -v`
Expected: FAIL with `ImportError: cannot import name 'User' from 'app.models'`

**Step 3: Rewrite app/models.py**

```python
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    email_connections: Mapped[list["EmailConnection"]] = relationship(back_populates="user")
    streaming_accounts: Mapped[list["StreamingAccount"]] = relationship(back_populates="user")


class EmailConnection(Base):
    __tablename__ = "email_connections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    email_address: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_secret_ref: Mapped[str] = mapped_column(Text, nullable=False)
    imap_server: Mapped[str] = mapped_column(String(255), nullable=False)
    imap_port: Mapped[int] = mapped_column(Integer, default=993)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="email_connections")
    streaming_accounts: Mapped[list["StreamingAccount"]] = relationship(back_populates="email_connection")


class StreamingAccount(Base):
    __tablename__ = "streaming_accounts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    email_connection_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("email_connections.id"), nullable=False)
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_label: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="streaming_accounts")
    email_connection: Mapped["EmailConnection"] = relationship(back_populates="streaming_accounts")


class SharedAccess(Base):
    __tablename__ = "shared_access"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    grantee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    streaming_account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("streaming_accounts.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    owner: Mapped["User"] = relationship(foreign_keys=[owner_id])
    grantee: Mapped["User"] = relationship(foreign_keys=[grantee_id])
    streaming_account: Mapped["StreamingAccount"] = relationship()


class VerificationRequest(Base):
    __tablename__ = "verification_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    requester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    streaming_account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("streaming_accounts.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    code: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    confidence: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    error: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    requester: Mapped["User"] = relationship()
    streaming_account: Mapped["StreamingAccount"] = relationship()
    events: Mapped[list["VerificationEvent"]] = relationship(back_populates="verification_request")


class VerificationEvent(Base):
    __tablename__ = "verification_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_new_uuid)
    verification_request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("verification_requests.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    verification_request: Mapped["VerificationRequest"] = relationship(back_populates="events")
```

**Step 4: Run tests to verify they pass**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_models.py -v`
Expected: 7 passed

**Step 5: Commit**

```bash
git add app/models.py tests/test_models.py
git commit -m "feat: define all SQLAlchemy ORM models for core entities"
```

---

### Task 4: Define Pydantic request/response schemas

**Files:**
- Create: `app/schemas.py`
- Test: `tests/test_schemas.py`

**Step 1: Write the failing tests**

Create `tests/test_schemas.py`:

```python
import uuid
from datetime import datetime, timezone

from app.schemas import (
    EmailConnectionCreate,
    EmailConnectionResponse,
    StreamingAccountCreate,
    StreamingAccountResponse,
    SharedAccessCreate,
    SharedAccessResponse,
    VerificationRequestCreate,
    VerificationResultResponse,
)


def test_email_connection_create_valid():
    data = EmailConnectionCreate(
        provider="gmail",
        email_address="user@gmail.com",
        app_password="my-secret-password",
        imap_server="imap.gmail.com",
        imap_port=993,
    )
    assert data.provider == "gmail"
    assert data.app_password == "my-secret-password"


def test_email_connection_response_hides_secret():
    resp = EmailConnectionResponse(
        id=uuid.uuid4(),
        provider="gmail",
        email_address="user@gmail.com",
        imap_server="imap.gmail.com",
        imap_port=993,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
    )
    data = resp.model_dump()
    assert "encrypted_secret_ref" not in data
    assert "app_password" not in data
    assert data["is_verified"] is True


def test_streaming_account_create_valid():
    data = StreamingAccountCreate(
        email_connection_id=uuid.uuid4(),
        service_name="Hulu",
        account_label="Family Hulu",
    )
    assert data.service_name == "Hulu"


def test_streaming_account_response():
    resp = StreamingAccountResponse(
        id=uuid.uuid4(),
        service_name="Hulu",
        account_label="Family Hulu",
        email_connection_id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
    )
    assert resp.service_name == "Hulu"


def test_shared_access_create_valid():
    data = SharedAccessCreate(
        grantee_id=uuid.uuid4(),
        streaming_account_id=uuid.uuid4(),
    )
    assert data.grantee_id is not None


def test_shared_access_response():
    resp = SharedAccessResponse(
        id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        grantee_id=uuid.uuid4(),
        streaming_account_id=uuid.uuid4(),
        created_at=datetime.now(timezone.utc),
        revoked_at=None,
    )
    assert resp.revoked_at is None


def test_verification_request_create():
    data = VerificationRequestCreate(
        streaming_account_id=uuid.uuid4(),
    )
    assert data.streaming_account_id is not None


def test_verification_result_response():
    resp = VerificationResultResponse(
        id=uuid.uuid4(),
        streaming_account_id=uuid.uuid4(),
        status="completed",
        code="123456",
        source_service="Hulu",
        received_at=datetime.now(timezone.utc),
        confidence="high",
        error=None,
    )
    assert resp.code == "123456"
    assert resp.confidence == "high"


def test_verification_result_response_failed():
    resp = VerificationResultResponse(
        id=uuid.uuid4(),
        streaming_account_id=uuid.uuid4(),
        status="failed",
        code=None,
        source_service="Hulu",
        received_at=None,
        confidence=None,
        error="No matching email found",
    )
    assert resp.error == "No matching email found"
    assert resp.code is None
```

**Step 2: Run tests to verify they fail**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_schemas.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.schemas'`

**Step 3: Write app/schemas.py**

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


# --- Email Connections ---

class EmailConnectionCreate(BaseModel):
    provider: str
    email_address: str
    app_password: str  # plaintext in request, encrypted before storage
    imap_server: str
    imap_port: int = 993


class EmailConnectionResponse(BaseModel):
    id: uuid.UUID
    provider: str
    email_address: str
    imap_server: str
    imap_port: int
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Streaming Accounts ---

class StreamingAccountCreate(BaseModel):
    email_connection_id: uuid.UUID
    service_name: str
    account_label: str


class StreamingAccountResponse(BaseModel):
    id: uuid.UUID
    service_name: str
    account_label: str
    email_connection_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Shared Access ---

class SharedAccessCreate(BaseModel):
    grantee_id: uuid.UUID
    streaming_account_id: uuid.UUID


class SharedAccessResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    grantee_id: uuid.UUID
    streaming_account_id: uuid.UUID
    created_at: datetime
    revoked_at: datetime | None = None

    model_config = {"from_attributes": True}


# --- Verification ---

class VerificationRequestCreate(BaseModel):
    streaming_account_id: uuid.UUID


class VerificationResultResponse(BaseModel):
    id: uuid.UUID
    streaming_account_id: uuid.UUID
    status: str
    code: str | None = None
    source_service: str | None = None
    received_at: datetime | None = None
    confidence: str | None = None
    error: str | None = None

    model_config = {"from_attributes": True}
```

**Step 4: Run tests to verify they pass**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_schemas.py -v`
Expected: 9 passed

**Step 5: Commit**

```bash
git add app/schemas.py tests/test_schemas.py
git commit -m "feat: add Pydantic request/response schemas for all entities"
```

---

### Task 5: Import models in Alembic env and generate initial migration

**Files:**
- Modify: `alembic/env.py` (ensure models are imported so Base.metadata has all tables)
- Create: `alembic/versions/<auto>_initial_schema.py` (autogenerated)

**Step 1: Add model import to alembic/env.py**

Add this import near the top of `alembic/env.py`, after the existing `from app.database import Base` line:

```python
import app.models  # noqa: F401 — register all models with Base.metadata
```

This ensures Alembic sees all the tables when autogenerating.

**Step 2: Generate the initial migration**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m alembic revision --autogenerate -m "initial schema"`
Expected: Creates a migration file in `alembic/versions/` with all 6 tables.

**Step 3: Verify the migration applies cleanly**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m alembic upgrade head`
Expected: Creates tables in dev.db (or test.db). No errors.

**Step 4: Verify by downgrading and re-upgrading**

Run:
```bash
cd C:/Users/james/Documents/hulu-verification-code
python -m alembic downgrade base
python -m alembic upgrade head
```
Expected: Both commands succeed without errors.

**Step 5: Commit**

```bash
git add alembic/
git commit -m "feat: add initial Alembic migration with all 6 tables"
```

---

### Task 6: Run full test suite and verify

**Step 1: Run all tests**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/ -v`
Expected: All tests pass (6 existing + 4 encryption + 7 models + 9 schemas = 26 tests).

**Step 2: Verify alembic migration still works**

Run:
```bash
cd C:/Users/james/Documents/hulu-verification-code
rm -f dev.db
python -m alembic upgrade head
```
Expected: Fresh database created with all tables.

**Step 3: Final commit if any fixups needed**

Only commit if changes were required to fix issues found in steps 1-2.
