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
