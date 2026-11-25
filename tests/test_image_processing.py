"""
Unit Tests for Image Processing Module
"""

from PIL import Image
import numpy as np

import config
from utils.image_processing import (
    ensure_rgb,
    resize_and_crop,
    resize_and_padding,
    visualize_mask,
    create_comparison_grid
)


def test_ensure_rgb_rgba():
    rgba = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
    rgb = ensure_rgb(rgba)
    assert rgb.mode == "RGB"
    assert rgb.size == (100, 100)


def test_resize_and_crop_aspect():
    # Wide image
    wide = Image.new("RGB", (1200, 600), (10, 20, 30))
    res = resize_and_crop(wide, (768, 1024))
    assert res.size == (768, 1024)

    # Tall image
    tall = Image.new("RGB", (400, 1200), (10, 20, 30))
    res2 = resize_and_crop(tall, (768, 1024))
    assert res2.size == (768, 1024)


def test_resize_and_padding_aspect():
    # Square garment padded onto 768x1024 canvas
    square_cloth = Image.new("RGB", (600, 600), (255, 0, 0))
    res = resize_and_padding(square_cloth, (768, 1024))
    assert res.size == (768, 1024)

    # Corners should be white padding
    corner_pixel = res.getpixel((5, 5))
    assert corner_pixel == (255, 255, 255)


def test_create_comparison_grid():
    p = Image.new("RGB", (768, 1024), (100, 100, 100))
    c = Image.new("RGB", (768, 1024), (200, 200, 200))
    r = Image.new("RGB", (768, 1024), (150, 150, 150))

    grid = create_comparison_grid(p, c, r, height=400)
    assert grid.size[1] == 400
    assert grid.size[0] > 400
