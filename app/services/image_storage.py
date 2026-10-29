from io import BytesIO
import warnings

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_WIDTH = 10_000
MAX_IMAGE_HEIGHT = 10_000
MAX_IMAGE_PIXELS = 25_000_000

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}


async def read_uploaded_image(
    file: UploadFile,
    max_size_bytes: int,
) -> bytes:
    """Read and validate an uploaded image in memory."""

    try:
        content_type = file.content_type

        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError("Unsupported image type")

        content = await file.read(max_size_bytes + 1)

        if not content:
            raise ValueError("Uploaded image is empty")

        if len(content) > max_size_bytes:
            raise ValueError("Image exceeds maximum allowed size")

        try:
            with warnings.catch_warnings():
                warnings.simplefilter(
                    "error",
                    Image.DecompressionBombWarning,
                )

                with Image.open(BytesIO(content)) as image:
                    width, height = image.size
                    actual_format = image.format

                    if (
                        width > MAX_IMAGE_WIDTH
                        or height > MAX_IMAGE_HEIGHT
                        or width * height > MAX_IMAGE_PIXELS
                    ):
                        raise ValueError(
                            "Image dimensions exceed maximum allowed limits"
                        )

                    image.verify()

        except ValueError:
            raise
        except (
            UnidentifiedImageError,
            Image.DecompressionBombWarning,
            Image.DecompressionBombError,
            OSError,
            SyntaxError,
        ):
            raise ValueError("Invalid image content") from None

        if actual_format != ALLOWED_CONTENT_TYPES[content_type]:
            raise ValueError(
                "Image content does not match content type"
            )

        return content

    finally:
        await file.close()