from datetime import timedelta

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.models import User
from tests.conftest import auth_header, create_test_user


# --- Password hashing ---

def test_hash_and_verify_password():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


# --- Registration ---

def test_register_success(client):
    resp = client.post("/v1/auth/register", json={
        "email": "new@example.com",
        "display_name": "New User",
        "password": "strongpass123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client, db_session):
    create_test_user(db_session, email="dup@example.com")
    resp = client.post("/v1/auth/register", json={
        "email": "dup@example.com",
        "display_name": "Dup",
        "password": "pass123",
    })
    assert resp.status_code == 409


def test_register_invalid_email(client):
    resp = client.post("/v1/auth/register", json={
        "email": "not-an-email",
        "display_name": "Bad",
        "password": "pass123",
    })
    assert resp.status_code == 422


# --- Login ---

def test_login_success(client, db_session):
    create_test_user(db_session, email="login@example.com", password="mypass")
    resp = client.post("/v1/auth/login", json={
        "email": "login@example.com",
        "password": "mypass",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


def test_login_wrong_password(client, db_session):
    create_test_user(db_session, email="login2@example.com", password="correct")
    resp = client.post("/v1/auth/login", json={
        "email": "login2@example.com",
        "password": "wrong",
    })
    assert resp.status_code == 401


def test_login_nonexistent_user(client):
    resp = client.post("/v1/auth/login", json={
        "email": "ghost@example.com",
        "password": "pass",
    })
    assert resp.status_code == 401


# --- Token validation ---

def test_authenticated_endpoint_with_valid_token(client, db_session):
    _, token = create_test_user(db_session)
    resp = client.get("/v1/streaming-accounts", headers=auth_header(token))
    assert resp.status_code == 200


def test_authenticated_endpoint_without_token(client):
    resp = client.get("/v1/streaming-accounts")
    assert resp.status_code == 401


def test_authenticated_endpoint_with_bad_token(client):
    resp = client.get(
        "/v1/streaming-accounts",
        headers=auth_header("not.a.real.token"),
    )
    assert resp.status_code == 401


def test_authenticated_endpoint_with_expired_token(client, db_session):
    user, _ = create_test_user(db_session)
    expired_token = create_access_token(
        str(user.id), expires_delta=timedelta(seconds=-1)
    )
    resp = client.get(
        "/v1/streaming-accounts",
        headers=auth_header(expired_token),
    )
    assert resp.status_code == 401
