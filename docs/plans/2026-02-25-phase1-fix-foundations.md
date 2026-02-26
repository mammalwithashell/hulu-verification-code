# Phase 1: Fix Foundations Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Get the app running locally with clean deps, correct Docker setup, SQLAlchemy database layer, Alembic migrations, and a `/v1` router structure.

**Architecture:** FastAPI app with SQLAlchemy ORM (SQLite locally, PostgreSQL in prod via `DATABASE_URL`). All routes under `/v1` prefix. Alembic manages schema migrations.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, uvicorn, pydantic, python-dotenv

---

### Task 1: Fix requirements.txt

**Files:**
- Rewrite: `app/requirements.txt`

**Step 1: Rewrite requirements.txt with clean encoding and correct deps**

```txt
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.5
python-dotenv==1.0.1
html2text==2024.2.26
PyJWT==2.10.1
sqlalchemy==2.0.36
alembic==1.14.1
aiosqlite==0.20.0
psycopg2-binary==3.2.4
```

**Step 2: Verify pip can parse it**

Run: `cd C:/Users/james/Documents/hulu-verification-code && pip install -r app/requirements.txt --dry-run`
Expected: No parse errors, shows list of packages to install.

**Step 3: Commit**

```bash
git add app/requirements.txt
git commit -m "fix: rewrite requirements.txt with clean encoding and updated deps"
```

---

### Task 2: Add .env.example

**Files:**
- Create: `.env.example`

**Step 1: Create .env.example**

```env
# Database — SQLite for local dev, PostgreSQL (Supabase) in production
DATABASE_URL=sqlite:///./dev.db

# API
API_PORT=8081
APP_ENV=development
LOG_LEVEL=info

# Auth
SECRET_KEY=change-me-to-a-random-string
ALGORITHM=HS256

# IMAP defaults
IMAP_DEFAULT_PORT=993
IMAP_TIMEOUT_SECONDS=15
VERIFICATION_LOOKBACK_MINUTES=15
VERIFICATION_MAX_MESSAGES=20

# Security
SECRET_ENCRYPTION_KEY=change-me-to-a-random-string
REDACTION_ENABLED=true
```

**Step 2: Commit**

```bash
git add .env.example
git commit -m "feat: add .env.example with all config vars"
```

---

### Task 3: Add app/config.py

**Files:**
- Create: `app/config.py`

**Step 1: Write config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./dev.db"
    api_port: int = 8081
    app_env: str = "development"
    log_level: str = "info"
    secret_key: str = "change-me-to-a-random-string"
    algorithm: str = "HS256"
    imap_default_port: int = 993
    imap_timeout_seconds: int = 15
    verification_lookback_minutes: int = 15
    verification_max_messages: int = 20
    secret_encryption_key: str = "change-me-to-a-random-string"
    redaction_enabled: bool = True

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
```

Note: `pydantic-settings` is a separate package from `pydantic`. Add it to requirements.txt:
```
pydantic-settings==2.7.1
```

**Step 2: Commit**

```bash
git add app/config.py app/requirements.txt
git commit -m "feat: add typed config with pydantic-settings"
```

---

### Task 4: Add app/database.py

**Files:**
- Create: `app/database.py`

**Step 1: Write the failing test**

Create `tests/test_database.py`:

```python
from app.database import engine, SessionLocal, Base


def test_engine_is_created():
    assert engine is not None


def test_session_factory_returns_session():
    session = SessionLocal()
    try:
        assert session is not None
        assert session.bind is not None
    finally:
        session.close()


def test_base_has_metadata():
    assert Base.metadata is not None
```

Also create `tests/__init__.py` (empty) and `tests/conftest.py`:

```python
import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
```

**Step 2: Run test to verify it fails**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_database.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.database'`

**Step 3: Write app/database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 4: Run test to verify it passes**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_database.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add app/database.py tests/
git commit -m "feat: add SQLAlchemy database layer with config-driven URL"
```

---

### Task 5: Set up Alembic

**Files:**
- Create: `alembic.ini` (generated)
- Create: `alembic/env.py` (customized)
- Create: `alembic/versions/` (empty dir)

**Step 1: Initialize Alembic**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m alembic init alembic`
Expected: Creates `alembic.ini` and `alembic/` directory.

**Step 2: Edit alembic/env.py to use app config and Base**

Replace the `sqlalchemy.url` config in `alembic/env.py`:
- Import `from app.config import settings` and `from app.database import Base`
- Set `config.set_main_option("sqlalchemy.url", settings.database_url)`
- Set `target_metadata = Base.metadata`

Key changes in `alembic/env.py`:

```python
from app.config import settings
from app.database import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata
```

**Step 3: Edit alembic.ini**

Change the `sqlalchemy.url` line to a placeholder (env.py overrides it):
```ini
sqlalchemy.url = sqlite:///./dev.db
```

**Step 4: Verify alembic can run**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m alembic heads`
Expected: No errors, shows empty heads (no migrations yet).

**Step 5: Commit**

```bash
git add alembic.ini alembic/
git commit -m "feat: initialize Alembic with config-driven database URL"
```

---

### Task 6: Restructure app/main.py

**Files:**
- Rewrite: `app/main.py`

**Step 1: Write the failing test**

Create `tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_root_returns_not_found():
    response = client.get("/")
    assert response.status_code == 404


def test_old_code_endpoint_gone():
    response = client.get("/code")
    assert response.status_code == 404
```

**Step 2: Run test to verify it fails**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_health.py -v`
Expected: FAIL — old `/code` endpoint still exists, no `/v1/health`.

**Step 3: Rewrite app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

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
```

**Step 4: Run test to verify it passes**

Run: `cd C:/Users/james/Documents/hulu-verification-code && python -m pytest tests/test_health.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add app/main.py tests/test_health.py
git commit -m "feat: restructure main.py with /v1 router and health endpoint"
```

---

### Task 7: Fix dockerfile

**Files:**
- Rewrite: `dockerfile`

**Step 1: Rewrite dockerfile**

```dockerfile
FROM python:3.12-slim

RUN adduser --disabled-password --gecos "" appuser

WORKDIR /code

COPY app/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY alembic.ini /code/alembic.ini
COPY alembic /code/alembic
COPY app /code/app

USER appuser

EXPOSE 8081

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8081/v1/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
```

**Step 2: Verify docker build succeeds**

Run: `cd C:/Users/james/Documents/hulu-verification-code && docker build -t hulu-verification-code .`
Expected: Build completes without errors.

**Step 3: Commit**

```bash
git add dockerfile
git commit -m "fix: correct dockerfile paths, port 8081, non-root user, healthcheck"
```

---

### Task 8: Add .gitignore entries and clean up

**Files:**
- Modify: `.gitignore`

**Step 1: Update .gitignore**

Add these entries:
```
*.db
test.db
dev.db
```

**Step 2: Remove stale root-level files from git tracking**

The original `email_client.py`, `main.py`, `models.py`, `servers.py` were moved to `app/` but git still shows them as deleted. Stage the deletions:

```bash
git add email_client.py main.py models.py servers.py
```

**Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: update gitignore, remove stale root-level files"
```

---

### Task 9: Final verification

**Step 1: Install deps and run all tests**

Run:
```bash
cd C:/Users/james/Documents/hulu-verification-code
pip install -r app/requirements.txt
python -m pytest tests/ -v
```
Expected: All tests pass.

**Step 2: Start the server locally**

Run:
```bash
cd C:/Users/james/Documents/hulu-verification-code
uvicorn app.main:app --host 0.0.0.0 --port 8081
```
Expected: Server starts on port 8081. `GET http://localhost:8081/v1/health` returns `{"status": "ok", "env": "development"}`.

**Step 3: Final commit if any fixups needed**
