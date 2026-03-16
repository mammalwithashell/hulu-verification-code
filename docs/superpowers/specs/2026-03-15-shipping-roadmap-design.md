# Shipping Roadmap: Hulu Verification Code Assistant

**Date:** 2026-03-15
**Goal:** Deploy a functional multi-user verification-code retrieval service for ~20 users on a DigitalOcean Droplet.

## Context

Phases 1-3 are complete on the `phase1/fix-foundations` branch:
- FastAPI backend with SQLAlchemy ORM, Alembic migrations, JWT auth
- All 6 data models (User, EmailConnection, StreamingAccount, SharedAccess, VerificationRequest, VerificationEvent)
- All 7 API endpoints stubbed/implemented under `/v1`
- Pydantic schemas, Fernet encryption, bcrypt password hashing
- 56 passing tests covering models, schemas, auth, authorization, and endpoint behavior

The existing `email_client.py` is legacy code (env-var-driven, single mailbox). It needs to be replaced with a per-connection IMAP client.

### Deliberate Deviations from AGENTS.md

The current data models diverge from the AGENTS.md entity spec in a few places. These are intentional simplifications that should be reconciled:

- **`SharedAccess` is missing a `permissions` field.** AGENTS.md specifies `permissions` (e.g., `["request_verification_code"]`). For MVP with ~20 users, a share grant implies full verification access. The `permissions` column should be added in Phase 5 to support future granularity, defaulting to `["request_verification_code"]`.
- **`EmailConnection` is missing an `auth_type` field.** AGENTS.md specifies `auth_type` (e.g., `"app_password"`). This should be added in Phase 5 since the IMAP client may need to distinguish app passwords from OAuth flows.
- **`StreamingAccount.account_label` vs AGENTS.md's `login_identifier`.** The implementation uses `account_label` as a more general name. This is intentional — `account_label` covers cases where the login identifier isn't meaningful to display.
- **`user_id` vs `owner_user_id`, `grantee_id` vs `shared_with_user_id`.** Shortened for code ergonomics. The semantics are identical.

## Target Architecture

- **Backend:** FastAPI on port 8081
- **Frontend:** React (Vite) on port 5174 in dev, static build served by reverse proxy in prod
- **Database:** SQLite with WAL mode on a Docker volume (sufficient for ~20 users)
- **Deployment:** Single DigitalOcean Droplet ($6/mo), Docker Compose, Caddy for HTTPS
- **Domain:** DigitalOcean-provided URL initially

## Core User Flow

1. Account owner registers, connects their email inbox (IMAP credentials encrypted at rest)
2. Owner adds streaming accounts linked to that email connection
3. Owner shares access with other users by granting them permission
4. Shared user triggers a verification code request
5. System connects to the owner's email via IMAP, finds the latest code, returns it
6. Shared user sees the code and can log into the streaming service

---

## Phase 4: Deploy Skeleton

**Goal:** Get the existing API running on a DigitalOcean Droplet with Docker before adding more features. Proves the deployment pipeline early.

### Deliverables
- Create Dockerfile (one exists on the branch already but verify it's correct)
- Docker Compose config: FastAPI container + SQLite volume
- Alembic migrations run on container startup
- Environment variables configured on the Droplet (SECRET_KEY, SECRET_ENCRYPTION_KEY, DATABASE_URL)
- `/v1/health`, register, and login verified working on the live URL

### Pre-requisite
- Merge `phase1/fix-foundations` branch (with all Phase 2/3 work) to main

### Technical Notes
- SQLite with WAL mode for concurrent read tolerance
- SQLAlchemy pool configured with `StaticPool` or serialized writes for SQLite safety
- No HTTPS yet (added in Phase 7)

---

## Phase 5: Real IMAP Integration

**Goal:** Wire actual email retrieval into the API so verification requests return real codes.

### Deliverables

#### Data Model Additions
- Add `permissions` column to `SharedAccess` (JSON list, default `["request_verification_code"]`)
- Add `auth_type` column to `EmailConnection` (string, e.g., `"app_password"`)
- Alembic migration for both changes
- Update Pydantic schemas to include new fields

#### IMAP Client Rewrite
- New `app/imap_client.py` replacing the legacy `email_client.py`
- Accepts connection params (host, port, credentials) as arguments, not env vars
- Decrypts `encrypted_secret_ref` at call time, never logs or returns the secret
- Configurable timeout (`IMAP_TIMEOUT_SECONDS`, default 15s)

#### Email Connection Testing
- `POST /v1/email-connections/test` performs a real IMAP login and disconnects
- Returns structured success/failure (not a stub)

#### Bounded Mailbox Search
- Only scans the last N messages (`VERIFICATION_MAX_MESSAGES`, default 20)
- Only considers messages within the lookback window (`VERIFICATION_LOOKBACK_MINUTES`, default 15)
- Filters by provider-specific sender addresses and subject patterns before parsing

#### OTP Parsing
- Provider-specific regex patterns (Hulu, Netflix, HBO Max, Disney+, etc.)
- Generic fallback: 4-8 digit code extraction
- Parse both HTML and plain text MIME parts
- Return normalized result: `{ code, source_service, received_at, confidence, error }`

#### Verification Flow Completion
- `POST /v1/verification/request` triggers real IMAP fetch, updates status to completed/failed
- Audit events recorded: `requested`, `imap_connected`, `code_found`/`code_not_found`, `completed`/`failed`

#### Tests
- Unit tests for OTP parsing across provider templates
- Integration tests with mocked IMAP server
- Timeout and error handling tests
- Security tests: verify no plaintext secrets in API responses or logs
- Port policy tests: verify startup/docs use 8081/5174, never 8000/5173

---

## Phase 6: React Frontend

**Goal:** Functional React UI — forms, lists, status displays. Minimal styling, no design system.

### Deliverables

#### Project Setup
- Vite + React, dev server on port 5174
- API client module targeting `/v1` endpoints
- Token storage and auth header injection

#### Pages
- **Auth:** Register and login forms
- **Email Connections:** Add connection form (provider, email, app password, IMAP host/port), test button, list connections
- **Streaming Accounts:** Add account form (service name, label, linked email connection), list accounts
- **Sharing:** Grant access form (user email, select account), revoke button, list active shares
- **Verification:** Trigger code request button, poll for result, display code prominently

#### Build & Serve
- Production build output served by the reverse proxy on the Droplet alongside the API

---

## Phase 7: Production Hardening

**Goal:** Minimum viability for real daily use by trusted users.

### Deliverables

#### Security
- HTTPS via Let's Encrypt (Caddy as reverse proxy handles this automatically)
- Log redaction middleware: strip passwords, tokens, and secret-like strings from all log output
- Rate limiting on `/v1/auth/*` and `/v1/verification/*` endpoints

#### Infrastructure
- Docker Compose: API + frontend static files + Caddy + SQLite volume
- `.env.production.example` documenting all required vars

#### Frontend Resilience
- Handle API connection failures gracefully
- Handle expired JWT tokens (redirect to login)
- Loading and error states on all async operations

### Explicitly Not Included (YAGNI)
- Monitoring/alerting dashboards
- CI/CD pipeline
- Automated database backups
- Custom domain or DNS setup

---

## Dependency Graph

```
Phase 4 (Deploy Skeleton)
    └── Phase 5 (IMAP Integration)
            └── Phase 6 (React Frontend)
                    └── Phase 7 (Production Hardening)
```

Each phase is deployed incrementally to the Droplet as it completes.

**Note:** Phase 6 frontend development can begin in parallel with Phase 5 since the API stubs already return structured responses. However, full end-to-end testing requires Phase 5 to be complete.

## Risks

| Risk | Mitigation |
|------|------------|
| Email providers blocking IMAP logins | Document app password setup per provider; test with Gmail and Yahoo first |
| SQLite write contention under concurrent verification requests | WAL mode + serialized writes; monitor and migrate to Postgres if needed |
| IMAP fetch latency causing request timeouts | Async background processing if sync approach proves too slow |
| Provider-specific email templates changing | Generic fallback regex; log parse failures for iteration |
