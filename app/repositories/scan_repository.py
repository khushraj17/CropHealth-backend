import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.scan import Scan


def create_scan(
    db: Session,
    image_path: str,
    crop_type: str | None = None,
    predicted_disease: str | None = None,
    confidence: float | None = None,
) -> Scan:
    scan = Scan(
        image_path=image_path,
        crop_type=crop_type,
        predicted_disease=predicted_disease,
        confidence=confidence,
    )

    db.add(scan)
    db.commit()
    db.refresh(scan)

    return scan


def get_scan_by_id(
    db: Session,
    scan_id: uuid.UUID,
) -> Scan | None:
    statement = select(Scan).where(Scan.id == scan_id)

    return db.scalar(statement)