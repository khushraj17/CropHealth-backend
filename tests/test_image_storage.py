from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile
from PIL import Image

from app.services.image_storage import save_uploaded_image

@pytest.mark.anyio
async def test_save_valid_image(tmp_path):
    image_content = create_test_image()

    upload = UploadFile(
        file=BytesIO(image_content),
        filename="test.jpg",
        headers={"content-type": "image/jpeg"},
    )

    saved_path = await save_uploaded_image(
        file=upload,
        upload_dir=str(tmp_path),
        max_size_bytes=1024 * 1024,
    )

    saved_file = Path(saved_path)

    assert saved_file.exists()
    assert saved_file.read_bytes() == image_content
    assert saved_file.suffix == ".jpg"


@pytest.mark.anyio
async def test_reject_invalid_image_content(tmp_path):
    upload = UploadFile(
        file=BytesIO(b"This is not a real image"),
        filename="fake.jpg",
        headers={"content-type": "image/jpeg"},
    )

    with pytest.raises(ValueError, match="Invalid image content"):
        await save_uploaded_image(
            file=upload,
            upload_dir=str(tmp_path),
            max_size_bytes=1024,
        )


@pytest.mark.anyio
async def test_reject_unsupported_content_type(tmp_path):
    upload = UploadFile(
        file=BytesIO(b"some-content"),
        filename="test.txt",
        headers={"content-type": "text/plain"},
    )

    with pytest.raises(ValueError, match="Unsupported image type"):
        await save_uploaded_image(
            file=upload,
            upload_dir=str(tmp_path),
            max_size_bytes=1024,
        )


@pytest.mark.anyio
async def test_reject_empty_image(tmp_path):
    upload = UploadFile(
        file=BytesIO(b""),
        filename="empty.jpg",
        headers={"content-type": "image/jpeg"},
    )

    with pytest.raises(ValueError, match="Uploaded image is empty"):
        await save_uploaded_image(
            file=upload,
            upload_dir=str(tmp_path),
            max_size_bytes=1024,
        )


@pytest.mark.anyio
async def test_reject_oversized_image(tmp_path):
    upload = UploadFile(
        file=BytesIO(b"x" * 2048),
        filename="large.jpg",
        headers={"content-type": "image/jpeg"},
    )

    with pytest.raises(
        ValueError,
        match="Image exceeds maximum allowed size",
    ):
        await save_uploaded_image(
            file=upload,
            upload_dir=str(tmp_path),
            max_size_bytes=1024,
        )


def create_test_image() -> bytes:
    buffer = BytesIO()

    image = Image.new("RGB", (10, 10), color="green")
    image.save(buffer, format="JPEG")

    return buffer.getvalue()

@pytest.mark.anyio
async def test_reject_image_with_excessive_dimensions(tmp_path):
    buffer = BytesIO()

    image = Image.new("RGB", (10_001, 1), color="green")
    image.save(buffer, format="JPEG")

    upload = UploadFile(
        file=BytesIO(buffer.getvalue()),
        filename="oversized.jpg",
        headers={"content-type": "image/jpeg"},
    )

    with pytest.raises(
        ValueError,
        match="Image dimensions exceed maximum allowed limits",
    ):
        await save_uploaded_image(
            file=upload,
            upload_dir=str(tmp_path),
            max_size_bytes=1024 * 1024,
        )