import re
from typing import Tuple, Optional
from core.config import AppConfig
from core.exceptions import ValidationError
from core.constants import RegionType

def validate_field_name(name: str, config: AppConfig) -> Tuple[bool, Optional[str]]:
    """
    Valida el nombre de un campo según las reglas configuradas.
    
    Args:
        name: Nombre del campo a validar
        config: Configuración de la aplicación
    
    Returns:
        Tuple[bool, Optional[str]]: (es_válido, mensaje_error)
    """
    if not name:
        return False, "El nombre del campo no puede estar vacío"
        
    if len(name) > config.max_field_name_length:
        return False, f"El nombre no puede exceder {config.max_field_name_length} caracteres"
        
    if not re.match(config.field_name_pattern, name):
        return False, "El nombre solo puede contener letras mayúsculas, números y guiones bajos"
        
    return True, None

def validate_coordinates(x: float, y: float, width: float, height: float) -> None:
    """
    Valida las coordenadas de un campo.
    
    Args:
        x: Coordenada X
        y: Coordenada Y
        width: Ancho
        height: Alto
    
    Raises:
        ValidationError: Si las coordenadas son inválidas
    """
    if any(coord < 0 for coord in [x, y, width, height]):
        raise ValidationError("Las coordenadas no pueden ser negativas")
        
    if width <= 0 or height <= 0:
        raise ValidationError("El ancho y alto deben ser mayores que cero")

def validate_field_type(field_type: str) -> None:
    """
    Valida que el tipo de campo sea uno de los permitidos.
    
    Args:
        field_type: Tipo de campo a validar
    
    Raises:
        ValidationError: Si el tipo de campo no es válido
    """
    try:
        RegionType(field_type)
    except ValueError:
        valid_types = ", ".join(rt.value for rt in RegionType)
        raise ValidationError(
            f"Tipo de campo inválido. Debe ser uno de: {valid_types}"
        )