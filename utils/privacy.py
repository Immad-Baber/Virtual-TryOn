"""
Privacy & Ephemeral Storage Module
==================================
Guarantees user privacy by ensuring uploaded personal photos and intermediate
representations are stored only ephemerally and automatically purged after use.
"""

import os
import time
import uuid
import logging
from pathlib import Path
from typing import Optional, List
from PIL import Image

import config

logger = logging.getLogger("VirtualTryOn.Privacy")


def get_ephemeral_filepath(prefix: str = "upload", suffix: str = ".png") -> Path:
    """
    Generates a secure, non-guessable ephemeral path inside the temporary directory.
    """
    token = uuid.uuid4().hex[:12]
    timestamp = int(time.time())
    filename = f"{prefix}_{timestamp}_{token}{suffix}"
    return config.TEMP_DIR / filename


def save_ephemeral_image(image: Image.Image, prefix: str = "img") -> Path:
    """
    Saves an in-memory image to ephemeral temporary storage.
    Returns the path for pipeline consumption.
    """
    filepath = get_ephemeral_filepath(prefix=prefix, suffix=".png")
    image.save(filepath, format="PNG")
    return filepath


def purge_file(filepath: Optional[Path]) -> bool:
    """
    Safely deletes a single temporary file if it exists.
    """
    if filepath is None:
        return False
    try:
        p = Path(filepath)
        if p.exists() and p.is_file():
            p.unlink()
            return True
    except Exception as e:
        logger.warning(f"Failed to delete ephemeral file {filepath}: {e}")
    return False


def purge_ephemeral_directory(max_age_seconds: int = config.MAX_TEMP_FILE_AGE_SECONDS) -> int:
    """
    Scans the temporary uploads directory and deletes files older than max_age_seconds.
    Prevents storage buildup while keeping active requests intact.
    """
    now = time.time()
    deleted_count = 0

    if not config.TEMP_DIR.exists():
        return 0

    for file_path in config.TEMP_DIR.glob("*.*"):
        try:
            if file_path.is_file():
                age = now - file_path.stat().st_mtime
                if age > max_age_seconds:
                    file_path.unlink()
                    deleted_count += 1
        except Exception as e:
            logger.debug(f"Could not purge {file_path}: {e}")

    return deleted_count
