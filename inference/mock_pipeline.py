"""
Mock Try-On Pipeline Module
============================
Used when a dedicated NVIDIA GPU is unavailable (such as local laptops with
integrated graphics like Intel UHD 620).

Allows the full application UI, input validation, mask visualization, image processing,
and download workflow to be tested locally without crashing or causing Out-Of-Memory errors.
Clearly watermarks outputs to maintain absolute academic honesty.
"""

import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Optional, Callable

import config
from utils.image_processing import resize_and_crop, resize_and_padding, ensure_rgb


class MockTryOnPipeline:
    """
    Simulates the CatVTON inference pipeline on CPU for UI testing and verification.
    """
    def __init__(self, device: str = "cpu"):
        self.device = device
        self.is_mock = True

    def __call__(
        self,
        image: Image.Image,
        condition_image: Image.Image,
        mask: Optional[Image.Image] = None,
        num_inference_steps: int = 35,
        guidance_scale: float = 2.5,
        generator=None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        **kwargs
    ) -> Image.Image:
        """
        Simulates diffusion steps with simulated progress, then produces a
        composited prototype preview with an academic disclaimer watermark.
        """
        # Step 1: Preprocess inputs
        target_size = (config.DEFAULT_WIDTH, config.DEFAULT_HEIGHT)
        person = resize_and_crop(ensure_rgb(image), target_size)
        cloth = resize_and_padding(ensure_rgb(condition_image), target_size)

        # Step 2: Fallback mask if not supplied
        if mask is None:
            # Generate a standard upper-body rectangular mask
            mask_np = np.zeros((config.DEFAULT_HEIGHT, config.DEFAULT_WIDTH), dtype=np.uint8)
            # Torso region: 30% from top to 75% from top
            y_start = int(config.DEFAULT_HEIGHT * 0.28)
            y_end = int(config.DEFAULT_HEIGHT * 0.75)
            x_start = int(config.DEFAULT_WIDTH * 0.20)
            x_end = int(config.DEFAULT_WIDTH * 0.80)
            mask_np[y_start:y_end, x_start:x_end] = 255
            mask = Image.fromarray(mask_np)
        else:
            mask = mask.convert("L").resize(target_size, Image.NEAREST)

        mask_np = np.array(mask) > 128

        # Step 3: Simulate diffusion progress
        sim_steps = min(num_inference_steps, 10)
        for step in range(sim_steps):
            if progress_callback:
                progress_callback((step + 1) / sim_steps, f"Simulating denoising step {step + 1}/{num_inference_steps}...")
            time.sleep(0.04)

        # Step 4: Create composited simulation
        person_np = np.array(person).astype(np.float32)
        cloth_np = np.array(cloth).astype(np.float32)

        # Invert cloth white background to isolate garment
        is_cloth_white = (cloth_np[:, :, 0] > 240) & (cloth_np[:, :, 1] > 240) & (cloth_np[:, :, 2] > 240)
        garment_mask = mask_np & (~is_cloth_white)

        # Composite garment onto person
        result_np = person_np.copy()
        result_np[garment_mask] = cloth_np[garment_mask] * 0.85 + person_np[garment_mask] * 0.15
        result_img = Image.fromarray(np.clip(result_np, 0, 255).astype(np.uint8))

        # Step 5: Add academic honesty disclaimer banner
        draw = ImageDraw.Draw(result_img)
        banner_height = 42
        w, h = result_img.size
        draw.rectangle([(0, h - banner_height), (w, h)], fill=(30, 41, 59))
        text = "PROTOTYPE CPU PREVIEW  |  Run in Google Colab T4 GPU for CatVTON Diffusion Model"
        draw.text((w // 2, h - banner_height // 2), text, fill=(241, 245, 249), anchor="mm")

        return result_img
