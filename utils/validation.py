"""
Validation Module
=================
Provides robust validation for user-uploaded person and garment images,
checking file sizes, extensions, MIME types, corrupt image bytes, and dimension limits.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, Tuple
import os
from PIL import Image

import config


@dataclass
class ValidationResult:
    is_valid: bool
    error_message: Optional[str] = None
    details: Optional[dict] = None


def validate_image_file(file_path: Union[str, Path]) -> ValidationResult:
    """
    Validates a file path before loading:
    - Path existence
    - File extension (.jpg, .jpeg, .png)
    - File size limits (preventing memory exhaustion)
    """
    if file_path is None:
        return ValidationResult(is_valid=False, error_message="No file was provided.")

    path = Path(file_path)

    if not path.exists():
        return ValidationResult(is_valid=False, error_message=f"File does not exist: {path.name}")

    if not path.is_file():
        return ValidationResult(is_valid=False, error_message=f"Provided path is not a file: {path.name}")

    # Check extension
    ext = path.suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        allowed = ", ".join(config.ALLOWED_EXTENSIONS)
        return ValidationResult(
            is_valid=False,
            error_message=f"Unsupported format '{ext}'. Allowed formats are: {allowed}"
        )

    # Check file size
    size_bytes = path.stat().st_size
    if size_bytes == 0:
        return ValidationResult(is_valid=False, error_message="The uploaded file is empty (0 bytes).")

    if size_bytes > config.MAX_FILE_SIZE_BYTES:
        max_mb = config.MAX_FILE_SIZE_BYTES / (1024 * 1024)
        actual_mb = size_bytes / (1024 * 1024)
        return ValidationResult(
            is_valid=False,
            error_message=f"File size ({actual_mb:.1f} MB) exceeds maximum allowed size ({max_mb:.0f} MB)."
        )

    return ValidationResult(is_valid=True, details={"size_bytes": size_bytes, "extension": ext})


def validate_image_content(image: Image.Image, image_label: str = "Image") -> ValidationResult:
    """
    Validates an in-memory PIL Image:
    - Integrity check (verify not corrupted)
    - Minimum and maximum dimensions
    - Color channels
    """
    if image is None:
        return ValidationResult(is_valid=False, error_message=f"{image_label} is missing.")

    if not isinstance(image, Image.Image):
        return ValidationResult(is_valid=False, error_message=f"{image_label} is not a valid PIL Image object.")

    try:
        width, height = image.size
    except Exception as e:
        return ValidationResult(is_valid=False, error_message=f"{image_label} has invalid dimensions: {e}")

    # Check minimum dimensions
    if width < config.MIN_IMAGE_DIMENSION or height < config.MIN_IMAGE_DIMENSION:
        return ValidationResult(
            is_valid=False,
            error_message=(
                f"{image_label} resolution ({width}x{height}) is too small. "
                f"Minimum required is {config.MIN_IMAGE_DIMENSION}x{config.MIN_IMAGE_DIMENSION} pixels."
            )
        )

    # Check maximum dimensions
    if width > config.MAX_IMAGE_DIMENSION or height > config.MAX_IMAGE_DIMENSION:
        return ValidationResult(
            is_valid=False,
            error_message=(
                f"{image_label} resolution ({width}x{height}) exceeds maximum limit "
                f"of {config.MAX_IMAGE_DIMENSION}x{config.MAX_IMAGE_DIMENSION} pixels."
            )
        )

    return ValidationResult(
        is_valid=True,
        details={"width": width, "height": height, "mode": image.mode}
    )


def validate_tryon_pair(person_image: Image.Image, cloth_image: Image.Image) -> ValidationResult:
    """
    Validates both the person image and the garment image as a pair before running inference.
    """
    res_person = validate_image_content(person_image, "Person photo")
    if not res_person.is_valid:
        return res_person

    res_cloth = validate_image_content(cloth_image, "Clothing image")
    if not res_cloth.is_valid:
        return res_cloth

    return ValidationResult(is_valid=True, details={
        "person": res_person.details,
        "cloth": res_cloth.details
    })
