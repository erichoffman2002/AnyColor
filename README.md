# AnyColor

A PyQt6-based application for color adjustments and effects on images. This tool allows you to apply various color adjustments, special effects, and glow/border effects to images.

## Features

- Color balance adjustments (Cyan-Red, Magenta-Green, Yellow-Blue)
- Hue rotation
- Special effects (Negative, Greyscale, Neon Outburst, etc.)
- Glow and border effects with customizable colors and widths
- Directory batch processing
- Real-time preview
- Support for transparent backgrounds

## Requirements

- Python 3.6+
- PyQt6
- Pillow (PIL)
- NumPy

## Installation

1. Clone the repository:
```bash
git clone https://github.com/erichoffman2002/AnyColor.git
```

2. Install the required packages:
```bash
pip install PyQt6 Pillow numpy
```

## Usage

Run the application:
```bash
python AnyColor.py
```

1. Click "Load Directory" to select a directory containing PNG images
2. Use the color adjustment sliders to modify the image colors
3. Apply special effects from the "Special Effects" tab
4. Add glow or border effects from the "Glow/Border" tab
5. Save individual images or process the entire directory

## License

This project is licensed under the MIT License - see the LICENSE file for details. 