import uuid
from datetime import datetime

from pydantic import BaseModel


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
