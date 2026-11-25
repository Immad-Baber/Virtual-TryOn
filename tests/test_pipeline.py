"""
Unit Tests for TryOn Engine
"""

from PIL import Image
from inference.tryon import VirtualTryOnEngine


def test_tryon_engine_mock_execution():
    engine = VirtualTryOnEngine(force_mock=True)
    assert engine.is_mock is True

    person = Image.new("RGB", (768, 1024), (200, 180, 160))
    cloth = Image.new("RGB", (768, 1024), (20, 40, 180))

    result = engine.execute_tryon(
        person_image=person,
        cloth_image=cloth,
        num_inference_steps=5
    )

    assert result["success"] is True
    assert result["error"] is None
    assert result["result_image"] is not None
    assert result["comparison_grid"] is not None
    assert result["result_image"].size == (768, 1024)
