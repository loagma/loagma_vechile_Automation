"""Logging configuration and setup."""
import logging
import sys

from pythonjsonlogger import jsonlogger


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        timestamp=True
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Optional: File handler for production
    # file_handler = logging.FileHandler("app.log")
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)
    
    logger.info(f"Logging configured at {log_level} level")
