import json
import yaml
import logging
import logging.config
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import os
import shutil
from dotenv import load_dotenv
import sys

class ConfigurationManager:
    def __init__(self, json_path: Optional[str] = None, yaml_path: Optional[str] = None):
        """Initialize Configuration Manager with both JSON and YAML configurations"""
        # Load environment variables early from .env
        load_dotenv()
        
        # Use env vars if paths are not explicitly provided, fallback to defaults
        default_json = os.getenv("WWIP_JSON_CONFIG", "config/config.json")
        default_yaml = os.getenv("WWIP_YAML_CONFIG", "config/config.yaml")
        
        self.json_path = Path(json_path if json_path else default_json)
        self.yaml_path = Path(yaml_path if yaml_path else default_yaml)
        self.config = self._load_default_config()
        self._setup_logging()  # Set up logging early
        self.logger = logging.getLogger(__name__)
        self._load_configurations()
        self._validate_config()
        self.setup_directories()

    def _setup_logging(self) -> None:
        """Apply logging configuration"""
        try:
            log_config = self.get_logging_config()
            logging.config.dictConfig(log_config)
        except Exception as e:
            print(f"Failed to set up logging: {e}")  # Fallback to print if logging fails

    def _load_json_config(self) -> Dict[str, Any]:
        """Load JSON configuration file"""
        try:
            if self.json_path.exists():
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load JSON config from {self.json_path}: {e}")
        return {}

    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        try:
            if self.yaml_path.exists():
                with open(self.yaml_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.error(f"Failed to load YAML config from {self.yaml_path}: {e}")
        return {}

    def _deep_merge(self, source: Dict[str, Any], destination: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        for key, value in source.items():
            if isinstance(value, dict):
                node = destination.setdefault(key, {})
                if isinstance(node, dict):
                    self._deep_merge(value, node)
                else:
                    destination[key] = value
            else:
                destination[key] = value
        return destination

    def _load_configurations(self) -> None:
        """Load and merge all configurations"""
        yaml_config = self._load_yaml_config()
        if yaml_config:
            self.config = self._deep_merge(yaml_config, self.config)
        json_config = self._load_json_config()
        if json_config:
            self.config = self._deep_merge(json_config, self.config)

    def _validate_config(self) -> None:
        """Validate critical configuration values"""
        try:
            # Validate window dimensions
            if self.get('window.width', 1200) <= 0 or self.get('window.height', 800) <= 0:
                self.logger.warning("Invalid window dimensions, resetting to defaults")
                self.set('window.width', 1200)
                self.set('window.height', 800)

            # Validate resource paths
            for res_type in self.get('resources', {}):
                directory = self.get(f'resources.{res_type}.directory')
                if directory and not Path(directory).is_absolute() and not Path(directory).exists():
                    self.logger.warning(f"Resource directory {directory} does not exist")

            # Validate CSV config
            csv_config = self.get('data.csv', {})
            if 'quoting' in csv_config and csv_config['quoting'] not in [0, 1, 2, 3]:  # csv.QUOTE_* constants
                self.logger.warning("Invalid CSV quoting value, resetting to QUOTE_MINIMAL")
                self.set('data.csv.quoting', 0)  # csv.QUOTE_MINIMAL
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")

    def setup_directories(self) -> None:
        """Setup required application directories"""
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent
            
        directories = {
            'config': self.json_path.parent,
            'logs': base_dir / os.getenv('WWIP_LOG_DIR', 'logs'),
            'data': base_dir / os.getenv('WWIP_DATA_DIR', 'data_imported'),
            'exports': base_dir / os.getenv('WWIP_EXPORTS_DIR', 'exports'),
            'resources': {
                'app_icon': base_dir / self.get('resources.app_icon.directory', 'resources/app_icon'),
                'images': base_dir / self.get('resources.images.directory', 'resources/images'),
                'control_icons': base_dir / self.get('resources.control_icons.directory', 'resources/control_icons'),
                'icons': base_dir / self.get('resources.icons.directory', 'resources/icons'),
                'logos': base_dir / self.get('resources.logos.directory', 'resources/logos')
            }
        }
        
        for name, path in directories.items():
            try:
                if isinstance(path, dict):
                    for subname, subpath in path.items():
                        if not subpath.exists():
                            subpath.mkdir(parents=True, exist_ok=True)
                            self.logger.info(f"Created directory: {subpath}")
                else:
                    if not path.exists():
                        path.mkdir(parents=True, exist_ok=True)
                        self.logger.info(f"Created directory: {path}")
            except PermissionError:
                self.logger.error(f"Permission denied creating directory {path}")
            except Exception as e:
                self.logger.error(f"Failed to create directory {path}: {e}")

    def _load_default_config(self) -> Dict[str, Any]:
        """Define default configuration values"""
        return {
            'app': {
                'title': os.getenv('WWIP_APP_TITLE', 'Wind Wise Insights Pro'),
                'version': os.getenv('WWIP_APP_VERSION', '1.0.0'),
                'build_date': datetime.now().strftime('%Y.%m.%d'),
                'style': os.getenv('WWIP_APP_STYLE', 'dark'),
                'language': os.getenv('WWIP_LANGUAGE', 'en'),
                'splash_screen': {
                    'show': os.getenv('WWIP_SHOW_SPLASH', 'True').lower() == 'true',
                    'duration': int(os.getenv('WWIP_SPLASH_DURATION', '2000'))
                }
            },
            'database': {
                'path': os.getenv('DB_PATH', 'data/wind_insight.db'),
                'timeout': int(os.getenv('DB_TIMEOUT', '30'))
            },
            'window': {
                'width': int(os.getenv('WWIP_WINDOW_WIDTH', '1200')),
                'height': int(os.getenv('WWIP_WINDOW_HEIGHT', '800')),
                'state': 'maximized',
                'menubar_visible': True
            },
            'resources': {
                'app_icon': {
                    'directory': 'resources/app_icon',
                    'app_icon': 'WWIP.ico'
                },
                'images': {
                    'directory': 'resources/images',
                    'splash': 'splash.png'
                },
                'control_icons': {
                    'directory': 'resources/control_icons'
                },
                'icons': {
                    'directory': 'resources/icons'
                },
                'logos': {
                    'directory': 'resources/logos'
                }
            },
            'data': {
                'recent_files': [],
                'max_recent': 10,
                'auto_save': True,
                'save_interval': 300,
                'date_format': '%d/%m/%Y %H:%M',
                'csv': {
                    'encoding': 'utf-8',
                    'fallback_encodings': ['latin1', 'iso-8859-1', 'cp1252'],
                    'delimiter': ',',
                    'decimal': '.',
                    'thousands': ',',
                    'quoting': 0,  # csv.QUOTE_MINIMAL
                    'strict_validation': True,
                    'sample_size': 10
                }
            },
            'analysis': {
                'default_metrics': [
                    'power',
                    'wind_speed',
                    'direction'
                ],
                'time_window': '10min',
                'outlier_threshold': 3,
                'missing_data_strategy': 'interpolate'
            },
            'visualization': {
                'theme': 'wwip_dark',
                'colors': [
                    '#3498db',
                    '#2ecc71',
                    '#e74c3c',
                    '#f1c40f'
                ],
                'dpi': 100,
                'grid': True,
                'legend': True,
                'default_plot_type': 'Scatter',
                'default_marker': 'Circle',
                'default_size': 8.0
            },
            'export': {
                'default_format': 'xlsx',
                'chart_format': 'png',
                'report_template': 'default'
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key with dot notation."""
        try:
            value = self.config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            self.logger.warning(f"Configuration key '{key}' not found, returning default: {default}")
            return default

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value by key with dot notation."""
        try:
            keys = key.split('.')
            target = self.config
            for k in keys[:-1]:
                target = target.setdefault(k, {})
            target[keys[-1]] = value
            self._save_configurations()
        except Exception as e:
            self.logger.error(f"Failed to set configuration key '{key}': {e}")

    def _save_configurations(self) -> None:
        """Save current configuration to both JSON and YAML files with backup."""
        try:
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
            self.yaml_path.parent.mkdir(parents=True, exist_ok=True)

            # Backup existing files
            for path in [self.json_path, self.yaml_path]:
                if path.exists():
                    backup_path = path.with_suffix(path.suffix + '.backup')
                    shutil.copy(path, backup_path)
                    self.logger.info(f"Created backup: {backup_path}")

            # Save to JSON
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            self.logger.info(f"Saved configuration to {self.json_path}")

            # Save to YAML
            with open(self.yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            self.logger.info(f"Saved configuration to {self.yaml_path}")
        except Exception as e:
            self.logger.error(f"Failed to save configurations: {e}")

    def get_resource_path(self, resource_type: str, resource_name: Optional[str] = None) -> Path:
        """Get the full path for a resource."""
        try:
            base_path = Path(self.get(f'resources.{resource_type}.directory'))
            if not base_path.exists():
                self.logger.warning(f"Resource directory {base_path} does not exist")
            return base_path / resource_name if resource_name else base_path
        except (KeyError, TypeError):
            self.logger.error(f"Resource type '{resource_type}' not found in configuration")
            return Path('resources') / resource_type / (resource_name or '')

    def get_csv_config(self) -> Dict[str, Any]:
        """Get CSV-specific configuration."""
        csv_config = self.get('data.csv', {})
        # Ensure all required CSV parameters are present
        defaults = self._load_default_config()['data']['csv']
        return {**defaults, **csv_config}

    def get_window_config(self) -> Dict[str, Any]:
        """Get window-specific configuration."""
        return self.get('window', {})

    def get_visualization_config(self) -> Dict[str, Any]:
        """Get visualization-specific configuration."""
        return self.get('visualization', {})

    def update_recent_files(self, file_path: str) -> None:
        """Update the list of recent files."""
        try:
            file_path = str(Path(file_path).resolve())  # Normalize path
            if not Path(file_path).exists():
                self.logger.warning(f"File {file_path} does not exist, not adding to recent files")
                return
            recent_files = self.get('data.recent_files', [])
            max_recent = self.get('data.max_recent', 10)
            
            if file_path in recent_files:
                recent_files.remove(file_path)
            
            recent_files.insert(0, file_path)
            recent_files = recent_files[:max_recent]
            
            self.set('data.recent_files', recent_files)
        except Exception as e:
            self.logger.error(f"Failed to update recent files with {file_path}: {e}")

    def save_config(self) -> None:
        """Save current configuration to file"""
        self._save_configurations()

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent
            
        log_dir = base_dir / os.getenv('WWIP_LOG_DIR', 'logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handlers = {
            "file_handler": {
                "class": "logging.FileHandler",
                "filename": str(log_dir / "app.log"),
                "mode": "a",
                "formatter": "detailed",
                "encoding": "utf-8"
            }
        }
        
        active_handlers = ["file_handler"]
        
        # Only add StreamHandler if sys.stdout exists (prevents crash in PyInstaller --windowed)
        if sys.stdout is not None:
            handlers["console_handler"] = {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "detailed"
            }
            active_handlers.append("console_handler")
            
        return {
            "version": 1,
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s - [%(levelname)s] - %(name)s:%(lineno)d - %(message)s"
                }
            },
            "handlers": handlers,
            "loggers": {
                "": {
                    "handlers": active_handlers,
                    "level": "DEBUG", # Set to DEBUG to capture detailed module flow
                    "propagate": False
                }
            }
        }