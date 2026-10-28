import uuid
from pathlib import Path

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError
import warnings

from PIL import Image, UnidentifiedImageError
from io import BytesIO

MAX_IMAGE_WIDTH = 10_000
MAX_IMAGE_HEIGHT = 10_000
MAX_IMAGE_PIXELS = 25_000_000

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def save_uploaded_image(
    file: UploadFile,
    upload_dir: str,
    max_size_bytes: int,
) -> str:
    destination = None

    try:
        # 1. Check the declared content type
        content_type = file.content_type

        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError("Unsupported image type")

        # 2. Read the file while enforcing the size limit
        content = await file.read(max_size_bytes + 1)

        if not content:
            raise ValueError("Uploaded image is empty")

        if len(content) > max_size_bytes:
            raise ValueError("Image exceeds maximum allowed size")

        # 3. Verify that the content is an actual image
                # Verify the actual image content and dimensions.
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
        # 4. Match the actual image format to the declared type
        expected_formats = {
            "image/jpeg": "JPEG",
            "image/png": "PNG",
            "image/webp": "WEBP",
        }

        if actual_format != expected_formats[content_type]:
            raise ValueError("Image content does not match content type")

        # 5. Generate a unique filename
        directory = Path(upload_dir)
        directory.mkdir(parents=True, exist_ok=True)

        extension = ALLOWED_CONTENT_TYPES[content_type]
        filename = f"{uuid.uuid4().hex}{extension}"
        destination = directory / filename

        # 6. Create the file without overwriting an existing file
        with destination.open("xb") as output:
            output.write(content)

        return str(destination)

    except Exception:
        if destination is not None:
            destination.unlink(missing_ok=True)
        raise

    finally:
        await file.close()