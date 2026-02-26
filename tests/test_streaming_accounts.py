import uuid

from app.models import EmailConnection
from app.encryption import encrypt_secret
from app.auth import get_current_user


def _seed_email_connection(db_session, user):
    conn = EmailConnection(
        user_id=user.id,
        provider="gmail",
        email_address="test@gmail.com",
        encrypted_secret_ref=encrypt_secret("fake-password"),
        imap_server="imap.gmail.com",
        imap_port=993,
    )
    db_session.add(conn)
    db_session.commit()
    db_session.refresh(conn)
    return conn


def test_create_streaming_account(client, db_session):
    user = get_current_user(db_session)
    conn = _seed_email_connection(db_session, user)

    resp = client.post("/v1/streaming-accounts", json={
        "email_connection_id": str(conn.id),
        "service_name": "Hulu",
        "account_label": "Family Hulu",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["service_name"] == "Hulu"
    assert data["account_label"] == "Family Hulu"
    assert "id" in data


def test_create_streaming_account_bad_connection(client, db_session):
    resp = client.post("/v1/streaming-accounts", json={
        "email_connection_id": str(uuid.uuid4()),
        "service_name": "Hulu",
        "account_label": "Family Hulu",
    })
    assert resp.status_code == 404


def test_list_streaming_accounts_empty(client):
    resp = client.get("/v1/streaming-accounts")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_streaming_accounts_returns_owned(client, db_session):
    user = get_current_user(db_session)
    conn = _seed_email_connection(db_session, user)

    client.post("/v1/streaming-accounts", json={
        "email_connection_id": str(conn.id),
        "service_name": "Hulu",
        "account_label": "Family Hulu",
    })

    resp = client.get("/v1/streaming-accounts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["service_name"] == "Hulu"
