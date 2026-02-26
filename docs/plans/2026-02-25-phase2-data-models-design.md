# Phase 2: Data Models + Storage Design

**Goal:** Define all SQLAlchemy models, add Fernet encryption for secrets, generate the initial Alembic migration.

## Entities

### users
- `id` (UUID, PK), `email` (unique), `display_name`, `created_at`

### email_connections
- `id` (UUID, PK), `user_id` (FK → users), `provider` (gmail/yahoo/etc), `email_address`, `encrypted_secret_ref` (Fernet-encrypted app password), `imap_server`, `imap_port`, `is_verified` (bool), `created_at`

### streaming_accounts
- `id` (UUID, PK), `user_id` (FK → users), `email_connection_id` (FK → email_connections), `service_name` (Hulu/Netflix/etc), `account_label`, `created_at`

### shared_access
- `id` (UUID, PK), `owner_id` (FK → users), `grantee_id` (FK → users), `streaming_account_id` (FK → streaming_accounts), `created_at`, `revoked_at` (nullable)

### verification_requests
- `id` (UUID, PK), `requester_id` (FK → users), `streaming_account_id` (FK → streaming_accounts), `status` (pending/completed/failed), `code`, `confidence`, `error`, `requested_at`, `completed_at`

### verification_events
- `id` (UUID, PK), `verification_request_id` (FK → verification_requests), `event_type` (requested/searching/found/failed/etc), `detail`, `created_at`

## Encryption

- Fernet symmetric encryption via `cryptography` library
- `SECRET_ENCRYPTION_KEY` from .env used to derive Fernet key
- `encrypt_secret(plaintext) → ciphertext`, `decrypt_secret(ciphertext) → plaintext`
- Secrets never logged or returned in API responses

## Pydantic Schemas

- Request/response models for each entity
- `encrypted_secret_ref` never in response models
- Only `is_verified` and `provider` exposed for email connections

## Files

- `app/models.py` — SQLAlchemy ORM models
- `app/schemas.py` — Pydantic request/response schemas
- `app/encryption.py` — Fernet helpers
- `alembic/versions/` — initial migration
- `app/requirements.txt` — add `cryptography`
- `tests/` — model, encryption, schema tests
