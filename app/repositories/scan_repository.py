import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.scan import Scan


def create_scan(
    db: Session,
    crop_type: str | None = None,
    predicted_disease: str | None = None,
    confidence: float | None = None,
    image_url: str | None = None,
    imagekit_file_id: str | None = None,
) -> Scan:
    scan = Scan(
        image_url=image_url,
        imagekit_file_id=imagekit_file_id,
        crop_type=crop_type,
        predicted_disease=predicted_disease,
        confidence=confidence,
    )

    try:
        db.add(scan)
        db.commit()
        db.refresh(scan)
    except Exception:
        db.rollback()
        raise

    return scan


def get_scan_by_id(
    db: Session,
    scan_id: uuid.UUID,
) -> Scan | None:
    statement = select(Scan).where(Scan.id == scan_id)
    return db.scalar(statement)
