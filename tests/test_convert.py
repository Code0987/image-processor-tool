"""Tests for end-to-end single-image conversion and path building."""
import os

from PIL import Image

from image_ops import build_output_path, convert_single_image, save_image


def test_build_output_path():
    path = build_output_path("/tmp/photos/cat.JPEG", "/out", "png")
    assert path == os.path.join("/out", "cat.png")


def test_convert_png_to_jpg(rgb_png, tmp_img_dir):
    out_dir = str(tmp_img_dir["output"])
    result = convert_single_image(rgb_png, out_dir, "jpg", quality=90)
    assert os.path.isfile(result)
    assert result.endswith(".jpg")
    with Image.open(result) as img:
        assert img.format == "JPEG"
        assert img.size == (100, 50)


def test_convert_with_resize_and_grayscale(rgb_png, tmp_img_dir):
    out_dir = str(tmp_img_dir["output"])
    result = convert_single_image(
        rgb_png,
        out_dir,
        "png",
        enable_resize=True,
        resize_width=50,
        resize_height=50,
        maintain_aspect=True,
        grayscale=True,
    )
    with Image.open(result) as img:
        assert img.size == (50, 25)
        assert img.mode in ("L", "LA")


def test_convert_rgba_to_jpeg(rgba_png, tmp_img_dir):
    """RGBA must be converted so JPEG save does not fail."""
    out_dir = str(tmp_img_dir["output"])
    result = convert_single_image(rgba_png, out_dir, "jpg")
    with Image.open(result) as img:
        assert img.format == "JPEG"
        assert img.mode == "RGB"


def test_convert_gif_frame(multi_frame_gif, tmp_img_dir):
    out_dir = str(tmp_img_dir["output"])
    result = convert_single_image(multi_frame_gif, out_dir, "png", gif_frame=1)
    with Image.open(result) as img:
        # Second frame is green
        assert img.convert("RGB").getpixel((0, 0)) == (0, 255, 0)


def test_convert_webp(rgb_png, tmp_img_dir):
    out_dir = str(tmp_img_dir["output"])
    result = convert_single_image(rgb_png, out_dir, "webp", quality=80)
    with Image.open(result) as img:
        assert img.format == "WEBP"


def test_batch_style_multiple_inputs(rgb_png, rgba_png, tmp_img_dir):
    out_dir = str(tmp_img_dir["output"])
    paths = []
    for src in (rgb_png, rgba_png):
        paths.append(convert_single_image(src, out_dir, "png"))
    assert len(paths) == 2
    assert all(os.path.isfile(p) for p in paths)
    names = {os.path.basename(p) for p in paths}
    assert names == {"sample.png", "alpha.png"}


def test_save_image_quality_clamped(tmp_img_dir):
    img = Image.new("RGB", (8, 8), color=(10, 20, 30))
    path = str(tmp_img_dir["output"] / "q.jpg")
    # Extreme quality values should not raise
    save_image(img, path, "jpg", quality=999)
    assert os.path.isfile(path)
