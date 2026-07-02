"""Tests for image transforms and GIF handling."""
from PIL import Image

from image_ops import apply_transforms, count_gif_frames, extract_gif_frame


def test_resize_disabled_preserves_size():
    img = Image.new("RGB", (100, 50), color=(1, 2, 3))
    out = apply_transforms(img, enable_resize=False, resize_width=10, resize_height=10)
    assert out.size == (100, 50)


def test_resize_exact_without_aspect():
    img = Image.new("RGB", (100, 50), color=(1, 2, 3))
    out = apply_transforms(
        img,
        enable_resize=True,
        resize_width=40,
        resize_height=20,
        maintain_aspect=False,
    )
    assert out.size == (40, 20)


def test_resize_with_aspect_fits_inside_box():
    img = Image.new("RGB", (100, 50), color=(1, 2, 3))
    out = apply_transforms(
        img,
        enable_resize=True,
        resize_width=50,
        resize_height=50,
        maintain_aspect=True,
    )
    # 100x50 scaled to fit in 50x50 -> 50x25
    assert out.size == (50, 25)


def test_grayscale_mode():
    img = Image.new("RGB", (10, 10), color=(255, 0, 0))
    out = apply_transforms(img, grayscale=True)
    assert out.mode in ("L", "LA")


def test_rotate_zero_no_change():
    img = Image.new("RGB", (20, 10), color=(0, 0, 0))
    out = apply_transforms(img, rotate_degrees=0)
    assert out.size == (20, 10)


def test_rotate_90_swaps_dimensions():
    img = Image.new("RGB", (20, 10), color=(0, 0, 0))
    out = apply_transforms(img, rotate_degrees=90)
    assert out.size == (10, 20)


def test_rotate_clamped_to_360_is_noop_like():
    img = Image.new("RGB", (20, 10), color=(0, 0, 0))
    # 360 degrees is full rotation; expand still yields same logical orientation
    out = apply_transforms(img, rotate_degrees=360)
    assert out.size == (20, 10)


def test_count_gif_frames(multi_frame_gif):
    assert count_gif_frames(multi_frame_gif) == 3


def test_extract_gif_frame_by_index(multi_frame_gif):
    # GIF frames are often palette mode — compare as RGB
    with Image.open(multi_frame_gif) as img:
        frame0 = extract_gif_frame(img, 0).convert("RGB")
    with Image.open(multi_frame_gif) as img:
        frame1 = extract_gif_frame(img, 1).convert("RGB")
    with Image.open(multi_frame_gif) as img:
        frame2 = extract_gif_frame(img, 2).convert("RGB")
    # Distinct solid colors
    assert frame0.getpixel((0, 0)) == (255, 0, 0)
    assert frame1.getpixel((0, 0)) == (0, 255, 0)
    assert frame2.getpixel((0, 0)) == (0, 0, 255)


def test_extract_gif_frame_out_of_range_falls_back_to_first(multi_frame_gif):
    with Image.open(multi_frame_gif) as img:
        frame = extract_gif_frame(img, 99).convert("RGB")
    assert frame.getpixel((0, 0)) == (255, 0, 0)
