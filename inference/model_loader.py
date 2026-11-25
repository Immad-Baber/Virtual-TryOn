"""
Model Loader Module
===================
Provides safe, modular initialization and loading of CatVTON diffusion weights,
device placement, memory monitoring, and graceful fallback to MockPipeline when
running on unsupported local hardware (like Intel UHD 620 iGPU).
"""

import os
import logging
import torch
from typing import Tuple, Any, Optional

import config

logger = logging.getLogger("VirtualTryOn.ModelLoader")


def get_hardware_info() -> dict:
    """
    Returns diagnostic information about host GPU and memory.
    """
    info = {
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU (Intel / Host)",
        "total_memory_gb": 0.0,
        "free_memory_gb": 0.0,
        "mode": "GPU (Accelerated Diffusion)" if torch.cuda.is_available() else "CPU (Mock / Diagnostic Mode)"
    }

    if torch.cuda.is_available():
        free_bytes, total_bytes = torch.cuda.mem_get_info(0)
        info["total_memory_gb"] = round(total_bytes / (1024 ** 3), 2)
        info["free_memory_gb"] = round(free_bytes / (1024 ** 3), 2)

    return info


def load_tryon_pipeline(
    base_model_path: str = config.BASE_MODEL_ID,
    catvton_repo_path: str = config.CATVTON_REPO_ID,
    version: str = "mix",
    mixed_precision: str = config.DEFAULT_MIXED_PRECISION,
    force_mock: bool = False
) -> Tuple[Any, dict]:
    """
    Loads the Virtual Try-On pipeline.
    
    If CUDA is available and force_mock is False, instantiates the real CatVTONPipeline.
    Otherwise, instantiates MockTryOnPipeline to allow zero-crash UI development and testing.
    
    Returns:
        (pipeline_instance, status_dict)
    """
    hw_info = get_hardware_info()

    if force_mock or not hw_info["cuda_available"]:
        logger.info("Using MockTryOnPipeline (CPU mode / no compatible NVIDIA GPU detected).")
        from inference.mock_pipeline import MockTryOnPipeline
        pipeline = MockTryOnPipeline(device="cpu")
        status = {
            "status": "ready_mock",
            "device": "cpu",
            "message": "Running on CPU in prototype mode. Launch on Google Colab T4 for neural diffusion inference.",
            "hardware": hw_info
        }
        return pipeline, status

    # CUDA is available - Load genuine CatVTON
    try:
        from huggingface_hub import snapshot_download
        from inference.pipeline import CatVTONPipeline
        from utils.catvton_utils import init_weight_dtype

        logger.info(f"Downloading/Verifying CatVTON checkpoints from {catvton_repo_path}...")
        repo_local_path = snapshot_download(repo_id=catvton_repo_path)

        weight_dtype = init_weight_dtype(mixed_precision)

        logger.info(f"Instantiating CatVTONPipeline with base={base_model_path}, precision={mixed_precision}...")
        pipeline = CatVTONPipeline(
            base_ckpt=base_model_path,
            attn_ckpt=repo_local_path,
            attn_ckpt_version=version,
            weight_dtype=weight_dtype,
            use_tf32=config.USE_TF32,
            device="cuda"
        )

        status = {
            "status": "ready_gpu",
            "device": "cuda",
            "message": f"CatVTON diffusion model loaded successfully on {hw_info['device_name']} ({hw_info['free_memory_gb']} GB free VRAM).",
            "hardware": hw_info
        }
        return pipeline, status

    except Exception as e:
        logger.error(f"Failed to load CatVTON model onto GPU: {e}. Falling back to MockPipeline.")
        from inference.mock_pipeline import MockTryOnPipeline
        pipeline = MockTryOnPipeline(device="cpu")
        status = {
            "status": "error_fallback_to_mock",
            "device": "cpu",
            "error": str(e),
            "message": f"GPU loading error: {e}. Active fallback: Mock pipeline.",
            "hardware": hw_info
        }
        return pipeline, status
