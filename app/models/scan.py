import uuid
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, Float, String, Uuid, func

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Scan(Base):
    __tablename__ = "scans"

    __table_args__ = ( CheckConstraint(
        "status IN ('uploaded', 'processing', 'completed', 'failed')",
        name="ck_scans_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


    crop_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    
    predicted_disease: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="uploaded",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    image_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    imagekit_file_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )