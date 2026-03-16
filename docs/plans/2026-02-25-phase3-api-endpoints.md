# Phase 3: Core API Endpoints Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement all 7 `/v1` endpoints with stub auth, test fixtures, and proper error handling.

**Architecture:** Four router modules mounted by main.py. A shared test conftest provides an in-memory SQLite session and a test user. A stub `get_current_user` dependency returns a hardcoded user (swapped for real JWT in Phase 4).

**Tech Stack:** FastAPI routers, SQLAlchemy sessions via `Depends(get_db)`, Pydantic schemas, pytest with TestClient

---

### Task 1: Test fixtures and stub auth

**Files:**
- Create: `app/auth.py`
- Create: `app/routers/__init__.py`
- Modify: `tests/conftest.py`
- Test: `tests/test_auth.py`

**Step 1: Write the failing test**

Create `tests/test_auth.py`:

```python
from app.auth import get_current_user
from app.models import User
from app.database import get_db


def test_get_current_user_returns_user(db_session):
    user = get_current_user(db_session)
    assert user is not None
    assert isinstance(user, User)
    assert user.email == "testuser@example.com"


def test_get_current_user_is_idempotent(db_session):
    user1 = get_current_user(db_session)
    user2 = get_current_user(db_session)
    assert user1.id == user2.id
```

**Step 2: Rewrite `tests/conftest.py` with shared fixtures**

```python
import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ.setdefault("SECRET_ENCRYPTION_KEY", "test-key-for-unit-tests-only!!")

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    """Create a fresh in-memory database for each test."""
    engine = create_engine("sqlite:///:memory:")

    # Enable foreign key enforcement for SQLite
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
```

**Step 3: Write `app/auth.py`**

```python
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
```

**Step 4: Create `app/routers/__init__.py`** (empty file)

**Step 5: Run tests to verify they pass**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_auth.py -v`
Expected: 2 passed

Also run all existing tests to check for regressions:
Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/ -v`
Expected: All pass (some existing tests may need updating if conftest changes break them)

Note: The existing `test_database.py` tests import directly from `app.database` and don't use the `db_session` fixture, so they should still pass. The existing `test_health.py` uses its own `TestClient(app)` without DB override, so it should still pass. The `test_models.py` tests create their own in-memory engines, so they should still pass.

**Step 6: Commit**

```bash
git add app/auth.py app/routers/__init__.py tests/conftest.py tests/test_auth.py
git commit -m "feat: add stub auth, test fixtures, and router package"
```

---

### Task 2: Email connections router

**Files:**
- Create: `app/routers/email_connections.py`
- Modify: `app/main.py` (include router)
- Test: `tests/test_email_connections.py`

**Step 1: Write the failing tests**

Create `tests/test_email_connections.py`:

```python
def test_test_email_connection_valid(client):
    resp = client.post("/v1/email-connections/test", json={
        "provider": "gmail",
        "email_address": "user@gmail.com",
        "app_password": "fake-password",
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "stub")


def test_test_email_connection_missing_fields(client):
    resp = client.post("/v1/email-connections/test", json={
        "provider": "gmail",
    })
    assert resp.status_code == 422
```

**Step 2: Run tests to verify they fail**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_email_connections.py -v`
Expected: FAIL — 404 (no route)

**Step 3: Write `app/routers/email_connections.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, EmailConnection
from app.schemas import EmailConnectionCreate, EmailConnectionResponse
from app.encryption import encrypt_secret

router = APIRouter(prefix="/v1/email-connections", tags=["email-connections"])


@router.post("/test")
def test_email_connection(
    payload: EmailConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validate IMAP credentials. Stub: validates shape only. Real IMAP in Phase 5."""
    return {"status": "stub", "message": "Connection test not yet implemented. Credentials shape is valid."}
```

**Step 4: Add router to `app/main.py`**

Add after the CORS middleware block:

```python
from app.routers import email_connections

app.include_router(email_connections.router)
```

**Step 5: Run tests to verify they pass**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_email_connections.py -v`
Expected: 2 passed

**Step 6: Commit**

```bash
git add app/routers/email_connections.py app/main.py tests/test_email_connections.py
git commit -m "feat: add POST /v1/email-connections/test endpoint"
```

---

### Task 3: Streaming accounts router

**Files:**
- Create: `app/routers/streaming_accounts.py`
- Modify: `app/main.py` (include router)
- Test: `tests/test_streaming_accounts.py`

**Step 1: Write the failing tests**

Create `tests/test_streaming_accounts.py`:

```python
import uuid


def _create_email_connection(client):
    """Helper: create an email connection so we can link a streaming account."""
    # We need to insert directly since we only have a test endpoint, not a create endpoint
    # Instead, use the client fixture's db_session
    pass


def _seed_email_connection(db_session, user):
    """Seed an email connection for testing."""
    from app.models import EmailConnection
    from app.encryption import encrypt_secret

    conn = EmailConnection(
        user_id=user.id,
        provider="gmail",
        email_address="test@gmail.com",
        encrypted_secret_ref=encrypt_secret("fake-password"),
        imap_server="imap.gmail.com",
        imap_port=993,
    )
    db_session.add(conn)
    db_session.commit()
    db_session.refresh(conn)
    return conn


def test_create_streaming_account(client, db_session):
    from app.auth import get_current_user
    user = get_current_user(db_session)
    conn = _seed_email_connection(db_session, user)

    resp = client.post("/v1/streaming-accounts", json={
        "email_connection_id": str(conn.id),
        "service_name": "Hulu",
        "account_label": "Family Hulu",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["service_name"] == "Hulu"
    assert data["account_label"] == "Family Hulu"
    assert "id" in data


def test_create_streaming_account_bad_connection(client, db_session):
    resp = client.post("/v1/streaming-accounts", json={
        "email_connection_id": str(uuid.uuid4()),
        "service_name": "Hulu",
        "account_label": "Family Hulu",
    })
    assert resp.status_code == 404


def test_list_streaming_accounts_empty(client):
    resp = client.get("/v1/streaming-accounts")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_streaming_accounts_returns_owned(client, db_session):
    from app.auth import get_current_user
    user = get_current_user(db_session)
    conn = _seed_email_connection(db_session, user)

    client.post("/v1/streaming-accounts", json={
        "email_connection_id": str(conn.id),
        "service_name": "Hulu",
        "account_label": "Family Hulu",
    })

    resp = client.get("/v1/streaming-accounts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["service_name"] == "Hulu"
```

**Step 2: Run tests to verify they fail**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_streaming_accounts.py -v`
Expected: FAIL — 404 (no route)

**Step 3: Write `app/routers/streaming_accounts.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, EmailConnection, StreamingAccount, SharedAccess
from app.schemas import StreamingAccountCreate, StreamingAccountResponse

router = APIRouter(prefix="/v1/streaming-accounts", tags=["streaming-accounts"])


@router.post("", status_code=201, response_model=StreamingAccountResponse)
def create_streaming_account(
    payload: StreamingAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = db.query(EmailConnection).filter(
        EmailConnection.id == payload.email_connection_id,
        EmailConnection.user_id == current_user.id,
    ).first()
    if conn is None:
        raise HTTPException(status_code=404, detail="email_connection_not_found")

    account = StreamingAccount(
        user_id=current_user.id,
        email_connection_id=conn.id,
        service_name=payload.service_name,
        account_label=payload.account_label,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("", response_model=list[StreamingAccountResponse])
def list_streaming_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Owned accounts
    owned = db.query(StreamingAccount).filter(
        StreamingAccount.user_id == current_user.id,
    ).all()

    # Shared accounts (active shares only)
    shared_ids = db.query(SharedAccess.streaming_account_id).filter(
        SharedAccess.grantee_id == current_user.id,
        SharedAccess.revoked_at.is_(None),
    ).subquery()

    shared = db.query(StreamingAccount).filter(
        StreamingAccount.id.in_(shared_ids),
    ).all()

    # Deduplicate
    seen = {a.id for a in owned}
    result = list(owned)
    for a in shared:
        if a.id not in seen:
            result.append(a)
    return result
```

**Step 4: Add router to `app/main.py`**

Add import and include:

```python
from app.routers import email_connections, streaming_accounts

app.include_router(email_connections.router)
app.include_router(streaming_accounts.router)
```

**Step 5: Run tests to verify they pass**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_streaming_accounts.py -v`
Expected: 4 passed

**Step 6: Commit**

```bash
git add app/routers/streaming_accounts.py app/main.py tests/test_streaming_accounts.py
git commit -m "feat: add POST/GET /v1/streaming-accounts endpoints"
```

---

### Task 4: Verification router

**Files:**
- Create: `app/routers/verification.py`
- Modify: `app/main.py` (include router)
- Test: `tests/test_verification.py`

**Step 1: Write the failing tests**

Create `tests/test_verification.py`:

```python
import uuid

from app.models import EmailConnection, StreamingAccount
from app.encryption import encrypt_secret
from app.auth import get_current_user


def _seed_account(db_session):
    user = get_current_user(db_session)
    conn = EmailConnection(
        user_id=user.id,
        provider="gmail",
        email_address="test@gmail.com",
        encrypted_secret_ref=encrypt_secret("fake"),
        imap_server="imap.gmail.com",
        imap_port=993,
    )
    db_session.add(conn)
    db_session.flush()

    account = StreamingAccount(
        user_id=user.id,
        email_connection_id=conn.id,
        service_name="Hulu",
        account_label="Family Hulu",
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return user, account


def test_create_verification_request(client, db_session):
    user, account = _seed_account(db_session)
    resp = client.post("/v1/verification/request", json={
        "streaming_account_id": str(account.id),
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert data["streaming_account_id"] == str(account.id)
    assert "id" in data


def test_create_verification_request_bad_account(client, db_session):
    resp = client.post("/v1/verification/request", json={
        "streaming_account_id": str(uuid.uuid4()),
    })
    assert resp.status_code == 404


def test_get_verification_request(client, db_session):
    user, account = _seed_account(db_session)
    create_resp = client.post("/v1/verification/request", json={
        "streaming_account_id": str(account.id),
    })
    request_id = create_resp.json()["id"]

    resp = client.get(f"/v1/verification/{request_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == request_id
    assert data["status"] == "pending"


def test_get_verification_request_not_found(client, db_session):
    resp = client.get(f"/v1/verification/{uuid.uuid4()}")
    assert resp.status_code == 404
```

**Step 2: Run tests to verify they fail**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_verification.py -v`
Expected: FAIL — 404 (no route)

**Step 3: Write `app/routers/verification.py`**

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, StreamingAccount, SharedAccess, VerificationRequest, VerificationEvent
from app.schemas import VerificationRequestCreate, VerificationResultResponse

router = APIRouter(prefix="/v1/verification", tags=["verification"])


def _user_can_access_account(db: Session, user: User, account_id: uuid.UUID) -> bool:
    """Check if user owns the account or has active shared access."""
    account = db.query(StreamingAccount).filter(
        StreamingAccount.id == account_id,
    ).first()
    if account is None:
        return False
    if account.user_id == user.id:
        return True
    share = db.query(SharedAccess).filter(
        SharedAccess.grantee_id == user.id,
        SharedAccess.streaming_account_id == account_id,
        SharedAccess.revoked_at.is_(None),
    ).first()
    return share is not None


@router.post("/request", status_code=201, response_model=VerificationResultResponse)
def create_verification_request(
    payload: VerificationRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _user_can_access_account(db, current_user, payload.streaming_account_id):
        raise HTTPException(status_code=404, detail="streaming_account_not_found")

    account = db.query(StreamingAccount).get(payload.streaming_account_id)

    req = VerificationRequest(
        requester_id=current_user.id,
        streaming_account_id=payload.streaming_account_id,
        status="pending",
    )
    db.add(req)
    db.flush()

    event = VerificationEvent(
        verification_request_id=req.id,
        event_type="requested",
        detail=f"Verification requested by {current_user.email}",
    )
    db.add(event)
    db.commit()
    db.refresh(req)

    return VerificationResultResponse(
        id=req.id,
        streaming_account_id=req.streaming_account_id,
        status=req.status,
        code=req.code,
        source_service=account.service_name,
        received_at=req.completed_at,
        confidence=req.confidence,
        error=req.error,
    )


@router.get("/{request_id}", response_model=VerificationResultResponse)
def get_verification_request(
    request_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = db.query(VerificationRequest).filter(
        VerificationRequest.id == request_id,
    ).first()
    if req is None:
        raise HTTPException(status_code=404, detail="verification_request_not_found")

    # Auth check: must be the requester or the account owner
    account = db.query(StreamingAccount).get(req.streaming_account_id)
    if req.requester_id != current_user.id and account.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="verification_request_not_found")

    return VerificationResultResponse(
        id=req.id,
        streaming_account_id=req.streaming_account_id,
        status=req.status,
        code=req.code,
        source_service=account.service_name,
        received_at=req.completed_at,
        confidence=req.confidence,
        error=req.error,
    )
```

**Step 4: Add router to `app/main.py`**

Add import and include:

```python
from app.routers import email_connections, streaming_accounts, verification

app.include_router(verification.router)
```

**Step 5: Run tests to verify they pass**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_verification.py -v`
Expected: 4 passed

**Step 6: Commit**

```bash
git add app/routers/verification.py app/main.py tests/test_verification.py
git commit -m "feat: add POST/GET /v1/verification endpoints"
```

---

### Task 5: Shares router

**Files:**
- Create: `app/routers/shares.py`
- Modify: `app/main.py` (include router)
- Test: `tests/test_shares.py`

**Step 1: Write the failing tests**

Create `tests/test_shares.py`:

```python
import uuid

from app.models import User, EmailConnection, StreamingAccount
from app.encryption import encrypt_secret
from app.auth import get_current_user


def _seed_owner_and_account(db_session):
    owner = get_current_user(db_session)
    conn = EmailConnection(
        user_id=owner.id,
        provider="gmail",
        email_address="owner@gmail.com",
        encrypted_secret_ref=encrypt_secret("fake"),
        imap_server="imap.gmail.com",
        imap_port=993,
    )
    db_session.add(conn)
    db_session.flush()

    account = StreamingAccount(
        user_id=owner.id,
        email_connection_id=conn.id,
        service_name="Hulu",
        account_label="Family Hulu",
    )
    db_session.add(account)
    db_session.flush()

    grantee = User(email="grantee@example.com", display_name="Grantee")
    db_session.add(grantee)
    db_session.commit()
    db_session.refresh(owner)
    db_session.refresh(account)
    db_session.refresh(grantee)
    return owner, account, grantee


def test_create_share(client, db_session):
    owner, account, grantee = _seed_owner_and_account(db_session)

    resp = client.post("/v1/shares", json={
        "grantee_id": str(grantee.id),
        "streaming_account_id": str(account.id),
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["owner_id"] == str(owner.id)
    assert data["grantee_id"] == str(grantee.id)
    assert data["revoked_at"] is None


def test_create_share_not_owner(client, db_session):
    """Can't share an account you don't own."""
    resp = client.post("/v1/shares", json={
        "grantee_id": str(uuid.uuid4()),
        "streaming_account_id": str(uuid.uuid4()),
    })
    assert resp.status_code == 404


def test_delete_share(client, db_session):
    owner, account, grantee = _seed_owner_and_account(db_session)

    create_resp = client.post("/v1/shares", json={
        "grantee_id": str(grantee.id),
        "streaming_account_id": str(account.id),
    })
    share_id = create_resp.json()["id"]

    del_resp = client.delete(f"/v1/shares/{share_id}")
    assert del_resp.status_code == 200
    data = del_resp.json()
    assert data["revoked_at"] is not None


def test_delete_share_not_found(client, db_session):
    resp = client.delete(f"/v1/shares/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_delete_share_already_revoked(client, db_session):
    owner, account, grantee = _seed_owner_and_account(db_session)

    create_resp = client.post("/v1/shares", json={
        "grantee_id": str(grantee.id),
        "streaming_account_id": str(account.id),
    })
    share_id = create_resp.json()["id"]

    client.delete(f"/v1/shares/{share_id}")
    resp = client.delete(f"/v1/shares/{share_id}")
    assert resp.status_code == 400
```

**Step 2: Run tests to verify they fail**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_shares.py -v`
Expected: FAIL — 404 (no route)

**Step 3: Write `app/routers/shares.py`**

```python
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, StreamingAccount, SharedAccess
from app.schemas import SharedAccessCreate, SharedAccessResponse

router = APIRouter(prefix="/v1/shares", tags=["shares"])


@router.post("", status_code=201, response_model=SharedAccessResponse)
def create_share(
    payload: SharedAccessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify current user owns the account
    account = db.query(StreamingAccount).filter(
        StreamingAccount.id == payload.streaming_account_id,
        StreamingAccount.user_id == current_user.id,
    ).first()
    if account is None:
        raise HTTPException(status_code=404, detail="streaming_account_not_found")

    # Verify grantee exists
    grantee = db.query(User).filter(User.id == payload.grantee_id).first()
    if grantee is None:
        raise HTTPException(status_code=404, detail="grantee_not_found")

    share = SharedAccess(
        owner_id=current_user.id,
        grantee_id=payload.grantee_id,
        streaming_account_id=payload.streaming_account_id,
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    return share


@router.delete("/{share_id}", response_model=SharedAccessResponse)
def revoke_share(
    share_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    share = db.query(SharedAccess).filter(
        SharedAccess.id == share_id,
        SharedAccess.owner_id == current_user.id,
    ).first()
    if share is None:
        raise HTTPException(status_code=404, detail="share_not_found")

    if share.revoked_at is not None:
        raise HTTPException(status_code=400, detail="share_already_revoked")

    share.revoked_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(share)
    return share
```

**Step 4: Add router to `app/main.py`**

Final `app/main.py` should look like:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import email_connections, streaming_accounts, verification, shares

app = FastAPI(title="Hulu Verification Code API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/v1/health")
def health():
    return {"status": "ok", "env": settings.app_env}


app.include_router(email_connections.router)
app.include_router(streaming_accounts.router)
app.include_router(verification.router)
app.include_router(shares.router)
```

**Step 5: Run tests to verify they pass**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_shares.py -v`
Expected: 5 passed

**Step 6: Commit**

```bash
git add app/routers/shares.py app/main.py tests/test_shares.py
git commit -m "feat: add POST/DELETE /v1/shares endpoints"
```

---

### Task 6: Final verification

**Step 1: Run full test suite**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/ -v`
Expected: All tests pass (~40+ tests)

**Step 2: Start server and manually verify endpoints**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m uvicorn app.main:app --port 8081`

Verify these respond:
- `GET http://localhost:8081/v1/health` → 200
- `GET http://localhost:8081/v1/streaming-accounts` → 200 (empty list)
- `GET http://localhost:8081/docs` → Swagger UI with all endpoints

**Step 3: Fix any issues and commit if needed**
