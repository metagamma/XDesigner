from typing import List, Optional, Dict, Any
import logging
from pathlib import Path
from datetime import datetime

from core.config import AppConfig
from core.models import Template, Field
from core.exceptions import DatabaseError, ValidationError
from core.constants import RegionType
from database.connection import DatabaseConnection
from database.repository import TemplateRepository

class TemplateService:
    """
    Servicio de alto nivel para operaciones de plantillas y campos.
    Implementa la lógica de negocio y coordina el acceso a datos.
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.connection = DatabaseConnection(config)
        self.repository = TemplateRepository(self.connection)

    def initialize(self) -> None:
        """
        Inicializa las conexiones y recursos del servicio.
        
        Raises:
            DatabaseError: Si hay error en la inicialización
        """
        try:
            self.connection.initialize()
            self.logger.info("Servicio de plantillas inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando servicio: {e}")
            raise DatabaseError("Error al inicializar servicio de plantillas") from e

    def close(self) -> None:
        """Libera recursos y cierra conexiones."""
        try:
            self.connection.close()
            self.logger.info("Servicio de plantillas cerrado")
        except Exception as e:
            self.logger.error(f"Error cerrando servicio: {e}")

    def get_templates(self) -> List[Template]:
        """
        Obtiene todas las plantillas disponibles.
        
        Returns:
            List[Template]: Lista de plantillas
            
        Raises:
            DatabaseError: Si hay error al obtener las plantillas
        """
        try:
            templates = self.repository.get_templates()
            
            # Validar existencia de archivos de imagen
            for template in templates:
                if not Path(template.Imagen).exists():
                    self.logger.warning(
                        f"Archivo de imagen no encontrado para plantilla {template.ID}: {template.Imagen}"
                    )
                    
            return templates
            
        except Exception as e:
            self.logger.error(f"Error obteniendo plantillas: {e}")
            raise DatabaseError("Error al obtener plantillas") from e

    def get_template(self, template_id: int) -> Optional[Template]:
        """
        Obtiene una plantilla específica con validaciones.
        
        Args:
            template_id: ID de la plantilla
            
        Returns:
            Optional[Template]: Plantilla encontrada o None
            
        Raises:
            ValidationError: Si el ID es inválido
            DatabaseError: Si hay error en la consulta
        """
        try:
            if template_id <= 0:
                raise ValidationError("ID de plantilla debe ser mayor que cero")
                
            template = self.repository.get_template_by_id(template_id)
            
            if template and not Path(template.Imagen).exists():
                self.logger.warning(
                    f"Archivo de imagen no encontrado: {template.Imagen}"
                )
                
            return template
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error obteniendo plantilla {template_id}: {e}")
            raise DatabaseError(f"Error al obtener plantilla {template_id}") from e

    def create_template(self, template: Template) -> int:
        """
        Crea una nueva plantilla con validaciones adicionales.
        
        Args:
            template: Objeto Template con los datos
            
        Returns:
            int: ID de la plantilla creada
            
        Raises:
            ValidationError: Si los datos son inválidos
            DatabaseError: Si hay error en la creación
        """
        try:
            # Validar existencia de imagen
            if not Path(template.Imagen).exists():
                raise ValidationError(f"Archivo de imagen no encontrado: {template.Imagen}")
            
            # Validar nombre único
            existing = self.repository.search_templates(template.Nombre)
            if any(t.Nombre == template.Nombre for t in existing):
                raise ValidationError(f"Ya existe una plantilla con el nombre: {template.Nombre}")
            
            return self.repository.create_template(template)
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creando plantilla: {e}")
            raise DatabaseError("Error al crear plantilla") from e

    def update_template(self, template: Template) -> bool:
        """
        Actualiza una plantilla existente con validaciones.
        
        Args:
            template: Objeto Template con los datos actualizados
            
        Returns:
            bool: True si se actualizó correctamente
            
        Raises:
            ValidationError: Si los datos son inválidos
            DatabaseError: Si hay error en la actualización
        """
        try:
            # Verificar que existe la plantilla
            existing = self.repository.get_template_by_id(template.ID)
            if not existing:
                raise ValidationError(f"No existe plantilla con ID: {template.ID}")
            
            # Validar existencia de imagen
            if not Path(template.Imagen).exists():
                raise ValidationError(f"Archivo de imagen no encontrado: {template.Imagen}")
            
            # Validar nombre único (excepto para la misma plantilla)
            templates = self.repository.search_templates(template.Nombre)
            if any(t.Nombre == template.Nombre and t.ID != template.ID for t in templates):
                raise ValidationError(f"Ya existe una plantilla con el nombre: {template.Nombre}")
            
            return self.repository.update_template(template)
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error actualizando plantilla {template.ID}: {e}")
            raise DatabaseError(f"Error al actualizar plantilla {template.ID}") from e

    def delete_template(self, template_id: int) -> bool:
        """
        Elimina una plantilla y sus campos asociados.
        
        Args:
            template_id: ID de la plantilla
            
        Returns:
            bool: True si se eliminó correctamente
            
        Raises:
            ValidationError: Si el ID es inválido
            DatabaseError: Si hay error en la eliminación
        """
        try:
            # Verificar que existe la plantilla
            template = self.repository.get_template_by_id(template_id)
            if not template:
                raise ValidationError(f"No existe plantilla con ID: {template_id}")
            
            # Obtener campos asociados para logging
            fields = self.repository.get_template_fields(template_id)
            
            # Eliminar plantilla y campos
            success = self.repository.delete_template(template_id)
            
            if success:
                self.logger.info(
                    f"Plantilla {template_id} eliminada junto con {len(fields)} campos"
                )
            
            return success
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error eliminando plantilla {template_id}: {e}")
            raise DatabaseError(f"Error al eliminar plantilla {template_id}") from e

    def get_template_fields(self, template_id: int) -> List[Field]:
        """
        Obtiene todos los campos de una plantilla organizados por página.
        
        Args:
            template_id: ID de la plantilla
            
        Returns:
            List[Field]: Lista de campos ordenados por página
            
        Raises:
            ValidationError: Si el ID es inválido
            DatabaseError: Si hay error en la consulta
        """
        try:
            # Verificar que existe la plantilla
            if not self.repository.get_template_by_id(template_id):
                raise ValidationError(f"No existe plantilla con ID: {template_id}")
            
            return self.repository.get_template_fields(template_id)
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error obteniendo campos de plantilla {template_id}: {e}")
            raise DatabaseError(f"Error al obtener campos") from e

    def create_field(self, field: Field) -> int:
        """
        Crea un nuevo campo con validaciones de solapamiento.
        
        Args:
            field: Objeto Field con los datos del campo
            
        Returns:
            int: ID del campo creado
            
        Raises:
            ValidationError: Si los datos son inválidos o hay solapamiento
            DatabaseError: Si hay error en la creación
        """
        try:
            # Verificar que existe la plantilla
            if not self.repository.get_template_by_id(field.ID_Template):
                raise ValidationError(f"No existe plantilla con ID: {field.ID_Template}")
            
            # Validar tipo de campo
            if field.Tipo_Campo not in [t.value for t in RegionType]:
                valid_types = ", ".join(t.value for t in RegionType)
                raise ValidationError(f"Tipo de campo debe ser uno de: {valid_types}")
            
            # Validar dimensiones mínimas (20px convertido a pulgadas)
            min_size_inches = 20 / field._dpi
            if field.Cord_width < min_size_inches or field.Cord_height < min_size_inches:
                raise ValidationError(
                    f"El campo debe tener al menos 20 píxeles de ancho y alto "
                    f"({min_size_inches:.4f} pulgadas a {field._dpi} DPI)"
                )
            
            # Verificar solapamiento con otros campos en la misma página
            existing_fields = self.repository.get_fields_by_page(
                field.ID_Template, 
                field.NroPagina
            )
            
            for existing in existing_fields:
                if field.intersects(existing):
                    raise ValidationError(
                        f"El campo se solapa con el campo existente: {existing.Nombre_Campo}"
                    )
            
            return self.repository.create_field(field)
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creando campo: {e}")
            raise DatabaseError("Error al crear campo") from e

    def update_field(self, field: Field) -> bool:
        """
        Actualiza un campo existente con validaciones de solapamiento.
        
        Args:
            field: Objeto Field con los datos actualizados
            
        Returns:
            bool: True si se actualizó correctamente
            
        Raises:
            ValidationError: Si los datos son inválidos o hay solapamiento
            DatabaseError: Si hay error en la actualización
        """
        try:
            # Verificar que existe el campo
            existing = self.repository.get_field_by_id(field.ID)
            if not existing:
                raise ValidationError(f"No existe campo con ID: {field.ID}")
            
            # Verificar que existe la plantilla
            if not self.repository.get_template_by_id(field.ID_Template):
                raise ValidationError(f"No existe plantilla con ID: {field.ID_Template}")
            
            # Validar tipo de campo
            if field.Tipo_Campo not in [t.value for t in RegionType]:
                valid_types = ", ".join(t.value for t in RegionType)
                raise ValidationError(f"Tipo de campo debe ser uno de: {valid_types}")
            
            # Validar dimensiones mínimas
            min_size_inches = 20 / field._dpi
            if field.Cord_width < min_size_inches or field.Cord_height < min_size_inches:
                raise ValidationError(
                    f"El campo debe tener al menos 20 píxeles de ancho y alto "
                    f"({min_size_inches:.4f} pulgadas a {field._dpi} DPI)"
                )
            
            # Verificar solapamiento con otros campos
            other_fields = self.repository.get_fields_by_page(
                field.ID_Template,
                field.NroPagina
            )
            
            for other in other_fields:
                if other.ID != field.ID and field.intersects(other):
                    raise ValidationError(
                        f"El campo se solapa con el campo existente: {other.Nombre_Campo}"
                    )
            
            return self.repository.update_field(field)
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error actualizando campo {field.ID}: {e}")
            raise DatabaseError(f"Error al actualizar campo {field.ID}") from e

    def delete_field(self, field_id: int) -> bool:
        """
        Elimina un campo.
        
        Args:
            field_id: ID del campo
            
        Returns:
            bool: True si se eliminó correctamente
            
        Raises:
            ValidationError: Si el ID es inválido
            DatabaseError: Si hay error en la eliminación
        """
        try:
            # Verificar que existe el campo
            field = self.repository.get_field_by_id(field_id)
            if not field:
                raise ValidationError(f"No existe campo con ID: {field_id}")
            
            return self.repository.delete_field(field_id)
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error eliminando campo {field_id}: {e}")
            raise DatabaseError(f"Error al eliminar campo {field_id}") from e

    def get_fields_by_page(self, template_id: int, page_number: int) -> List[Field]:
        """
        Obtiene los campos de una página específica.
        
        Args:
            template_id: ID de la plantilla
            page_number: Número de página
            
        Returns:
            List[Field]: Lista de campos en la página
            
        Raises:
            ValidationError: Si los parámetros son inválidos
            DatabaseError: Si hay error en la consulta
        """
        try:
            # Verificar que existe la plantilla
            template = self.repository.get_template_by_id(template_id)
            if not template:
                raise ValidationError(f"No existe plantilla con ID: {template_id}")
            
            # Validar número de página
            if page_number < 0:
                raise ValidationError("El número de página no puede ser negativo")
            
            return self.repository.get_fields_by_page(template_id, page_number)
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(
                f"Error obteniendo campos de página {page_number} "
                f"de plantilla {template_id}: {e}"
            )
            raise DatabaseError("Error al obtener campos por página") from e

    def move_field(self, field_id: int, new_x: float, new_y: float) -> bool:
        """
        Mueve un campo a nuevas coordenadas.
        
        Args:
            field_id: ID del campo
            new_x: Nueva coordenada X en pulgadas
            new_y: Nueva coordenada Y en pulgadas
            
        Returns:
            bool: True si se movió correctamente
            
        Raises:
            ValidationError: Si las coordenadas son inválidas
            DatabaseError: Si hay error en la actualización
        """
        try:
            # Obtener campo actual
            field = self.repository.get_field_by_id(field_id)
            if not field:
                raise ValidationError(f"No existe campo con ID: {field_id}")
            
            # Validar coordenadas
            if new_x < 0 or new_y < 0:
                raise ValidationError("Las coordenadas no pueden ser negativas")
            
            # Actualizar coordenadas
            field.Cord_x = new_x
            field.Cord_y = new_y
            
            # Verificar solapamiento en nueva posición
            other_fields = self.repository.get_fields_by_page(
                field.ID_Template,
                field.NroPagina
            )
            
            for other in other_fields:
                if other.ID != field.ID and field.intersects(other):
                    raise ValidationError(
                        f"La nueva posición se solapa con el campo: {other.Nombre_Campo}"
                    )
            
            return self.repository.update_field(field)
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error moviendo campo {field_id}: {e}")
            raise DatabaseError(f"Error al mover campo {field_id}") from e

    def resize_field(self, field_id: int, new_width: float, new_height: float) -> bool:
        """
        Cambia el tamaño de un campo.
        
        Args:
            field_id: ID del campo
            new_width: Nuevo ancho en pulgadas
            new_height: Nuevo alto en pulgadas
            
        Returns:
            bool: True si se redimensionó correctamente
            
        Raises:
            ValidationError: Si las dimensiones son inválidas
            DatabaseError: Si hay error en la actualización
        """
        try:
            # Obtener campo actual
            field = self.repository.get_field_by_id(field_id)
            if not field:
                raise ValidationError(f"No existe campo con ID: {field_id}")
            
            # Validar dimensiones mínimas (20px convertido a pulgadas)
            min_size_inches = 20 / field._dpi
            if new_width < min_size_inches or new_height < min_size_inches:
                raise ValidationError(
                    f"El campo debe tener al menos 20 píxeles de ancho y alto "
                    f"({min_size_inches:.4f} pulgadas a {field._dpi} DPI)"
                )
            
            # Actualizar dimensiones
            field.Cord_width = new_width
            field.Cord_height = new_height
            
            # Verificar solapamiento con nuevo tamaño
            other_fields = self.repository.get_fields_by_page(
                field.ID_Template,
                field.NroPagina
            )
            
            for other in other_fields:
                if other.ID != field.ID and field.intersects(other):
                    raise ValidationError(
                        f"Las nuevas dimensiones se solapan con el campo: {other.Nombre_Campo}"
                    )
            
            return self.repository.update_field(field)
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error redimensionando campo {field_id}: {e}")
            raise DatabaseError(f"Error al redimensionar campo {field_id}") from e

    def rename_field(self, field_id: int, new_name: str) -> bool:
        """
        Renombra un campo.
        
        Args:
            field_id: ID del campo
            new_name: Nuevo nombre
            
        Returns:
            bool: True si se renombró correctamente
            
        Raises:
            ValidationError: Si el nombre es inválido
            DatabaseError: Si hay error en la actualización
        """
        try:
            # Obtener campo actual
            field = self.repository.get_field_by_id(field_id)
            if not field:
                raise ValidationError(f"No existe campo con ID: {field_id}")
            
            # Validar nuevo nombre
            new_name = new_name.strip().upper()
            if not new_name:
                raise ValidationError("El nombre no puede estar vacío")
                
            if len(new_name) > 100:
                raise ValidationError("El nombre no puede exceder 100 caracteres")
            
            # Verificar nombre único en la plantilla
            existing_fields = self.repository.get_template_fields(field.ID_Template)
            if any(f.Nombre_Campo == new_name and f.ID != field_id for f in existing_fields):
                raise ValidationError(f"Ya existe un campo con el nombre: {new_name}")
            
            # Actualizar nombre
            field.Nombre_Campo = new_name
            return self.repository.update_field(field)
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error renombrando campo {field_id}: {e}")
            raise DatabaseError(f"Error al renombrar campo {field_id}") from e

    def change_field_type(self, field_id: int, new_type: str) -> bool:
        """
        Cambia el tipo de un campo.
        
        Args:
            field_id: ID del campo
            new_type: Nuevo tipo (OMR, ICR, BARCODE, XMARK)
            
        Returns:
            bool: True si se cambió correctamente
            
        Raises:
            ValidationError: Si el tipo es inválido
            DatabaseError: Si hay error en la actualización
        """
        try:
            # Obtener campo actual
            field = self.repository.get_field_by_id(field_id)
            if not field:
                raise ValidationError(f"No existe campo con ID: {field_id}")
            
            # Validar nuevo tipo
            if new_type not in [t.value for t in RegionType]:
                valid_types = ", ".join(t.value for t in RegionType)
                raise ValidationError(f"Tipo de campo debe ser uno de: {valid_types}")
            
            # Actualizar tipo
            field.Tipo_Campo = new_type
            return self.repository.update_field(field)
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error cambiando tipo de campo {field_id}: {e}")
            raise DatabaseError(f"Error al cambiar tipo de campo {field_id}") from e

    def duplicate_template(self, template_id: int, new_name: str) -> int:
        """
        Duplica una plantilla y todos sus campos.
        
        Args:
            template_id: ID de la plantilla a duplicar
            new_name: Nombre para la nueva plantilla
            
        Returns:
            int: ID de la nueva plantilla
            
        Raises:
            ValidationError: Si los parámetros son inválidos
            DatabaseError: Si hay error en la duplicación
        """
        try:
            # Verificar que existe la plantilla original
            template = self.repository.get_template_by_id(template_id)
            if not template:
                raise ValidationError(f"No existe plantilla con ID: {template_id}")
            
            # Validar nuevo nombre
            new_name = new_name.strip()
            if not new_name:
                raise ValidationError("El nombre no puede estar vacío")
            
            # Verificar que el archivo de imagen existe
            if not Path(template.Imagen).exists():
                raise ValidationError(f"Archivo de imagen no encontrado: {template.Imagen}")
            
            # Verificar nombre único
            existing = self.repository.search_templates(new_name)
            if any(t.Nombre == new_name for t in existing):
                raise ValidationError(f"Ya existe una plantilla con el nombre: {new_name}")
            
            return self.repository.duplicate_template(template_id, new_name)
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error duplicando plantilla {template_id}: {e}")
            raise DatabaseError(f"Error al duplicar plantilla {template_id}") from e

    def validate_template(self, template_id: int) -> List[str]:
        """
        Valida la integridad de una plantilla y sus campos.
        
        Args:
            template_id: ID de la plantilla a validar
            
        Returns:
            List[str]: Lista de mensajes de error/advertencia
            
        Raises:
            ValidationError: Si el ID es inválido
            DatabaseError: Si hay error en la validación
        """
        try:
            warnings = []
            
            # Verificar que existe la plantilla
            template = self.repository.get_template_by_id(template_id)
            if not template:
                raise ValidationError(f"No existe plantilla con ID: {template_id}")
            
            # Validar archivo de imagen
            if not Path(template.Imagen).exists():
                warnings.append(f"Archivo de imagen no encontrado: {template.Imagen}")
            
            # Obtener campos
            fields = self.repository.get_template_fields(template_id)
            
            # Validar nombres duplicados
            field_names = {}
            for field in fields:
                if field.Nombre_Campo in field_names:
                    warnings.append(
                        f"Campo duplicado: {field.Nombre_Campo} en páginas "
                        f"{field_names[field.Nombre_Campo]} y {field.NroPagina}"
                    )
                field_names[field.Nombre_Campo] = field.NroPagina
            
            # Validar solapamientos por página
            for i, field1 in enumerate(fields):
                for field2 in fields[i+1:]:
                    if (field1.NroPagina == field2.NroPagina and 
                        field1.intersects(field2)):
                        warnings.append(
                            f"Campos solapados en página {field1.NroPagina}: "
                            f"{field1.Nombre_Campo} y {field2.Nombre_Campo}"
                        )
            
            # Validar dimensiones mínimas
            min_size_inches = 20 / (field._dpi if fields else 300)
            for field in fields:
                if field.Cord_width < min_size_inches or field.Cord_height < min_size_inches:
                    warnings.append(
                        f"Campo {field.Nombre_Campo} menor que 20 píxeles"
                    )
            
            return warnings
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error validando plantilla {template_id}: {e}")
            raise DatabaseError(f"Error al validar plantilla {template_id}") from e
            