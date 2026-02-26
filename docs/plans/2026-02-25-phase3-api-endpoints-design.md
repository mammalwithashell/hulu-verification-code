# Phase 3: Core API Endpoints Design

**Goal:** Implement all 7 `/v1` endpoints with stub auth, wired to real models and database.

## Router Structure

- `app/routers/email_connections.py` — email connection endpoints
- `app/routers/streaming_accounts.py` — streaming account CRUD
- `app/routers/verification.py` — verification request/result
- `app/routers/shares.py` — grant/revoke shared access

## Stub Auth (`app/auth.py`)

`get_current_user()` dependency returns a hardcoded test user. Phase 4 swaps for real JWT.

## Endpoints

| Method | Path | Behavior |
|--------|------|----------|
| POST | /v1/email-connections/test | Validate IMAP creds shape, stub connection test |
| POST | /v1/streaming-accounts | Create account linked to email connection |
| GET | /v1/streaming-accounts | List owned + shared accounts |
| POST | /v1/verification/request | Create request + audit event, status pending |
| GET | /v1/verification/{request_id} | Return status/result, auth check |
| POST | /v1/shares | Owner grants access |
| DELETE | /v1/shares/{share_id} | Soft-delete via revoked_at |

## Error Format

```json
{"detail": "streaming_account_not_found", "message": "Streaming account does not exist"}
```

## Deferred

- Actual IMAP retrieval (Phase 5)
- Real auth (Phase 4)
- Real IMAP connection test (Phase 5)

## Testing

Per-router test files, in-memory SQLite via overridden get_db dependency.
