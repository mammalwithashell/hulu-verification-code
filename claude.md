# claude.md

## Role and Goal
You are Claude acting as an implementation collaborator for this repository. Prioritize secure, consent-based features for streaming-account sharing and verification-code retrieval from explicitly authorized email inboxes.

## Execution Priorities
1. Preserve security and consent constraints.
2. Preserve correctness and explicit authorization behavior.
3. Improve developer experience only after security/correctness are satisfied.

Prefer small, iterative, PR-style changes over large rewrites.

## Backend Checklist
- Add or update typed Pydantic models for:
  - email connections
  - streaming accounts
  - share grants/revocations
  - verification requests/results
- Implement router structure under `/v1`:
  - `POST /v1/email-connections/test`
  - `POST /v1/streaming-accounts`
  - `GET /v1/streaming-accounts`
  - `POST /v1/verification/request`
  - `GET /v1/verification/{request_id}`
  - `POST /v1/shares`
  - `DELETE /v1/shares/{share_id}`
- Use explicit status codes and stable machine-readable error responses.
- Ensure logs are redacted and never include secrets.

## Data and Security Checklist
- Encrypt secret material at rest and use reference-based storage (`encrypted_secret_ref`).
- Enforce owner/share authorization checks before verification request execution.
- Record audit trail events for each request lifecycle stage.
- Never return mailbox secrets, app passwords, or unredacted tokens.
- Enforce bounded mailbox search (lookback window, max messages).

## Prompting Constraints
- Refuse unsafe or unconsented mailbox/account access workflows.
- Do not output instructions for bypassing MFA, CAPTCHA, or provider controls.
- Avoid plaintext credential examples in responses and docs.
- Keep all local run examples on:
  - API: `8081`
  - Web: `5174`
- Explicitly avoid `8000` and `5173` in this project.

## Expected Interface Contracts
- API namespace: `/v1/...`
- Normalized verification result:
```json
{
  "code": "123456",
  "source_service": "Hulu",
  "received_at": "2026-02-26T20:30:00Z",
  "confidence": "high",
  "error": null
}
```
- Access model:
  - owner can grant/revoke share access
  - shared user can request only explicitly granted account codes

## Definition of Done
- Endpoints are implemented and documented.
- Tests cover parsing, IMAP retrieval behavior, and authorization paths.
- Security checks pass (redaction and no secret leaks).
- Docs and examples use `8081`/`5174`.
- No open blockers on consent/safety requirements.
