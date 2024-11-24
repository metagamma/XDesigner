import re
from typing import Optional, Tuple

def validate_field_name(name: str) -> Tuple[bool, Optional[str]]:
    """Validate field name."""
    if not name:
        return False, "Field name cannot be empty"
    if len(name) > 100:
        return False, "Field name cannot exceed 100 characters"
    if not re.match(r'^[A-Z0-9_]+$', name):
        return False, "Field name must contain only uppercase letters, numbers, and underscores"
    return True, None