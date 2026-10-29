from io import BytesIO
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.db.session import get_db


def create_test_image() -> bytes:
    """Create a valid in-memory JPEG image for testing."""
    image = Image.new("RGB", (64, 64), color="green")
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_complete_scan_workflow():
    image_bytes = create_test_image()

    fake_scan_id = uuid4()
    fake_image_url = "https://ik.imagekit.io/test/crop-scan.jpg"
    fake_file_id = "imagekit-test-file-id"

    saved_records = []

    class FakeScan:
        def __init__(self, **kwargs):
            self.id = fake_scan_id
            self.crop_type = kwargs["crop_type"]
            self.status = "completed"
            self.created_at = "2026-01-01T00:00:00"
            self.image_url = kwargs["image_url"]
            self.imagekit_file_id = kwargs["imagekit_file_id"]
            self.predicted_disease = kwargs["predicted_disease"]
            self.confidence = kwargs["confidence"]

    def fake_create_scan(**kwargs):
        assert "image_path" not in kwargs
        scan = FakeScan(**kwargs)
        saved_records.append(scan)
        return scan

    def override_get_db():
        yield object()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with (
            patch(
                "app.api.routes.scans.predict_image",
                return_value={
                    "disease": "Tomato___healthy",
                    "confidence": 0.98,
                },
            ) as mock_predict,
            patch(
                "app.api.routes.scans.upload_image_to_imagekit",
                return_value={
                    "image_url": fake_image_url,
                    "imagekit_file_id": fake_file_id,
                },
            ) as mock_imagekit_upload,
            patch(
                "app.api.routes.scans.create_scan_record",
                side_effect=fake_create_scan,
            ) as mock_db_save,
        ):
            client = TestClient(app)

            response = client.post(
                "/api/v2/scans/upload",
                files={
                    "file": (
                        "tomato.jpg",
                        image_bytes,
                        "image/jpeg",
                    )
                },
                data={"crop_type": "tomato"},
            )

        assert response.status_code == 201, response.text

        result = response.json()

        assert result["id"] == str(fake_scan_id)
        assert result["crop_type"] == "tomato"
        assert result["image_url"] == fake_image_url
        assert result["prediction"]["disease"] == "Tomato___healthy"
        assert result["prediction"]["confidence"] == 0.98

        mock_predict.assert_called_once()
        mock_imagekit_upload.assert_called_once_with(
            image_content=image_bytes,
            content_type="image/jpeg",
        )
        mock_db_save.assert_called_once()

        saved_scan = saved_records[0]

        assert saved_scan.image_url == fake_image_url
        assert saved_scan.imagekit_file_id == fake_file_id
        assert saved_scan.predicted_disease == "Tomato___healthy"
        assert saved_scan.confidence == 0.98

        assert not hasattr(saved_scan, "image_path")

    finally:
        app.dependency_overrides.pop(get_db, None)
