from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class Template:
    """Modelo de datos para plantillas."""
    ID: int
    Nombre: str
    Xmp: str
    Imagen: str
    ID_Grado: int
    
    @property
    def is_valid(self) -> bool:
        """Verifica si la plantilla tiene todos los campos requeridos."""
        return bool(self.Nombre and self.Imagen and self.ID_Grado)

@dataclass
class Field:
    """Modelo de datos para campos de plantilla."""
    ID: int
    ID_Template: int
    Nombre_Campo: str
    Tipo_Campo: str
    Cord_x: float
    Cord_y: float
    Cord_width: float
    Cord_height: float
    NroPagina: int
    IdRectangulo: int
    
    @property
    def area(self) -> float:
        """Calcula el área del campo en unidades cuadradas."""
        return self.Cord_width * self.Cord_height
    
    @property
    def center(self) -> tuple[float, float]:
        """Calcula el centro del campo."""
        return (
            self.Cord_x + (self.Cord_width / 2),
            self.Cord_y + (self.Cord_height / 2)
        )
    
    def intersects(self, other: 'Field') -> bool:
        """Verifica si este campo intersecta con otro."""
        return not (
            self.Cord_x + self.Cord_width < other.Cord_x or
            other.Cord_x + other.Cord_width < self.Cord_x or
            self.Cord_y + self.Cord_height < other.Cord_y or
            other.Cord_y + other.Cord_height < self.Cord_y
        )