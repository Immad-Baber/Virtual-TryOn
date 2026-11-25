"""
Image Processing Module
=======================
Handles aspect-ratio preserving resizing, smart padding, format conversion,
mask visualization, and side-by-side comparison grids for virtual try-on.
"""

from typing import Tuple, List, Optional
import numpy as np
from PIL import Image, ImageOps

import config


def ensure_rgb(image: Image.Image) -> Image.Image:
    """
    Ensures the image is in 3-channel RGB format.
    Handles transparency/alpha channels by blending onto a white background.
    """
    if image.mode == "RGB":
        return image
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        alpha_img = image.convert("RGBA")
        background = Image.new("RGBA", alpha_img.size, (255, 255, 255, 255))
        blended = Image.alpha_composite(background, alpha_img)
        return blended.convert("RGB")
    return image.convert("RGB")


def resize_and_crop(image: Image.Image, target_size: Tuple[int, int] = (config.DEFAULT_WIDTH, config.DEFAULT_HEIGHT)) -> Image.Image:
    """
    Crops the image to match the target aspect ratio, then resizes it using high-quality LANCZOS.
    Best for person images to fill the canvas without stretching or distortion.
    """
    w, h = image.size
    target_w, target_h = target_size

    target_ratio = target_w / target_h
    current_ratio = w / h

    if current_ratio < target_ratio:
        # Image is too tall -> crop top/bottom
        new_w = w
        new_h = int(w / target_ratio)
    else:
        # Image is too wide -> crop left/right
        new_h = h
        new_w = int(h * target_ratio)

    left = (w - new_w) // 2
    top = (h - new_h) // 2
    right = left + new_w
    bottom = top + new_h

    cropped = image.crop((left, top, right, bottom))
    return cropped.resize(target_size, Image.LANCZOS)


def resize_and_padding(
    image: Image.Image,
    target_size: Tuple[int, int] = (config.DEFAULT_WIDTH, config.DEFAULT_HEIGHT),
    pad_color: Tuple[int, int, int] = (255, 255, 255)
) -> Image.Image:
    """
    Resizes the clothing image while strictly preserving its original aspect ratio,
    then pads with white background to center it within the target dimensions.
    This ensures garments (shirts, kurtas) are never artificially distorted or squashed.
    """
    w, h = image.size
    target_w, target_h = target_size

    target_ratio = target_w / target_h
    current_ratio = w / h

    if current_ratio < target_ratio:
        # Fit height
        new_h = target_h
        new_w = max(1, int(w * target_h / h))
    else:
        # Fit width
        new_w = target_w
        new_h = max(1, int(h * target_w / w))

    resized_garment = image.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGB", target_size, pad_color)
    offset_x = (target_w - new_w) // 2
    offset_y = (target_h - new_h) // 2
    canvas.paste(resized_garment, (offset_x, offset_y))

    return canvas


def visualize_mask(image: Image.Image, mask: Image.Image, alpha: float = 0.5) -> Image.Image:
    """
    Visualizes the target inpainting mask as a colored semi-transparent overlay
    over the person image for visual verification and student debugging.
    """
    rgb_img = ensure_rgb(image).copy()
    w, h = rgb_img.size

    mask_l = mask.convert("L").resize((w, h), Image.NEAREST)
    mask_np = np.array(mask_l) > 128

    overlay = np.array(rgb_img).astype(np.float32)
    # Highlight inpaint region with a distinct soft cyan tint
    tint = np.array([0, 180, 240], dtype=np.float32)

    overlay[mask_np] = overlay[mask_np] * (1.0 - alpha) + tint * alpha
    overlay = np.clip(overlay, 0, 255).astype(np.uint8)

    return Image.fromarray(overlay)


def create_comparison_grid(
    person_image: Image.Image,
    cloth_image: Image.Image,
    result_image: Image.Image,
    mask_preview: Optional[Image.Image] = None,
    height: int = 512
) -> Image.Image:
    """
    Assembles a side-by-side comparison banner:
    [Original Person | Selected Garment | (Optional Mask) | Virtual Try-On Result]
    Scaled to a consistent height for easy downloading and portfolio presentation.
    """
    components = [person_image, cloth_image]
    if mask_preview is not None:
        components.append(mask_preview)
    components.append(result_image)

    # Resize all components to matching height while keeping their aspect ratio
    resized_components = []
    for img in components:
        w, h = img.size
        new_w = max(1, int(w * (height / h)))
        resized_components.append(ensure_rgb(img).resize((new_w, height), Image.LANCZOS))

    total_width = sum(img.size[0] for img in resized_components) + (len(resized_components) - 1) * 8
    grid = Image.new("RGB", (total_width, height), (245, 247, 250))

    x_offset = 0
    for img in resized_components:
        grid.paste(img, (x_offset, 0))
        x_offset += img.size[0] + 8

    return grid
