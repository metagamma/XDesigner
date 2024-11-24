from typing import List, Optional, Tuple
from core.config import AppConfig
from database.repository import DatabaseRepository, Template, Field

class DatabaseService:
    def __init__(self, config: AppConfig):
        self.config = config
        connection_string = (
            f"DRIVER={{{config.db_driver}}};"
            f"SERVER={config.db_server};"
            f"DATABASE={config.db_name};"
            f"UID={config.db_user};"
            f"PWD={config.db_password};"
            f"TrustServerCertificate={config.db_trust_certificate};"
            f"MultipleActiveResultSets={config.db_multiple_active_resultsets}"
        )
        self.repository = DatabaseRepository(connection_string)

    def initialize(self):
        self.repository.connect()

    def close(self):
        self.repository.close()

    def get_templates(self) -> List[Template]:
        return self.repository.get_templates()

    def get_template(self, template_id: int) -> Optional[Template]:
        return self.repository.get_template_by_id(template_id)

    def create_template(self, template: Template) -> int:
        return self.repository.create_template(template)

    def update_template(self, template: Template) -> bool:
        return self.repository.update_template(template)

    def delete_template(self, template_id: int) -> bool:
        return self.repository.delete_template(template_id)

    def get_template_fields(self, template_id: int) -> List[Field]:
        return self.repository.get_fields_by_template(template_id)

    def create_field(self, field: Field) -> int:
        return self.repository.create_field(field)

    def update_field(self, field: Field) -> bool:
        return self.repository.update_field(field)

    def delete_field(self, field_id: int) -> bool:
        return self.repository.delete_field(field_id)