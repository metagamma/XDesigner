from enum import Enum
from typing import List, Set, Tuple

# Constants
class RegionType(Enum):
    """Tipos de campos soportados."""
    OMR = "OMR"
    ICR = "ICR"
    BARCODE = "BARCODE"
    XMARK = "XMARK"
    
    @classmethod
    def get_choices(cls) -> List[Tuple[str, str]]:
        """Retorna las opciones para la UI."""
        return [(t.value, t.value) for t in cls]

class TemplateStatus(Enum):
    """Estados de plantilla."""
    DRAFT = "DRAFT"      # En proceso de creación
    ACTIVE = "ACTIVE"    # Lista para usar
    ARCHIVED = "ARCHIVED"  # Desactivada/Histórica
    
    @classmethod
    def get_choices(cls) -> List[Tuple[str, str]]:
        """Retorna las opciones para la UI."""
        return [(t.value, t.value) for t in cls]
    
MIN_IMAGE_DPI: int = 300
MIN_FIELD_SIZE_PX: int = 20
MAX_NAME_LENGTH: int = 100
ALLOWED_IMAGE_EXTENSIONS: Set[str] = {'.tif', '.tiff'}