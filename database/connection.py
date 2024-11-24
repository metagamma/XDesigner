from typing import Optional, Any, List, Dict, Tuple
from datetime import datetime, timedelta
import logging
import time
import pyodbc
from contextlib import contextmanager

from core.config import AppConfig
from core.exceptions import DatabaseError

class Cache:
    """Simple cache implementation with timeout."""
    
    def __init__(self, timeout_seconds: int = 300):
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._timeout = timeout_seconds
        
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key not in self._cache:
            return None
        
        value, timestamp = self._cache[key]
        if datetime.now() - timestamp > timedelta(seconds=self._timeout):
            del self._cache[key]
            return None
            
        return value
        
    def set(self, key: str, value: Any) -> None:
        """Store value in cache with current timestamp."""
        self._cache[key] = (value, datetime.now())
        
    def delete(self, key: str) -> None:
        """Remove entry from cache."""
        self._cache.pop(key, None)
        
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

class DatabaseConnection:
    """SQL Server connection manager."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.connection: Optional[pyodbc.Connection] = None
        
    def initialize(self) -> None:
        """Initialize connection with retry policy."""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                if self.connection and not self.connection.closed:
                    self.close()
                    
                self.connection = pyodbc.connect(
                    self.config.get_connection_string(), 
                    autocommit=True
                )
                self.logger.info("Database connection initialized")
                return
                
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    time.sleep(retry_delay)
                else:
                    raise DatabaseError("Failed to initialize database connection") from e

    @contextmanager
    def get_cursor(self):
        """Provide cursor with automatic reconnection and cleanup."""
        if not self.connection or self.connection.closed:
            self.initialize()
            
        cursor = self.connection.cursor()
        try:
            yield cursor
        except pyodbc.Error as e:
            if any(err in str(e) for err in [
                'Connection is closed',
                'Connection reset',
                'Connection timeout',
                'Connection lost',
                'Communication link failure'
            ]):
                self.initialize()
                raise DatabaseError("Connection error - please retry") from e
            raise DatabaseError(f"Database error: {str(e)}") from e
        finally:
            cursor.close()
            
    @contextmanager
    def transaction(self):
        """Provide transaction context with automatic commit/rollback."""
        with self.get_cursor() as cursor:
            try:
                cursor.execute("BEGIN TRANSACTION")
                yield cursor
                cursor.execute("COMMIT")
            except Exception:
                cursor.execute("ROLLBACK")
                raise
                
    def close(self) -> None:
        """Safely close connection."""
        if self.connection and not self.connection.closed:
            try:
                self.connection.close()
            finally:
                self.connection = None
                self.logger.info("Connection closed")