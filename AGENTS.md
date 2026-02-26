# AGENTS.md

## Project Purpose
This project is a multi-user verification-code assistant for streaming accounts. It lets users retrieve verification codes from their own email inboxes or from inboxes they are explicitly authorized to access, while managing shared streaming account records (for example Netflix, Hulu, HBO Max, and others) mapped to the email source used for verification.

## Non-Negotiable Safety and Consent Rules
- Explicit consent from the account and email owner is required before any access.
- Unauthorized mailbox access is prohibited.
- Credential stuffing, scraping, bypass behavior, and stealth automation are prohibited.
- Never store or expose plaintext secrets in logs, commits, screenshots, or API responses.
- Prefer app passwords and IMAP-specific credentials instead of primary account passwords when available.
- Follow provider Terms of Service and applicable local laws.

## System Scope
### In Scope
- Account catalog: service name, login identifier, and linked email source.
- Verification-code retrieval from the linked mailbox.
- Multi-user sharing model with explicit owner-managed permissions.

### Out of Scope
- Breaking MFA or bypassing security protections (including CAPTCHA bypass).
- Credential exfiltration.
- Hidden/background mailbox polling without user intent.

## Current Repo Reality (Grounding)
- Existing backend: FastAPI in `app/main.py` with `GET /code`.
- Existing email retrieval/parser logic: `app/email_client.py`.
- Existing IMAP server mapping: `app/servers.py` (`gmail`, `yahoo`).
- Existing technical debt to track: current `dockerfile` copies `./requirements.txt`, but repository requirements currently live at `app/requirements.txt`.

## Target Architecture (Implementation Guidance)
- Backend service default port: `8081`.
- Frontend service default port: `5174`.
- Python/FastAPI backend remains the baseline.

### Core Entities
- `users`
- `email_connections`
  - fields: `id`, `owner_user_id`, `email_address`, `imap_host`, `imap_port`, `auth_type`, `encrypted_secret_ref`, `created_at`
- `streaming_accounts`
  - fields: `id`, `owner_user_id`, `service_name`, `login_identifier`, `email_connection_id`, `created_at`
- `shared_access`
  - fields: `id`, `streaming_account_id`, `owner_user_id`, `shared_with_user_id`, `permissions`, `created_at`, `revoked_at`
- `verification_requests`
  - fields: `id`, `streaming_account_id`, `requested_by_user_id`, `status`, `created_at`, `completed_at`
- `verification_events`
  - fields: `id`, `verification_request_id`, `event_type`, `message_redacted`, `created_at`

### Secret Handling
- Encrypt secret material at rest.
- Never return mailbox password or app password in API responses.
- Redact secrets and token-like strings in logs.
- Keep least-privilege data access controls in storage and service layers.

## Proposed API Interfaces
Base namespace: `/v1`

### `POST /v1/email-connections/test`
Purpose: validate IMAP connectivity and credentials before saving.

Example request:
```json
{
  "email_address": "owner@example.com",
  "imap_host": "imap.gmail.com",
  "imap_port": 993,
  "auth_type": "app_password",
  "secret": "app-password-value"
}
```

Example response:
```json
{
  "ok": true,
  "message": "IMAP login successful"
}
```

### `POST /v1/streaming-accounts`
Purpose: store a streaming account linked to an email connection.

Example request:
```json
{
  "service_name": "Hulu",
  "login_identifier": "friend_login@example.com",
  "email_connection_id": "ec_123"
}
```

Example response:
```json
{
  "id": "sa_123",
  "service_name": "Hulu",
  "login_identifier": "friend_login@example.com",
  "email_connection_id": "ec_123"
}
```

### `GET /v1/streaming-accounts`
Purpose: list owner and shared streaming accounts visible to the authenticated user.

### `POST /v1/verification/request`
Purpose: start retrieval of the most recent valid verification code for an authorized account.

Example request:
```json
{
  "streaming_account_id": "sa_123"
}
```

Example response:
```json
{
  "request_id": "vr_123",
  "status": "processing"
}
```

### `GET /v1/verification/{request_id}`
Purpose: retrieve request status and normalized verification result.

Normalized result contract:
```json
{
  "code": "123456",
  "source_service": "Hulu",
  "received_at": "2026-02-26T20:30:00Z",
  "confidence": "high",
  "error": null
}
```

### `POST /v1/shares`
Purpose: grant a user permission to request verification codes for an account.

Example request:
```json
{
  "streaming_account_id": "sa_123",
  "shared_with_user_id": "user_456",
  "permissions": ["request_verification_code"]
}
```

### `DELETE /v1/shares/{share_id}`
Purpose: revoke previously granted shared access.

## Code Extraction Rules for Verification
- Query only recent emails in a constrained time window (default 15 minutes, configurable).
- Filter by provider-specific sender and subject patterns before parsing.
- Parse both HTML and plain text parts; normalize to text before regex extraction.
- Use provider-specific regex first, then fallback generic OTP regex.
- Reject stale candidates outside the recency window.
- Return normalized output:
  - `{ code, source_service, received_at, confidence, error }`

## Operational Defaults
- API service binds to `0.0.0.0:8081` in local/dev docs and examples.
- Web service binds to `0.0.0.0:5174` in local/dev docs and examples.
- Do not use ports `8000` or `5173` in examples for this repo.
- All secrets/config must come from environment variables.

### `.env.example` Keys (Documentation Contract)
```env
API_PORT=8081
WEB_PORT=5174
APP_ENV=development
LOG_LEVEL=info

SUPABASE_URL=
SUPABASE_KEY=
SECRET_KEY=
ALGORITHM=HS256

IMAP_DEFAULT_PORT=993
IMAP_TIMEOUT_SECONDS=15
VERIFICATION_LOOKBACK_MINUTES=15
VERIFICATION_MAX_MESSAGES=20

SECRET_ENCRYPTION_KEY=
REDACTION_ENABLED=true
```

## Testing and Acceptance Criteria
- Unit tests:
  - parse/extract OTP codes from multiple real-world template variants.
  - sender/subject filters and fallback regex behavior.
- Integration tests:
  - IMAP login/test flow (mocked server or fixture).
  - mailbox search and latest-code selection behavior.
- AuthZ tests:
  - owner can request their account code.
  - shared user can request only granted accounts.
  - unauthorized user is denied.
- Security tests:
  - no plaintext secret appears in logs or API responses.
- Port policy checks:
  - startup and docs examples use `8081`/`5174`, never `8000`/`5173`.

## Contribution Rules for Agents
- Keep changes minimal, reversible, and scoped to the requested behavior.
- Add or update tests when behavior changes.
- Document every new env var, API field, and data shape change.
- Preserve consent-first guardrails and refuse unsafe implementation requests.
