import time
import pyodbc
import logging
from typing import Optional
from contextlib import contextmanager

from core.config import AppConfig
from core.exceptions import DatabaseError

class DatabaseConnection:
    """Manejador de conexión a SQL Server."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.connection: Optional[pyodbc.Connection] = None
        self._create_connection_string()

    def _create_connection_string(self) -> None:
        """Configura la cadena de conexión con parámetros optimizados."""
        self.connection_string = (
            f"DRIVER={{{self.config.db_driver}}};"
            f"SERVER={self.config.db_server};"
            f"DATABASE={self.config.db_name};"
            f"UID={self.config.db_user};"
            f"PWD={self.config.db_password};"
            f"TrustServerCertificate={self.config.db_trust_certificate};"
            f"MultipleActiveResultSets={self.config.db_multiple_active_resultsets};"
            f"Connection Timeout={self.config.db_connection_timeout};"
            f"Query Timeout={self.config.db_query_timeout};"
            f"Pool Timeout={self.config.db_pool_timeout};"
            f"Min Pool Size={self.config.db_pool_min_size};"
            f"Max Pool Size={self.config.db_pool_max_size};"
            f"Connection Lifetime={self.config.db_connection_lifetime};"
            f"Connection Reset={self.config.db_connection_reset};"
        )

    def initialize(self) -> None:
        """Inicializa la conexión con política de reintentos."""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                if self.connection and not self.connection.closed:
                    self.close()
                    
                self.connection = pyodbc.connect(self.connection_string, autocommit=True)
                self.logger.info("Conexión a base de datos inicializada")
                return
                
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Intento {attempt + 1} fallido: {e}")
                    time.sleep(retry_delay)
                else:
                    self.logger.error(f"Error al inicializar conexión: {e}")
                    raise DatabaseError("Error en la conexión a la base de datos") from e

    @contextmanager
    def get_cursor(self):
        """Provee un cursor con manejo automático de reconexión y cierre."""
        try:
            if not self.connection or self.connection.closed:
                self.initialize()
                
            cursor = self.connection.cursor()
            try:
                yield cursor
            finally:
                cursor.close()
        except pyodbc.Error as e:
            if self._is_connection_error(e):
                self.initialize()
                raise DatabaseError("Error de conexión - intente nuevamente") from e
            raise DatabaseError(f"Error de base de datos: {str(e)}") from e

    def _is_connection_error(self, error: pyodbc.Error) -> bool:
        """Identifica errores relacionados con la conexión."""
        connection_errors = [
            'Connection is closed',
            'Connection reset',
            'Connection timeout',
            'Connection lost',
            'Communication link failure',
            'Transport-level error'
        ]
        return any(err in str(error) for err in connection_errors)
            
    def close(self) -> None:
        """Cierra la conexión de manera segura."""
        if self.connection:
            try:
                if not self.connection.closed:
                    self.connection.close()
            except Exception as e:
                self.logger.error(f"Error cerrando conexión: {e}")
            finally:
                self.connection = None
                self.logger.info("Conexión cerrada")
    
    def __del__(self):
        """Asegura el cierre de la conexión al destruir el objeto."""
        self.close()