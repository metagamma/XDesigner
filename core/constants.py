from enum import Enum

class RegionType(Enum):
    """Tipos de campos soportados en el sistema."""
    OMR = "OMR"
    ICR = "ICR"
    BARCODE = "BARCODE"
    XMARK = "XMARK"
    
    @classmethod
    def get_choices(cls):
        """Retorna las opciones disponibles para la UI."""
        return [(t.value, t.value) for t in cls]

class TemplateStatus(Enum):
    """Estados posibles de una plantilla."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

class FieldValidation(Enum):
    """Tipos de validación para campos."""
    REQUIRED = "REQUIRED"
    NUMERIC = "NUMERIC"
    ALPHANUMERIC = "ALPHANUMERIC"
    CUSTOM = "CUSTOM"