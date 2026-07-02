"""Tests for config serialization and round-trip."""
from image_ops import config_to_yaml_text, load_yaml, save_config_file


def test_config_to_yaml_text_contains_keys():
    text = config_to_yaml_text(
        {
            "output_format": "jpg",
            "resize_width": 100,
            "resize_height": 200,
            "maintain_aspect_ratio": True,
            "enable_resize": False,
            "rotate_degrees": 15,
            "grayscale": False,
            "quality": 88,
            "gif_frame": 1,
        },
        input_format="png",
    )
    assert "input_format: png" in text
    assert "output_format: jpg" in text
    assert "resize_width: 100" in text
    assert "maintain_aspect_ratio: true" in text
    assert "enable_resize: false" in text
    assert "quality: 88" in text


def test_save_and_load_roundtrip(tmp_path):
    path = str(tmp_path / "round.yaml")
    settings = {
        "output_format": "webp",
        "resize_width": 640,
        "resize_height": 480,
        "maintain_aspect_ratio": False,
        "enable_resize": True,
        "rotate_degrees": 45,
        "grayscale": True,
        "quality": 60,
        "gif_frame": 3,
    }
    save_config_file(path, settings, input_format="gif")
    loaded = load_yaml(path)
    assert loaded["input_format"] == "gif"
    assert loaded["output_format"] == "webp"
    assert loaded["resize_width"] == 640
    assert loaded["resize_height"] == 480
    assert loaded["maintain_aspect_ratio"] is False
    assert loaded["enable_resize"] is True
    assert loaded["rotate_degrees"] == 45
    assert loaded["grayscale"] is True
    assert loaded["quality"] == 60
    assert loaded["gif_frame"] == 3


def test_load_project_default_config():
    """Smoke-test the repo's config.yaml if present."""
    import os

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cfg_path = os.path.join(root, "config.yaml")
    if not os.path.isfile(cfg_path):
        return
    cfg = load_yaml(cfg_path)
    assert "output_format" in cfg
