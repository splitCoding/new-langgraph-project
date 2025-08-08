"""Logging utilities for review package."""

import logging
import sys
from typing import Optional


def setup_review_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup logger for review package.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    
    return logger


def get_review_logger(name: Optional[str] = None) -> logging.Logger:
    """Get logger instance for review package.
    
    Args:
        name: Logger name (defaults to review)
        
    Returns:
        Logger instance
    """
    logger_name = f"review.{name}" if name else "review"
    return setup_review_logger(logger_name)