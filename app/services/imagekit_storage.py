from functools import lru_cache
from uuid import uuid4

from imagekitio import ImageKit

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_imagekit() -> ImageKit:
    settings = get_settings()

    return ImageKit(
        private_key=settings.imagekit_private_key,
    )


def upload_image_to_imagekit(
    image_content: bytes,
    content_type: str,
) -> dict[str, str]:
    """Upload image bytes directly to ImageKit without local storage."""

    imagekit = get_imagekit()

    extensions = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }

    extension = extensions.get(content_type)

    if extension is None:
        raise ValueError("Unsupported image type")

    if not image_content:
        raise ValueError("Image content is empty")

    file_name = f"tomato-scan-{uuid4().hex}{extension}"

    response = imagekit.files.upload(
        file=image_content,
        file_name=file_name,
        folder="/crop-health/scans",
    )

    if not response.url or not response.file_id:
        raise RuntimeError(
            "ImageKit upload did not return the expected details"
        )

    return {
        "image_url": response.url,
        "imagekit_file_id": response.file_id,
    }


def delete_image_from_imagekit(file_id: str) -> None:
    """Delete an uploaded image from ImageKit using its file ID."""

    imagekit = get_imagekit()
    imagekit.files.delete(file_id)