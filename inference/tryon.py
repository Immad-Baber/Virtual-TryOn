"""
Virtual Try-On Engine (Orchestrator)
=====================================
Coordinates the end-to-end Virtual Try-On execution:
1. Pair validation (dimensions, formats, security)
2. Preprocessing & aspect-ratio normalization
3. Mask acquisition (user brush, SegFormer segmentation, or anatomical default)
4. Model inference (CatVTON on GPU or MockPipeline on CPU)
5. Comparison banner generation and ephemeral cleanup
"""

import time
import logging
from typing import Optional, Tuple, Dict, Any, Callable
from PIL import Image

import config
from utils.validation import validate_tryon_pair, ValidationResult
from utils.image_processing import (
    ensure_rgb,
    resize_and_crop,
    resize_and_padding,
    visualize_mask,
    create_comparison_grid
)
from utils.privacy import purge_ephemeral_directory
from inference.model_loader import load_tryon_pipeline

logger = logging.getLogger("VirtualTryOn.Engine")


class VirtualTryOnEngine:
    """
    Unified controller for virtual try-on inference.
    """
    def __init__(
        self,
        base_model_path: str = config.BASE_MODEL_ID,
        catvton_repo_path: str = config.CATVTON_REPO_ID,
        force_mock: bool = False
    ):
        self.pipeline, self.status = load_tryon_pipeline(
            base_model_path=base_model_path,
            catvton_repo_path=catvton_repo_path,
            force_mock=force_mock
        )
        self.is_mock = getattr(self.pipeline, "is_mock", False)

    def execute_tryon(
        self,
        person_image: Image.Image,
        cloth_image: Image.Image,
        user_mask: Optional[Image.Image] = None,
        cloth_type: str = "upper",
        num_inference_steps: int = config.DEFAULT_STEPS,
        guidance_scale: float = config.DEFAULT_GUIDANCE_SCALE,
        seed: int = 42,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes the virtual try-on workflow.

        Returns a dictionary:
        {
            "success": bool,
            "error": Optional[str],
            "result_image": PIL.Image,
            "comparison_grid": PIL.Image,
            "mask_preview": PIL.Image,
            "latency_seconds": float,
            "mode": str
        }
        """
        start_time = time.time()

        # Step 1: Validate inputs
        if progress_callback:
            progress_callback(0.05, "Validating input images...")

        val_res = validate_tryon_pair(person_image, cloth_image)
        if not val_res.is_valid:
            return {
                "success": False,
                "error": val_res.error_message,
                "result_image": None,
                "comparison_grid": None,
                "mask_preview": None,
                "latency_seconds": 0.0,
                "mode": "Error"
            }

        # Step 2: Ensure standard RGB format
        person_rgb = ensure_rgb(person_image)
        cloth_rgb = ensure_rgb(cloth_image)

        target_size = (config.DEFAULT_WIDTH, config.DEFAULT_HEIGHT)
        person_prepared = resize_and_crop(person_rgb, target_size)
        cloth_prepared = resize_and_padding(cloth_rgb, target_size)

        # Step 3: Handle inpainting mask
        if progress_callback:
            progress_callback(0.15, "Preparing garment mask...")

        active_mask = None
        if user_mask is not None:
            # User painted a custom mask in Gradio
            active_mask = user_mask.convert("L").resize(target_size, Image.NEAREST)

        # Generate mask preview overlay
        mask_preview = None
        if active_mask is not None:
            mask_preview = visualize_mask(person_prepared, active_mask)

        # Step 4: Run inference
        if progress_callback:
            progress_callback(0.25, f"Running try-on pipeline ({self.pipeline.__class__.__name__})...")

        try:
            if self.is_mock:
                result_image = self.pipeline(
                    image=person_prepared,
                    condition_image=cloth_prepared,
                    mask=active_mask,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    progress_callback=progress_callback
                )
            else:
                import torch
                generator = torch.Generator(device=config.DEVICE).manual_seed(seed) if seed != -1 else None

                # For genuine CatVTON, if no mask was drawn by user, generate one or use AutoMasker
                if active_mask is None:
                    # Default anatomical upper-body mask (covers torso and chest)
                    import numpy as np
                    m_arr = np.zeros((config.DEFAULT_HEIGHT, config.DEFAULT_WIDTH), dtype=np.uint8)
                    m_arr[int(config.DEFAULT_HEIGHT * 0.28):int(config.DEFAULT_HEIGHT * 0.78),
                          int(config.DEFAULT_WIDTH * 0.18):int(config.DEFAULT_WIDTH * 0.82)] = 255
                    active_mask = Image.fromarray(m_arr)
                    mask_preview = visualize_mask(person_prepared, active_mask)

                raw_output = self.pipeline(
                    image=person_prepared,
                    condition_image=cloth_prepared,
                    mask=active_mask,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    generator=generator
                )
                result_image = raw_output[0] if isinstance(raw_output, (list, tuple)) else raw_output

            if progress_callback:
                progress_callback(0.90, "Assembling comparison visualization...")

            # Step 5: Build side-by-side comparison banner
            comparison_grid = create_comparison_grid(
                person_image=person_prepared,
                cloth_image=cloth_prepared,
                result_image=result_image,
                mask_preview=mask_preview
            )

            # Step 6: Purge any stale ephemeral scratch files
            purge_ephemeral_directory()

            latency = round(time.time() - start_time, 2)
            mode_name = "Mock CPU (Local Dev)" if self.is_mock else "CatVTON Diffusion (GPU)"

            if progress_callback:
                progress_callback(1.0, f"Try-On completed in {latency}s!")

            return {
                "success": True,
                "error": None,
                "result_image": result_image,
                "comparison_grid": comparison_grid,
                "mask_preview": mask_preview,
                "latency_seconds": latency,
                "mode": mode_name
            }

        except Exception as e:
            logger.exception("Error during Virtual Try-On inference:")
            return {
                "success": False,
                "error": f"Inference pipeline error: {str(e)}",
                "result_image": None,
                "comparison_grid": None,
                "mask_preview": None,
                "latency_seconds": round(time.time() - start_time, 2),
                "mode": "Error"
            }
