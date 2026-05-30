import logging
import sys
import os
from datetime import datetime
from enum import Enum
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Dict, Any, Optional, Union
from functools import wraps
import traceback

class LogLevel(Enum):
    """Logging levels enumeration"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class LogConfig:
    """Logger configuration constants"""
    DEFAULT_NAME = "WindWiseInsightPro"
    DEFAULT_LEVEL = LogLevel.INFO.value
    DEFAULT_FORMAT = "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"
    FILE_SIZE_LIMIT = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5
    LOG_DIR = Path("logs")
    LOG_DIR.mkdir(exist_ok=True)

class CustomLogger:
    """Enhanced logger implementation with singleton pattern"""
    _instance: Optional[logging.Logger] = None
    _config: Dict[str, Any] = {}
    
    @classmethod
    def get_logger(cls, config: Dict[str, Any] = None) -> logging.Logger:
        """Get or create logger instance"""
        if cls._instance is None:
            cls._config = config or {}
            cls._instance = cls._setup_logger()
        return cls._instance
    
    @classmethod
    def _setup_logger(cls) -> logging.Logger:
        """Setup enhanced logger with configuration"""
        name = cls._config.get("name", LogConfig.DEFAULT_NAME)
        log_level = cls._config.get("log_level", LogConfig.DEFAULT_LEVEL)
        log_format = cls._config.get("format", LogConfig.DEFAULT_FORMAT)
        
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        logger.handlers.clear()
        
        formatter = logging.Formatter(log_format)
        
        handlers = [
            cls._create_file_handler(formatter, log_level),
            cls._create_console_handler(formatter, log_level),
            cls._create_timed_handler(formatter, log_level)
        ]
        
        for handler in handlers:
            logger.addHandler(handler)
        
        return logger
    
    @staticmethod
    def _create_file_handler(formatter: logging.Formatter, level: int) -> RotatingFileHandler:
        """Create size-based rotating file handler"""
        log_file = LogConfig.LOG_DIR / f"app_{datetime.now():%Y%m%d}.log"
        handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=LogConfig.FILE_SIZE_LIMIT,
            backupCount=LogConfig.BACKUP_COUNT,
            encoding='utf-8'
        )
        handler.setFormatter(formatter)
        handler.setLevel(level)
        return handler
    
    @staticmethod
    def _create_timed_handler(formatter: logging.Formatter, level: int) -> TimedRotatingFileHandler:
        """Create time-based rotating file handler"""
        log_file = LogConfig.LOG_DIR / "app_timed.log"
        handler = TimedRotatingFileHandler(
            filename=str(log_file),
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        handler.setFormatter(formatter)
        handler.setLevel(level)
        return handler
    
    @staticmethod
    def _create_console_handler(formatter: logging.Formatter, level: int) -> logging.StreamHandler:
        """Create console handler"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        handler.setLevel(level)
        return handler

class LoggerWrapper:
    """Wrapper for convenient logging with context"""
    def __init__(self):
        self._logger = CustomLogger.get_logger()
    
    def _add_context(self, message: str) -> str:
        """Add context information to log messages"""
        frame = sys._getframe(2)
        filename = os.path.basename(frame.f_code.co_filename)
        lineno = frame.f_lineno
        return f"{filename}:{lineno} - {message}"
    
    def debug(self, message: str, *args, **kwargs) -> None:
        self._logger.debug(self._add_context(message), *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs) -> None:
        self._logger.info(self._add_context(message), *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs) -> None:
        self._logger.warning(self._add_context(message), *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs) -> None:
        self._logger.error(self._add_context(message), *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs) -> None:
        self._logger.critical(self._add_context(message), *args, **kwargs)
    
    def exception(self, message: str, *args, exc_info: bool = True, **kwargs) -> None:
        self._logger.exception(self._add_context(message), *args, exc_info=exc_info, **kwargs)

def log_exceptions(func):
    """Decorator to automatically log exceptions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Exception in {func.__name__}: {str(e)}", exc_info=True)
            raise
    return wrapper

# Initialize with default configuration
DEFAULT_CONFIG = {
    "name": LogConfig.DEFAULT_NAME,
    "log_level": LogConfig.DEFAULT_LEVEL,
    "format": LogConfig.DEFAULT_FORMAT
}

# Create global instances
logger = CustomLogger.get_logger(DEFAULT_CONFIG)
log = LoggerWrapper()

# Export common logging functions
def log_info(message: str, *args: Any) -> None:
    """Log an info level message"""
    logger.info(message, *args)

def log_error(message: str, *args: Any, exc_info: bool = True) -> None:
    """Log an error level message with exception info"""
    logger.error(message, *args, exc_info=exc_info)

def log_warning(message: str, *args: Any) -> None:
    """Log a warning level message"""
    logger.warning(message, *args)

def log_debug(message: str, *args: Any) -> None:
    """Log a debug level message"""
    logger.debug(message, *args)

def setup_logger(config: Dict[str, Any] = None) -> logging.Logger:
    """Initialize and configure the application logger
    
    Args:
        config (Dict[str, Any], optional): Logger configuration. Defaults to None.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    return CustomLogger.get_logger(config or DEFAULT_CONFIG)

# Export all necessary symbols
__all__ = [
    'logger',
    'log',
    'LogLevel',
    'CustomLogger',
    'LoggerWrapper',
    'log_exceptions',
    'log_info',
    'log_error',
    'log_warning',
    'log_debug',
    'setup_logger'
]