"""
Unit Tests for Validation Module
"""

import pytest
from pathlib import Path
from PIL import Image

import config
from utils.validation import (
    validate_image_file,
    validate_image_content,
    validate_tryon_pair
)


def test_validate_image_file_valid(tmp_path):
    # Create valid temp jpg
    test_img = Image.new("RGB", (512, 512), (100, 150, 200))
    file_path = tmp_path / "test.jpg"
    test_img.save(file_path, "JPEG")

    result = validate_image_file(file_path)
    assert result.is_valid is True
    assert result.error_message is None


def test_validate_image_file_nonexistent():
    result = validate_image_file("non_existent_file.png")
    assert result.is_valid is False
    assert "File does not exist" in result.error_message


def test_validate_image_file_invalid_ext(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("not an image")

    result = validate_image_file(file_path)
    assert result.is_valid is False
    assert "Unsupported format" in result.error_message


def test_validate_image_file_empty(tmp_path):
    file_path = tmp_path / "empty.png"
    file_path.touch()

    result = validate_image_file(file_path)
    assert result.is_valid is False
    assert "empty" in result.error_message


def test_validate_image_content_too_small():
    tiny_img = Image.new("RGB", (100, 100), (0, 0, 0))
    result = validate_image_content(tiny_img, "Test image")
    assert result.is_valid is False
    assert "too small" in result.error_message


def test_validate_image_content_valid():
    valid_img = Image.new("RGB", (768, 1024), (255, 255, 255))
    result = validate_image_content(valid_img, "Valid image")
    assert result.is_valid is True
    assert result.details["width"] == 768
    assert result.details["height"] == 1024


def test_validate_tryon_pair_success():
    person = Image.new("RGB", (768, 1024), (200, 200, 200))
    cloth = Image.new("RGB", (768, 1024), (50, 50, 200))

    result = validate_tryon_pair(person, cloth)
    assert result.is_valid is True
