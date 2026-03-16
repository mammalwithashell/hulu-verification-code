import uuid

from app.models import EmailConnection, StreamingAccount, SharedAccess
from app.encryption import encrypt_secret
from app.auth import hash_password
from tests.conftest import create_test_user, auth_header


def _seed_account(db_session):
    user, token = create_test_user(db_session)
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
    return user, token, account


def test_create_verification_request(client, db_session):
    user, token, account = _seed_account(db_session)
    resp = client.post("/v1/verification/request", json={
        "streaming_account_id": str(account.id),
    }, headers=auth_header(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert data["streaming_account_id"] == str(account.id)
    assert "id" in data


def test_create_verification_request_bad_account(client, db_session, auth_headers):
    resp = client.post("/v1/verification/request", json={
        "streaming_account_id": str(uuid.uuid4()),
    }, headers=auth_headers)
    assert resp.status_code == 404


def test_get_verification_request(client, db_session):
    user, token, account = _seed_account(db_session)
    headers = auth_header(token)
    create_resp = client.post("/v1/verification/request", json={
        "streaming_account_id": str(account.id),
    }, headers=headers)
    request_id = create_resp.json()["id"]

    resp = client.get(f"/v1/verification/{request_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == request_id
    assert data["status"] == "pending"


def test_get_verification_request_not_found(client, db_session, auth_headers):
    resp = client.get(f"/v1/verification/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


# --- Authorization tests ---

def test_shared_user_can_request_verification(client, db_session):
    """A user with an active share grant can request verification codes."""
    owner, owner_token, account = _seed_account(db_session)
    grantee, grantee_token = create_test_user(
        db_session, email="grantee@example.com", display_name="Grantee"
    )

    # Owner grants access
    share = SharedAccess(
        owner_id=owner.id,
        grantee_id=grantee.id,
        streaming_account_id=account.id,
    )
    db_session.add(share)
    db_session.commit()

    resp = client.post("/v1/verification/request", json={
        "streaming_account_id": str(account.id),
    }, headers=auth_header(grantee_token))
    assert resp.status_code == 201


def test_unauthorized_user_cannot_request_verification(client, db_session):
    """A user with no share grant is denied."""
    owner, owner_token, account = _seed_account(db_session)
    stranger, stranger_token = create_test_user(
        db_session, email="stranger@example.com", display_name="Stranger"
    )

    resp = client.post("/v1/verification/request", json={
        "streaming_account_id": str(account.id),
    }, headers=auth_header(stranger_token))
    assert resp.status_code == 404


def test_revoked_share_denies_verification(client, db_session):
    """A user whose share was revoked is denied."""
    from datetime import datetime, timezone

    owner, owner_token, account = _seed_account(db_session)
    grantee, grantee_token = create_test_user(
        db_session, email="revoked@example.com", display_name="Revoked"
    )

    share = SharedAccess(
        owner_id=owner.id,
        grantee_id=grantee.id,
        streaming_account_id=account.id,
        revoked_at=datetime.now(timezone.utc),
    )
    db_session.add(share)
    db_session.commit()

    resp = client.post("/v1/verification/request", json={
        "streaming_account_id": str(account.id),
    }, headers=auth_header(grantee_token))
    assert resp.status_code == 404


def test_unauthenticated_request_denied(client):
    """No token at all returns 401."""
    resp = client.post("/v1/verification/request", json={
        "streaming_account_id": str(uuid.uuid4()),
    })
    assert resp.status_code == 401
