from datetime import datetime
import time
from typing import List, Optional, Dict, Any
import logging
from contextlib import contextmanager

from core.config import AppConfig
from core.models import Template, Field
from core.exceptions import DatabaseError, ValidationError
from core.validators import validate_field_name, validate_field_type
from database.connection import DatabaseConnection
from database.repository import TemplateRepository

class DatabaseService:
    """Servicio para operaciones de base de datos con lógica de negocio."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.connection = DatabaseConnection(config)
        self.repository = TemplateRepository(self.connection)
        self._cache = {}

    def initialize(self) -> None:
        """Inicializa las conexiones y recursos necesarios."""
        try:
            self.connection.initialize()
            self.logger.info("Servicio de base de datos inicializado")
        except Exception as e:
            self.logger.error(f"Error inicializando servicio: {e}")
            raise DatabaseError("Error al inicializar servicio", original_error=e)

    def close(self) -> None:
        """Libera recursos y cierra conexiones."""
        try:
            self._cache.clear()
            self.connection.close()
            self.logger.info("Servicio de base de datos cerrado")
        except Exception as e:
            self.logger.error(f"Error cerrando servicio: {e}")

    @contextmanager
    def transaction(self):
        """Provee un contexto transaccional."""
        with self.connection.get_cursor() as cursor:
            try:
                cursor.execute("BEGIN TRANSACTION")
                yield
                cursor.execute("COMMIT")
            except Exception as e:
                cursor.execute("ROLLBACK")
                self.logger.error(f"Error en transacción: {e}")
                raise

    def get_templates(self, use_cache: bool = True) -> List[Template]:
        """Obtiene todas las plantillas disponibles."""
        if use_cache and 'templates' in self._cache:
            return self._cache['templates']
            
        templates = self.repository.get_templates()
        
        if use_cache:
            self._cache['templates'] = templates
            
        return templates

    def get_template(self, template_id: int, use_cache: bool = True) -> Optional[Template]:
        """Obtiene una plantilla específica."""
        if use_cache and 'template' in self._cache and self._cache['template'].ID == template_id:
            return self._cache['template']
            
        template = self.repository.get_template_by_id(template_id)
        
        if use_cache and template:
            self._cache['template'] = template
            
        return template

    def create_template(self, template: Template) -> int:
        """
        Crea una nueva plantilla.

        Args:
            template: Datos de la plantilla

        Returns:
            int: ID de la plantilla creada

        Raises:
            DatabaseError: Si hay error en la creación
            ValidationError: Si los datos son inválidos
        """
        try:
            with self.transaction():
                template_id = self.repository.create_template(template)
                self._cache.clear()  # Invalidar caché
                return template_id
        except (DatabaseError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error creando plantilla: {e}")
            raise DatabaseError("Error al crear plantilla", original_error=e)

    def update_template(self, template: Template) -> bool:
        """
        Actualiza una plantilla existente.

        Args:
            template: Datos actualizados de la plantilla

        Returns:
            bool: True si se actualizó correctamente

        Raises:
            DatabaseError: Si hay error en la actualización
            ValidationError: Si los datos son inválidos
        """
        try:
            with self.transaction():
                success = self.repository.update_template(template)
                if success:
                    self._cache.clear()  # Invalidar caché
                return success
        except (DatabaseError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error actualizando plantilla {template.ID}: {e}")
            raise DatabaseError(f"Error al actualizar plantilla", original_error=e)

    def delete_template(self, template_id: int) -> bool:
        """
        Elimina una plantilla y todos sus campos asociados.

        Args:
            template_id: ID de la plantilla a eliminar

        Returns:
            bool: True si se eliminó correctamente

        Raises:
            DatabaseError: Si hay error en la eliminación
        """
        try:
            with self.transaction():
                success = self.repository.delete_template(template_id)
                if success:
                    self._cache.clear()  # Invalidar caché
                return success
        except DatabaseError:
            raise
        except Exception as e:
            self.logger.error(f"Error eliminando plantilla {template_id}: {e}")
            raise DatabaseError("Error al eliminar plantilla", original_error=e)

    def get_template_fields(self, template_id: int, use_cache: bool = True) -> List[Field]:
        """
        Obtiene todos los campos de una plantilla.

        Args:
            template_id: ID de la plantilla
            use_cache: Si se debe usar caché

        Returns:
            List[Field]: Lista de campos

        Raises:
            DatabaseError: Si hay error en la consulta
        """
        cache_key = f'fields_{template_id}'
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        fields = self.repository.get_template_fields(template_id)
        
        if use_cache:
            self._cache[cache_key] = fields
            
        return fields

    def create_field(self, field: Field) -> int:
        """
        Crea un nuevo campo en una plantilla.

        Args:
            field: Datos del campo

        Returns:
            int: ID del campo creado

        Raises:
            DatabaseError: Si hay error en la creación
            ValidationError: Si los datos son inválidos
        """
        try:
            # Verificar si hay campos superpuestos
            existing_fields = self.get_template_fields(field.ID_Template)
            for existing_field in existing_fields:
                if (existing_field.NroPagina == field.NroPagina and 
                    field.intersects(existing_field)):
                    raise ValidationError(
                        "El campo se superpone con un campo existente",
                        field=existing_field.Nombre_Campo
                    )

            with self.transaction():
                field_id = self.repository.create_field(field)
                self._cache.clear()  # Invalidar caché
                return field_id
        except (DatabaseError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error creando campo: {e}")
            raise DatabaseError("Error al crear campo", original_error=e)

    def update_field(self, field: Field) -> bool:
        """
        Actualiza un campo existente.

        Args:
            field: Datos actualizados del campo

        Returns:
            bool: True si se actualizó correctamente

        Raises:
            DatabaseError: Si hay error en la actualización
            ValidationError: Si los datos son inválidos
        """
        try:
            # Verificar si hay campos superpuestos
            existing_fields = self.get_template_fields(field.ID_Template)
            for existing_field in existing_fields:
                if (existing_field.ID != field.ID and 
                    existing_field.NroPagina == field.NroPagina and 
                    field.intersects(existing_field)):
                    raise ValidationError(
                        "El campo se superpone con un campo existente",
                        field=existing_field.Nombre_Campo
                    )

            with self.transaction():
                success = self.repository.update_field(field)
                if success:
                    self._cache.clear()  # Invalidar caché
                return success
        except (DatabaseError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error actualizando campo {field.ID}: {e}")
            raise DatabaseError("Error al actualizar campo", original_error=e)

    def delete_field(self, field_id: int) -> bool:
        """
        Elimina un campo.

        Args:
            field_id: ID del campo a eliminar

        Returns:
            bool: True si se eliminó correctamente

        Raises:
            DatabaseError: Si hay error en la eliminación
        """
        try:
            with self.transaction():
                success = self.repository.delete_field(field_id)
                if success:
                    self._cache.clear()  # Invalidar caché
                return success
        except DatabaseError:
            raise
        except Exception as e:
            self.logger.error(f"Error eliminando campo {field_id}: {e}")
            raise DatabaseError("Error al eliminar campo", original_error=e)

    def get_field(self, field_id: int) -> Optional[Field]:
        """
        Obtiene un campo específico.

        Args:
            field_id: ID del campo

        Returns:
            Optional[Field]: Campo encontrado o None

        Raises:
            DatabaseError: Si hay error en la consulta
        """
        return self.repository.get_field_by_id(field_id)

    def move_field(self, field_id: int, new_x: float, new_y: float) -> bool:
        """
        Mueve un campo a nuevas coordenadas.

        Args:
            field_id: ID del campo
            new_x: Nueva coordenada X
            new_y: Nueva coordenada Y

        Returns:
            bool: True si se movió correctamente

        Raises:
            DatabaseError: Si hay error en la actualización
            ValidationError: Si las coordenadas son inválidas
        """
        try:
            field = self.get_field(field_id)
            if not field:
                raise ValidationError(f"Campo {field_id} no encontrado")

            # Actualizar coordenadas
            field.Cord_x = new_x
            field.Cord_y = new_y

            return self.update_field(field)
        except (DatabaseError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error moviendo campo {field_id}: {e}")
            raise DatabaseError("Error al mover campo", original_error=e)

    def resize_field(self, field_id: int, new_width: float, new_height: float) -> bool:
        """
        Redimensiona un campo.

        Args:
            field_id: ID del campo
            new_width: Nuevo ancho
            new_height: Nuevo alto

        Returns:
            bool: True si se redimensionó correctamente

        Raises:
            DatabaseError: Si hay error en la actualización
            ValidationError: Si las dimensiones son inválidas
        """
        try:
            field = self.get_field(field_id)
            if not field:
                raise ValidationError(f"Campo {field_id} no encontrado")

            # Validar nuevas dimensiones
            if new_width <= 0 or new_height <= 0:
                raise ValidationError("Las dimensiones deben ser mayores que cero")

            # Actualizar dimensiones
            field.Cord_width = new_width
            field.Cord_height = new_height

            return self.update_field(field)
        except (DatabaseError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error redimensionando campo {field_id}: {e}")
            raise DatabaseError("Error al redimensionar campo", original_error=e)

    def rename_field(self, field_id: int, new_name: str) -> bool:
        """
        Renombra un campo.

        Args:
            field_id: ID del campo
            new_name: Nuevo nombre

        Returns:
            bool: True si se renombró correctamente

        Raises:
            DatabaseError: Si hay error en la actualización
            ValidationError: Si el nombre es inválido
        """
        try:
            field = self.get_field(field_id)
            if not field:
                raise ValidationError(f"Campo {field_id} no encontrado")

            # Validar nuevo nombre
            valid, error_msg = validate_field_name(new_name)
            if not valid:
                raise ValidationError(error_msg)

            # Actualizar nombre
            field.Nombre_Campo = new_name

            return self.update_field(field)
        except (DatabaseError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error renombrando campo {field_id}: {e}")
            raise DatabaseError("Error al renombrar campo", original_error=e)

    def change_field_type(self, field_id: int, new_type: str) -> bool:
        """
        Cambia el tipo de un campo.

        Args:
            field_id: ID del campo
            new_type: Nuevo tipo de campo

        Returns:
            bool: True si se cambió correctamente

        Raises:
            DatabaseError: Si hay error en la actualización
            ValidationError: Si el tipo es inválido
        """
        try:
            field = self.get_field(field_id)
            if not field:
                raise ValidationError(f"Campo {field_id} no encontrado")

            # Validar nuevo tipo
            validate_field_type(new_type)

            # Actualizar tipo
            field.Tipo_Campo = new_type

            return self.update_field(field)
        except (DatabaseError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error cambiando tipo de campo {field_id}: {e}")
            raise DatabaseError("Error al cambiar tipo de campo", original_error=e)
        
    
    def search_templates(self, query: str, use_cache: bool = False) -> List[Template]:
        """
        Busca plantillas por nombre.

        Args:
            query: Texto a buscar en el nombre de las plantillas
            use_cache: Si se debe usar caché (generalmente False para búsquedas)

        Returns:
            List[Template]: Lista de plantillas que coinciden con la búsqueda

        Raises:
            DatabaseError: Si hay error en la búsqueda
        """
        try:
            # Para búsquedas, generalmente no queremos usar caché
            if not query.strip():
                return self.get_templates(use_cache=use_cache)
                
            # Validar longitud mínima de búsqueda
            if len(query.strip()) < 2:
                raise ValidationError("La búsqueda debe tener al menos 2 caracteres")
                
            # Sanitizar la consulta
            query = query.strip().replace('%', '').replace('_', '')
            
            return self.repository.search_templates(query)
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error en búsqueda de plantillas: {e}")
            raise DatabaseError("Error al buscar plantillas", original_error=e)

    def duplicate_template(self, template_id: int, new_name: str) -> int:
        """
        Duplica una plantilla existente con todos sus campos.

        Args:
            template_id: ID de la plantilla a duplicar
            new_name: Nombre para la nueva plantilla

        Returns:
            int: ID de la nueva plantilla

        Raises:
            DatabaseError: Si hay error en la duplicación
            ValidationError: Si los datos son inválidos
        """
        try:
            # Verificar que la plantilla existe
            original = self.get_template(template_id)
            if not original:
                raise ValidationError(f"Plantilla {template_id} no encontrada")
                
            # Verificar que el nuevo nombre no existe
            existing = self.search_templates(new_name)
            if any(t.Nombre == new_name for t in existing):
                raise ValidationError(f"Ya existe una plantilla con el nombre '{new_name}'")
                
            # Validar nuevo nombre
            if not new_name or len(new_name.strip()) == 0:
                raise ValidationError("El nombre no puede estar vacío")
                
            if len(new_name) > 100:  # Ajustar según tu esquema
                raise ValidationError("El nombre excede la longitud máxima permitida")

            with self.transaction():
                # Duplicar la plantilla y sus campos
                new_id = self.repository.duplicate_template(template_id, new_name)
                
                # Limpiar caché ya que se agregó una nueva plantilla
                self._cache.clear()
                
                # Registrar en el log
                self.logger.info(
                    f"Plantilla {template_id} duplicada como {new_id} "
                    f"con nombre '{new_name}'"
                )
                
                return new_id
                
        except (ValidationError, DatabaseError):
            raise
        except Exception as e:
            self.logger.error(f"Error duplicando plantilla {template_id}: {e}")
            raise DatabaseError("Error al duplicar plantilla", original_error=e)

    def export_template(self, template_id: int) -> Dict[str, Any]:
        """
        Exporta una plantilla y sus campos en formato serializable.

        Args:
            template_id: ID de la plantilla a exportar

        Returns:
            Dict[str, Any]: Datos de la plantilla y sus campos

        Raises:
            DatabaseError: Si hay error en la exportación
            ValidationError: Si la plantilla no existe
        """
        try:
            # Obtener la plantilla
            template = self.get_template(template_id)
            if not template:
                raise ValidationError(f"Plantilla {template_id} no encontrada")
                
            # Obtener los campos
            fields = self.get_template_fields(template_id)
            
            # Crear estructura de exportación
            export_data = {
                'template': {
                    'nombre': template.Nombre,
                    'xmp': template.Xmp,
                    'imagen': template.Imagen,
                    'id_grado': template.ID_Grado,
                    'fecha_exportacion': datetime.now().isoformat()
                },
                'fields': [
                    {
                        'nombre': field.Nombre_Campo,
                        'tipo': field.Tipo_Campo,
                        'coordenadas': {
                            'x': field.Cord_x,
                            'y': field.Cord_y,
                            'width': field.Cord_width,
                            'height': field.Cord_height
                        },
                        'pagina': field.NroPagina,
                        'id_rectangulo': field.IdRectangulo
                    }
                    for field in fields
                ]
            }
            
            return export_data
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error exportando plantilla {template_id}: {e}")
            raise DatabaseError("Error al exportar plantilla", original_error=e)

    def import_template(self, export_data: Dict[str, Any]) -> int:
        """
        Importa una plantilla desde un formato exportado.

        Args:
            export_data: Datos de la plantilla a importar

        Returns:
            int: ID de la plantilla importada

        Raises:
            DatabaseError: Si hay error en la importación
            ValidationError: Si los datos son inválidos
        """
        try:
            # Validar estructura de datos
            required_template_keys = {'nombre', 'xmp', 'imagen', 'id_grado'}
            if not all(k in export_data.get('template', {}) for k in required_template_keys):
                raise ValidationError("Datos de plantilla incompletos")
                
            if 'fields' not in export_data:
                raise ValidationError("Faltan datos de campos")
                
            # Verificar nombre único
            template_name = export_data['template']['nombre']
            existing = self.search_templates(template_name)
            if any(t.Nombre == template_name for t in existing):
                template_name = f"{template_name}_imported_{int(time.time())}"

            with self.transaction():
                # Crear plantilla
                template = Template(
                    ID=0,
                    Nombre=template_name,
                    Xmp=export_data['template']['xmp'],
                    Imagen=export_data['template']['imagen'],
                    ID_Grado=export_data['template']['id_grado']
                )
                
                template_id = self.create_template(template)
                
                # Crear campos
                for field_data in export_data['fields']:
                    field = Field(
                        ID=0,
                        ID_Template=template_id,
                        Nombre_Campo=field_data['nombre'],
                        Tipo_Campo=field_data['tipo'],
                        Cord_x=field_data['coordenadas']['x'],
                        Cord_y=field_data['coordenadas']['y'],
                        Cord_width=field_data['coordenadas']['width'],
                        Cord_height=field_data['coordenadas']['height'],
                        NroPagina=field_data['pagina'],
                        IdRectangulo=field_data['id_rectangulo']
                    )
                    
                    self.create_field(field)
                    
                self.logger.info(
                    f"Plantilla importada con ID {template_id} "
                    f"y nombre '{template_name}'"
                )
                
                return template_id
                
        except (ValidationError, DatabaseError):
            raise
        except Exception as e:
            self.logger.error(f"Error importando plantilla: {e}")
            raise DatabaseError("Error al importar plantilla", original_error=e)