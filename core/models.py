from dataclasses import dataclass, field
from typing import Tuple, Optional
from pathlib import Path

from core.exceptions import ValidationError, ImageError
from core.constants import RegionType
from utils.image_utils import get_image_dpi, get_tiff_page_count

@dataclass
class Template:
    """
    Modelo de datos para plantillas de emplantillado.
    Representa una plantilla TIFF con sus campos asociados.
    """
    ID: int
    Nombre: str
    Xmp: str
    Imagen: str  # Ruta al archivo TIFF
    ID_Grado: int
    _dpi: Optional[int] = field(default=None, init=False)
    _page_count: Optional[int] = field(default=None, init=False)
    
    def __post_init__(self):
        """Inicializa y valida la plantilla al crear la instancia."""
        self.validate()
        self._initialize_image_properties()

    def _initialize_image_properties(self) -> None:
        """Inicializa propiedades de la imagen TIFF si existe."""
        if not self.Imagen:
            return
            
        image_path = Path(self.Imagen)
        if not image_path.exists():
            return
            
        if image_path.suffix.lower() not in {'.tif', '.tiff'}:
            raise ImageError(
                "El archivo debe ser TIFF", 
                image_path=str(image_path)
            )
            
        try:
            # Usar las funciones de utils.image_utils
            dpi_x, dpi_y = get_image_dpi(str(image_path))
            if dpi_x != dpi_y:
                raise ImageError(
                    f"DPI no uniforme: {dpi_x}x{dpi_y}",
                    image_path=str(image_path),
                    dpi=dpi_x
                )
            self._dpi = dpi_x
            self._page_count = get_tiff_page_count(str(image_path))
        except Exception as e:
            raise ImageError(
                f"Error leyendo imagen: {str(e)}", 
                image_path=str(image_path)
            )

    @property
    def is_valid(self) -> bool:
        """Verifica si la plantilla tiene todos los campos requeridos."""
        try:
            self.validate()
            return True
        except ValidationError:
            return False

    def validate(self) -> None:
        """Valida todos los campos de la plantilla."""
        if not self.Nombre:
            raise ValidationError("El nombre de la plantilla es requerido")
        if not self.Imagen:
            raise ValidationError("La ruta de imagen es requerida")
        if self.ID_Grado <= 0:
            raise ValidationError("ID_Grado debe ser mayor que cero")

    @property
    def dpi(self) -> int:
        """Obtiene el DPI de la imagen. Por defecto 300."""
        if self._dpi is None:
            self._initialize_image_properties()
        return self._dpi or 300

    @property
    def page_count(self) -> int:
        """Obtiene el número de páginas del TIFF."""
        if self._page_count is None:
            self._initialize_image_properties()
        return self._page_count or 1

@dataclass
class Field:
    """
    Modelo de datos para campos de emplantillado.
    Las coordenadas se almacenan en pulgadas pero se trabajan en píxeles en la UI.
    """
    ID: int
    ID_Template: int
    Nombre_Campo: str
    Tipo_Campo: str
    Cord_x: float  # en pulgadas
    Cord_y: float  # en pulgadas
    Cord_width: float  # en pulgadas
    Cord_height: float  # en pulgadas
    NroPagina: int
    IdRectangulo: int
    _dpi: int = field(default=300, init=False)
    
    def __post_init__(self):
        """Valida el campo al crear la instancia."""
        self.validate()
    
    def validate(self) -> None:
        """Valida todos los atributos del campo."""
        if not self.Nombre_Campo:
            raise ValidationError("El nombre del campo es requerido")
            
        if not self.Nombre_Campo.isupper():
            raise ValidationError("El nombre del campo debe estar en mayúsculas")
            
        try:
            RegionType(self.Tipo_Campo)
        except ValueError:
            valid_types = ", ".join(t.value for t in RegionType)
            raise ValidationError(f"Tipo de campo debe ser uno de: {valid_types}")
            
        if any(v < 0 for v in [self.Cord_x, self.Cord_y, self.Cord_width, self.Cord_height]):
            raise ValidationError("Las coordenadas no pueden ser negativas")
            
        if self.Cord_width <= 0 or self.Cord_height <= 0:
            raise ValidationError("Las dimensiones deben ser mayores que cero")
            
        if self.NroPagina < 0:
            raise ValidationError("El número de página no puede ser negativo")
            
        if self.ID_Template <= 0:
            raise ValidationError("ID_Template debe ser mayor que cero")
    
    def intersects(self, other: 'Field') -> bool:
        """Verifica si este campo se intersecta con otro en la misma página."""
        if self.NroPagina != other.NroPagina:
            return False
            
        return not (
            self.Cord_x + self.Cord_width < other.Cord_x or
            other.Cord_x + other.Cord_width < self.Cord_x or
            self.Cord_y + self.Cord_height < other.Cord_y or
            other.Cord_y + other.Cord_height < self.Cord_y
        )

    def from_pixels(self, x: int, y: int, width: int, height: int, dpi: int) -> None:
        """Actualiza las coordenadas desde píxeles a pulgadas."""
        self._dpi = dpi
        self.Cord_x = x / dpi
        self.Cord_y = y / dpi
        self.Cord_width = width / dpi
        self.Cord_height = height / dpi

    def to_pixels(self, dpi: Optional[int] = None) -> Tuple[int, int, int, int]:
        """Obtiene las coordenadas en píxeles."""
        dpi = dpi or self._dpi
        return (
            round(self.Cord_x * dpi),
            round(self.Cord_y * dpi),
            round(self.Cord_width * dpi),
            round(self.Cord_height * dpi)
        )

    @property
    def area_inches(self) -> float:
        """Obtiene el área en pulgadas cuadradas."""
        return self.Cord_width * self.Cord_height

    @property 
    def area_pixels(self) -> float:
        """Obtiene el área en píxeles cuadrados."""
        return self.area_inches * (self._dpi ** 2)