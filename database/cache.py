from typing import Optional, Any, Callable
from datetime import datetime, timedelta
import functools
import logging

class Cache:
    """Implementación de caché con expiración por tiempo."""
    
    def __init__(self, timeout_seconds: int = 300):
        self._cache = {}
        self._timeout = timeout_seconds
        self.logger = logging.getLogger(__name__)

    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché si no ha expirado."""
        if key not in self._cache:
            return None
            
        value, timestamp = self._cache[key]
        if datetime.now() - timestamp > timedelta(seconds=self._timeout):
            del self._cache[key]
            return None
            
        return value

    def set(self, key: str, value: Any) -> None:
        """Guarda un valor en el caché con timestamp actual."""
        self._cache[key] = (value, datetime.now())

    def delete(self, key: str) -> None:
        """Elimina una entrada del caché."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Limpia todo el caché."""
        self._cache.clear()
        
        
def cache_decorator(timeout: int = 300):
    """
    Decorador para cachear resultados de métodos.
    
    Args:
        timeout: Tiempo de expiración en segundos
        
    Examples:
        >>> @cache_decorator(timeout=60)
        ... def get_user(self, user_id: int):
        ...     return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if not hasattr(self, '_cache'):
                self._cache = Cache(timeout)
                
            # Crear clave única para la combinación de método y argumentos
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Intentar obtener del caché
            cached_value = self._cache.get(cache_key)
            if cached_value is not None:
                return cached_value
                
            # Ejecutar método y guardar en caché
            result = func(self, *args, **kwargs)
            self._cache.set(cache_key, result)
            return result
        return wrapper
    return decorator

def cache_invalidator(func: Callable):
    """
    Decorador para invalidar caché después de operaciones de escritura.
    
    Examples:
        >>> @cache_invalidator
        ... def update_user(self, user_id: int, data: dict):
        ...     self.db.execute("UPDATE users SET name = ? WHERE id = ?", 
        ...                     (data['name'], user_id))
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if hasattr(self, '_cache'):
            self._cache.clear()
        return result
    return wrapper