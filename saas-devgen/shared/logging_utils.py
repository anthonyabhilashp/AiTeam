"""Shared logging utilities for all services."""
import os
import logging
import sys
from datetime import datetime
from typing import Optional
from shared.config import settings


def setup_logger(service_name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logger for a service with detailed logging.
    
    Args:
        service_name: Name of the service
        log_file: Optional log file name (will be created in logs folder)
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(settings.log_dir, exist_ok=True)
    
    # Clean up old log files (delete and create new)
    if log_file:
        log_path = os.path.join(settings.log_dir, log_file)
        if os.path.exists(log_path):
            os.remove(log_path)
    
    # Configure logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if log_file specified
    if log_file:
        log_path = os.path.join(settings.log_dir, log_file)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Log file created: {log_path}")
    
    logger.info(f"Logger initialized for {service_name}")
    return logger


def log_api_call(logger: logging.Logger, method: str, endpoint: str, status_code: int, 
                 duration: float, user_id: Optional[str] = None, tenant_id: Optional[str] = None):
    """Log API call details."""
    log_data = {
        "method": method,
        "endpoint": endpoint,
        "status_code": status_code,
        "duration_ms": round(duration * 1000, 2),
        "user_id": user_id,
        "tenant_id": tenant_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    logger.info(f"API_CALL: {log_data}")


def log_error(logger: logging.Logger, error: Exception, context: dict = None):
    """Log error with context."""
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    logger.error(f"ERROR: {error_data}", exc_info=True)
