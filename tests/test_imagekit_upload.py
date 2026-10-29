from pathlib import Path

from app.services.imagekit_storage import upload_image_to_imagekit

# Apne project mein maujood ek test image ka path do.
image_path = Path("uploads/test_leaf.jpg")

if not image_path.is_file():
    raise FileNotFoundError(f"Test image not found: {image_path}")

result = upload_image_to_imagekit(str(image_path))

print("Image uploaded successfully")
print("Image URL:", result["image_url"])
print("ImageKit file ID:", result["imagekit_file_id"])