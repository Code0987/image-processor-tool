"""Pure image/config helpers used by the GUI and tests (no Tkinter)."""
import os

from PIL import Image, ImageOps, ImageSequence


def load_yaml(file_path):
    """Load a flat key: value YAML-like config file into a dict."""
    config = {}
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        # Convert types
                        if value.lower() == 'true':
                            value = True
                        elif value.lower() == 'false':
                            value = False
                        elif value.isdigit():
                            value = int(value)
                        elif value.replace('.', '', 1).isdigit():
                            value = float(value)
                        config[key] = value
    except Exception:
        pass
    return config


def is_positive_int_or_empty(value):
    """Return True if value is '' or an int >= 0 (for entry validation)."""
    if value == "":
        return True
    try:
        return int(value) >= 0
    except (TypeError, ValueError):
        return False


def is_valid_quality(value):
    """Return True if value is '' or an int in 1..100."""
    if value == "":
        return True
    try:
        return 1 <= int(value) <= 100
    except (TypeError, ValueError):
        return False


def extract_gif_frame(img, frame_index=0):
    """Return a single frame from an animated image; falls back to first frame."""
    frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
    if not frames:
        return img
    index = max(0, frame_index)
    if index < len(frames):
        return frames[index]
    return frames[0]


def count_gif_frames(file_path):
    """Return number of frames in a GIF (or multi-frame) image file."""
    with Image.open(file_path) as img:
        return sum(1 for _ in ImageSequence.Iterator(img))


def apply_transforms(
    img,
    *,
    enable_resize=False,
    resize_width=800,
    resize_height=600,
    maintain_aspect=True,
    rotate_degrees=0,
    grayscale=False,
):
    """Apply resize / rotate / grayscale transforms and return the result."""
    if enable_resize:
        width = max(1, int(resize_width))
        height = max(1, int(resize_height))
        if maintain_aspect:
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
        else:
            img = img.resize((width, height), Image.Resampling.LANCZOS)

    degrees = max(0, min(360, int(rotate_degrees)))
    if degrees != 0:
        img = img.rotate(degrees, expand=True)

    if grayscale:
        img = ImageOps.grayscale(img)

    return img


def build_output_path(input_path, output_dir, output_format):
    """Build output path: <output_dir>/<basename>.<format>."""
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    return os.path.join(output_dir, f"{base_name}.{output_format}")


def save_image(img, output_path, output_format, quality=85):
    """Save image with format-appropriate options. Returns the path written."""
    output_format = output_format.lower()
    save_kwargs = {}
    quality = max(1, min(100, int(quality)))
    if output_format in ('jpg', 'jpeg', 'webp'):
        save_kwargs['quality'] = quality
    if output_format == 'webp':
        save_kwargs['method'] = 6

    pil_format = 'JPEG' if output_format == 'jpg' else output_format.upper()
    # JPEG cannot save palette/RGBA modes without conversion
    if pil_format == 'JPEG' and img.mode in ('RGBA', 'P', 'LA'):
        img = img.convert('RGB')
    img.save(output_path, format=pil_format, **save_kwargs)
    return output_path


def convert_single_image(
    input_path,
    output_dir,
    output_format,
    *,
    enable_resize=False,
    resize_width=800,
    resize_height=600,
    maintain_aspect=True,
    rotate_degrees=0,
    grayscale=False,
    quality=85,
    gif_frame=0,
):
    """Open, transform, and save one image. Returns output path."""
    with Image.open(input_path) as opened:
        # Extract GIF frame while the file handle is still open (multi-frame)
        if input_path.lower().endswith('.gif'):
            img = extract_gif_frame(opened, gif_frame)
        else:
            img = opened.copy()

    img = apply_transforms(
        img,
        enable_resize=enable_resize,
        resize_width=resize_width,
        resize_height=resize_height,
        maintain_aspect=maintain_aspect,
        rotate_degrees=rotate_degrees,
        grayscale=grayscale,
    )

    output_path = build_output_path(input_path, output_dir, output_format.lower())
    return save_image(img, output_path, output_format, quality=quality)


def config_to_yaml_text(settings, input_format='jpg'):
    """Serialize settings dict to simple YAML text."""
    lines = [
        "# Image Converter Configuration",
        f"input_format: {input_format}",
        f"output_format: {settings.get('output_format', 'png')}",
        f"resize_width: {settings.get('resize_width', 800)}",
        f"resize_height: {settings.get('resize_height', 600)}",
        f"maintain_aspect_ratio: {str(settings.get('maintain_aspect_ratio', True)).lower()}",
        f"enable_resize: {str(settings.get('enable_resize', False)).lower()}",
        f"rotate_degrees: {settings.get('rotate_degrees', 0)}",
        f"grayscale: {str(settings.get('grayscale', False)).lower()}",
        f"quality: {settings.get('quality', 85)}",
        f"gif_frame: {settings.get('gif_frame', 0)}",
        "",
    ]
    return "\n".join(lines)


def save_config_file(config_file, settings, input_format='jpg'):
    """Write settings to a config file path."""
    with open(config_file, 'w') as f:
        f.write(config_to_yaml_text(settings, input_format=input_format))
    return config_file
