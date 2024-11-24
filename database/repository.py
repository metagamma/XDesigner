from typing import List, Optional, Dict, Any, Tuple
import logging
from core.models import Template, Field
from core.exceptions import DatabaseError, ValidationError
from core.validators import validate_field_name, validate_coordinates, validate_field_type
from .connection import DatabaseConnection

class TemplateRepository:
    """Repositorio para operaciones CRUD de plantillas y campos."""
    
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.logger = logging.getLogger(__name__)

    def get_templates(self) -> List[Template]:
        """
        Obtiene todas las plantillas disponibles.

        Returns:
            List[Template]: Lista de plantillas

        Raises:
            DatabaseError: Si hay error en la consulta
        """
        try:
            query = """
            SELECT ID, Nombre, Xmp, Imagen, ID_Grado
            FROM Tbl_Template
            ORDER BY Nombre
            """
            
            with self.connection.get_cursor() as cursor:
                cursor.execute(query)
                return [Template(*row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Error obteniendo plantillas: {e}")
            raise DatabaseError("Error al obtener plantillas", original_error=e)

    def get_template_by_id(self, template_id: int) -> Optional[Template]:
        """
        Obtiene una plantilla específica por su ID.

        Args:
            template_id: ID de la plantilla

        Returns:
            Optional[Template]: Plantilla encontrada o None

        Raises:
            DatabaseError: Si hay error en la consulta
        """
        try:
            query = """
            SELECT ID, Nombre, Xmp, Imagen, ID_Grado
            FROM Tbl_Template
            WHERE ID = ?
            """
            
            with self.connection.get_cursor() as cursor:
                cursor.execute(query, (template_id,))
                row = cursor.fetchone()
                return Template(*row) if row else None
                
        except Exception as e:
            self.logger.error(f"Error obteniendo plantilla {template_id}: {e}")
            raise DatabaseError(f"Error al obtener plantilla {template_id}", original_error=e)

    def create_template(self, template: Template) -> int:
        """
        Crea una nueva plantilla.

        Args:
            template: Datos de la plantilla

        Returns:
            int: ID de la plantilla creada

        Raises:
            DatabaseError: Si hay error en la inserción
            ValidationError: Si los datos son inválidos
        """
        try:
            if not template.is_valid:
                raise ValidationError("Datos de plantilla incompletos")

            query = """
            INSERT INTO Tbl_Template (Nombre, Xmp, Imagen, ID_Grado)
            VALUES (?, ?, ?, ?)
            """
            
            with self.connection.get_cursor() as cursor:
                cursor.execute(
                    query,
                    (template.Nombre, template.Xmp, template.Imagen, template.ID_Grado)
                )
                return cursor.execute("SELECT @@IDENTITY").fetchval()
                
        except ValidationError:
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
            if not template.is_valid:
                raise ValidationError("Datos de plantilla incompletos")

            query = """
            UPDATE Tbl_Template
            SET Nombre = ?, Xmp = ?, Imagen = ?, ID_Grado = ?
            WHERE ID = ?
            """
            
            with self.connection.get_cursor() as cursor:
                cursor.execute(
                    query,
                    (template.Nombre, template.Xmp, template.Imagen, 
                     template.ID_Grado, template.ID)
                )
                return cursor.rowcount > 0
                
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error actualizando plantilla {template.ID}: {e}")
            raise DatabaseError(f"Error al actualizar plantilla {template.ID}", original_error=e)

    def delete_template(self, template_id: int) -> bool:
        """
        Elimina una plantilla y sus campos asociados.

        Args:
            template_id: ID de la plantilla a eliminar

        Returns:
            bool: True si se eliminó correctamente

        Raises:
            DatabaseError: Si hay error en la eliminación
        """
        try:
            with self.connection.get_cursor() as cursor:
                # Primero eliminar campos asociados
                cursor.execute(
                    "DELETE FROM Tbl_Fields WHERE ID_Template = ?",
                    (template_id,)
                )
                
                # Luego eliminar la plantilla
                cursor.execute(
                    "DELETE FROM Tbl_Template WHERE ID = ?",
                    (template_id,)
                )
                
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error eliminando plantilla {template_id}: {e}")
            raise DatabaseError(f"Error al eliminar plantilla {template_id}", original_error=e)

    def get_template_fields(self, template_id: int) -> List[Field]:
        """
        Obtiene todos los campos de una plantilla.

        Args:
            template_id: ID de la plantilla

        Returns:
            List[Field]: Lista de campos

        Raises:
            DatabaseError: Si hay error en la consulta
        """
        try:
            query = """
            SELECT ID, ID_Template, Nombre_Campo, Tipo_Campo,
                   Cord_x, Cord_y, Cord_width, Cord_height,
                   NroPagina, IdRectangulo
            FROM Tbl_Fields
            WHERE ID_Template = ?
            ORDER BY NroPagina, Nombre_Campo
            """
            
            with self.connection.get_cursor() as cursor:
                cursor.execute(query, (template_id,))
                return [Field(*row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Error obteniendo campos de plantilla {template_id}: {e}")
            raise DatabaseError(f"Error al obtener campos", original_error=e)

    def create_field(self, field: Field) -> int:
        """
        Crea un nuevo campo en una plantilla.

        Args:
            field: Datos del campo

        Returns:
            int: ID del campo creado

        Raises:
            DatabaseError: Si hay error en la inserción
            ValidationError: Si los datos son inválidos
        """
        try:
            # Validaciones
            valid, error_msg = validate_field_name(field.Nombre_Campo)
            if not valid:
                raise ValidationError(error_msg, field="Nombre_Campo")
                
            validate_field_type(field.Tipo_Campo)
            validate_coordinates(field.Cord_x, field.Cord_y, 
                              field.Cord_width, field.Cord_height)

            query = """
            INSERT INTO Tbl_Fields 
            (ID_Template, Nombre_Campo, Tipo_Campo,
             Cord_x, Cord_y, Cord_width, Cord_height,
             NroPagina, IdRectangulo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            with self.connection.get_cursor() as cursor:
                cursor.execute(
                    query,
                    (field.ID_Template, field.Nombre_Campo, field.Tipo_Campo,
                     field.Cord_x, field.Cord_y, field.Cord_width, field.Cord_height,
                     field.NroPagina, field.IdRectangulo)
                )
                return cursor.execute("SELECT @@IDENTITY").fetchval()
                
        except ValidationError:
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
            # Validaciones
            valid, error_msg = validate_field_name(field.Nombre_Campo)
            if not valid:
                raise ValidationError(error_msg, field="Nombre_Campo")
                
            validate_field_type(field.Tipo_Campo)
            validate_coordinates(field.Cord_x, field.Cord_y, 
                              field.Cord_width, field.Cord_height)

            query = """
            UPDATE Tbl_Fields
            SET Nombre_Campo = ?, Tipo_Campo = ?,
                Cord_x = ?, Cord_y = ?, 
                Cord_width = ?, Cord_height = ?,
                NroPagina = ?, IdRectangulo = ?
            WHERE ID = ? AND ID_Template = ?
            """
            
            with self.connection.get_cursor() as cursor:
                cursor.execute(
                    query,
                    (field.Nombre_Campo, field.Tipo_Campo,
                     field.Cord_x, field.Cord_y, field.Cord_width, field.Cord_height,
                     field.NroPagina, field.IdRectangulo,
                     field.ID, field.ID_Template)
                )
                return cursor.rowcount > 0
                
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error actualizando campo {field.ID}: {e}")
            raise DatabaseError(f"Error al actualizar campo {field.ID}", original_error=e)

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
            query = "DELETE FROM Tbl_Fields WHERE ID = ?"
            
            with self.connection.get_cursor() as cursor:
                cursor.execute(query, (field_id,))
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Error eliminando campo {field_id}: {e}")
            raise DatabaseError(f"Error al eliminar campo {field_id}", original_error=e)

    def get_field_by_id(self, field_id: int) -> Optional[Field]:
        """
        Obtiene un campo específico por su ID.

        Args:
            field_id: ID del campo

        Returns:
            Optional[Field]: Campo encontrado o None

        Raises:
            DatabaseError: Si hay error en la consulta
        """
        try:
            query = """
            SELECT ID, ID_Template, Nombre_Campo, Tipo_Campo,
                   Cord_x, Cord_y, Cord_width, Cord_height,
                   NroPagina, IdRectangulo
            FROM Tbl_Fields
            WHERE ID = ?
            """
            
            with self.connection.get_cursor() as cursor:
                cursor.execute(query, (field_id,))
                row = cursor.fetchone()
                return Field(*row) if row else None
                
        except Exception as e:
            self.logger.error(f"Error obteniendo campo {field_id}: {e}")
            raise DatabaseError(f"Error al obtener campo {field_id}", original_error=e)
        
    
    def search_templates(self, query: str) -> List[Template]:
        """Búsqueda de plantillas por nombre."""
        try:
            sql = """
            SELECT ID, Nombre, Xmp, Imagen, ID_Grado
            FROM Tbl_Template
            WHERE Nombre LIKE ?
            ORDER BY Nombre
            """
            with self.connection.get_cursor() as cursor:
                cursor.execute(sql, (f'%{query}%',))
                return [Template(*row) for row in cursor.fetchall()]
        except Exception as e:
            raise DatabaseError(f"Error en búsqueda de plantillas: {str(e)}")


    def duplicate_template(self, template_id: int, new_name: str) -> int:
        """Duplica una plantilla y sus campos."""
        try:
            with self.connection.transaction() as cursor:
                # Duplicar plantilla
                cursor.execute("""
                    INSERT INTO Tbl_Template (Nombre, Xmp, Imagen, ID_Grado)
                    SELECT ?, Xmp, Imagen, ID_Grado
                    FROM Tbl_Template WHERE ID = ?
                    """, (new_name, template_id))
                
                new_template_id = cursor.execute("SELECT @@IDENTITY").fetchval()
                
                # Duplicar campos
                cursor.execute("""
                    INSERT INTO Tbl_Fields 
                    (ID_Template, Nombre_Campo, Tipo_Campo, Cord_x, 
                     Cord_y, Cord_width, Cord_height, NroPagina, IdRectangulo)
                    SELECT ?, Nombre_Campo, Tipo_Campo, Cord_x,
                           Cord_y, Cord_width, Cord_height, NroPagina, IdRectangulo
                    FROM Tbl_Fields 
                    WHERE ID_Template = ?
                    """, (new_template_id, template_id))
                
                return new_template_id
        except Exception as e:
            raise DatabaseError(f"Error duplicando plantilla: {str(e)}")