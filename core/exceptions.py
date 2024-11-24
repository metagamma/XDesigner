from typing import Optional, Any, Dict

class ApplicationError(Exception):
    """Excepción base para la aplicación."""
    def __init__(self, message: str, code: str = "ERROR", details: Optional[Dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class DatabaseError(ApplicationError):
    """Error en operaciones de base de datos."""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            details={"original_error": str(original_error)} if original_error else None
        )

class ValidationError(ApplicationError):
    """Error de validación de datos."""
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field, "value": value} if field else None
        )

class ImageError(ApplicationError):
    """Error relacionado con imágenes."""
    def __init__(self, message: str, image_path: str, dpi: Optional[int] = None):
        details = {"image_path": image_path}
        if dpi:
            details["dpi"] = dpi
        super().__init__(message=message, code="IMAGE_ERROR", details=details)

class TemplateError(ApplicationError):
    """Error relacionado con plantillas."""
    def __init__(self, message: str, template_id: Optional[int] = None):
        super().__init__(
            message=message,
            code="TEMPLATE_ERROR",
            details={"template_id": template_id} if template_id else None
        )

def handle_exception(exc: Exception) -> ApplicationError:
    """Convierte excepciones genéricas en excepciones de la aplicación."""
    if isinstance(exc, ApplicationError):
        return exc
        
    exception_mapping = {
        ValueError: ValidationError,
        FileNotFoundError: ImageError,
        OSError: ImageError,
        TypeError: ValidationError
    }
    
    exception_class = exception_mapping.get(type(exc), ApplicationError)
    return exception_class(str(exc))