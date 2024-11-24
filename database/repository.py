from typing import List, Optional, Dict, Any, Tuple
import logging
from core.models import Template, Field
from core.exceptions import DatabaseError, ValidationError
from core.validators import validate_field_name, validate_coordinates, validate_field_type
from .connection import DatabaseConnection


class TemplateRepository:
    """CRUD operations for templates and fields."""
    
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.logger = logging.getLogger(__name__)
        
    def get_templates(self) -> List[Template]:
        """Get all available templates."""
        query = """
        SELECT ID, Nombre, Xmp, Imagen, ID_Grado
        FROM Tbl_Template
        ORDER BY Nombre
        """
        
        with self.connection.get_cursor() as cursor:
            cursor.execute(query)
            return [Template(*row) for row in cursor.fetchall()]
            
    def get_template_by_id(self, template_id: int) -> Optional[Template]:
        """Get specific template by ID."""
        query = """
        SELECT ID, Nombre, Xmp, Imagen, ID_Grado
        FROM Tbl_Template
        WHERE ID = ?
        """
        
        with self.connection.get_cursor() as cursor:
            cursor.execute(query, (template_id,))
            row = cursor.fetchone()
            return Template(*row) if row else None
            
    def create_template(self, template: Template) -> int:
        """Create new template."""
        template.validate()
        
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
            
    def update_template(self, template: Template) -> bool:
        """Update existing template."""
        template.validate()
        
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
            
    def delete_template(self, template_id: int) -> bool:
        """Delete template and its associated fields."""
        with self.connection.transaction() as cursor:
            cursor.execute(
                "DELETE FROM Tbl_Fields WHERE ID_Template = ?",
                (template_id,)
            )
            cursor.execute(
                "DELETE FROM Tbl_Template WHERE ID = ?",
                (template_id,)
            )
            return cursor.rowcount > 0
            
    def get_template_fields(self, template_id: int) -> List[Field]:
        """Get all fields for a template."""
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
            
    def create_field(self, field: Field) -> int:
        """Create new field."""
        field.validate()
        
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

    def update_field(self, field: Field) -> bool:
        """Update existing field."""
        field.validate()
        
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

    def delete_field(self, field_id: int) -> bool:
        """Delete a field."""
        query = "DELETE FROM Tbl_Fields WHERE ID = ?"
        
        with self.connection.get_cursor() as cursor:
            cursor.execute(query, (field_id,))
            return cursor.rowcount > 0

    def get_field_by_id(self, field_id: int) -> Optional[Field]:
        """Get specific field by ID."""
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

    def search_templates(self, query: str) -> List[Template]:
        """Search templates by name."""
        query = f"%{query.strip()}%"
        
        sql = """
        SELECT ID, Nombre, Xmp, Imagen, ID_Grado
        FROM Tbl_Template
        WHERE Nombre LIKE ?
        ORDER BY Nombre
        """
        
        with self.connection.get_cursor() as cursor:
            cursor.execute(sql, (query,))
            return [Template(*row) for row in cursor.fetchall()]

    def duplicate_template(self, template_id: int, new_name: str) -> int:
        """Duplicate a template and its fields."""
        with self.connection.transaction() as cursor:
            # Duplicate template
            cursor.execute("""
                INSERT INTO Tbl_Template (Nombre, Xmp, Imagen, ID_Grado)
                SELECT ?, Xmp, Imagen, ID_Grado
                FROM Tbl_Template WHERE ID = ?
                """, (new_name, template_id))
            
            new_template_id = cursor.execute("SELECT @@IDENTITY").fetchval()
            
            # Duplicate fields
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