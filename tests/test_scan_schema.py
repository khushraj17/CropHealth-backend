import pytest
from pydantic import ValidationError

from app.schemas.scan import ScanCreate


@pytest.mark.parametrize(
    ("crop_type", "expected"),
    [
        ("wheat", "wheat"),
        (" Wheat ", "wheat"),
        ("RICE", "rice"),
        (None, None),
    ],
)
def test_valid_crop_types(crop_type, expected):
    scan = ScanCreate(
        image_path="uploads/test.jpg",
        crop_type=crop_type,
    )

    assert scan.crop_type == expected


@pytest.mark.parametrize(
    "crop_type",
    [
        "",
        "   ",
        "unknown_crop",
    ],
)
def test_invalid_crop_types(crop_type):
    with pytest.raises(ValidationError):
        ScanCreate(
            image_path="uploads/test.jpg",
            crop_type=crop_type,
        )