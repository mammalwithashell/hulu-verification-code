import uuid

from app.models import EmailConnection, StreamingAccount
from app.encryption import encrypt_secret
from app.auth import get_current_user


def _seed_account(db_session):
    user = get_current_user(db_session)
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
    return user, account


def test_create_verification_request(client, db_session):
    user, account = _seed_account(db_session)
    resp = client.post("/v1/verification/request", json={
        "streaming_account_id": str(account.id),
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert data["streaming_account_id"] == str(account.id)
    assert "id" in data


def test_create_verification_request_bad_account(client, db_session):
    resp = client.post("/v1/verification/request", json={
        "streaming_account_id": str(uuid.uuid4()),
    })
    assert resp.status_code == 404


def test_get_verification_request(client, db_session):
    user, account = _seed_account(db_session)
    create_resp = client.post("/v1/verification/request", json={
        "streaming_account_id": str(account.id),
    })
    request_id = create_resp.json()["id"]

    resp = client.get(f"/v1/verification/{request_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == request_id
    assert data["status"] == "pending"


def test_get_verification_request_not_found(client, db_session):
    resp = client.get(f"/v1/verification/{uuid.uuid4()}")
    assert resp.status_code == 404
