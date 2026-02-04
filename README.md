# Image Converter Desktop Application

A Python-based desktop application for converting images between different formats with various transformations using PIL (Pillow).

## Features
- Support for input formats: JPG, JPEG, PNG, WEBP, GIF (with frame selection for GIF)
- Output formats: JPG, JPEG, PNG, WEBP
- Batch processing: select and convert multiple images at once
- GIF support: auto-detects & shows frame count below preview when GIF selected
- Transformations:
  - Resize (optional; unchecked preserves original dimensions) with optional aspect ratio maintenance
  - Rotate by specified degrees
  - Convert to grayscale (remove colors)
  - Quality adjustment for JPG/WEBP
- Reusable config.yaml for pre-loading settings
- Simple Tkinter GUI

## Requirements
- Python 3.x
- Pillow (PIL) library: `pip install pillow`

## Usage
1. Run the application: `python image_converter.py`
2. Browse and select one or more input images (multi-select supported)
3. Choose output format
4. Select output directory (images will be saved with original base names + new format)
5. Apply desired transformations (applied to all images)
6. Click "Convert Batch" (output folder auto-opens after success)
7. Use Config section to browse/load/save multiple reusable config files (e.g. different presets)

## Config Files
Supports multiple user-selected .yaml files (default: config.yaml) for saving/loading settings. Browse button allows selecting/creating different configs for various use cases.

