from typing import List, Optional
from dataclasses import dataclass
import pyodbc
from core.exceptions import DatabaseError

@dataclass
class Template:
    ID: int
    Nombre: str
    Xmp: str
    Imagen: str
    ID_Grado: int

@dataclass
class Field:
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

class DatabaseRepository:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None

    def connect(self):
        try:
            self.connection = pyodbc.connect(self.connection_string)
        except Exception as e:
            raise DatabaseError(f"Failed to connect to database: {str(e)}")

    def close(self):
        if self.connection:
            self.connection.close()

    def get_templates(self) -> List[Template]:
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT ID, Nombre, Xmp, Imagen, ID_Grado FROM Tbl_Template")
            templates = []
            for row in cursor.fetchall():
                templates.append(Template(*row))
            return templates
        except Exception as e:
            raise DatabaseError(f"Failed to fetch templates: {str(e)}")

    def get_template_by_id(self, template_id: int) -> Optional[Template]:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT ID, Nombre, Xmp, Imagen, ID_Grado FROM Tbl_Template WHERE ID = ?",
                (template_id,)
            )
            row = cursor.fetchone()
            return Template(*row) if row else None
        except Exception as e:
            raise DatabaseError(f"Failed to fetch template {template_id}: {str(e)}")

    def create_template(self, template: Template) -> int:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO Tbl_Template (Nombre, Xmp, Imagen, ID_Grado)
                VALUES (?, ?, ?, ?)
                """,
                (template.Nombre, template.Xmp, template.Imagen, template.ID_Grado)
            )
            self.connection.commit()
            return cursor.execute("SELECT @@IDENTITY").fetchval()
        except Exception as e:
            raise DatabaseError(f"Failed to create template: {str(e)}")

    def update_template(self, template: Template) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE Tbl_Template
                SET Nombre = ?, Xmp = ?, Imagen = ?, ID_Grado = ?
                WHERE ID = ?
                """,
                (template.Nombre, template.Xmp, template.Imagen, template.ID_Grado, template.ID)
            )
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            raise DatabaseError(f"Failed to update template {template.ID}: {str(e)}")

    def delete_template(self, template_id: int) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM Tbl_Template WHERE ID = ?", (template_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            raise DatabaseError(f"Failed to delete template {template_id}: {str(e)}")

    def get_fields_by_template(self, template_id: int) -> List[Field]:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT ID, ID_Template, Nombre_Campo, Tipo_Campo, 
                       Cord_x, Cord_y, Cord_width, Cord_height, 
                       NroPagina, IdRectangulo
                FROM Tbl_Fields
                WHERE ID_Template = ?
                ORDER BY NroPagina, Nombre_Campo
                """,
                (template_id,)
            )
            fields = []
            for row in cursor.fetchall():
                fields.append(Field(*row))
            return fields
        except Exception as e:
            raise DatabaseError(f"Failed to fetch fields for template {template_id}: {str(e)}")

    def create_field(self, field: Field) -> int:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO Tbl_Fields 
                (ID_Template, Nombre_Campo, Tipo_Campo, Cord_x, Cord_y, 
                Cord_width, Cord_height, NroPagina, IdRectangulo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (field.ID_Template, field.Nombre_Campo, field.Tipo_Campo,
                 field.Cord_x, field.Cord_y, field.Cord_width, field.Cord_height,
                 field.NroPagina, field.IdRectangulo)
            )
            self.connection.commit()
            return cursor.execute("SELECT @@IDENTITY").fetchval()
        except Exception as e:
            raise DatabaseError(f"Failed to create field: {str(e)}")

    def update_field(self, field: Field) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE Tbl_Fields
                SET Nombre_Campo = ?, Tipo_Campo = ?, Cord_x = ?, 
                    Cord_y = ?, Cord_width = ?, Cord_height = ?,
                    NroPagina = ?, IdRectangulo = ?
                WHERE ID = ? AND ID_Template = ?
                """,
                (field.Nombre_Campo, field.Tipo_Campo, field.Cord_x,
                 field.Cord_y, field.Cord_width, field.Cord_height,
                 field.NroPagina, field.IdRectangulo, field.ID,
                 field.ID_Template)
            )
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            raise DatabaseError(f"Failed to update field {field.ID}: {str(e)}")

    def delete_field(self, field_id: int) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM Tbl_Fields WHERE ID = ?", (field_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            raise DatabaseError(f"Failed to delete field {field_id}: {str(e)}")