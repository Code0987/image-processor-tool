"""Tests for load_yaml."""
from image_ops import load_yaml


def test_load_yaml_types_and_comments(sample_config_path):
    cfg = load_yaml(sample_config_path)
    assert cfg["input_format"] == "png"
    assert cfg["output_format"] == "webp"
    assert cfg["resize_width"] == 320
    assert cfg["resize_height"] == 240
    assert cfg["maintain_aspect_ratio"] is False
    assert cfg["enable_resize"] is True
    assert cfg["rotate_degrees"] == 90
    assert cfg["grayscale"] is True
    assert cfg["quality"] == 70
    assert cfg["gif_frame"] == 2


def test_load_yaml_missing_file_returns_empty(tmp_path):
    assert load_yaml(str(tmp_path / "nope.yaml")) == {}


def test_load_yaml_empty_file(tmp_path):
    p = tmp_path / "empty.yaml"
    p.write_text("")
    assert load_yaml(str(p)) == {}


def test_load_yaml_ignores_comments_and_blank_lines(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("# comment\n\nfoo: 1\n# another\nbar: true\n")
    assert load_yaml(str(p)) == {"foo": 1, "bar": True}


def test_load_yaml_float(tmp_path):
    p = tmp_path / "f.yaml"
    p.write_text("scale: 1.5\n")
    assert load_yaml(str(p)) == {"scale": 1.5}


def test_load_yaml_string_with_spaces(tmp_path):
    p = tmp_path / "s.yaml"
    p.write_text("name: hello world\n")
    assert load_yaml(str(p)) == {"name": "hello world"}
