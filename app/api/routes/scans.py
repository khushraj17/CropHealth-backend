from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.repositories.scan_repository import (
    create_scan as create_scan_record,
    get_scan_by_id,
)

from app.schemas.scan import (
    ScanResponse,
    ScanCreate,
    ScanUploadResponse,
    normalize_crop_type,
)
from PIL import Image
from app.ml.predictor import predict_image

from app.services.image_storage import save_uploaded_image
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scans", tags=["Scans"])


@router.post(
    "",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_scan( payload: ScanCreate, db: Session = Depends(get_db)):
    scan = create_scan_record(
        db=db,
        image_path = payload.image_path,
        crop_type = payload.crop_type,
        )

    return scan


@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan_endpoint(
    scan_id: UUID,
    db: Session = Depends(get_db),
):
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

    # Step 1: Validate crop type
    try:
        crop_type = normalize_crop_type(crop_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    # Current trained model supports tomato only.
    if crop_type is None:
        crop_type = "tomato"
    elif crop_type != "tomato":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The current trained model supports tomato images only",
        )

    # Step 2: Validate and save uploaded image
    try:
        image_path = await save_uploaded_image(
            file=file,
            upload_dir=settings.upload_dir,
            max_size_bytes=settings.max_upload_size_bytes,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # Step 3: Run ML prediction
    try:
        with Image.open(image_path) as image:
            prediction = predict_image(image)

    except Exception as exc:
        try:
            Path(image_path).unlink(missing_ok=True)
        except OSError:
            logger.exception(
                "Failed to clean up image after prediction failure"
            )

        logger.exception("Crop disease prediction failed")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image prediction failed",
        ) from exc

    # Step 4: Create scan record in the database
    try:
        scan = create_scan_record(
            db=db,
            image_path=image_path,
            crop_type=crop_type,
            predicted_disease=prediction["disease"],
            confidence=prediction["confidence"],
        )
    except Exception:
        try:
            Path(image_path).unlink(missing_ok=True)
        except OSError:
            logger.exception(
                "Failed to clean up uploaded image after database failure"
            )

        raise

    # Step 5: Return scan details and prediction
    return ScanUploadResponse(
        id=scan.id,
        crop_type=scan.crop_type,
        status=scan.status,
        created_at=scan.created_at,
        prediction=prediction,
    )