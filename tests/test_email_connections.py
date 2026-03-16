def test_test_email_connection_valid(client, auth_headers):
    resp = client.post("/v1/email-connections/test", json={
        "provider": "gmail",
        "email_address": "user@gmail.com",
        "app_password": "fake-password",
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "stub")


def test_test_email_connection_missing_fields(client, auth_headers):
    resp = client.post("/v1/email-connections/test", json={
        "provider": "gmail",
    }, headers=auth_headers)
    assert resp.status_code == 422


def test_test_email_connection_unauthenticated(client):
    resp = client.post("/v1/email-connections/test", json={
        "provider": "gmail",
        "email_address": "user@gmail.com",
        "app_password": "fake-password",
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
    })
    assert resp.status_code == 401
