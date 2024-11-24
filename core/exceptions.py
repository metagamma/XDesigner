from typing import Optional, Any, Dict

class ApplicationError(Exception):
    """Excepción base para la aplicación."""
    def __init__(self, message: str, code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)

class DatabaseError(ApplicationError):
    """Error en operaciones de base de datos."""
    def __init__(self, message: str, original_error: Optional[Exception] = None, **kwargs):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            details={"original_error": str(original_error)} if original_error else None,
            **kwargs
        )

class ValidationError(ApplicationError):
    """Error de validación de datos."""
    def __init__(self, message: str, field: Optional[str] = None, 
                 value: Optional[Any] = None, **kwargs):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={
                "field": field,
                "value": value
            } if field else None,
            **kwargs
        )

class TemplateError(ApplicationError):
    """Error relacionado con plantillas."""
    def __init__(self, message: str, template_id: Optional[int] = None, **kwargs):
        super().__init__(
            message=message,
            code="TEMPLATE_ERROR",
            details={"template_id": template_id} if template_id else None,
            **kwargs
        )

class FieldError(ApplicationError):
    """Error relacionado con campos de plantilla."""
    def __init__(self, message: str, field_id: Optional[int] = None, 
                 field_name: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            code="FIELD_ERROR",
            details={
                "field_id": field_id,
                "field_name": field_name
            } if field_id or field_name else None,
            **kwargs
        )

class ImageError(ApplicationError):
    """Error relacionado con procesamiento de imágenes."""
    def __init__(self, message: str, image_path: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(
            message=message,
            code="IMAGE_ERROR",
            details={"image_path": image_path, **details} if details else {"image_path": image_path},
            **kwargs
        )

class CoordinateError(ApplicationError):
    """Error relacionado con coordenadas de campos."""
    def __init__(self, message: str, x: Optional[float] = None, 
                 y: Optional[float] = None, **kwargs):
        super().__init__(
            message=message,
            code="COORDINATE_ERROR",
            details={"x": x, "y": y} if x is not None and y is not None else None,
            **kwargs
        )