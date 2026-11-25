"""
Cloth Masker Module
===================
Provides robust, multi-strategy inpainting mask generation for Virtual Try-On:
1. SegFormer semantic parsing (pure PyTorch, ATR class hierarchy)
2. Hand-aware Anatomical Agnostic Mask (protects hands, prevents bleed to pixel 1023)
3. Extended Kurta/Kameez Ethnic Mask (covers extended hemline to mid-thigh)
4. Geometric Polygon Mask (retained as an experimental ablation baseline)
"""

import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from typing import Optional, Union, Tuple
import logging

try:
    from scipy import ndimage
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

import config

logger = logging.getLogger("VirtualTryOn.Masker")

# ATR Dataset class indices used by SegFormer (mattmdjaga/segformer_b2_clothes)
ATR_CLASSES = {
    "Background": 0, "Hat": 1, "Hair": 2, "Sunglasses": 3,
    "Upper-clothes": 4, "Skirt": 5, "Pants": 6, "Dress": 7,
    "Belt": 8, "Left-shoe": 9, "Right-shoe": 10, "Face": 11,
    "Left-leg": 12, "Right-leg": 13, "Left-arm": 14, "Right-arm": 15,
    "Bag": 16, "Scarf": 17
}


def create_geometric_polygon_mask(
    image_size: Tuple[int, int] = (config.DEFAULT_WIDTH, config.DEFAULT_HEIGHT)
) -> Image.Image:
    """
    Constructs a naive 6-point flat geometric polygon mask across the upper torso.
    Used exclusively as an ablation baseline to demonstrate the 'boxy shirt' failure mode.
    """
    w, h = image_size
    neck_y = int(h * 0.18)
    shoulder_y = int(h * 0.24)
    waist_y = int(h * 0.52)

    poly_pts = [
        (int(w * 0.35), neck_y),
        (int(w * 0.85), shoulder_y),
        (int(w * 0.82), waist_y),
        (int(w * 0.18), waist_y),
        (int(w * 0.15), shoulder_y),
        (int(w * 0.65), neck_y)
    ]
    mask_img = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask_img)
    draw.polygon(poly_pts, fill=255)
    return mask_img


def create_anatomical_upper_mask(
    image_size: Tuple[int, int] = (config.DEFAULT_WIDTH, config.DEFAULT_HEIGHT),
    torso_top_ratio: float = 0.22,
    torso_bottom_ratio: float = 0.54,
    torso_left_ratio: float = 0.18,
    torso_right_ratio: float = 0.82,
    blur_radius: int = 9
) -> Image.Image:
    """
    Constructs a geometrically normalized anatomical agnostic mask covering the
    human upper torso while strictly preserving head (top 22%) and waist/legs (below 54%).
    """
    w, h = image_size
    mask_img = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask_img)

    y_start = int(h * torso_top_ratio)
    y_end = int(h * torso_bottom_ratio)
    x_start = int(w * torso_left_ratio)
    x_end = int(w * torso_right_ratio)

    draw.rectangle([x_start, y_start, x_end, y_end], fill=255)

    # Shoulder curve ellipse
    ellipse_top = max(0, y_start - int((y_end - y_start) * 0.12))
    ellipse_bottom = min(h, y_start + int((y_end - y_start) * 0.45))
    draw.ellipse([x_start - 25, ellipse_top, x_end + 25, ellipse_bottom], fill=255)

    if blur_radius > 0:
        mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    return mask_img


def build_catvton_mask_from_segformer_parse(
    parse_map: np.ndarray,
    target_size: Tuple[int, int] = (config.DEFAULT_WIDTH, config.DEFAULT_HEIGHT),
    category: str = "upper",
    include_arms: bool = True,
    protect_hands: bool = True,
    dilate_kernel_size: int = 15,
    blur_radius: int = 7
) -> Image.Image:
    """
    Transforms a raw SegFormer ATR semantic parse map into a CatVTON-compatible agnostic mask.
    
    Parameters:
    - parse_map: 2D integer ndarray from SegFormer with ATR class indices.
    - target_size: (width, height) tuple.
    - category: "upper" (standard shirt/blouse), "extended_kurta" (knee-length Pakistani attire), or "overall".
    - include_arms: If True, masks upper arms for short/long sleeve transfer.
    - protect_hands: If True, clips arm mask above wrists to prevent hand distortion (avoids bleed to row 1023).
    - dilate_kernel_size: Morphological dilation kernel size.
    - blur_radius: Gaussian blur sigma to soften latent space transitions.
    """
    h, w = parse_map.shape

    # 1. Base upper clothing
    inpaint_mask = np.isin(parse_map, [ATR_CLASSES["Upper-clothes"], ATR_CLASSES["Dress"]])

    # 2. Upper arm handling with hand protection
    if include_arms:
        arms_mask = np.isin(parse_map, [ATR_CLASSES["Left-arm"], ATR_CLASSES["Right-arm"]])
        
        if protect_hands:
            # Find vertical bounds of upper clothing to estimate waist level
            upper_y_indices = np.where(inpaint_mask)[0]
            if len(upper_y_indices) > 0:
                waist_y = upper_y_indices.max()
                # Hands are in the lower extremities of the arms (typically below waist + 15% torso height)
                # Clip the arm mask so it covers sleeves down to mid-forearm, strictly protecting hands
                arm_cutoff_y = min(h - 1, waist_y + int(h * 0.08))
                arms_mask[arm_cutoff_y:, :] = False
            else:
                # If no upper clothing detected, cap arms at 65% of image height
                arms_mask[int(h * 0.65):, :] = False
                
        inpaint_mask = inpaint_mask | arms_mask

    # 3. Extended Kurta / Kameez handling (Phase 3)
    # A kurta extends below the belt to mid-thigh. We include the upper 40% of pants/thighs
    if category in ["extended_kurta", "kurta", "kameez"]:
        pants_mask = (parse_map == ATR_CLASSES["Pants"])
        pants_y_indices = np.where(pants_mask)[0]
        if len(pants_y_indices) > 0:
            top_pants_y = pants_y_indices.min()
            bottom_pants_y = pants_y_indices.max()
            thigh_cutoff_y = top_pants_y + int((bottom_pants_y - top_pants_y) * 0.45)
            kurta_thigh_mask = np.zeros_like(pants_mask)
            kurta_thigh_mask[top_pants_y:thigh_cutoff_y, :] = pants_mask[top_pants_y:thigh_cutoff_y, :]
            inpaint_mask = inpaint_mask | kurta_thigh_mask

    # 4. Strictly protected regions (never repainted)
    protected_classes = [
        ATR_CLASSES["Face"],
        ATR_CLASSES["Hair"],
        ATR_CLASSES["Hat"],
        ATR_CLASSES["Sunglasses"],
        ATR_CLASSES["Left-shoe"],
        ATR_CLASSES["Right-shoe"]
    ]
    
    # For standard upper, pants and legs are strictly protected
    if category not in ["extended_kurta", "kurta", "kameez"]:
        protected_classes.extend([
            ATR_CLASSES["Pants"],
            ATR_CLASSES["Skirt"],
            ATR_CLASSES["Left-leg"],
            ATR_CLASSES["Right-leg"]
        ])
    else:
        # For kurta, protect lower legs and feet
        protected_classes.extend([
            ATR_CLASSES["Left-leg"],
            ATR_CLASSES["Right-leg"]
        ])

    protect_mask = np.isin(parse_map, protected_classes)

    # 5. Apply protection subtraction
    final_binary = inpaint_mask & (~protect_mask)

    # Check minimum clothing pixel count
    clothing_pixel_count = np.sum(final_binary)
    if clothing_pixel_count < (w * h * 0.02):
        logger.warning("SegFormer detected negligible upper-body clothing (<2% of image). Falling back to anatomical mask.")
        return create_anatomical_upper_mask(image_size=target_size)

    # 6. Dilation
    if dilate_kernel_size > 0 and HAS_SCIPY:
        iterations = max(1, dilate_kernel_size // 5)
        dilated = ndimage.binary_dilation(final_binary, iterations=iterations)
        dilated[protect_mask] = False
        mask_uint8 = (dilated.astype(np.uint8)) * 255
    else:
        mask_uint8 = (final_binary.astype(np.uint8)) * 255

    mask_pil = Image.fromarray(mask_uint8).resize(target_size, Image.NEAREST)

    # 7. Gaussian blur
    if blur_radius > 0:
        mask_pil = mask_pil.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    return mask_pil
