"""
Unit Tests for Privacy & Ephemeral Storage Module
"""

import time
from pathlib import Path
from PIL import Image

import config
from utils.privacy import (
    save_ephemeral_image,
    purge_file,
    purge_ephemeral_directory
)


def test_save_and_purge_file():
    img = Image.new("RGB", (256, 256), (50, 100, 150))
    saved_path = save_ephemeral_image(img, prefix="test_priv")

    assert saved_path.exists()
    assert saved_path.is_file()

    purged = purge_file(saved_path)
    assert purged is True
    assert not saved_path.exists()


def test_purge_ephemeral_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "TEMP_DIR", tmp_path)

    # Create stale file
    stale_file = tmp_path / "stale.png"
    stale_file.write_text("dummy")

    # Manually age file
    past = time.time() - 400
    import os
    os.utime(stale_file, (past, past))

    # Create fresh file
    fresh_file = tmp_path / "fresh.png"
    fresh_file.write_text("dummy fresh")

    deleted = purge_ephemeral_directory(max_age_seconds=300)
    assert deleted == 1
    assert not stale_file.exists()
    assert fresh_file.exists()
