from enum import Enum
from typing import Optional, Dict, Any, Callable
import traceback
import threading
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox
from utils.logger import logger

class ErrorType(Enum):
    """Error type enumeration"""
    GENERIC = "generic"
    DATA = "data"
    FILE = "file"
    NETWORK = "network"
    DATABASE = "database"
    VISUALIZATION = "visualization"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class UnifiedErrorManager:
    """Centralized error management system"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.error_history = []
            self.error_handlers = {}
            self._setup_default_handlers()
            self._initialized = True
    
    def _setup_default_handlers(self):
        """Setup default error handlers for each error type"""
        self.error_handlers = {
            ErrorType.GENERIC: self._handle_generic_error,
            ErrorType.DATA: self._handle_data_error,
            ErrorType.FILE: self._handle_file_error,
            ErrorType.NETWORK: self._handle_network_error,
            ErrorType.DATABASE: self._handle_database_error,
            ErrorType.VISUALIZATION: self._handle_visualization_error,
            ErrorType.AUTHENTICATION: self._handle_auth_error,
            ErrorType.VALIDATION: self._handle_validation_error,
        }
    
    def handle_error(self, 
                    exception: Exception, 
                    error_type: ErrorType = ErrorType.GENERIC,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    context: Optional[Dict[str, Any]] = None,
                    show_dialog: bool = True,
                    custom_message: Optional[str] = None) -> None:
        """
        Unified error handling method
        
        Args:
            exception: The exception that occurred
            error_type: Type of error
            severity: Severity level
            context: Additional context information
            show_dialog: Whether to show error dialog to user
            custom_message: Custom user-friendly message
        """
        error_info = {
            'timestamp': datetime.now(),
            'type': error_type.value,
            'severity': severity.value,
            'exception': str(exception),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        # Log the error
        self._log_error(error_info)
        
        # Store in history
        self.error_history.append(error_info)
        
        # Handle based on type
        handler = self.error_handlers.get(error_type, self._handle_generic_error)
        handler(exception, severity, context, show_dialog, custom_message)
    
    def _log_error(self, error_info: Dict[str, Any]) -> None:
        """Log error with appropriate level"""
        severity = error_info['severity']
        message = f"[{error_info['type'].upper()}] {error_info['exception']}"
        
        if severity == ErrorSeverity.CRITICAL.value:
            logger.critical(message, exc_info=True)
        elif severity == ErrorSeverity.HIGH.value:
            logger.error(message, exc_info=True)
        elif severity == ErrorSeverity.MEDIUM.value:
            logger.warning(message)
        else:
            logger.info(message)
    
    def _show_error_dialog(self, title: str, message: str, severity: ErrorSeverity) -> None:
        """Show error dialog to user"""
        try:
            icon = QMessageBox.Critical if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else QMessageBox.Warning
            QMessageBox(icon, title, message).exec_()
        except Exception as e:
            logger.error(f"Failed to show error dialog: {e}")
    
    def _handle_generic_error(self, exception, severity, context, show_dialog, custom_message):
        """Handle generic errors"""
        message = custom_message or f"An error occurred: {str(exception)}"
        if show_dialog:
            self._show_error_dialog("Error", message, severity)
    
    def _handle_data_error(self, exception, severity, context, show_dialog, custom_message):
        """Handle data processing errors"""
        message = custom_message or f"Data processing error: {str(exception)}"
        if show_dialog:
            self._show_error_dialog("Data Error", message, severity)
    
    def _handle_file_error(self, exception, severity, context, show_dialog, custom_message):
        """Handle file operation errors"""
        message = custom_message or f"File operation error: {str(exception)}"
        if show_dialog:
            self._show_error_dialog("File Error", message, severity)
    
    def _handle_network_error(self, exception, severity, context, show_dialog, custom_message):
        """Handle network errors"""
        message = custom_message or "Network connection error occurred"
        if show_dialog:
            self._show_error_dialog("Network Error", message, severity)
    
    def _handle_database_error(self, exception, severity, context, show_dialog, custom_message):
        """Handle database errors"""
        message = custom_message or "Database operation error occurred"
        if show_dialog:
            self._show_error_dialog("Database Error", message, severity)
    
    def _handle_visualization_error(self, exception, severity, context, show_dialog, custom_message):
        """Handle visualization errors"""
        message = custom_message or f"Visualization error: {str(exception)}"
        if show_dialog:
            self._show_error_dialog("Visualization Error", message, severity)
    
    def _handle_auth_error(self, exception, severity, context, show_dialog, custom_message):
        """Handle authentication errors"""
        message = custom_message or "Authentication error occurred"
        if show_dialog:
            self._show_error_dialog("Authentication Error", message, severity)
    
    def _handle_validation_error(self, exception, severity, context, show_dialog, custom_message):
        """Handle validation errors"""
        message = custom_message or f"Validation error: {str(exception)}"
        if show_dialog:
            self._show_error_dialog("Validation Error", message, severity)
    
    def register_custom_handler(self, error_type: ErrorType, handler: Callable) -> None:
        """Register custom error handler"""
        self.error_handlers[error_type] = handler
    
    def get_error_history(self) -> list:
        """Get error history"""
        return self.error_history.copy()
    
    def clear_error_history(self) -> None:
        """Clear error history"""
        self.error_history.clear()

# Global instance
error_manager = UnifiedErrorManager()

# Convenience functions for backward compatibility
def handle_exception(exception, message="An error occurred"):
    error_manager.handle_error(exception, ErrorType.GENERIC, ErrorSeverity.MEDIUM, custom_message=message)

def handle_data_exception(exception):
    error_manager.handle_error(exception, ErrorType.DATA, ErrorSeverity.MEDIUM)

def handle_file_exception(exception):
    error_manager.handle_error(exception, ErrorType.FILE, ErrorSeverity.MEDIUM)

def handle_network_exception(exception):
    error_manager.handle_error(exception, ErrorType.NETWORK, ErrorSeverity.HIGH)

def handle_database_exception(exception):
    error_manager.handle_error(exception, ErrorType.DATABASE, ErrorSeverity.HIGH)

def handle_visualization_exception(exception):
    error_manager.handle_error(exception, ErrorType.VISUALIZATION, ErrorSeverity.MEDIUM)

def show_error_message(title, message):
    logger.error(f"{title}: {message}")
    QMessageBox.critical(None, title, message)

# Exception decorator
def log_exceptions(func):
    """Decorator to automatically handle exceptions"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_manager.handle_error(e, ErrorType.GENERIC, ErrorSeverity.MEDIUM, 
                                     context={'function': func.__name__})
            raise
    return wrapper

def handle_error_simple(exception, message=None, show_dialog=True):
    """
    Simplified error handling for common cases
    
    Args:
        exception: The exception that occurred
        message: Custom user-friendly message
        show_dialog: Whether to show dialog to user
    """
    error_manager.handle_error(
        exception, 
        ErrorType.GENERIC, 
        ErrorSeverity.MEDIUM,
        custom_message=message,
        show_dialog=show_dialog
    )


def setup_thread_exception_hook():
    """Set up exception hook for threads"""
    def thread_exception_hook(args):
        error_manager.handle_error(args.exc_value, ErrorType.GENERIC, ErrorSeverity.HIGH,
                                 context={'thread': True}, show_dialog=False)
    
    threading.excepthook = thread_exception_hook
