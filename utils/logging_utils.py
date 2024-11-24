import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import json
import traceback


class CustomFormatter(logging.Formatter):
    """Custom formatter with different formats per log level."""
    def __init__(self):
        super().__init__()
        self.formatters = {
            logging.DEBUG: logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            logging.INFO: logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'),
            logging.WARNING: logging.Formatter('%(asctime)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d'),
            logging.ERROR: logging.Formatter('%(asctime)s - %(levelname)s - %(message)s\nPath: %(pathname)s:%(lineno)d\nFunction: %(funcName)s'),
            logging.CRITICAL: logging.Formatter('%(asctime)s - %(levelname)s - %(message)s\nPath: %(pathname)s:%(lineno)d\nFunction: %(funcName)s\nProcess: %(process)d')
        }
        
    def format(self, record):
        formatter = self.formatters.get(record.levelno, self.formatters[logging.DEBUG])
        if record.exc_info:
            record.exc_text = ''.join(traceback.format_exception(*record.exc_info))
        return formatter.format(record)

def setup_logging(
    log_path: Path,
    level: int = logging.INFO,
    max_bytes: int = 5_242_880,  # 5MB
    backup_count: int = 5,
    json_format: bool = False
) -> None:
    """Set up logging with file and console handlers."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Formatter selection
    formatter = (
        logging.Formatter(json.dumps({
            'timestamp': '%(asctime)s',
            'level': '%(levelname)s',
            'message': '%(message)s',
            'module': '%(module)s',
            'function': '%(funcName)s',
            'line': '%(lineno)d',
            'path': '%(pathname)s'
        }))
        if json_format else CustomFormatter()
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configure external library logging
    for lib in ['PIL', 'opencv', 'tensorflow', 'matplotlib', 'urllib3']:
        logging.getLogger(lib).setLevel(logging.WARNING)

def get_logger(name: str, context: Optional[dict] = None) -> logging.Logger:
    """Get a logger with optional context."""
    logger = logging.getLogger(name)
    if context:
        return logging.LoggerAdapter(logger, context)
    return logger