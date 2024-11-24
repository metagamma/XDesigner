from enum import Enum, auto
from typing import Set

class ProcessingStatus(Enum):
    """Estados posibles del procesamiento de imágenes."""
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    PARTIAL = auto()

class RegionType(Enum):
    OMR = "OMR"
    ICR = "ICR"
    BARCODE = "BARCODE"
    XMARK = "XMARK"


ALLOWED_IMAGE_EXTENSIONS: Set[str] = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp'}
MIN_IMAGE_DPI: int = 300
