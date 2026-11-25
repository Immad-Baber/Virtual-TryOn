"""
Tests for Evaluation Metrics Module
"""

import numpy as np
from PIL import Image
from evaluation.metrics import compute_ssim_numpy, evaluate_identity_preservation


def test_compute_ssim_identical():
    img1 = np.ones((100, 100, 3), dtype=np.uint8) * 128
    img2 = np.ones((100, 100, 3), dtype=np.uint8) * 128
    ssim_val = compute_ssim_numpy(img1, img2)
    assert abs(ssim_val - 1.0) < 1e-4


def test_evaluate_identity_preservation():
    p = Image.new("RGB", (768, 1024), (200, 150, 100))
    r = Image.new("RGB", (768, 1024), (200, 150, 100))
    
    # Modify torso region in result
    r_np = np.array(r)
    r_np[300:600, :, :] = 0  # Inpainted region changed to black
    r_modified = Image.fromarray(r_np)
    
    res = evaluate_identity_preservation(p, r_modified)
    # Head and lower body were unchanged, so their SSIM must be 1.0
    assert abs(res["head_identity_ssim"] - 1.0) < 1e-3
    assert abs(res["lower_body_ssim"] - 1.0) < 1e-3
