import logging
from functools import lru_cache
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms
from torchvision.models import efficientnet_b0

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "ML" / "best_crop_disease_model.pth"

DEVICE = torch.device("cpu")


def get_transform(image_size: int = 224):
    """Apply the same preprocessing used during model training."""
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])


@lru_cache(maxsize=1)
def load_model():
    """Load the trained model once and reuse it."""
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Trained model file not found: {MODEL_PATH}"
        )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=DEVICE,
        weights_only=True,
    )

    class_names = checkpoint["class_names"]
    num_classes = checkpoint["num_classes"]
    image_size = checkpoint.get("image_size", 224)

    if len(class_names) != num_classes:
        raise ValueError(
            "Model class count does not match class names."
        )

    model = efficientnet_b0(weights=None)

    in_features = model.classifier[1].in_features

    model.classifier = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_features, num_classes),
    )

    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(DEVICE)
    model.eval()

    logger.info("Crop disease model loaded successfully")

    return model, class_names, get_transform(image_size)


def predict_image(image: Image.Image) -> dict:
    """Predict a crop disease from a PIL image."""
    model, class_names, transform = load_model()

    image = image.convert("RGB")
    image_tensor = transform(image).unsqueeze(0).to(DEVICE)

    with torch.inference_mode():
        logits = model(image_tensor)
        probabilities = torch.softmax(logits, dim=1)

        confidence, predicted_index = probabilities.max(dim=1)

    index = predicted_index.item()
    disease = class_names[index]
    confidence_score = confidence.item()

    return {
        "disease": disease,
        "confidence": round(confidence_score * 100, 2),
    }