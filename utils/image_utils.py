from typing import Tuple, Optional
import PIL.Image
from PIL import Image
from pathlib import Path

def get_image_dpi(image_path: str) -> Tuple[int, int]:
    """Get the DPI of an image."""
    try:
        with Image.open(image_path) as img:
            dpi = img.info.get('dpi', (300, 300))
            return (int(dpi[0]), int(dpi[1]))
    except Exception as e:
        return (300, 300)  # Default DPI if not found

def pixels_to_inches(pixels: float, dpi: int) -> float:
    """Convert pixels to inches based on DPI."""
    return pixels / dpi

def inches_to_pixels(inches: float, dpi: int) -> float:
    """Convert inches to pixels based on DPI."""
    return inches * dpi

def get_tiff_page_count(image_path: str) -> int:
    """Get the number of pages in a TIFF file."""
    try:
        with Image.open(image_path) as img:
            i = 0
            while True:
                try:
                    img.seek(i)
                    i += 1
                except EOFError:
                    break
            return i
    except Exception as e:
        return 0

