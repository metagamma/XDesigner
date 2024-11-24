import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from core.models import Template, Field
from core.exceptions import DatabaseError, ValidationError
from database.connection import DatabaseConnection

class TemplateRepository:
    """Repositorio para operaciones CRUD de plantillas y campos."""
    
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.logger = logging.getLogger(__name__)

    def get_templates(self) -> List[Template]:
        """Obtiene todas las plantillas disponibles."""
        query = """
        SELECT ID, Nombre, Xmp, Imagen, ID_Grado
        FROM Tbl_Template
        ORDER BY Nombre
        """
        
        try:
            with self.connection.get_cursor() as cursor:
                cursor.execute(query)
                return [Template(*row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error obteniendo plantillas: {e}")
            raise DatabaseError("Error al obtener plantillas") from e

    def get_template_by_id(self, template_id: int) -> Optional[Template]:
        """Obtiene una plantilla específica por ID."""
        query = """
        SELECT ID, Nombre, Xmp, Imagen, ID_Grado
        FROM Tbl_Template
        WHERE ID = ?
        """
        
        try:
            with self.connection.get_cursor() as cursor:
                cursor.execute(query, (template_id,))
                row = cursor.fetchone()
                return Template(*row) if row else None
        except Exception as e:
            self.logger.error(f"Error obteniendo plantilla {template_id}: {e}")
            raise DatabaseError(f"Error al obtener plantilla {template_id}") from e
        
        
    def create_template(self, template: Template) -> int:
        """
        Crea una nueva plantilla.
        
        Args:
            template: Objeto Template con los datos de la plantilla
            
        Returns:
            int: ID de la plantilla creada
            
        Raises:
            DatabaseError: Si hay error en la inserción
            ValidationError: Si los datos no son válidos
        """
        try:
            # Validar plantilla
            template.validate()
            
            query = """
            INSERT INTO Tbl_Template (Nombre, Xmp, Imagen, ID_Grado)
            VALUES (?, ?, ?, ?);
            SELECT SCOPE_IDENTITY();
            """
            
            with self.connection.transaction() as cursor:
                cursor.execute(
                    query,
                    (template.Nombre, template.Xmp, template.Imagen, template.ID_Grado)
                )
                new_id = cursor.fetchval()
                self.logger.info(f"Plantilla creada con ID: {new_id}")
                return new_id
                
        except Exception as e:
            self.logger.error(f"Error creando plantilla: {e}")
            raise DatabaseError("Error al crear plantilla") from e

    def update_template(self, template: Template) -> bool:
        """
        Actualiza una plantilla existente.
        
        Args:
            template: Objeto Template con los datos actualizados
            
        Returns:
            bool: True si se actualizó correctamente
            
        Raises:
            DatabaseError: Si hay error en la actualización
            ValidationError: Si los datos no son válidos
        """
        try:
            template.validate()
            
            query = """
            UPDATE Tbl_Template
            SET Nombre = ?, Xmp = ?, Imagen = ?, ID_Grado = ?
            WHERE ID = ?
            """
            
            with self.connection.transaction() as cursor:
                cursor.execute(
                    query,
                    (template.Nombre, template.Xmp, template.Imagen, 
                     template.ID_Grado, template.ID)
                )
                rows_affected = cursor.rowcount
                if rows_affected > 0:
                    self.logger.info(f"Plantilla {template.ID} actualizada")
                return rows_affected > 0
                
        except Exception as e:
            self.logger.error(f"Error actualizando plantilla {template.ID}: {e}")
            raise DatabaseError(f"Error al actualizar plantilla {template.ID}") from e

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
            with self.connection.transaction() as cursor:
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
                
                rows_affected = cursor.rowcount
                if rows_affected > 0:
                    self.logger.info(f"Plantilla {template_id} eliminada")
                return rows_affected > 0
                
        except Exception as e:
            self.logger.error(f"Error eliminando plantilla {template_id}: {e}")
            raise DatabaseError(f"Error al eliminar plantilla {template_id}") from e

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
            raise DatabaseError(f"Error al obtener campos de plantilla {template_id}") from e

    def get_field_by_id(self, field_id: int) -> Optional[Field]:
        """
        Obtiene un campo específico por su ID.
        
        Args:
            field_id: ID del campo
            
        Returns:
            Optional[Field]: Campo encontrado o None
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
            raise DatabaseError(f"Error al obtener campo {field_id}") from e

    def create_field(self, field: Field) -> int:
        """
        Crea un nuevo campo en una plantilla.
        
        Args:
            field: Objeto Field con los datos del campo
            
        Returns:
            int: ID del campo creado
        """
        try:
            field.validate()
            
            query = """
            INSERT INTO Tbl_Fields 
            (ID_Template, Nombre_Campo, Tipo_Campo,
             Cord_x, Cord_y, Cord_width, Cord_height,
             NroPagina, IdRectangulo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            SELECT SCOPE_IDENTITY();
            """
            
            with self.connection.transaction() as cursor:
                cursor.execute(
                    query,
                    (field.ID_Template, field.Nombre_Campo, field.Tipo_Campo,
                     field.Cord_x, field.Cord_y, field.Cord_width, field.Cord_height,
                     field.NroPagina, field.IdRectangulo)
                )
                new_id = cursor.fetchval()
                self.logger.info(f"Campo creado con ID: {new_id}")
                return new_id
                
        except Exception as e:
            self.logger.error(f"Error creando campo: {e}")
            raise DatabaseError("Error al crear campo") from e

    def update_field(self, field: Field) -> bool:
        """
        Actualiza un campo existente.
        
        Args:
            field: Objeto Field con los datos actualizados
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            field.validate()
            
            query = """
            UPDATE Tbl_Fields
            SET Nombre_Campo = ?, Tipo_Campo = ?,
                Cord_x = ?, Cord_y = ?, 
                Cord_width = ?, Cord_height = ?,
                NroPagina = ?, IdRectangulo = ?
            WHERE ID = ? AND ID_Template = ?
            """
            
            with self.connection.transaction() as cursor:
                cursor.execute(
                    query,
                    (field.Nombre_Campo, field.Tipo_Campo,
                     field.Cord_x, field.Cord_y, field.Cord_width, field.Cord_height,
                     field.NroPagina, field.IdRectangulo,
                     field.ID, field.ID_Template)
                )
                rows_affected = cursor.rowcount
                if rows_affected > 0:
                    self.logger.info(f"Campo {field.ID} actualizado")
                return rows_affected > 0
                
        except Exception as e:
            self.logger.error(f"Error actualizando campo {field.ID}: {e}")
            raise DatabaseError(f"Error al actualizar campo {field.ID}") from e

    def delete_field(self, field_id: int) -> bool:
        """
        Elimina un campo.
        
        Args:
            field_id: ID del campo a eliminar
            
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            query = "DELETE FROM Tbl_Fields WHERE ID = ?"
            
            with self.connection.transaction() as cursor:
                cursor.execute(query, (field_id,))
                rows_affected = cursor.rowcount
                if rows_affected > 0:
                    self.logger.info(f"Campo {field_id} eliminado")
                return rows_affected > 0
                
        except Exception as e:
            self.logger.error(f"Error eliminando campo {field_id}: {e}")
            raise DatabaseError(f"Error al eliminar campo {field_id}") from e

    def get_fields_by_page(self, template_id: int, page_number: int) -> List[Field]:
        """
        Obtiene todos los campos de una página específica.
        
        Args:
            template_id: ID de la plantilla
            page_number: Número de página
            
        Returns:
            List[Field]: Lista de campos en la página
        """
        try:
            query = """
            SELECT ID, ID_Template, Nombre_Campo, Tipo_Campo,
                   Cord_x, Cord_y, Cord_width, Cord_height,
                   NroPagina, IdRectangulo
            FROM Tbl_Fields
            WHERE ID_Template = ? AND NroPagina = ?
            ORDER BY Nombre_Campo
            """
            
            with self.connection.get_cursor() as cursor:
                cursor.execute(query, (template_id, page_number))
                return [Field(*row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(
                f"Error obteniendo campos de plantilla {template_id} página {page_number}: {e}"
            )
            raise DatabaseError("Error al obtener campos por página") from e

    def search_templates(self, query_text: str) -> List[Template]:
        """
        Busca plantillas por nombre.
        
        Args:
            query_text: Texto a buscar
            
        Returns:
            List[Template]: Lista de plantillas que coinciden
        """
        try:
            query = """
            SELECT ID, Nombre, Xmp, Imagen, ID_Grado
            FROM Tbl_Template
            WHERE Nombre LIKE ?
            ORDER BY Nombre
            """
            
            with self.connection.get_cursor() as cursor:
                cursor.execute(query, (f"%{query_text}%",))
                return [Template(*row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Error buscando plantillas: {e}")
            raise DatabaseError("Error al buscar plantillas") from e

    def duplicate_template(self, template_id: int, new_name: str) -> int:
        """
        Duplica una plantilla y sus campos.
        
        Args:
            template_id: ID de la plantilla a duplicar
            new_name: Nombre para la nueva plantilla
            
        Returns:
            int: ID de la nueva plantilla
        """
        try:
            with self.connection.transaction() as cursor:
                # Duplicar plantilla
                cursor.execute("""
                    INSERT INTO Tbl_Template (Nombre, Xmp, Imagen, ID_Grado)
                    OUTPUT INSERTED.ID
                    SELECT ?, Xmp, Imagen, ID_Grado
                    FROM Tbl_Template WHERE ID = ?
                """, (new_name, template_id))
                
                new_template_id = cursor.fetchval()
                
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
                
                self.logger.info(f"Plantilla {template_id} duplicada como {new_template_id}")
                return new_template_id
                
        except Exception as e:
            self.logger.error(f"Error duplicando plantilla {template_id}: {e}")
            raise DatabaseError(f"Error al duplicar plantilla {template_id}") from e