# """
# Wind Data Insight Pro - Technical Developer Documentation
# ========================================================

# This module provides comprehensive technical documentation for developers
# working on the Wind Data Insight Pro application.

# Author: Development Team
# Version: 1.0.0
# License: MIT
# """

# from typing import Dict, List, Any, Optional, Tuple
# from dataclasses import dataclass
# from enum import Enum
# import os
# import sys
# from pathlib import Path

# # =============================================================================
# # ARCHITECTURE OVERVIEW
# # =============================================================================

# class ArchitecturePattern(Enum):
#     """Application follows MVC pattern with service-oriented backend"""
#     MVC = "Model-View-Controller"
#     SERVICE_ORIENTED = "Service-Oriented Architecture"
#     DESKTOP_APPLICATION = "PyQt5 Desktop Application"

# @dataclass
# class TechnologyStack:
#     """Complete technology stack used in the application"""
    
#     # Frontend Technologies
#     gui_framework: str = "PyQt5"
#     charting: List[str] = None
#     visualization: List[str] = None
    
#     # Data Processing
#     data_manipulation: List[str] = None
#     scientific_computing: List[str] = None
#     machine_learning: List[str] = None
    
#     # Backend (Optional)
#     web_framework: str = "FastAPI"
#     server: str = "Uvicorn"
#     http_client: str = "HTTPx"
    
#     # Development Tools
#     build_tool: str = "PyInstaller"
#     code_formatter: str = "Black"
#     linter: str = "Pylint"
#     testing: str = "Pytest"
    
#     def __post_init__(self):
#         if self.charting is None:
#             self.charting = ["PyQtChart", "PyQtGraph", "Matplotlib", "Seaborn", "Windrose"]
#         if self.visualization is None:
#             self.visualization = ["Matplotlib", "Seaborn", "PyQtGraph"]
#         if self.data_manipulation is None:
#             self.data_manipulation = ["Pandas", "NumPy"]
#         if self.scientific_computing is None:
#             self.scientific_computing = ["SciPy", "NumPy"]
#         if self.machine_learning is None:
#             self.machine_learning = ["Scikit-learn"]

# # =============================================================================
# # PROJECT STRUCTURE
# # =============================================================================

# class ProjectStructure:
#     """Defines the complete project directory structure"""
    
#     ROOT_FILES = [
#         "WWIP_APP.py",           # Main application entry point
#         "main_app.py",           # Alternative entry point
#         "build.py",              # Build automation script
#         "requirements.txt",      # Python dependencies
#         "LICENSE",               # License file
#         "README.md"              # Project documentation
#     ]
    
#     DIRECTORIES = {
#         "config/": {
#             "description": "Configuration management",
#             "files": ["config.json", "config.yaml", "config.py"],
#             "purpose": "Centralized configuration handling"
#         },
#         "controllers/": {
#             "description": "Business logic layer",
#             "subdirs": ["data_controller/"],
#             "files": [
#                 "file_menu_controller.py",  # Project management
#                 "analysis.py",              # Analysis operations
#                 "visualization.py",         # Visualization logic
#                 "data_processing.py",       # Data processing
#                 "file_handler.py"           # File operations
#             ],
#             "purpose": "MVC Controller layer - business logic and event handling"
#         },
#         "models/": {
#             "description": "Data models and schemas",
#             "files": [
#                 "base_classes.py",          # Base window classes
#                 "user_model.py",            # User data models
#                 "scada_utils.py",           # SCADA data utilities
#                 "user_schema_model.py"      # User schema definitions
#             ],
#             "purpose": "Data models, validation, and business entities"
#         },
#         "views/": {
#             "description": "User interface components",
#             "subdirs": [
#                 "components/",              # Reusable UI components
#                 "dialogs/",                 # Modal dialogs
#                 "visualization_components/", # Chart and graph components
#                 "ranking/",                 # Ranking interface
#                 "start/",                   # Start screen
#                 "time_series/"              # Time series components
#             ],
#             "purpose": "MVC View layer - user interface and presentation"
#         },
#         "services/": {
#             "description": "Service layer",
#             "subdirs": ["api/", "services/"],
#             "files": ["api_client.py", "auth_manager.py"],
#             "purpose": "External service integration and API communication"
#         },
#         "utils/": {
#             "description": "Utility functions",
#             "files": [
#                 "logger.py",                # Logging utilities
#                 "error_handler.py",         # Error handling
#                 "cache_manager.py",         # Caching utilities
#                 "datetime_utils.py",        # Date/time utilities
#                 "csv_handler.py",           # CSV processing
#                 "thread_safety.py"         # Thread safety utilities
#             ],
#             "purpose": "Common utilities and helper functions"
#         },
#         "resources/": {
#             "description": "Static resources",
#             "subdirs": [
#                 "app_icon/",                # Application icons
#                 "images/",                  # UI images
#                 "control_icons/",           # Control panel icons
#                 "direction/",               # Direction indicators
#                 "icons/",                   # General icons
#                 "logos/"                    # Application logos
#             ],
#             "purpose": "Static assets and resources"
#         },
#         "data/": {
#             "description": "Data storage",
#             "files": ["users.json"],
#             "purpose": "Local data storage and user data"
#         }
#     }

# # =============================================================================
# # CORE COMPONENTS
# # =============================================================================

# class ConfigurationManager:
#     """
#     Centralized configuration management system
    
#     Features:
#     - Dual format support (JSON + YAML)
#     - Deep configuration merging
#     - Automatic validation
#     - Directory structure setup
#     - Logging configuration
#     """
    
#     def __init__(self, json_path: str = "config/config.json", 
#                  yaml_path: str = "config/config.yaml"):
#         """Initialize Configuration Manager with both JSON and YAML configurations"""
#         self.json_path = Path(json_path)
#         self.yaml_path = Path(yaml_path)
#         self.config = self._load_default_config()
#         self._setup_logging()
#         self._load_configurations()
#         self._validate_config()
#         self.setup_directories()
    
#     def get(self, key: str, default: Any = None) -> Any:
#         """Get configuration value using dot notation (e.g., 'app.title')"""
#         pass
    
#     def set(self, key: str, value: Any) -> None:
#         """Set configuration value using dot notation"""
#         pass
    
#     def get_resource_path(self, resource_type: str, resource_name: str = None) -> Path:
#         """Get full path for a resource"""
#         pass

# class ProjectController:
#     """
#     Project lifecycle management
    
#     Handles:
#     - Project creation, opening, saving
#     - Project metadata management
#     - Auto-save functionality
#     - Recent projects tracking
#     - Project state signals
#     """
    
#     # Qt Signals for project state changes
#     project_opened = "pyqtSignal(str)"
#     project_saved = "pyqtSignal(str)"
#     project_closed = "pyqtSignal()"
#     project_modified = "pyqtSignal()"
    
#     PROJECT_STRUCTURE = {
#         "metadata": {
#             "name": "str",
#             "created_date": "ISO timestamp",
#             "last_modified": "ISO timestamp",
#             "version": "str",
#             "description": "str",
#             "author": "str",
#             "capacity": "str",
#             "location": "str"
#         },
#         "data": {
#             "datasets": "List[Dict]",
#             "active_dataset": "Dict",
#             "data_sources": "List[str]",
#             "preprocessing_history": "List[Dict]"
#         },
#         "analysis": {
#             "performed_analyses": "List[Dict]",
#             "results": "Dict",
#             "analysis_history": "List[Dict]",
#             "parameters": "Dict"
#         },
#         "visualizations": {
#             "charts": "List[Dict]",
#             "settings": "Dict",
#             "custom_themes": "List[Dict]",
#             "export_history": "List[Dict]"
#         },
#         "settings": {
#             "auto_save": "bool",
#             "save_interval": "int",
#             "default_chart_theme": "str",
#             "data_precision": "int",
#             "units": "str"
#         }
#     }
    
#     def new_project(self) -> None:
#         """Create new project with metadata dialog"""
#         pass
    
#     def open_project(self) -> None:
#         """Open existing project file"""
#         pass
    
#     def save_project(self, save_as: bool = False) -> bool:
#         """Save current project"""
#         pass
    
#     def mark_as_modified(self) -> None:
#         """Mark project as modified"""
#         pass

# class MainApplication:
#     """
#     Main application class (WWIPApp)
    
#     Architecture:
#     - Extends QMainWindow
#     - Implements MVC pattern
#     - Manages application lifecycle
#     - Coordinates all components
#     """
    
#     COMPONENTS = {
#         "MenuBarModule": "Application menu system",
#         "CentralWidget": "Main content area with data table",
#         "ControlPanel": "Right-side control panel (dockable)",
#         "RightSideBar": "Additional controls sidebar",
#         "DataTableModule": "Data display and manipulation",
#         "FileHandler": "File operations and data loading",
#         "ProjectController": "Project management",
#         "ConfigurationManager": "Configuration handling"
#     }
    
#     def __init__(self):
#         """Initialize main application components"""
#         # Configuration setup
#         self.config = "ConfigurationManager()"
#         self.project_controller = "ProjectController(self)"
        
#         # UI Components
#         self.menu_bar_module = "MenuBarModule(self)"
#         self.central_widget = "CentralWidget(self)"
#         self.control_panel = "ControlPanel(self)"
#         self.data_table_module = "DataTableModule()"
        
#         # Services
#         self.data_manager = "DataManager()"
#         self.file_handler = "FileHandler()"
        
#         # Setup
#         self.setup_ui()
#         self.connect_signals()

# # =============================================================================
# # API ARCHITECTURE
# # =============================================================================

# class APIClient:
#     """
#     Asynchronous API client for backend integration
    
#     Features:
#     - JWT authentication
#     - MFA support
#     - User management
#     - Resource management
#     - Request handling
#     """
    
#     ENDPOINTS = {
#         # Authentication
#         "/token": "POST - User login",
#         "/token/mfa-verify": "POST - MFA verification",
#         "/mfa/verify-setup": "POST - MFA setup verification",
#         "/change-password-first-login": "POST - Password change",
        
#         # User Management
#         "/users/": "GET - List users",
#         "/superadmin/users/": "POST - Create user",
#         "/users/{user_id}": "DELETE - Delete user",
#         "/users/{user_id}/role": "PATCH - Update user role",
#         "/users/{user_id}/reset-password": "POST - Reset password",
        
#         # Resource Management
#         "/resources/": "GET - List resources",
#         "/resources/upload": "POST - Upload resource",
#         "/resources/{resource_id}": "DELETE/PATCH - Manage resource",
#         "/resources/{resource_id}/permissions": "GET - Resource permissions",
        
#         # Request Management
#         "/requests/": "GET - List requests",
#         "/requests/{request_id}": "PATCH - Update request status",
#         "/requests/resource-access": "POST - Request resource access"
#     }
    
#     async def login_user(self, username: str, password: str) -> Dict[str, Any]:
#         """Authenticate user with optional MFA"""
#         pass
    
#     async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
#         """Create new user account"""
#         pass
    
#     async def upload_resource(self, file_path: str, resource_name: str, 
#                             resource_type: str, description: str = None) -> Dict[str, Any]:
#         """Upload resource file to backend"""
#         pass

# # =============================================================================
# # DATA MANAGEMENT
# # =============================================================================

# class DataFlow:
#     """
#     Data processing pipeline
    
#     Flow: File Input → Validation → Processing → Storage → Visualization
#     """
    
#     SUPPORTED_FORMATS = {
#         "CSV": {
#             "extensions": [".csv"],
#             "encoding_detection": True,
#             "delimiter_detection": True,
#             "fallback_encodings": ["utf-8", "latin1", "iso-8859-1", "cp1252"]
#         },
#         "Excel": {
#             "extensions": [".xlsx", ".xls"],
#             "sheet_selection": True,
#             "header_detection": True
#         },
#         "Project": {
#             "extensions": [".wdip"],
#             "format": "JSON",
#             "compression": False
#         }
#     }
    
#     PROCESSING_STEPS = [
#         "File validation",
#         "Encoding detection",
#         "Data type inference",
#         "Missing value handling",
#         "Data cleaning",
#         "Validation checks",
#         "Storage in DataManager",
#         "UI update"
#     ]

# class DataManager:
#     """
#     Central data storage and manipulation
    
#     Features:
#     - Pandas DataFrame backend
#     - Data validation
#     - Metadata tracking
#     - Change notifications
#     - Memory optimization
#     """
    
#     def load_data(self, data: "pandas.DataFrame") -> None:
#         """Load data into manager"""
#         pass
    
#     def get_data(self) -> "pandas.DataFrame":
#         """Get current dataset"""
#         pass
    
#     def validate_data(self, data: "pandas.DataFrame") -> bool:
#         """Validate data integrity"""
#         pass

# # =============================================================================
# # BUILD & DEPLOYMENT
# # =============================================================================

# class BuildManager:
#     """
#     Automated build system for creating distributable executables
    
#     Features:
#     - PyInstaller integration
#     - Dependency management
#     - Qt version detection
#     - Resource bundling
#     - Installer creation
#     """
    
#     BUILD_CONFIGURATION = {
#         "app_name": "Wind-Data-Insight-Pro",
#         "main_script": "main_app.py",
#         "build_type": "onefile",
#         "windowed": True,
#         "icon": "resources/app_icon/WWIP.ico",
#         "exclude_modules": [
#             "PyQt6", "PySide2", "PySide6", "tkinter",
#             "matplotlib.tests", "numpy.tests", "scipy.tests"
#         ],
#         "hidden_imports": [
#             "PyQt5", "PyQt5.QtCore", "PyQt5.QtWidgets", "PyQt5.QtGui",
#             "pandas", "numpy", "scipy", "sklearn", "matplotlib",
#             "pandas._libs.parsers", "pandas._libs.tslibs"
#         ]
#     }
    
#     def build(self) -> bool:
#         """Execute complete build process"""
#         steps = [
#             "verify_environment",
#             "detect_qt_version", 
#             "clean_artifacts",
#             "setup_build_environment",
#             "run_pyinstaller",
#             "verify_output",
#             "create_installer"
#         ]
#         return all(getattr(self, step)() for step in steps)
    
#     def verify_environment(self) -> bool:
#         """Verify build environment and dependencies"""
#         pass
    
#     def create_installer(self) -> bool:
#         """Create NSIS installer (Windows)"""
#         pass

# # =============================================================================
# # DEVELOPMENT GUIDELINES
# # =============================================================================

# class CodingStandards:
#     """Development guidelines and best practices"""
    
#     STYLE_GUIDE = {
#         "formatter": "Black (line length: 88)",
#         "linter": "Pylint",
#         "type_hints": "Encouraged for new code",
#         "docstrings": "Google style",
#         "imports": "Standard library → Third party → Local imports"
#     }
    
#     ERROR_HANDLING = {
#         "logging": "Use utils.logger for all logging",
#         "exceptions": "Use utils.error_handler for file operations",
#         "user_feedback": "Always provide user-friendly error messages",
#         "recovery": "Implement graceful degradation where possible"
#     }
    
#     PERFORMANCE = {
#         "memory": "Monitor large dataset handling",
#         "threading": "Use QThread for long operations", 
#         "caching": "Cache expensive computations",
#         "cleanup": "Proper resource cleanup in closeEvent"
#     }

# class TestingStrategy:
#     """Comprehensive testing approach"""
    
#     TEST_STRUCTURE = {
#         "tests/unit/": "Individual function/method tests",
#         "tests/integration/": "Component interaction tests", 
#         "tests/ui/": "User interface behavior tests",
#         "tests/performance/": "Performance and load tests"
#     }
    
#     TEST_CATEGORIES = {
#         "Unit Tests": [
#             "test_config.py - Configuration management",
#             "test_controllers.py - Business logic",
#             "test_models.py - Data models",
#             "test_utils.py - Utility functions"
#         ],
#         "Integration Tests": [
#             "test_file_operations.py - File I/O workflows",
#             "test_data_flow.py - Data processing pipeline",
#             "test_project_lifecycle.py - Project management"
#         ],
#         "UI Tests": [
#             "test_main_window.py - Main application window",
#             "test_dialogs.py - Dialog interactions",
#             "test_visualization.py - Chart and graph components"
#         ]
#     }
    
#     TESTING_COMMANDS = {
#         "run_all": "pytest",
#         "run_specific": "pytest tests/unit/test_config.py",
#         "with_coverage": "pytest --cov=. --cov-report=html",
#         "performance": "pytest tests/performance/ -v"
#     }

# # =============================================================================
# # SECURITY CONSIDERATIONS
# # =============================================================================

# class SecurityGuidelines:
#     """Security best practices and considerations"""
    
#     DATA_PROTECTION = {
#         "sensitive_data": "No hardcoded credentials or API keys",
#         "file_access": "Validate and sanitize all file paths",
#         "user_input": "Sanitize all user inputs",
#         "logging": "Never log sensitive information",
#         "encryption": "Use secure storage for sensitive data"
#     }
    
#     AUTHENTICATION = {
#         "jwt_tokens": "Secure token storage and rotation",
#         "mfa_support": "Two-factor authentication implementation",
#         "password_policies": "Strong password requirements",
#         "session_management": "Automatic timeout and cleanup",
#         "role_based_access": "Proper permission checking"
#     }

# # =============================================================================
# # TROUBLESHOOTING GUIDE
# # =============================================================================

# class TroubleshootingGuide:
#     """Common issues and solutions"""
    
#     COMMON_ISSUES = {
#         "Qt Import Errors": {
#             "symptoms": "ImportError: No module named 'PyQt5'",
#             "solutions": [
#                 "pip install PyQt5",
#                 "Check virtual environment activation",
#                 "Verify Python version compatibility"
#             ]
#         },
#         "Build Failures": {
#             "symptoms": "PyInstaller fails with missing modules",
#             "solutions": [
#                 "Update hidden imports in build.py",
#                 "Check for Qt version conflicts",
#                 "Verify all dependencies installed"
#             ]
#         },
#         "File Access Issues": {
#             "symptoms": "Permission denied errors",
#             "solutions": [
#                 "Check file/directory permissions",
#                 "Run as administrator (Windows)",
#                 "Verify file paths are correct"
#             ]
#         },
#         "Memory Issues": {
#             "symptoms": "Application crashes with large datasets",
#             "solutions": [
#                 "Implement chunked data processing",
#                 "Monitor memory usage",
#                 "Use data type optimization",
#                 "Implement lazy loading"
#             ]
#         }
#     }
    
#     DEBUG_CONFIGURATION = {
#         "enable_debug_logging": "logging.basicConfig(level=logging.DEBUG)",
#         "qt_debug_output": "os.environ['QT_LOGGING_RULES'] = '*=true'",
#         "memory_profiling": "Use memory_profiler package",
#         "performance_profiling": "Use cProfile module"
#     }

# # =============================================================================
# # DEPLOYMENT CHECKLIST
# # =============================================================================

# class DeploymentChecklist:
#     """Pre-deployment verification checklist"""
    
#     PRE_BUILD_CHECKS = [
#         "All tests passing",
#         "Code style compliance (Black, Pylint)",
#         "Documentation updated",
#         "Version numbers updated",
#         "Dependencies verified",
#         "Resource files present",
#         "Configuration files valid"
#     ]
    
#     BUILD_VERIFICATION = [
#         "Executable created successfully",
#         "All resources bundled",
#         "Application starts without errors",
#         "Core functionality working",
#         "File operations functional",
#         "UI responsive and complete"
#     ]
    
#     POST_BUILD_TASKS = [
#         "Installer creation (NSIS)",
#         "Digital signature (if applicable)",
#         "Antivirus scanning",
#         "Documentation packaging",
#         "Release notes preparation"
#     ]

# # =============================================================================
# # EXAMPLE USAGE AND INTEGRATION
# # =============================================================================

# def example_application_startup():
#     """Example of how the application components work together"""
    
#     # 1. Configuration Loading
#     config = ConfigurationManager(
#         json_path="config/config.json",
#         yaml_path="config/config.yaml"
#     )
    
#     # 2. Main Application Initialization
#     app = MainApplication()
#     app.config = config
    
#     # 3. Project Controller Setup
#     project_controller = ProjectController(app)
#     app.project_controller = project_controller
    
#     # 4. UI Component Creation
#     menu_bar = MenuBarModule(app)
#     central_widget = CentralWidget(app)
#     control_panel = ControlPanel(app)
    
#     # 5. Signal Connections
#     project_controller.project_opened.connect(app.on_project_opened)
#     project_controller.project_saved.connect(app.on_project_saved)
    
#     # 6. Application Launch
#     app.show()
#     return app

# def example_data_processing_workflow():
#     """Example of data processing workflow"""
    
#     # 1. File Selection and Validation
#     file_path = "data/wind_data.csv"
#     file_handler = FileHandler()
    
#     # 2. Data Loading with Error Handling
#     try:
#         data = file_handler.load_csv_file(file_path)
#     except Exception as e:
#         handle_file_exception(e)
#         return None
    
#     # 3. Data Validation and Processing
#     data_manager = DataManager()
#     if data_manager.validate_data(data):
#         data_manager.load_data(data)
    
#     # 4. UI Update
#     data_table = DataTableModule()
#     data_table.update_data_table(data)
    
#     # 5. Project State Update
#     project_controller = ProjectController()
#     project_controller.mark_as_modified()
    
#     return data

# # =============================================================================
# # CONFIGURATION TEMPLATES
# # =============================================================================

# DEFAULT_CONFIG_JSON = {
#     "app": {
#         "title": "Wind Data Insight Pro",
#         "version": "1.0.0",
#         "build_date": "2024.01.01",
#         "style": "dark",
#         "language": "en"
#     },
#     "window": {
#         "width": 1200,
#         "height": 800,
#         "state": "maximized",
#         "menubar_visible": True
#     },
#     "data": {
#         "recent_files": [],
#         "max_recent": 10,
#         "auto_save": True,
#         "save_interval": 300,
#         "csv": {
#             "encoding": "utf-8",
#             "delimiter": ",",
#             "decimal": ".",
#             "quoting": 0
#         }
#     },
#     "visualization": {
#         "theme": "wwip_dark",
#         "colors": ["#3498db", "#2ecc71", "#e74c3c", "#f1c40f"],
#         "dpi": 100,
#         "grid": True,
#         "legend": True
#     }
# }

# REQUIREMENTS_TXT = """
# # Core Dependencies
# PyQt5
# PyQtChart
# pandas
# numpy
# scipy
# scikit-learn
# pyqtgraph

# # Data Visualization
# seaborn
# matplotlib
# windrose

# # UI Enhancement
# qdarkstyle

# # Excel Support
# openpyxl
# xlsxwriter

# # Build Tools
# pyinstaller
# wheel
# setuptools

# # Development Tools
# black
# pylint
# pytest
# """

# if __name__ == "__main__":
#     print("Wind Data Insight Pro - Technical Documentation")
#     print("=" * 50)
#     print("This module contains comprehensive technical documentation")
#     print("for developers working on the Wind Data Insight Pro application.")
#     print("\nKey Components:")
#     print("- Architecture Overview")
#     print("- Technology Stack")
#     print("- Core Components")
#     print("- API Architecture") 
#     print("- Data Management")
#     print("- Build & Deployment")
#     print("- Development Guidelines")
#     print("- Security Considerations")
#     print("- Troubleshooting Guide")

import winreg
import os
import sys

def register_wdip_file_type():
    """Register .wdip file type with icon"""
    
    # Get paths
    app_path = os.path.abspath("WWIP_APP.py")
    icon_path = os.path.abspath("resources/app_icon/wdip_file.ico")
    python_exe = sys.executable
    
    try:
        # Create .wdip file association
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.wdip")
        winreg.SetValue(key, "", winreg.REG_SZ, "WindDataInsightPro.Project")
        winreg.CloseKey(key)
        
        # Set file type description
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\WindDataInsightPro.Project")
        winreg.SetValue(key, "", winreg.REG_SZ, "Wind Data Insight Pro Project")
        winreg.CloseKey(key)
        
        # Set icon
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\WindDataInsightPro.Project\DefaultIcon")
        winreg.SetValue(key, "", winreg.REG_SZ, icon_path)
        winreg.CloseKey(key)
        
        # Set open command
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\WindDataInsightPro.Project\shell\open\command")
        winreg.SetValue(key, "", winreg.REG_SZ, f'"{python_exe}" "{app_path}" --project "%1"')
        winreg.CloseKey(key)
        
        print("✅ File type registered successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    register_wdip_file_type()