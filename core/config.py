from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
from typing import Dict, Any

@dataclass
class AppConfig:
    """Configuración global de la aplicación."""
    APP_ROOT: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    LOGS_PATH: Path = field(init=False)
    
    # Base de datos
    db_config: Dict[str, Any] = field(default_factory=lambda: {
        "driver": "ODBC Driver 17 for SQL Server",
        "server": "127.0.0.1",
        "database": "ENLA2024",
        "user": "sa",
        "password": "admin.2023",
        "trust_certificate": "yes",
        "multiple_active_resultsets": "yes",
        "pool_min_size": 5,
        "pool_max_size": 20,
        "connection_timeout": 30,
        "query_timeout": 300,
        "pool_timeout": 30,
        "connection_lifetime": 0,
        "connection_reset": "Yes"
    })
    
    # Sistema
    system_config: Dict[str, Any] = field(default_factory=lambda: {
        "batch_size": 10,
        "max_threads": os.cpu_count() or 4,
        "timeout_seconds": 30,
        "max_retries": 3
    })
    
    # Logging
    log_config: Dict[str, Any] = field(default_factory=lambda: {
        "level": logging.INFO,
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "date_format": "%Y-%m-%d %H:%M:%S",
        "max_bytes": 5_242_880,  # 5MB
        "backup_count": 5,
        "json_format": False
    })
    
    # Imagen y procesamiento
    image_config: Dict[str, Any] = field(default_factory=lambda: {
        "min_dpi": 300,
        "min_area": 700000,
        "allowed_extensions": {'.tif', '.tiff'}
    })
    
    def __post_init__(self):
        """Inicializa rutas y crea directorios necesarios."""
        self.LOGS_PATH = self.APP_ROOT / "logs"
        self.LOGS_PATH.mkdir(parents=True, exist_ok=True)
    
    def get_log_config(self) -> Dict[str, Any]:
        """Obtiene configuración de logging para setup_logging."""
        return {
            "log_path": self.LOGS_PATH / "app.log",
            "level": self.log_config["level"],
            "max_bytes": self.log_config["max_bytes"],
            "backup_count": self.log_config["backup_count"],
            "json_format": self.log_config["json_format"]
        }