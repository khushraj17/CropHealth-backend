import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.scan import Scan
from app.repositories.scan_repository import (
    create_scan,
    get_scan_by_id,
)


def create_test_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    return engine, TestSessionLocal()


def test_create_and_get_scan():
    engine, db = create_test_session()

    try:
        created_scan = create_scan(
            db=db,
            image_path="uploads/test-image.jpg",
            crop_type="wheat",
        )

        assert created_scan.id is not None
        assert created_scan.image_path == "uploads/test-image.jpg"
        assert created_scan.crop_type == "wheat"
        assert created_scan.status == "uploaded"

        retrieved_scan = get_scan_by_id(
            db=db,
            scan_id=created_scan.id,
        )

        assert retrieved_scan is not None
        assert retrieved_scan.id == created_scan.id

    finally:
        db.close()
        engine.dispose()


def test_get_scan_by_unknown_id_returns_none():
    engine, db = create_test_session()

    try:
        result = get_scan_by_id(
            db=db,
            scan_id=uuid.uuid4(),
        )

        assert result is None

    finally:
        db.close()
        engine.dispose()