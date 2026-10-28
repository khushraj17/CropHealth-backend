from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


def create_test_image() -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (10, 10), color="green")
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_upload_valid_image(client: TestClient):
    response = client.post(
        "/api/v2/scans/upload",
        files={
            "file": (
                "tomato.jpg",
                create_test_image(),
                "image/jpeg",
            )
        },
        data={"crop_type": "tomato"},
    )

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert data["crop_type"] == "tomato"
    assert data["status"] == "uploaded"
    assert "created_at" in data


def test_upload_invalid_image(client: TestClient):
    response = client.post(
        "/api/v2/scans/upload",
        files={
            "file": (
                "fake.jpg",
                b"This is not an actual image",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid image content"


def test_upload_without_file(client: TestClient):
    response = client.post("/api/v2/scans/upload")

    assert response.status_code == 422


def test_upload_rejects_unsupported_crop(client: TestClient):
    response = client.post(
        "/api/v2/scans/upload",
        files={
            "file": (
                "tomato.jpg",
                create_test_image(),
                "image/jpeg",
            )
        },
        data={"crop_type": "unknown_crop"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Unsupported crop type"

def test_upload_rejects_empty_crop(client: TestClient):
    response = client.post(
        "/api/v2/scans/upload",
        files={
            "file": (
                "tomato.jpg",
                create_test_image(),
                "image/jpeg",
            )
        },
        data={"crop_type": "   "},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "crop_type cannot be empty"

