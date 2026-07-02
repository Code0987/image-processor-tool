"""Shared fixtures for image converter tests."""
import os
import sys

import pytest
from PIL import Image

# Ensure project root is on path when running pytest from anywhere
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture
def tmp_img_dir(tmp_path):
    """Directory for generated images and outputs."""
    input_dir = tmp_path / "inputs"
    output_dir = tmp_path / "outputs"
    input_dir.mkdir()
    output_dir.mkdir()
    return {"input": input_dir, "output": output_dir, "root": tmp_path}


@pytest.fixture
def rgb_png(tmp_img_dir):
    """Create a simple 100x50 RGB PNG."""
    path = tmp_img_dir["input"] / "sample.png"
    Image.new("RGB", (100, 50), color=(255, 0, 0)).save(path)
    return str(path)


@pytest.fixture
def rgba_png(tmp_img_dir):
    """Create an RGBA PNG (needs conversion for JPEG)."""
    path = tmp_img_dir["input"] / "alpha.png"
    Image.new("RGBA", (80, 60), color=(0, 255, 0, 128)).save(path)
    return str(path)


@pytest.fixture
def multi_frame_gif(tmp_img_dir):
    """Create a 3-frame GIF with distinct solid colors."""
    path = tmp_img_dir["input"] / "anim.gif"
    frames = [
        Image.new("RGB", (40, 40), color=(255, 0, 0)),
        Image.new("RGB", (40, 40), color=(0, 255, 0)),
        Image.new("RGB", (40, 40), color=(0, 0, 255)),
    ]
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=100,
        loop=0,
    )
    return str(path)


@pytest.fixture
def sample_config_path(tmp_img_dir):
    """Write a sample config.yaml and return its path."""
    path = tmp_img_dir["root"] / "test_config.yaml"
    path.write_text(
        """# test config
input_format: png
output_format: webp
resize_width: 320
resize_height: 240
maintain_aspect_ratio: false
enable_resize: true
rotate_degrees: 90
grayscale: true
quality: 70
gif_frame: 2
"""
    )
    return str(path)
