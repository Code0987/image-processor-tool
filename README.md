# Image Converter Desktop Application

A Python-based desktop application for converting images between different formats with various transformations using PIL (Pillow).

## Features
- Support for input formats: JPG, JPEG, PNG, WEBP, GIF (with frame selection for GIF)
- Output formats: JPG, JPEG, PNG, WEBP
- Batch processing: select and convert multiple images at once
- Transformations:
  - Resize with optional aspect ratio maintenance
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
6. Click "Convert Batch"
7. Use Save/Load Config for reusable settings

## Config File (config.yaml)
The application uses a config.yaml file to store default settings which can be modified and reloaded.

