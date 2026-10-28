import uuid


def test_create_scan(client):
    response = client.post(
        "/api/v2/scans",
        json={
            "image_path": "uploads/test-image.jpg",
            "crop_type": "wheat",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["crop_type"] == "wheat"
    assert data["status"] == "uploaded"
    assert uuid.UUID(data["id"])
    assert "created_at" in data


def test_get_missing_scan(client):
    scan_id = uuid.uuid4()

    response = client.get(f"/api/v2/scans/{scan_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Scan not found"


def test_create_scan_without_image_path(client):
    response = client.post(
        "/api/v2/scans",
        json={
            "crop_type": "wheat",
        },
    )

    assert response.status_code == 422