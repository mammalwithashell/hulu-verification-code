from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_root_returns_not_found():
    response = client.get("/")
    assert response.status_code == 404


def test_old_code_endpoint_gone():
    response = client.get("/code")
    assert response.status_code == 404
