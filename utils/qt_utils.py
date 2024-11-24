from PySide6.QtCore import QRect, QRectF
from typing import Tuple

def rect_to_normalized_coords(rect: QRect, image_width: int, image_height: int) -> QRectF:
    """Convert widget coordinates to normalized coordinates (0-1)."""
    return QRectF(
        rect.x() / image_width,
        rect.y() / image_height,
        rect.width() / image_width,
        rect.height() / image_height
    )

def normalized_to_rect_coords(rect: QRectF, image_width: int, image_height: int) -> QRect:
    """Convert normalized coordinates to widget coordinates."""
    return QRect(
        int(rect.x() * image_width),
        int(rect.y() * image_height),
        int(rect.width() * image_width),
        int(rect.height() * image_height)
    )