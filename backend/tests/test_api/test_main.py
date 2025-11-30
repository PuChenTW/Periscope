def test_health_check(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_ready(client):
    response = client.get("/health/ready/")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
