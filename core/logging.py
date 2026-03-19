"""
Logging configuration.
"""
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    """Configure logging for the application."""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger('django')
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'django.log'),
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
