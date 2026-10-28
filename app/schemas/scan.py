from pydantic import BaseModel, ConfigDict, Field, field_validator
import uuid
from datetime import datetime
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

SUPPORTED_CROPS = {
    "wheat",
    "rice",
    "maize",
    "tomato",
    "potato",
    "cotton",
    "sugarcane",
}


def normalize_crop_type(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().lower()

    if not normalized:
        raise ValueError("crop_type cannot be empty")

    if normalized not in SUPPORTED_CROPS:
        raise ValueError("Unsupported crop type")

    return normalized


class ScanCreate(BaseModel):
    image_path: str = Field(min_length=1, max_length=500)
    crop_type: str | None = Field(default=None, max_length=100)

    @field_validator("crop_type")
    @classmethod
    def validate_crop_type(cls, value: str | None) -> str | None:
        if value is None:
            return value

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError("crop_type cannot be empty")

        if normalized not in SUPPORTED_CROPS:
            raise ValueError("Unsupported crop type")

        return normalized

class ScanResponse(BaseModel):
    id: uuid.UUID
    crop_type: str | None
    status: str
    created_at: datetime
    prediction: PredictionResponse | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def build_prediction(cls, value):
        if isinstance(value, dict):
            return value

        disease = getattr(value, "predicted_disease", None)
        confidence = getattr(value, "confidence", None)

        prediction = None

        if disease is not None and confidence is not None:
            prediction = {
                "disease": disease,
                "confidence": confidence,
            }

        return {
            "id": value.id,
            "crop_type": value.crop_type,
            "status": value.status,
            "created_at": value.created_at,
            "prediction": prediction,
        }


class ScanUploadResponse(ScanResponse):
    prediction: PredictionResponse

class PredictionResponse(BaseModel):
    disease: str
    confidence: float = Field(ge=0, le=100)
