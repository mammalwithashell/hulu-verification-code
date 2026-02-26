import uuid

from app.models import User, EmailConnection, StreamingAccount
from app.encryption import encrypt_secret
from app.auth import get_current_user


def _seed_owner_and_account(db_session):
    owner = get_current_user(db_session)
    conn = EmailConnection(
        user_id=owner.id,
        provider="gmail",
        email_address="owner@gmail.com",
        encrypted_secret_ref=encrypt_secret("fake"),
        imap_server="imap.gmail.com",
        imap_port=993,
    )
    db_session.add(conn)
    db_session.flush()

    account = StreamingAccount(
        user_id=owner.id,
        email_connection_id=conn.id,
        service_name="Hulu",
        account_label="Family Hulu",
    )
    db_session.add(account)
    db_session.flush()

    grantee = User(email="grantee@example.com", display_name="Grantee")
    db_session.add(grantee)
    db_session.commit()
    db_session.refresh(owner)
    db_session.refresh(account)
    db_session.refresh(grantee)
    return owner, account, grantee


def test_create_share(client, db_session):
    owner, account, grantee = _seed_owner_and_account(db_session)

    resp = client.post("/v1/shares", json={
        "grantee_id": str(grantee.id),
        "streaming_account_id": str(account.id),
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["owner_id"] == str(owner.id)
    assert data["grantee_id"] == str(grantee.id)
    assert data["revoked_at"] is None


def test_create_share_not_owner(client, db_session):
    resp = client.post("/v1/shares", json={
        "grantee_id": str(uuid.uuid4()),
        "streaming_account_id": str(uuid.uuid4()),
    })
    assert resp.status_code == 404


def test_delete_share(client, db_session):
    owner, account, grantee = _seed_owner_and_account(db_session)

    create_resp = client.post("/v1/shares", json={
        "grantee_id": str(grantee.id),
        "streaming_account_id": str(account.id),
    })
    share_id = create_resp.json()["id"]

    del_resp = client.delete(f"/v1/shares/{share_id}")
    assert del_resp.status_code == 200
    data = del_resp.json()
    assert data["revoked_at"] is not None


def test_delete_share_not_found(client, db_session):
    resp = client.delete(f"/v1/shares/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_delete_share_already_revoked(client, db_session):
    owner, account, grantee = _seed_owner_and_account(db_session)

    create_resp = client.post("/v1/shares", json={
        "grantee_id": str(grantee.id),
        "streaming_account_id": str(account.id),
    })
    share_id = create_resp.json()["id"]

    client.delete(f"/v1/shares/{share_id}")
    resp = client.delete(f"/v1/shares/{share_id}")
    assert resp.status_code == 400
