# Image Converter Desktop Application

A Python-based desktop application for converting images between different formats with various transformations using PIL (Pillow).

## Features
- Support for input formats: JPG, JPEG, PNG, WEBP, GIF (with frame selection for GIF)
- Output formats: JPG, JPEG, PNG, WEBP
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
2. Select input image
3. Choose output format and path
4. Apply desired transformations
5. Click Convert
6. Use Save/Load Config for reusable settings

## Config File (config.yaml)
The application uses a config.yaml file to store default settings which can be modified and reloaded.

