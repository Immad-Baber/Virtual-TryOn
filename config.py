"""
AI-Powered Universal Virtual Try-On - Configuration Module
============================================================
Centralizes all system configuration, model paths, validation rules,
and privacy parameters for both local CPU development and Colab GPU execution.
"""

import os
from pathlib import Path
import torch

# Base Directories
BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = BASE_DIR / "sample_images"
TEMP_DIR = BASE_DIR / "temp_uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

# Ensure runtime directories exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Hardware & Execution Environment
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
USE_MOCK_FALLBACK = not torch.cuda.is_available()  # Automatically use safe mock when GPU unavailable
USE_TF32 = True if torch.cuda.is_available() else False
DEFAULT_MIXED_PRECISION = "bf16" if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else ("fp16" if torch.cuda.is_available() else "no")

# Model Repositories (Academic & Free-Access)
# Base Inpainting Model: Public, un-gated Stable Diffusion 1.5 inpainting backbone
BASE_MODEL_ID = "booksforcharlie/stable-diffusion-inpainting"
VAE_MODEL_ID = "stabilityai/sd-vae-ft-mse"
CATVTON_REPO_ID = "zhengchong/CatVTON"
CATVTON_MASKFREE_REPO_ID = "zhengchong/CatVTON-MaskFree"

# Segmentation / AutoMasking Model (Pure PyTorch, Zero-C++ Build Dependency)
SEGFORMER_CLOTHES_ID = "mattmdjaga/segformer_b2_clothes"

# Default Model Resolution & Quality
DEFAULT_WIDTH = 768
DEFAULT_HEIGHT = 1024
LOW_RES_WIDTH = 384
LOW_RES_HEIGHT = 512

# Default Generation Hyperparameters
DEFAULT_STEPS = 35
MIN_STEPS = 15
MAX_STEPS = 60
DEFAULT_GUIDANCE_SCALE = 2.5
MIN_GUIDANCE_SCALE = 1.0
MAX_GUIDANCE_SCALE = 7.0

# Image & Upload Validation Rules
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit
MIN_IMAGE_DIMENSION = 256
MAX_IMAGE_DIMENSION = 4096

# Privacy Policy & Ephemeral Storage
AUTO_DELETE_TEMP_FILES = True
MAX_TEMP_FILE_AGE_SECONDS = 300  # Clean files older than 5 minutes
PERSIST_USER_UPLOADS = False     # Never store sensitive personal user photos permanently
PRIVACY_DISCLAIMER = (
    "Privacy Notice: Uploaded photos are processed ephemerally in memory/temporary "
    "scratch space and are automatically purged. Images are never permanently retained, "
    "shared, or used for model training without explicit consent."
)
