"""
Logging configuration for Easy Docker Deploy.
"""
import json
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional, Union

from rich.logging import RichHandler

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in a structured JSON format.
    """
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        # Get the original format data
        record_dict = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            record_dict['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields from the record
        if hasattr(record, 'extra_fields'):
            record_dict.update(record.extra_fields)
        
        return json.dumps(record_dict)

class StructuredLogger(logging.Logger):
    """
    Custom logger that supports structured logging with extra fields.
    """
    def _log(
        self,
        level: int,
        msg: str,
        args: tuple,
        exc_info: Optional[tuple] = None,
        extra: Optional[Dict[str, Any]] = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        **kwargs: Any
    ) -> None:
        """
        Override _log to support structured logging with extra fields.
        """
        if extra is None:
            extra = {}
        if kwargs:
            if 'extra_fields' not in extra:
                extra['extra_fields'] = {}
            extra['extra_fields'].update(kwargs)
        super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)

def setup_logging(
    log_level: Union[str, int] = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    max_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    structured: bool = True,
    console: bool = True
) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: The logging level to use
        log_file: Optional path to a log file
        max_size: Maximum size of log file before rotation (in bytes)
        backup_count: Number of backup files to keep
        structured: Whether to use structured JSON logging
        console: Whether to enable console logging
    """
    # Register custom logger class
    logging.setLoggerClass(StructuredLogger)
    
    # Convert string log level to integer if needed
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper())
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_formatter = (
        StructuredFormatter() if structured
        else logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    )
    
    # Set up handlers
    handlers = []
    
    # Add console handler if requested
    if console:
        console_handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=True,
            show_level=True,
            show_path=False
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(log_level)
        handlers.append(console_handler)
    
    # Add file handler if log file specified
    if log_file:
        # Convert to Path object if string
        if isinstance(log_file, str):
            log_file = Path(log_file)
        
        # Create log directory if needed
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(message)s',
        datefmt='[%X]',
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Create logger for the application
    logger = logging.getLogger("easy_docker_deploy")
    logger.setLevel(log_level)
    
    # Log initial setup
    logger.debug(
        "Logging configured",
        **log_with_context(
            level=logging.getLevelName(log_level),
            log_file=str(log_file) if log_file else None,
            structured=structured
        )
    )

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.
    
    Args:
        name: The name of the logger (usually __name__)
    
    Returns:
        A configured logger instance
    """
    return logging.getLogger(f"easy_docker_deploy.{name}")

def log_with_context(**context: Any) -> Dict[str, Any]:
    """
    Create a context dictionary for structured logging.
    
    Usage:
        logger.info("Message", **log_with_context(user="john", action="login"))
    
    Args:
        **context: Keyword arguments to include in the log context
        
    Returns:
        Dictionary suitable for use as logging extra fields
    """
    return {'extra': {'extra_fields': context}} 