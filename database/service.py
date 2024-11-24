import re
from typing import List, Optional
import logging

from core.config import AppConfig
from core.models import Template, Field
from core.exceptions import ValidationError
from database.connection import Cache, DatabaseConnection
from database.repository import TemplateRepository
from core.constants import RegionType

class DatabaseService:
    """High-level database operations with business logic."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.connection = DatabaseConnection(config)
        self.repository = TemplateRepository(self.connection)
        self.cache = Cache(config.cache_timeout) if config.cache_enabled else None

    def initialize(self) -> None:
        """Initialize connections and resources."""
        self.connection.initialize()
        self.logger.info("Database service initialized")

    def close(self) -> None:
        """Release resources and close connections."""
        if self.cache:
            self.cache.clear()
        self.connection.close()
        self.logger.info("Database service closed")

    def get_templates(self, use_cache: bool = True) -> List[Template]:
        """Get all available templates."""
        if use_cache and self.cache:
            cached = self.cache.get('templates')
            if cached:
                return cached

        templates = self.repository.get_templates()
        
        if use_cache and self.cache:
            self.cache.set('templates', templates)
            
        return templates

    def get_template(self, template_id: int, use_cache: bool = True) -> Optional[Template]:
        """Get specific template."""
        cache_key = f'template_{template_id}'
        
        if use_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        template = self.repository.get_template_by_id(template_id)
        
        if use_cache and self.cache and template:
            self.cache.set(cache_key, template)
            
        return template

    def create_template(self, template: Template) -> int:
        """Create new template."""
        with self.connection.transaction() as cursor:
            template_id = self.repository.create_template(template)
            if self.cache:
                self.cache.clear()
            return template_id

    def update_template(self, template: Template) -> bool:
        """Update existing template."""
        with self.connection.transaction() as cursor:
            success = self.repository.update_template(template)
            if success and self.cache:
                self.cache.clear()
            return success

    def delete_template(self, template_id: int) -> bool:
        """Delete template and its fields."""
        with self.connection.transaction() as cursor:
            success = self.repository.delete_template(template_id)
            if success and self.cache:
                self.cache.clear()
            return success

    def get_template_fields(self, template_id: int, use_cache: bool = True) -> List[Field]:
        """Get all fields for a template."""
        cache_key = f'fields_{template_id}'
        
        if use_cache and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        fields = self.repository.get_template_fields(template_id)
        
        if use_cache and self.cache:
            self.cache.set(cache_key, fields)
            
        return fields

    def create_field(self, field: Field) -> int:
        """Create new field with overlap validation."""
        existing_fields = self.get_template_fields(field.ID_Template, use_cache=False)
        
        for existing_field in existing_fields:
            if (existing_field.NroPagina == field.NroPagina and 
                field.intersects(existing_field)):
                raise ValidationError(
                    "El campo se superpone con un campo existente",
                    field=existing_field.Nombre_Campo
                )

        with self.connection.transaction() as cursor:
            field_id = self.repository.create_field(field)
            if self.cache:
                self.cache.clear()
            return field_id

    def update_field(self, field: Field) -> bool:
        """Update field with overlap validation."""
        existing_fields = self.get_template_fields(field.ID_Template, use_cache=False)
        
        for existing_field in existing_fields:
            if (existing_field.ID != field.ID and 
                existing_field.NroPagina == field.NroPagina and 
                field.intersects(existing_field)):
                raise ValidationError(
                    "El campo se superpone con un campo existente",
                    field=existing_field.Nombre_Campo
                )

        with self.connection.transaction() as cursor:
            success = self.repository.update_field(field)
            if success and self.cache:
                self.cache.clear()
            return success

    def delete_field(self, field_id: int) -> bool:
        """Delete field."""
        with self.connection.transaction() as cursor:
            success = self.repository.delete_field(field_id)
            if success and self.cache:
                self.cache.clear()
            return success

    def get_field(self, field_id: int) -> Optional[Field]:
        """Get specific field."""
        return self.repository.get_field_by_id(field_id)

    def duplicate_template(self, template_id: int, new_name: str) -> int:
        """Duplicate template with validation."""
        # Verify template exists
        if not self.get_template(template_id):
            raise ValidationError(f"Template {template_id} not found")
            
        # Verify new name
        if not new_name.strip():
            raise ValidationError("Template name cannot be empty")
            
        existing = self.repository.search_templates(new_name)
        if any(t.Nombre == new_name for t in existing):
            raise ValidationError(f"Template with name '{new_name}' already exists")

        with self.connection.transaction() as cursor:
            new_id = self.repository.duplicate_template(template_id, new_name)
            if self.cache:
                self.cache.clear()
            return new_id
        
        
    def move_field(self, field_id: int, new_x: float, new_y: float) -> bool:
        """Move field to new coordinates."""
        field = self.get_field(field_id)
        if not field:
            raise ValidationError(f"Field {field_id} not found")

        field.Cord_x = new_x
        field.Cord_y = new_y
        
        return self.update_field(field)

    def resize_field(self, field_id: int, new_width: float, new_height: float) -> bool:
        """Resize field dimensions."""
        field = self.get_field(field_id)
        if not field:
            raise ValidationError(f"Field {field_id} not found")

        if new_width <= 0 or new_height <= 0:
            raise ValidationError("Dimensions must be greater than zero")

        field.Cord_width = new_width
        field.Cord_height = new_height
        
        return self.update_field(field)

    def change_field_type(self, field_id: int, new_type: str) -> bool:
        """Change field type."""
        field = self.get_field(field_id)
        if not field:
            raise ValidationError(f"Field {field_id} not found")

        # Validate new type
        if new_type not in [t.value for t in RegionType]:
            valid_types = ", ".join(t.value for t in RegionType)
            raise ValidationError(f"Type must be one of: {valid_types}")

        field.Tipo_Campo = new_type
        
        return self.update_field(field)

    def rename_field(self, field_id: int, new_name: str) -> bool:
        """Rename field."""
        field = self.get_field(field_id)
        if not field:
            raise ValidationError(f"Field {field_id} not found")

        # Format name to uppercase
        new_name = new_name.strip().upper()
        
        # Validate new name
        if not new_name:
            raise ValidationError("Field name cannot be empty")
        
        if not re.match(self.config.field_validation['name_pattern'], new_name):
            raise ValidationError("Name can only contain uppercase letters, numbers and underscores")
        
        if len(new_name) > self.config.field_validation['max_name_length']:
            raise ValidationError(f"Name cannot exceed {self.config.field_validation['max_name_length']} characters")

        field.Nombre_Campo = new_name
        
        return self.update_field(field)

    def search_fields(self, template_id: int, search_text: str) -> List[Field]:
        """Search fields by name within a template."""
        query = f"%{search_text.strip().upper()}%"
        
        sql = """
        SELECT ID, ID_Template, Nombre_Campo, Tipo_Campo,
               Cord_x, Cord_y, Cord_width, Cord_height,
               NroPagina, IdRectangulo
        FROM Tbl_Fields
        WHERE ID_Template = ? AND Nombre_Campo LIKE ?
        ORDER BY NroPagina, Nombre_Campo
        """
        
        with self.connection.get_cursor() as cursor:
            cursor.execute(sql, (template_id, query))
            return [Field(*row) for row in cursor.fetchall()]

    def get_fields_by_page(self, template_id: int, page_number: int) -> List[Field]:
        """Get all fields for a specific page of a template."""
        sql = """
        SELECT ID, ID_Template, Nombre_Campo, Tipo_Campo,
               Cord_x, Cord_y, Cord_width, Cord_height,
               NroPagina, IdRectangulo
        FROM Tbl_Fields
        WHERE ID_Template = ? AND NroPagina = ?
        ORDER BY Nombre_Campo
        """
        
        with self.connection.get_cursor() as cursor:
            cursor.execute(sql, (template_id, page_number))
            return [Field(*row) for row in cursor.fetchall()]