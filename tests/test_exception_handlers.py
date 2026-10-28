from fastapi import HTTPException

from app.main import app


def test_validation_error_format(client):
    response = client.post(
        "/api/v2/scans",
        json={"crop_type": "wheat"},
    )

    assert response.status_code == 422

    data = response.json()

    assert data["detail"] == "Request validation failed"
    assert "errors" in data


def test_http_exception_format(client):
    response = client.get(
        "/api/v2/scans/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Scan not found"}

def test_unexpected_exception_does_not_expose_details(client):
    @app.get("/test-server-error")
    def trigger_server_error():
        raise RuntimeError("secret database connection details")

    try:
        response = client.get("/test-server-error")
    finally:
        app.router.routes[:] = [
            route
            for route in app.router.routes
            if getattr(route, "path", None) != "/test-server-error"
        ]

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Internal server error"
    }
    assert "secret database connection details" not in response.text
    