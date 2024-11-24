import re
from typing import Tuple, Optional
from pathlib import Path

from core.config import AppConfig
from core.exceptions import ValidationError
from core.constants import RegionType

def validate_field_name(name: str, config: AppConfig) -> Tuple[bool, Optional[str]]:
    """
    Valida el nombre de un campo de emplantillado.
    
    Args:
        name: Nombre del campo (ej: 'PREGUNTA_1', 'RTA_A')
        config: Configuración con reglas de validación
    
    Returns:
        Tuple[bool, Optional[str]]: (es_válido, mensaje_error)
    """
    if not name:
        return False, "El nombre del campo no puede estar vacío"
        
    if not name.isupper():
        return False, "El nombre debe estar en mayúsculas"
        
    if len(name) > config.field_validation['max_name_length']:
        return False, f"El nombre no puede exceder {config.field_validation['max_name_length']} caracteres"
        
    if not re.match(config.field_validation['name_pattern'], name):
        return False, "El nombre solo puede contener letras mayúsculas, números y guiones bajos"
        
    return True, None

def validate_field_coordinates(x: float, y: float, width: float, height: float, dpi: int) -> None:
    """
    Valida las coordenadas y dimensiones de un campo de emplantillado.
    
    Args:
        x, y: Coordenadas en pulgadas
        width, height: Dimensiones en pulgadas
        dpi: DPI de la imagen
    
    Raises:
        ValidationError: Si las coordenadas o dimensiones son inválidas
    """
    # Validar tipos de datos
    if not all(isinstance(v, (int, float)) for v in [x, y, width, height]):
        raise ValidationError("Las coordenadas deben ser valores numéricos")
    
    # Validar valores negativos
    if any(v < 0 for v in [x, y, width, height]):
        raise ValidationError(
            "Las coordenadas y dimensiones no pueden ser negativas",
            details={'x': x, 'y': y, 'width': width, 'height': height}
        )
    
    # Validar dimensiones mínimas (20px convertido a pulgadas)
    min_inches = 20 / dpi
    if width < min_inches or height < min_inches:
        raise ValidationError(
            f"El campo debe tener al menos 20 píxeles de ancho y alto ({min_inches:.4f} pulgadas a {dpi} DPI)",
            details={'width': width, 'height': height, 'min_inches': min_inches}
        )

def validate_field_type(field_type: str) -> None:
    """
    Valida que el tipo de campo sea válido para emplantillado.
    
    Args:
        field_type: Tipo de campo (OMR, ICR, BARCODE, XMARK)
    
    Raises:
        ValidationError: Si el tipo no es válido
    """
    try:
        RegionType(field_type)
    except ValueError:
        valid_types = ", ".join(rt.value for rt in RegionType)
        raise ValidationError(
            f"Tipo de campo inválido. Debe ser uno de: {valid_types}",
            field="tipo_campo",
            value=field_type
        )

def validate_template(nombre: str, imagen: str, min_dpi: int = 300) -> None:
    """
    Valida los datos básicos de una plantilla.
    
    Args:
        nombre: Nombre de la plantilla
        imagen: Ruta de la imagen TIFF
        min_dpi: DPI mínimo requerido (default: 300)
    
    Raises:
        ValidationError: Si la validación falla
    """
    # Validar nombre
    if not nombre or not nombre.strip():
        raise ValidationError(
            "El nombre de la plantilla no puede estar vacío",
            field="nombre"
        )
    
    if len(nombre) > 100:
        raise ValidationError(
            "El nombre de la plantilla no puede exceder 100 caracteres",
            field="nombre",
            value=nombre
        )
    
    # Validar imagen
    if not imagen:
        raise ValidationError(
            "La ruta de imagen es requerida",
            field="imagen"
        )
    
    image_path = Path(imagen)
    if not image_path.exists():
        raise ValidationError(
            "El archivo de imagen no existe",
            field="imagen",
            value=str(image_path)
        )
    
    if image_path.suffix.lower() not in {'.tif', '.tiff'}:
        raise ValidationError(
            "La imagen debe estar en formato TIFF",
            field="imagen",
            value=str(image_path)
        )