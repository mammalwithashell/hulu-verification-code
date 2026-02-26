# gemini.md

## Mission Context
Build and maintain a secure verification-code request workflow for shared streaming accounts, where access is limited to owners and explicitly authorized collaborators.

## Planning Heuristics
Break work into vertical slices and validate each slice before moving forward:
1. Account storage slice
  - create and list streaming accounts linked to email connections
2. Sharing permissions slice
  - grant/revoke and enforce owner-managed access
3. Verification request pipeline slice
  - request, process, and fetch normalized verification results
4. Observability and hardening slice
  - auditing, redaction, and bounded mailbox scanning

## Implementation Constraints
- Consent-first boundaries are mandatory.
- No unsafe auth bypass, no stealth mailbox access, no CAPTCHA/MFA bypass guidance.
- Strict secret handling:
  - encrypt at rest
  - redact in logs
  - do not return secrets in API payloads
- Keep data retention minimal and purpose-bound.
- Use these local ports:
  - API `8081`
  - Web `5174`
- Do not use `8000` or `5173` for this project.

## Validation Matrix
### Functional Scenarios
- Owner requests code for owned account: success path.
- Shared user requests code for permitted account: success path.
- Unauthorized user requests code: access denied.
- Stale/no-code mailbox case: graceful failure with structured error.

### Non-Functional Scenarios
- Redaction check: no secret material in logs.
- Error contract check: consistent machine-readable API errors.
- Port compliance check: docs and startup commands use `8081`/`5174`.

## Interface Contracts to Preserve
- API namespace: `/v1/...`
- Core endpoints:
  - `POST /v1/email-connections/test`
  - `POST /v1/streaming-accounts`
  - `GET /v1/streaming-accounts`
  - `POST /v1/verification/request`
  - `GET /v1/verification/{request_id}`
  - `POST /v1/shares`
  - `DELETE /v1/shares/{share_id}`
- Normalized verification response:
```json
{
  "code": "123456",
  "source_service": "Hulu",
  "received_at": "2026-02-26T20:30:00Z",
  "confidence": "high",
  "error": null
}
```

## Output Style for Gemini
- Always state assumptions explicitly.
- Provide schema/API diffs when proposing structural changes.
- Include rollback notes for risky migrations or permission-model updates.
- Prefer concise, testable implementation steps over broad rewrites.
