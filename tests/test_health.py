from fastapi.testclient import TestClient
from app.main import app


def test_root_endpoimt():
    with TestClient(app) as clint:
        response = clint.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Crop Health AI API",
        "status": "running",
    }


def test_liveness_endpoint():
    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_endpoint():
    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "connected",
    }