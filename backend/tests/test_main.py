from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_auth_register():
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
            "timezone": "UTC",
        },
    )
    assert response.status_code == 200
    assert "message" in response.json()


def test_auth_login():
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "testpassword123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_user_profile():
    response = client.get("/users/me")
    assert response.status_code == 200
    assert "email" in response.json()


def test_digest_preview():
    response = client.get("/digest/preview")
    assert response.status_code == 200
    assert "articles" in response.json()
    assert len(response.json()["articles"]) > 0
