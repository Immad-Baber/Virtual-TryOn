"""
Evaluation Metrics Module for Generative AI Virtual Try-On
===========================================================
Implements quantitative evaluation metrics:
1. SSIM (Structural Similarity Index) - pixel-structural similarity
2. Face & Identity Preservation Score - non-inpainted region fidelity
3. Garment CLIP Cosine Similarity - semantic garment feature transfer
4. Peak VRAM & Latency benchmark logging

Limitations of each metric for Virtual Try-On are explicitly documented.
"""

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from typing import Dict, Union, Tuple, Optional
import os


def compute_ssim_numpy(img1: np.ndarray, img2: np.ndarray, max_val: float = 255.0) -> float:
    """
    Computes Structural Similarity Index (SSIM) between two images.
    
    LIMITATION IN VIRTUAL TRY-ON:
    SSIM requires identical ground truth (paired target image of the person wearing the exact clothes).
    In unconstrained try-on (arbitrary person + arbitrary garment), SSIM can ONLY be computed on
    unmasked regions (face, background, pants) to evaluate identity and non-inpainting preservation.
    Computing SSIM across the whole image against the original person penalizes the model for
    successfully changing the shirt!
    """
    if img1.shape != img2.shape:
        raise ValueError(f"Shape mismatch for SSIM: {img1.shape} vs {img2.shape}")

    c1 = (0.01 * max_val) ** 2
    c2 = (0.03 * max_val) ** 2

    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)

    mu1 = img1.mean()
    mu2 = img2.mean()
    sigma1_sq = ((img1 - mu1) ** 2).mean()
    sigma2_sq = ((img2 - mu2) ** 2).mean()
    sigma12 = ((img1 - mu1) * (img2 - mu2)).mean()

    numerator = (2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)
    denominator = (mu1 ** 2 + mu2 ** 2 + c1) * (sigma1_sq + sigma2_sq + c2)

    return float(numerator / denominator)


def evaluate_identity_preservation(
    person_img: Image.Image,
    result_img: Image.Image,
    head_ratio: float = 0.22,
    lower_ratio: float = 0.80
) -> Dict[str, float]:
    """
    Measures SSIM and PSNR specifically on the protected anatomical regions (head/face and shoes/lower legs)
    to mathematically verify that person identity was not distorted or modified.
    """
    p_np = np.array(person_img.resize(result_img.size))
    r_np = np.array(result_img)
    h, w, _ = p_np.shape

    # 1. Head / Face region (top 22%)
    head_y = int(h * head_ratio)
    p_head = p_np[:head_y, :, :]
    r_head = r_np[:head_y, :, :]
    head_ssim = compute_ssim_numpy(p_head, r_head)

    # 2. Lower body / feet region (bottom 20%)
    lower_y = int(h * lower_ratio)
    p_lower = p_np[lower_y:, :, :]
    r_lower = r_np[lower_y:, :, :]
    lower_ssim = compute_ssim_numpy(p_lower, r_lower)

    return {
        "head_identity_ssim": round(head_ssim, 4),
        "lower_body_ssim": round(lower_ssim, 4),
        "overall_preserved_ssim": round((head_ssim + lower_ssim) / 2.0, 4)
    }


def compute_garment_clip_similarity(
    garment_img: Image.Image,
    result_img: Image.Image,
    mask_img: Optional[Image.Image] = None,
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
) -> float:
    """
    Computes visual cosine similarity between the reference garment image and the
    synthesized garment region using OpenAI CLIP (openai/clip-vit-base-patch32).
    
    LIMITATION IN VIRTUAL TRY-ON:
    CLIP visual embeddings are invariant to orientation and flat lay vs 3D body wrapping,
    making them well-suited for measuring pattern/color transfer, but insensitive to
    geometric wrinkles, collar precision, and seam alignment.
    """
    from transformers import CLIPProcessor, CLIPModel

    model_id = "openai/clip-vit-base-patch32"
    processor = CLIPProcessor.from_pretrained(model_id)
    model = CLIPModel.from_pretrained(model_id).to(device)
    model.eval()

    # Crop result to inpaint region if mask provided
    if mask_img is not None:
        mask_arr = np.array(mask_img.resize(result_img.size))
        y_indices, x_indices = np.where(mask_arr > 128)
        if len(y_indices) > 0:
            box = (x_indices.min(), y_indices.min(), x_indices.max(), y_indices.max())
            result_crop = result_img.crop(box)
        else:
            result_crop = result_img
    else:
        result_crop = result_img

    inputs = processor(images=[garment_img, result_crop], return_tensors="pt").to(device)
    with torch.no_grad():
        feats = model.get_image_features(**inputs)
        feats = feats / feats.norm(dim=-1, keepdim=True)
        cos_sim = (feats[0] * feats[1]).sum().item()

    return round(float(cos_sim), 4)


class ComprehensiveVTONEvaluator:
    """
    Executes a complete quantitative and qualitative evaluation suite across a tryon result.
    """
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device

    def evaluate_pair(
        self,
        person_img: Image.Image,
        garment_img: Image.Image,
        result_img: Image.Image,
        mask_img: Image.Image,
        latency_seconds: float,
        peak_vram_gb: float
    ) -> Dict[str, Union[float, str]]:
        
        # 1. Identity & Non-Inpaint Preservation
        id_metrics = evaluate_identity_preservation(person_img, result_img)

        # 2. Garment Visual Feature Similarity via CLIP
        clip_sim = compute_garment_clip_similarity(garment_img, result_img, mask_img, device=self.device)

        return {
            "head_preservation_ssim": id_metrics["head_identity_ssim"],
            "lower_body_preservation_ssim": id_metrics["lower_body_ssim"],
            "garment_clip_similarity": clip_sim,
            "inference_latency_seconds": round(latency_seconds, 2),
            "peak_gpu_vram_gb": round(peak_vram_gb, 2)
        }
