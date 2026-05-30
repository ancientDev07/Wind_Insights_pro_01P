from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, List, Type
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QSettings
import logging
import json
from pathlib import Path

class Theme(Enum):
    SYSTEM = "System"
    LIGHT = "Light"
    DARK = "Dark"

# class FileFormat(Enum):
#     CSV = "CSV"
#     EXCEL = "Excel"

class WindSpeedUnit(Enum):
    METERS_PER_SECOND = "m/s"
    KILOMETERS_PER_HOUR = "km/h"
    MILES_PER_HOUR = "mph"
    KNOTS = "knots"

class DirectionFormat(Enum):
    DEGREES = "Degrees"
    CARDINALS = "Cardinals"
    BOTH = "Both"

# class WindShearMethod(Enum):
#     POWER_LAW = "Power Law"
#     LOG_LAW = "Log Law"
#     BOTH = "Both"

class SettingKey(str, Enum):
    """Centralized keys for all application settings."""
    THEME = "theme"
    DEFAULT_FILE_FORMAT = "default_file_format"
    WIND_SPEED_UNIT = "wind_speed_unit"
    DIRECTION_FORMAT = "direction_format"
    HEIGHT_LEVELS = "height_levels"
    DECIMAL_PRECISION = "decimal_precision"
    TURBULENCE_INTENSITY = "turbulence_intensity"
    EXPORT_DPI = "export_dpi"
    COLOR_SCHEME = "color_scheme"
    SHEAR_CALCULATION = "shear_calculation"

@dataclass
class SettingsDefaults:
    """Default values for all settings"""
    THEME: str = Theme.SYSTEM.value
    # FILE_FORMAT: str = FileFormat.CSV.value
    WIND_SPEED_UNIT: str = WindSpeedUnit.METERS_PER_SECOND.value
    DIRECTION_FORMAT: str = DirectionFormat.DEGREES.value
    # HEIGHT_LEVELS: str = "10,20,30,40,50,60,80,100"
    DECIMAL_PRECISION: int = 2
    # WINDROSE_SECTORS: int = 16
    DATA_VALIDATION: bool = True
    # TURBULENCE_INTENSITY: bool = True
    EXPORT_DPI: int = 300
    # DEFAULT_PLOT: str = "Wind Rose"
    # COLOR_SCHEME: str = "Blues"
    # MAP_PROJECTION: str = "Mercator"
    # SHEAR_CALCULATION: str = WindShearMethod.POWER_LAW.value

class SettingsManager:
    """Manages application settings persistence and validation"""
    
    def __init__(self, organization: str, application: str):
        self.settings = QSettings(organization, application)
        self.defaults = SettingsDefaults()
        self.logger = logging.getLogger(__name__)
        self._key_to_type_map = {
            SettingKey.THEME: str,
            SettingKey.DEFAULT_FILE_FORMAT: str,
            SettingKey.WIND_SPEED_UNIT: str,
            SettingKey.DIRECTION_FORMAT: str,
            SettingKey.HEIGHT_LEVELS: str,
            SettingKey.DECIMAL_PRECISION: int,
            SettingKey.TURBULENCE_INTENSITY: bool,
            SettingKey.EXPORT_DPI: int,
            SettingKey.COLOR_SCHEME: str,
            SettingKey.SHEAR_CALCULATION: str,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value with type safety and fallback to default."""
        default_value = default or getattr(self.defaults, key.upper(), None)
        setting_type: Type = self._key_to_type_map.get(key, type(default_value) if default_value is not None else str)
        
        return self.settings.value(key, default_value, type=setting_type)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value with validation"""
        try:
            self.settings.setValue(key, value)
            self.settings.sync()
        except Exception as e:
            self.logger.error(f"Failed to save setting {key}: {str(e)}")
            raise

    def reset_all(self) -> None:
        """Reset all settings to defaults"""
        self.settings.clear()
        self.settings.sync()

class SettingsDialog(QDialog):
    """
    Advanced settings dialog for wind application configuration.
    
    Signals:
        settings_changed: Emitted when settings are successfully saved.
    """
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.settings_manager = SettingsManager('WindWiseInsights', 'WWIP')
        self.widgets: Dict[str, Any] = {}

        self._init_ui()
        self._load_settings()

    def _init_ui(self) -> None:
        """Initialize the user interface"""
        self.setWindowTitle("WindWise Insights - Settings")
        self.setGeometry(300, 300, 600, 700)

        layout = QVBoxLayout(self)
        
        # Add settings groups
        layout.addWidget(self._create_general_settings())
        layout.addWidget(self._create_wind_data_settings())
        layout.addWidget(self._create_analysis_settings())
        layout.addWidget(self._create_visualization_settings())

        # Add dialog buttons
        self._add_dialog_buttons(layout)
        
        self.setLayout(layout)

    def _create_general_settings(self) -> QGroupBox:
        """Create general settings group"""
        group = QGroupBox("General Settings")
        layout = QFormLayout()

        # Theme selection
        theme_combo = QComboBox()
        theme_combo.addItems([theme.value for theme in Theme])
        self.widgets[SettingKey.THEME] = theme_combo
        layout.addRow("Theme:", theme_combo)

        # # File format
        # file_format = QComboBox()
        # file_format.addItems([fmt.value for fmt in FileFormat])
        # self.widgets[SettingKey.DEFAULT_FILE_FORMAT] = file_format
        # layout.addRow("Default File Format:", file_format)

        group.setLayout(layout)
        return group

    def _create_wind_data_settings(self) -> QGroupBox:
        """Create wind data settings group"""
        group = QGroupBox("Wind Data Settings")
        layout = QFormLayout()

        # Wind speed unit
        speed_unit = QComboBox()
        speed_unit.addItems([unit.value for unit in WindSpeedUnit])
        self.widgets[SettingKey.WIND_SPEED_UNIT] = speed_unit
        layout.addRow("Wind Speed Unit:", speed_unit)

        # Direction format
        direction_format = QComboBox()
        direction_format.addItems([fmt.value for fmt in DirectionFormat])
        self.widgets[SettingKey.DIRECTION_FORMAT] = direction_format
        layout.addRow("Direction Format:", direction_format)

        # # Height levels
        # height_levels = QLineEdit()
        # height_levels.setPlaceholderText(self.settings_manager.defaults.HEIGHT_LEVELS)
        # self.widgets[SettingKey.HEIGHT_LEVELS] = height_levels
        # layout.addRow("Measurement Heights (m):", height_levels)

        group.setLayout(layout)
        return group

    def _create_analysis_settings(self) -> QGroupBox:
        """Create analysis settings group"""
        group = QGroupBox("Analysis Settings")
        layout = QFormLayout()

        # Decimal precision
        precision = QSpinBox()
        precision.setRange(0, 6)
        self.widgets[SettingKey.DECIMAL_PRECISION] = precision
        layout.addRow("Decimal Precision:", precision)

        # # Wind shear calculation method
        # shear_method = QComboBox()
        # shear_method.addItems([method.value for method in WindShearMethod])
        # self.widgets[SettingKey.SHEAR_CALCULATION] = shear_method
        # layout.addRow("Wind Shear Method:", shear_method)

        # Turbulence intensity calculation
        # ti_calc = QCheckBox()
        # self.widgets[SettingKey.TURBULENCE_INTENSITY] = ti_calc
        # layout.addRow("Calculate Turbulence Intensity:", ti_calc)

        group.setLayout(layout)
        return group

    def _create_visualization_settings(self) -> QGroupBox:
        """Create visualization settings group"""
        group = QGroupBox("Visualization Settings")
        layout = QFormLayout()

        # Export resolution
        export_dpi = QSpinBox()
        export_dpi.setRange(72, 600)
        export_dpi.setSingleStep(72)
        export_dpi.setValue(self.settings_manager.defaults.EXPORT_DPI)
        self.widgets[SettingKey.EXPORT_DPI] = export_dpi
        layout.addRow("Export Resolution (DPI):", export_dpi)

        # Color scheme
        color_scheme = QComboBox()
        color_scheme.addItems(['Blues', 'Spectral', 'YlOrRd', 'Custom'])
        self.widgets[SettingKey.COLOR_SCHEME] = color_scheme
        layout.addRow("Color Scheme:", color_scheme)

        group.setLayout(layout)
        return group

    def _add_dialog_buttons(self, layout: QVBoxLayout) -> None:
        """Add dialog buttons to the layout"""
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | 
            QDialogButtonBox.Apply | QDialogButtonBox.Reset,
            Qt.Horizontal
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self._apply_settings)
        buttons.button(QDialogButtonBox.Reset).clicked.connect(self._reset_to_defaults)
        layout.addWidget(buttons)

    def _load_settings(self) -> None:
        """Load saved settings from SettingsManager"""
        try:
            for key, widget in self.widgets.items():
                value = self.settings_manager.get(key)
                if isinstance(widget, QComboBox):
                    index = widget.findText(value)
                    if index >= 0:
                        widget.setCurrentIndex(index)
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(value) # Value is already a bool from typed get()
                elif isinstance(widget, QSpinBox):
                    widget.setValue(value) # Value is already an int from typed get()
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(value))
            
            self.logger.debug("Settings loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading settings: {str(e)}")
            self._reset_to_defaults()

    def _apply_settings(self) -> None:
        """Apply and save current settings"""
        try:
            current_settings = self._get_current_settings()
            for key, value in current_settings.items():
                self.settings_manager.set(key, value)
            
            self.settings_changed.emit(current_settings)
            QMessageBox.information(self, "Success", "Settings applied successfully")
        except Exception as e:
            self.logger.error(f"Error applying settings: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to apply settings: {str(e)}")

    def _reset_to_defaults(self) -> None:
        """Reset all settings to their default values"""
        reply = QMessageBox.question(self, "Reset Settings",
                                     "Are you sure you want to reset all settings to their default values?\n"
                                     "This action cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                self.settings_manager.reset_all()
                self._load_settings()
                QMessageBox.information(self, "Settings Reset", 
                                      "All settings have been reset to default values.")
                self.settings_changed.emit(self._get_current_settings()) # Notify app of reset
            except Exception as e:
                self.logger.error(f"Error resetting settings: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to reset settings: {str(e)}")

    def _get_current_settings(self) -> Dict[str, Any]:
        """Get current settings from widgets"""
        return {
            key: (widget.currentText() if isinstance(widget, QComboBox) else
                 widget.isChecked() if isinstance(widget, QCheckBox) else
                 widget.text() if isinstance(widget, QLineEdit) else
                 widget.value())
            for key, widget in self.widgets.items()
        }

    def accept(self) -> None:
        """Override accept to apply settings before closing"""
        self._apply_settings()
        super().accept()