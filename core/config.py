import os
import logging
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class AppConfig:
    """Configuración global de la aplicación de emplantillado."""
    APP_ROOT: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    LOGS_PATH: Path = field(init=False)
    
    # Configuración de base de datos
    db_driver: str = "ODBC Driver 17 for SQL Server"
    db_server: str = "127.0.0.1"
    db_name: str = "BD_PLANTILLA_PRD"
    db_user: str = "sa"
    db_password: str = "admin.2023"
    db_trust_certificate: str = "yes"
    db_multiple_active_resultsets: str = "yes"
    db_pool_min_size: int = 5
    db_pool_max_size: int = 20
    db_connection_timeout: int = 30
    db_query_timeout: int = 300
    db_pool_timeout: int = 30
    db_connection_lifetime = 0
    db_connection_reset = "Yes"
    
    # Configuración de imágenes y visualización
    dpi_min: int = 300
    max_image_size: int = 20_000_000  # 20MB
    allowed_image_extensions: set = field(default_factory=lambda: {'.tif', '.tiff'})
    
    # Configuración de campos
    min_field_size: int = 20  # píxeles
    max_field_name_length: int = 100
    field_name_pattern: str = r'^[A-Z0-9_]+$'
    
    # Configuración de logging
    log_level: int = logging.INFO
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # Configuración de caché
    cache_enabled: bool = True
    cache_timeout: int = 300  # segundos
    
    def __post_init__(self):
        """Inicializa rutas y crea directorios necesarios."""
        self.LOGS_PATH = self.APP_ROOT / "logs"
        self.LOGS_PATH.mkdir(parents=True, exist_ok=True)