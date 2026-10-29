import logging
from io import BytesIO
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from PIL import Image
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.ml.predictor import predict_image
from app.repositories.scan_repository import (
    create_scan as create_scan_record,
    get_scan_by_id,
)
from app.schemas.scan import (
    ScanCreate,
    ScanResponse,
    ScanUploadResponse,
    normalize_crop_type,
)
from app.services.image_storage import read_uploaded_image
from app.services.imagekit_storage import (
    upload_image_to_imagekit,
    delete_image_from_imagekit,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scans", tags=["Scans"])


@router.post(
    "",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_scan(
    payload: ScanCreate,
    db: Session = Depends(get_db),
):
    """Create a scan record without uploading an image."""

    return create_scan_record(
        db=db,
        crop_type=payload.crop_type,
    )


@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan_endpoint(
    scan_id: UUID,
    db: Session = Depends(get_db),
):
    """Retrieve a scan by its ID."""

    scan = get_scan_by_id(db=db, scan_id=scan_id)

    if scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    return scan


@router.post(
    "/upload",
    response_model=ScanUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_scan(
    file: UploadFile = File(...),
    crop_type: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    imagekit_file_id: str | None = None

    try:
        # Step 1: Validate crop type
        try:
            crop_type = normalize_crop_type(crop_type)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        if crop_type is None:
            crop_type = "tomato"
        elif crop_type != "tomato":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The current trained model supports tomato images only",
            )

        # Step 2: Read and validate the image in RAM
        try:
            image_content = await read_uploaded_image(
                file=file,
                max_size_bytes=settings.max_upload_size_bytes,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        # Step 3: Run ML prediction directly from memory
        try:
            with Image.open(BytesIO(image_content)) as image:
                prediction = predict_image(image)
        except Exception as exc:
            logger.exception("Crop disease prediction failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Image prediction failed",
            ) from exc

        # Step 4: Upload the image bytes to ImageKit
        try:
            imagekit_result = upload_image_to_imagekit(
                image_content=image_content,
                content_type=file.content_type,
            )

            image_url = imagekit_result["image_url"]
            imagekit_file_id = imagekit_result["imagekit_file_id"]

        except Exception as exc:
            logger.exception("ImageKit upload failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Image storage upload failed",
            ) from exc

        # Step 5: Save ImageKit details and prediction in Neon
        try:
            scan = create_scan_record(
                db=db,
                image_url=image_url,
                imagekit_file_id=imagekit_file_id,
                crop_type=crop_type,
                predicted_disease=prediction["disease"],
                confidence=prediction["confidence"],
            )

        except Exception as exc:
            logger.exception("Failed to save scan in database")

            # Roll back the ImageKit upload if database saving fails.
            try:
                delete_image_from_imagekit(imagekit_file_id)
            except Exception:
                logger.exception(
                    "Failed to clean up ImageKit file after database failure"
                )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save scan",
            ) from exc

        return ScanUploadResponse(
            id=scan.id,
            crop_type=scan.crop_type,
            status=scan.status,
            created_at=scan.created_at,
            image_url=scan.image_url,
            prediction=prediction,
        )

    finally:
        await file.close()