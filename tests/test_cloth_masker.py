"""
Unit Tests for Cloth Masker Module
"""

import numpy as np
from PIL import Image

import config
from utils.cloth_masker import (
    ATR_CLASSES,
    create_anatomical_upper_mask,
    build_catvton_mask_from_segformer_parse
)


def test_create_anatomical_upper_mask():
    mask = create_anatomical_upper_mask((768, 1024))
    assert mask.size == (768, 1024)

    # Face area (top 15%) should be black (0)
    top_pixel = mask.getpixel((384, 50))
    assert top_pixel == 0

    # Lower body (bottom 10%) should be black (0)
    bottom_pixel = mask.getpixel((384, 950))
    assert bottom_pixel == 0

    # Center torso should be white (>200)
    center_pixel = mask.getpixel((384, 500))
    assert center_pixel > 200


def test_build_catvton_mask_from_segformer_parse():
    # Synthetic parse map
    h, w = 1000, 750
    parse = np.zeros((h, w), dtype=np.int64)

    # Face
    parse[50:200, 300:450] = ATR_CLASSES["Face"]
    # Upper clothing
    parse[250:600, 200:550] = ATR_CLASSES["Upper-clothes"]
    # Pants
    parse[650:950, 250:500] = ATR_CLASSES["Pants"]

    mask = build_catvton_mask_from_segformer_parse(parse, target_size=(768, 1024))
    assert mask.size == (768, 1024)

    mask_np = np.array(mask)

    # Face region should be 0 (protected)
    assert np.all(mask_np[50:200, 300:450] == 0)

    # Clothing region should be > 0 (inpainted)
    assert np.mean(mask_np[300:550, 250:500]) > 200
