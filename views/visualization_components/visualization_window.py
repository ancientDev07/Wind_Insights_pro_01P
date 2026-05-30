# from PyQt5.QtWidgets import *
# from PyQt5.QtCore import *
# from PyQt5.QtGui import *
# from matplotlib.figure import Figure
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
# import pandas as pd
# import numpy as np
# import time, traceback, gc, mplcursors
# from models import scada_utils as su
# from utils.collapsible_prop import CollapsibleSection
# from utils.datetime_utils import get_datetime_info
# from views.visualization_components.report_gen import EnhancedReportGenerator
# from . import plotting_logic as pl
# from typing import Optional
# from scipy.interpolate import interp1d
# import matplotlib.pyplot as plt

# class VisualizationWindow(QMainWindow):
#     update_plot_signal = pyqtSignal()
#     generate_report_signal = pyqtSignal()  # Define the signal for report generation

#     def __init__(self, data=None, turbine_name=None, parent=None, project_id=None):
#         super().__init__(parent)
        
#         # Set window title with turbine name
#         if turbine_name:
#             self.setWindowTitle(f"Visualization Window: {turbine_name}")
#         else:
#             self.setWindowTitle("Wind Data Visualization Tool")
#         self.setGeometry(100, 100, 1400, 800)
#         self.setFont(QFont("Time New Roman", 10))

#         # Initialize data attributes
#         self.data = data if data is not None else pd.DataFrame()
#         self.filtered_df = None
#         self.selected_plot = None
#         self.removed_data = None
#         self.column_cache = {}
#         self.standard_power_data = None
#         self.client_power_data = None
#         self.client_power_interp = None
#         self.interpolated_client_power = None
#         self.wind_speed_threshold = None
#         self.wind_speed_threshold_history = []
#             # Store project_id
#         self.project_id = project_id

#         # SDI: Independent window
#         self.setWindowFlags(Qt.Window)
#         self.setAttribute(Qt.WA_DeleteOnClose)
        
#         # Initialize UI components FIRST
#         self._init_ui_components()
        
#         # Setup UI
#         self.apply_styles()
#         self.process_data()
#         self.central_widget = QWidget()
#         self.setCentralWidget(self.central_widget)
#         self.init_ui()
        
#         # Process data AFTER UI is created
#         if not self.data.empty:
#             self._populate_column_cache()
        
#         # Setup docks and connect signals
#         self._setup_all_docks()
#         self.connect_signals()
#         # Initial plot setup
#         self.figure.add_subplot(111).text(0.5, 0.5, 'No data loaded', ha='center', va='center')

#     def _populate_column_cache(self):
#         """Populate column cache without calling UI methods"""
#         column_params = ["wind_speed", "nacelle_direction", "ambient_temp", "timestamp", 
#             "power", "rotor_speed", "nacelle_temp", "gearbox_temp", 
#             "generator_speed", "generator_temp" ]
        
#         for param in column_params:
#             matched_columns = su.find_matching_columns(self.data, param)
#             self.column_cache[param] = matched_columns[0] if matched_columns else None

#     def _init_ui_components(self):
#         """Initialize all UI components"""
#         # Create figure and canvas
#         self.figure = Figure(figsize=(10, 8))
#         self.canvas = FigureCanvas(self.figure)
        
#         # Initialize combo boxes
#         self.wind_speed_col = QComboBox(self)
#         self.wind_dir_col = QComboBox(self)
#         self.temp_col = QComboBox(self)
               
#         self.percentage_input = QLineEdit()
#         self.percentage_input.setText("5.0")
#         self.percentage_input.setEnabled(False)
#         self.percentage_input.setStyleSheet("color: black; background-color: white;")
#         # Initialize checkboxes
#         self._init_checkboxes()
#         # Initialize other components
#         self.background_color = QComboBox()
#         self.background_color.addItems(["white", "lightgray", "darkgray", "black"])
        
#         self._init_windrose_components()
    
#     def _init_checkboxes(self):
#         """Initialize all checkbox components"""
#         checkboxes = {
#             'show_grid': "Show Grid",
#             'show_legend': "Show Legend",
#             'enable_iec_binning': "Enable IEC Binning",
#             'show_std_dev': "Show Std Dev",
#             'show_original_values': "Show Original Values",
#             'remove_negative_power': "Remove Negative Power (≤ 0)",
#             'show_standard_power_curve': "Show Site Based Power Curve",
#             'enable_percentage_bands': "Enable ±n% Percentage Bands",
#             'show_plus_percentage': "Show +n% Curve",
#             'show_minus_percentage': "Show -n% Curve",
#             'fix_sample_size': "Fix Sample Size = 600",
#             'show_frequency_percentage': "Show Frequency as %"
#         }

#         for attr_name, text in checkboxes.items():
#             setattr(self, attr_name, QCheckBox(text))
    
#         # Set specific states
#         self.show_grid.setChecked(True)
#         self.show_plus_percentage.setChecked(False)
#         self.show_plus_percentage.setVisible(False)
#         self.show_minus_percentage.setChecked(False) 
#         self.show_minus_percentage.setVisible(False)
        
#     def _init_windrose_components(self):
#         """Initialize windrose sector components"""
#         self.windrose_checkboxes = {}
#         self.selected_sectors = 16
        
#         for sector in [8, 12, 16, 24, 36]:
#             checkbox = QCheckBox(f"{sector:02d} Sectors")
#             setattr(self, f'windrose_sectors_{sector:02d}', checkbox)
#             self.windrose_checkboxes[sector] = checkbox
        
#         self.windrose_sectors_16.setChecked(True)

#     def _setup_all_docks(self):
#         """Setup all dock widgets"""
#         self.setup_command_center()
#         self.setup_statistics_table()
#         self._setup_summary_dock()
#         self._setup_data_docks()
#         self._setup_status_bar()
    
#     def _setup_summary_dock(self):
#         """Setup summary dock widget"""
#         self.summary_dock = QDockWidget("Summary", self)
#         self.summary_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        
#         self.summary_table = QTableWidget()
#         self.summary_table.setColumnCount(2)
#         self.summary_table.setHorizontalHeaderLabels(["Metric", "Value"])
#         self.summary_table.horizontalHeader().setStretchLastSection(True)
#         self.summary_table.setAlternatingRowColors(True)
#         self.summary_table.setFont(QFont("Time Roman New", 10))
        
#         summary_widget = QWidget()
#         summary_layout = QVBoxLayout(summary_widget)
#         summary_layout.addWidget(self.summary_table)
#         self.summary_dock.setWidget(summary_widget)
#         self.addDockWidget(Qt.BottomDockWidgetArea, self.summary_dock)

#     def _setup_data_docks(self):
#         """Setup data-related dock widgets"""
#         dock_configs = [
#             ("Standard Power Data", "standard_data_dock", "standard_data_table"),
#             ("Deviation Data", "deviation_dock", "deviation_table"),
#             ("Percentage Bands Data", "percentage_bands_dock", "percentage_bands_table")
#         ]
        
#         for title, dock_attr, table_attr in dock_configs:
#             dock = QDockWidget(title, self)
#             table = QTableWidget()
            
#             if title == "Percentage Bands Data":
#                 widget = QWidget()
#                 layout = QVBoxLayout(widget)
#                 layout.addWidget(table)
                
#                 export_btn = QPushButton("Export Percentage Bands")
#                 export_btn.clicked.connect(self.export_percentage_bands)
#                 layout.addWidget(export_btn)
#                 dock.setWidget(widget)
#             else:
#                 dock.setWidget(table)
            
#             dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
#             self.addDockWidget(Qt.RightDockWidgetArea, dock)
#             dock.setVisible(False)
            
#             setattr(self, dock_attr, dock)
#             setattr(self, table_attr, table)

#     def _setup_status_bar(self):
#         """Setup status bar"""
#         self.statusBar = QStatusBar()
#         self.setStatusBar(self.statusBar)
    
#     def connect_signals(self):
#         """Connect all UI signals to their handlers"""
#         try:
#             # Core signals
#             signal_connections = [
#                 (self.update_plot_signal, self.update_plot),
#                 (self.generate_report_signal, self.generate_report),
#                 (self.background_color.currentIndexChanged, self.update_plot_signal.emit),
#             ]
#             # Checkbox signals
#             checkbox_signals = [
#                 'enable_iec_binning', 'remove_negative_power', 'show_grid', 'show_legend',
#                 'show_std_dev', 'show_original_values', 'fix_sample_size',
#                 'show_plus_percentage', 'show_minus_percentage','show_frequency_percentage'
#             ]
#             for checkbox_name in checkbox_signals:
#                 checkbox = getattr(self, checkbox_name)
#                 signal_connections.append((checkbox.stateChanged, self.update_plot_signal.emit))
#             # Special checkbox connections
#             signal_connections.extend([
#                 (self.remove_negative_power.stateChanged, self.show_removed_data_table),
#                 (self.show_standard_power_curve.stateChanged, self.handle_standard_power_curve_toggle),
#                 (self.fix_sample_size.stateChanged, self.show_removed_data_table),
#                 (self.enable_percentage_bands.stateChanged, self.toggle_percentage_input),
#                 (self.percentage_input.textChanged, self.update_plot_signal.emit),
#                 (self.wind_speed_col.currentIndexChanged, self.update_plot_signal.emit),
#                 (self.wind_dir_col.currentIndexChanged, self.update_plot_signal.emit),
#                 (self.temp_col.currentIndexChanged, self.update_plot_signal.emit),
#             ])
            
#             # Connect all signals
#             for signal, slot in signal_connections:
#                 signal.connect(slot)
            
#             # Connect windrose sector signals
#             self._connect_windrose_signals()
            
#         except Exception as e:
#             self.handle_errors(f"Error connecting signals: {str(e)}\n{traceback.format_exc()}")

#     def _connect_windrose_signals(self):
#         """Connect windrose sector checkbox signals"""
#         for sector, checkbox in self.windrose_checkboxes.items():
#             checkbox.stateChanged.connect(
#                 lambda state, cb=checkbox: self.on_windrose_sector_changed(cb)
#             )
#     def apply_styles(self):
#         self.setStyleSheet("""
#             QMainWindow { background-color: #f7f7f7; }
#             QGroupBox { font-weight: bold; border: 2px solid #d3d3d3; border-radius: 8px; margin-top: 15px; padding-top: 10px; background-color: #ffffff;}
#             QGroupBox::title {subcontrol-origin: margin; subcontrol-position: top left; padding: 4px 12px; background-color: #3498DB; color: white; border-radius: 4px; left: 10px; top: -8px;}
#             QCheckBox, QRadioButton { spacing: 5px; font-size: 11px; max-width: 200px; border: none; background-color: transparent; margin: 5px; }
#             QPushButton { background-color: #0078d7; color: white; border: none; padding: 6px 12px; border-radius: 4px; max-width: 180px; font-size: 11px;}
#             QPushButton:hover { background-color: #005a9e; }
#             QComboBox, QLineEdit { padding: 4px; border: 1px solid #ccc; border-radius: 4px; background-color: #ffffff; color: black; max-width: 150px; font-size: 11px;}  """)

#     def update_turbine_title(self, turbine: str) -> None:
#         self.setWindowTitle(f"Visualizing Turbine - {turbine}")

#     # def process_data(self):
#     #     if self.data.empty:
#     #         self.populate_comboboxes()
#     #         return
#     #     try:
#     #         timestamp_col = self.get_cached_columns("timestamp")
#     #         if timestamp_col and timestamp_col in self.data.columns:
#     #             self.data[timestamp_col] = pd.to_datetime(
#     #                 self.data[timestamp_col], errors='coerce')
#     #             self.data.dropna(subset=[timestamp_col], inplace=True)
#     #         self.populate_comboboxes()
#     #     except Exception as e:
#     #         self.handle_errors(f"Error processing data:\n{e}\n\n{traceback.format_exc()}")

#     def process_data(self):
#         if self.data.empty:
#             self.populate_comboboxes()
#             return
#         try:
#             timestamp_col = self.get_cached_columns("timestamp")
#             if timestamp_col and timestamp_col in self.data.columns:
#                 # FIX: Add format and dayfirst parameter
#                 self.data[timestamp_col] = pd.to_datetime(
#                     self.data[timestamp_col], 
#                     format='%d/%m/%Y %H:%M',
#                     dayfirst=True,
#                     errors='coerce'
#                 )
#                 self.data.dropna(subset=[timestamp_col], inplace=True)
#             self.populate_comboboxes()
#         except Exception as e:
#             self.handle_errors(f"Error processing data:\n{e}\n\n{traceback.format_exc()}")


#     def get_cached_columns(self, param):
#         if param not in self.column_cache:
#             matched_columns = su.find_matching_columns(self.data, param)
#             self.column_cache[param] = matched_columns[0] if matched_columns else None
#         return self.column_cache[param]
    
#     def populate_comboboxes(self):
#         self.wind_speed_col.clear()
#         self.wind_dir_col.clear()
#         self.temp_col.clear()
#         if self.data.empty:
#             return
        
#         # Parameter display names mapping
#         PARAMETER_DISPLAY_NAMES = {
#             'wind_speed': 'Wind Speed (m/s)',
#             'nacelle_direction': 'Wind Direction (°)',
#             'ambient_temp': 'Ambient Temperature (°C)',
#         }
        
#         def get_display_name(param_key):
#             return PARAMETER_DISPLAY_NAMES.get(param_key, param_key.replace('_', ' ').title())
        
#         wind_speed_cols = su.find_matching_columns(self.data, "wind_speed") or []
#         wind_dir_cols = su.find_matching_columns(self.data, "nacelle_direction") or []
#         ambient_temp_cols = su.find_matching_columns(self.data, "ambient_temp") or []
        
#         # Add items with display names but store original column names as data
#         for col in wind_speed_cols:
#             self.wind_speed_col.addItem(get_display_name('wind_speed'), col)
#         for col in wind_dir_cols:
#             self.wind_dir_col.addItem(get_display_name('nacelle_direction'), col)
#         for col in ambient_temp_cols:
#             self.temp_col.addItem(get_display_name('ambient_temp'), col)

#     def init_ui(self):
#         splitter = QSplitter(Qt.Horizontal, self.central_widget)
#         plot_panel = QWidget()
#         plot_layout = QVBoxLayout(plot_panel)
#         self.toolbar = NavigationToolbar(self.canvas, plot_panel)
#         plot_layout.addWidget(self.toolbar)
#         plot_layout.addWidget(self.canvas)
#         splitter.addWidget(plot_panel)
#         splitter.setSizes([350, 1050])
#         main_layout = QHBoxLayout(self.central_widget)
#         main_layout.addWidget(splitter)
#         self.central_widget.setLayout(main_layout)

#     def create_data_selection_group(self):
#         """Create the data selection UI group with optimized date handling and enable/disable checkboxes"""
#         content_widget = QWidget()
#         layout = QGridLayout(content_widget)
#         layout.setVerticalSpacing(8)
#         layout.setHorizontalSpacing(15)
#         # Get date range from data - OPTIMIZED
#         min_date, max_date, min_time, max_time, timestamp_col = get_datetime_info(self.data)
#         # Create enable/disable checkboxes
#         self.enable_date_filter = QCheckBox("Enable Date Filter")
#         self.enable_date_filter.setChecked(True)  # Default enabled
#         self.enable_date_filter.stateChanged.connect(self._toggle_date_filter)
#         layout.addWidget(self.enable_date_filter, 0, 0, 1, 2)
#         self.enable_time_filter = QCheckBox("Enable Time Filter")
#         self.enable_time_filter.setChecked(False)  # Default disabled
#         self.enable_time_filter.stateChanged.connect(self._toggle_time_filter)
#         layout.addWidget(self.enable_time_filter, 1, 0, 1, 2)
#         # Get date range from data - FIXED
#         min_date, max_date, min_time, max_time, timestamp_col = get_datetime_info(self.data)
#         # Use actual data dates or fallback
#         min_date_str = min_date
#         max_date_str = max_date
#         min_time_str = min_time if min_time else "00:00"
#         max_time_str = max_time if max_time else "23:59"
#         # Date selection widgets
#         self.start_date_label = QLabel("Start Date")
#         layout.addWidget(self.start_date_label, 2, 0)
#         self.start_date_only = QLineEdit(min_date_str)
#         self.start_date_only.setPlaceholderText("DD-MM-YYYY")
#         layout.addWidget(self.start_date_only, 2, 1)
#         self.end_date_label = QLabel("End Date")
#         layout.addWidget(self.end_date_label, 3, 0)
#         self.end_date_only = QLineEdit(max_date_str)
#         self.end_date_only.setPlaceholderText("DD-MM-YYYY")
#         layout.addWidget(self.end_date_only, 3, 1)
        
#         # Time selection widgets
#         self.start_time_label = QLabel(f"From Time ({min_time_str}):")
#         layout.addWidget(self.start_time_label, 4, 0)
#         self.start_time_only = QLineEdit(min_time_str)
#         self.start_time_only.setPlaceholderText("HH:MM")
#         layout.addWidget(self.start_time_only, 4, 1)
        
#         self.end_time_label = QLabel(f"To Time ({max_time_str}):")
#         layout.addWidget(self.end_time_label, 5, 0)
#         self.end_time_only = QLineEdit(max_time_str)
#         self.end_time_only.setPlaceholderText("HH:MM")
#         layout.addWidget(self.end_time_only, 5, 1)
        
#         # Initially set time filter widgets visibility
#         self._toggle_time_filter()
        
#         # Background color
#         layout.addWidget(QLabel("Background Color:"), 6, 0)
#         layout.addWidget(self.background_color, 6, 1)
#         # Wind parameters
#         layout.addWidget(QLabel("Wind Speed:"), 7, 0, Qt.AlignLeft)
#         layout.addWidget(self.wind_speed_col, 7, 1)
#         layout.addWidget(QLabel("Wind Direction:"), 8, 0, Qt.AlignLeft)
#         layout.addWidget(self.wind_dir_col, 8, 1)
#         layout.addWidget(QLabel("Temperature:"), 9, 0, Qt.AlignLeft)
#         layout.addWidget(self.temp_col, 9, 1)

#         # Update button
#         update_button = QPushButton("Update Plot")
#         update_button.clicked.connect(self.update_plot_signal.emit)
#         layout.addWidget(update_button, 10, 0, 1, 2, Qt.AlignCenter)
#         # Fix sample size checkbox
#         # layout.addWidget(self.fix_sample_size, 11, 0, 1, 2)
#         section = CollapsibleSection("Data Selection and Filtering", content_widget, expanded=True)
#         return section

#     def _toggle_date_filter(self):
#         """Toggle date filter widgets visibility and state"""
#         enabled = self.enable_date_filter.isChecked()
#         # Show/hide date widgets
#         self.start_date_label.setVisible(enabled)
#         self.start_date_only.setVisible(enabled)
#         self.end_date_label.setVisible(enabled)
#         self.end_date_only.setVisible(enabled)
#         # Enable/disable date widgets
#         self.start_date_label.setEnabled(enabled)
#         self.start_date_only.setEnabled(enabled)
#         self.end_date_label.setEnabled(enabled)
#         self.end_date_only.setEnabled(enabled)
#         # Update styling to show disabled state
#         style = "" if enabled else "color: gray;"
#         self.start_date_label.setStyleSheet(style)
#         self.end_date_label.setStyleSheet(style)
 
#     def _toggle_time_filter(self):
#         """Toggle time filter widgets visibility and state"""
#         enabled = self.enable_time_filter.isChecked()
#         # Show/hide time widgets
#         self.start_time_label.setVisible(enabled)
#         self.start_time_only.setVisible(enabled)
#         self.end_time_label.setVisible(enabled)
#         self.end_time_only.setVisible(enabled)
#         # Enable/disable time widgets
#         self.start_time_label.setEnabled(enabled)
#         self.start_time_only.setEnabled(enabled)
#         self.end_time_label.setEnabled(enabled)
#         self.end_time_only.setEnabled(enabled)
        
#     def create_windrose_options_group(self):
#         content_widget = QWidget()
#         layout = QGridLayout(content_widget)
#         layout.setVerticalSpacing(10)
#         layout.setHorizontalSpacing(15)
#         # Set default to 16 sectors
#         self.windrose_sectors_16.setChecked(True)
#         # Add to layout
#         layout.addWidget(self.windrose_sectors_08, 0, 0)
#         layout.addWidget(self.windrose_sectors_12, 0, 1)
#         layout.addWidget(self.windrose_sectors_16, 1, 0)
#         layout.addWidget(self.windrose_sectors_24, 1, 1)
#         layout.addWidget(self.windrose_sectors_36, 2, 0)
#         # Connect signals for mutual exclusivity
#         self.windrose_sectors_08.stateChanged.connect(lambda: self.on_windrose_sector_changed(self.windrose_sectors_08))
#         self.windrose_sectors_12.stateChanged.connect(lambda: self.on_windrose_sector_changed(self.windrose_sectors_12))
#         self.windrose_sectors_16.stateChanged.connect(lambda: self.on_windrose_sector_changed(self.windrose_sectors_16))
#         self.windrose_sectors_24.stateChanged.connect(lambda: self.on_windrose_sector_changed(self.windrose_sectors_24))
#         self.windrose_sectors_36.stateChanged.connect(lambda: self.on_windrose_sector_changed(self.windrose_sectors_36))
#         section = CollapsibleSection("Windrose Options", content_widget)
#         return section

#     def on_windrose_sector_changed(self, changed_checkbox):
#         """Handle windrose sector selection with mutual exclusivity"""
#         if not changed_checkbox.isChecked():
#             # Prevent unchecking if no others are checked
#             if not any(cb.isChecked() for cb in self.windrose_checkboxes.values()):
#                 changed_checkbox.setChecked(True)
#             return
        
#         # Uncheck all others and update selected sectors
#         for sector, checkbox in self.windrose_checkboxes.items():
#             if checkbox != changed_checkbox:
#                 checkbox.setChecked(False)
#             elif checkbox.isChecked():
#                 self.selected_sectors = sector
        
#         self.update_plot_signal.emit()
    
#     def toggle_percentage_input(self):
#         enabled = self.enable_percentage_bands.isChecked()
        
#         self.percentage_input.setEnabled(enabled)
#         self.show_plus_percentage.setEnabled(enabled)
#         self.show_minus_percentage.setEnabled(enabled)
        
#         # Show/hide the checkboxes
#         self.show_plus_percentage.setVisible(enabled)
#         self.show_minus_percentage.setVisible(enabled)
        
#         self.update_plot_signal.emit()

#     def ensure_exclusive_windrose_sector(self, changed_checkbox):
#         if changed_checkbox.isChecked():
#             for checkbox in [self.windrose_sectors_08, self.windrose_sectors_12, self.windrose_sectors_16, 
#                             self.windrose_sectors_24, self.windrose_sectors_36]:
#                 if checkbox != changed_checkbox:
#                     checkbox.setChecked(False)
#             if changed_checkbox == self.windrose_sectors_08:
#                 self.selected_sectors = 8
#             if changed_checkbox == self.windrose_sectors_12:
#                 self.selected_sectors = 12
#             elif changed_checkbox == self.windrose_sectors_16:
#                 self.selected_sectors = 16
#             elif changed_checkbox == self.windrose_sectors_24:
#                 self.selected_sectors = 24
#             elif changed_checkbox == self.windrose_sectors_36:
#                 self.selected_sectors = 36
#             self.update_plot_signal.emit()
#         else:
#             if not any(checkbox.isChecked() for checkbox in [self.windrose_sectors_08, self.windrose_sectors_12, self.windrose_sectors_16, self.windrose_sectors_24, 
#                                                             self.windrose_sectors_36]):
#                 changed_checkbox.setChecked(True)
    
#     def setup_command_center(self):
#         self.command_center = QDockWidget("Command Center", self)
#         self.command_center.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
#         self.command_center.setMinimumWidth(250)
#         self.command_center.setMaximumWidth(350)

#         scroll_area = QScrollArea()
#         scroll_widget = QWidget()
#         scroll_layout = QVBoxLayout(scroll_widget)
#         # Data Selection Section
#         data_selection_section = self.create_data_selection_group()
#         scroll_layout.addWidget(data_selection_section)
#         # Plot Options Section
#         plot_options_section = self.create_plot_options_group()
#         scroll_layout.addWidget(plot_options_section)
#         # Windrose Options Section
#         windrose_options_section = self.create_windrose_options_group()
#         scroll_layout.addWidget(windrose_options_section)
#         # Wind Analysis Section
#         wind_content = QWidget()
#         wind_layout = QVBoxLayout(wind_content)
#         btn_wind_rose = QPushButton("Wind Rose")
#         btn_wind_speed = QPushButton("Wind Speed Distribution")
#         btn_turbulence = QPushButton("Turbulence Intensity")
#         btn_wind_frequency = QPushButton("Wind Frequency Histogram")
#         wind_layout.addWidget(btn_wind_rose)
#         wind_layout.addWidget(btn_wind_speed)
#         wind_layout.addWidget(btn_turbulence)
#         wind_layout.addWidget(btn_wind_frequency)
#         wind_section = CollapsibleSection("Wind Analysis", wind_content)
#         scroll_layout.addWidget(wind_section)
#         # Performance & Power Section
#         power_content = QWidget()
#         power_layout = QVBoxLayout(power_content)
#         btn_power_curve = QPushButton("Site Based Power Curve")
#         btn_actual_power_curve = QPushButton("Actual Power Curve")
#         btn_binned_power_curve = QPushButton("Binned Power Curve")
#         btn_rotor_speed = QPushButton("Rotor Speed Graph")
#         btn_rotor_vs_gen = QPushButton("Rotor vs Generator Speed")
#         power_layout.addWidget(btn_power_curve)
#         power_layout.addWidget(btn_actual_power_curve)
#         power_layout.addWidget(btn_binned_power_curve)
#         power_layout.addWidget(btn_rotor_speed)
#         power_layout.addWidget(btn_rotor_vs_gen)
#         power_section = CollapsibleSection("Performance & Power", power_content)
#         scroll_layout.addWidget(power_section)
#         # Temperature & Mechanics Section
#         temp_content = QWidget()
#         temp_layout = QVBoxLayout(temp_content)
#         btn_ambient_vs_nacelle = QPushButton("Ambient vs Nacelle Temp")
#         btn_rotor_vs_gearbox = QPushButton("Rotor vs Gearbox Temp")
#         temp_layout.addWidget(btn_ambient_vs_nacelle)
#         temp_layout.addWidget(btn_rotor_vs_gearbox)
#         temp_section = CollapsibleSection("Temperature & Mechanics", temp_content)
#         scroll_layout.addWidget(temp_section)
#         # Other Section
#         other_content = QWidget()
#         other_layout = QVBoxLayout(other_content)
#         btn_joint = QPushButton("Joint Distribution")
#         btn_generate_report = QPushButton("Generate Report")

#         other_layout.addWidget(btn_joint)
#         other_layout.addWidget(btn_generate_report)
#         other_section = CollapsibleSection("Other", other_content)
#         scroll_layout.addWidget(other_section)

#         scroll_layout.addStretch()
#         scroll_widget.setLayout(scroll_layout)
#         scroll_area.setWidget(scroll_widget)
#         scroll_area.setWidgetResizable(True)
#         self.command_center.setWidget(scroll_area)
#         self.addDockWidget(Qt.LeftDockWidgetArea, self.command_center)

#         btn_wind_rose.clicked.connect(lambda: self.set_and_update("wind_rose"))
#         btn_wind_speed.clicked.connect(lambda: self.set_and_update("wind_speed_distribution"))
#         btn_turbulence.clicked.connect(lambda: self.set_and_update("turbulence_intensity"))
#         btn_wind_frequency.clicked.connect(lambda: self.set_and_update("wind_frequency_histogram"))
#         btn_power_curve.clicked.connect(lambda: self.set_and_update("power_curve"))
#         btn_actual_power_curve.clicked.connect(lambda: self.set_and_update("actual_power_curve"))
#         btn_binned_power_curve.clicked.connect(self.show_binned_power_curve_with_table)
#         btn_rotor_speed.clicked.connect(lambda: self.set_and_update("rotor_speed_graph"))
#         btn_rotor_vs_gen.clicked.connect(lambda: self.set_and_update("rotor_speed_vs_generator_speed"))
#         btn_ambient_vs_nacelle.clicked.connect(lambda: self.set_and_update("ambient_vs_nacelle_temperature"))
#         btn_rotor_vs_gearbox.clicked.connect(lambda: self.set_and_update("rotor_speed_vs_gearbox_temperature"))
#         btn_joint.clicked.connect(lambda: self.set_and_update("joint_distribution"))
#         btn_generate_report.clicked.connect(self.generate_report_signal.emit)
#         btn_wind_frequency.clicked.connect(lambda: self.set_and_update_with_table("wind_frequency_histogram"))

#     def _create_analysis_sections(self):
#         """Create all analysis button sections"""
#         sections = []
        
#         # Wind Analysis Section
#         wind_buttons = [
#             ("Wind Rose", "wind_rose"),
#             ("Wind Speed Distribution", "wind_speed_distribution"),
#             ("Turbulence Intensity", "turbulence_intensity"),
#             ("Wind Frequency", "wind_frequency_histogram")
#         ]
#         sections.append(self._create_button_section("Wind Analysis", wind_buttons))
#         # Performance & Power Section
#         power_buttons = [
#             ("Site-Based Power Curve", "power_curve"),
#             ("Actual Power Curve", "actual_power_curve"),
#             ("Binned Power Curve", lambda: self.show_binned_power_curve_with_table()),
#             ("Rotor Speed Graph", "rotor_speed_graph"),
#             ("Rotor vs Generator Speed", "rotor_speed_vs_generator_speed")
#         ]
#         sections.append(self._create_button_section("Performance & Power", power_buttons))
#         # Temperature & Mechanics Section
#         temp_buttons = [
#             ("Ambient vs Nacelle Temp", "ambient_vs_nacelle_temperature"),
#             ("Rotor vs Gearbox Temp", "rotor_speed_vs_gearbox_temperature")
#         ]
#         sections.append(self._create_button_section("Temperature & Mechanics", temp_buttons))
#         # Other Section
#         other_buttons = [
#             ("Joint Distribution", "joint_distribution"),
#             ("Generate Report", lambda: self.generate_report_signal.emit())
#         ]
#         sections.append(self._create_button_section("Other", other_buttons))
        
#         return sections

#     def _create_button_section(self, title, buttons):
#         """Create a collapsible section with buttons"""
#         content_widget = QWidget()
#         layout = QVBoxLayout(content_widget)
        
#         for button_text, action in buttons:
#             btn = QPushButton(button_text)
#             if callable(action):
#                 btn.clicked.connect(action)
#             else:
#                 btn.clicked.connect(lambda checked, plot=action: self.set_and_update(plot))
#             layout.addWidget(btn)
        
#         return CollapsibleSection(title, content_widget)
    
#     def create_plot_options_group(self):
#         """Create plot options control group"""
#         content_widget = QWidget()
#         layout = QGridLayout(content_widget)
#         layout.setVerticalSpacing(8)
#         layout.setHorizontalSpacing(10)
#         # Row 1-2: Display options
#         layout.addWidget(self.show_grid, 0, 0, 1, 2)
#         layout.addWidget(self.show_legend, 1, 0, 1, 2)   
#         # Row 3-4: IEC and std dev
#         layout.addWidget(self.enable_iec_binning, 2, 0, 1, 2)
#         layout.addWidget(self.remove_negative_power, 3, 0, 1, 2)
#         layout.addWidget(self.show_std_dev, 4, 0, 1, 2)
#         # Row 5: Original values and hourly avg
#         layout.addWidget(self.show_original_values, 5, 0, 1, 2)
#         layout.addWidget(self.show_frequency_percentage, 6, 0, 1, 2)
#         # Row 7-9: Power curve options
#         layout.addWidget(self.show_standard_power_curve, 7, 0, 1, 2)
#         layout.addWidget(self.enable_percentage_bands, 8, 0, 1, 2)
#         # Percentage input group
#         pct_widget = QWidget()
#         pct_layout = QHBoxLayout(pct_widget)
#         pct_layout.setContentsMargins(0, 0, 0, 0)
#         pct_layout.addWidget(QLabel("±"))
#         pct_layout.addWidget(self.percentage_input)
#         pct_layout.addWidget(QLabel("%"))
#         layout.addWidget(pct_widget, 9, 0, 1, 2)
#         # Row 10-11: Percentage band checkboxes
#         layout.addWidget(self.show_plus_percentage, 10, 0, 1, 2)
#         layout.addWidget(self.show_minus_percentage, 11, 0, 1, 2)
#         return CollapsibleSection("Plot Options", content_widget, expanded=True)

#     def set_and_update(self, plot_name):
#         self.selected_plot = plot_name
#         self.update_plot_signal.emit()

#     def setup_statistics_table(self):
#         self.stats_dock = QDockWidget("Statistics", self)
#         self.stats_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
#         self.stats_table = QTableWidget()
#         self.stats_table.setColumnCount(2)
#         self.stats_table.setHorizontalHeaderLabels(["Statistic", "Value"])
#         self.stats_table.horizontalHeader().setStretchLastSection(True)
#         self.stats_table.setAlternatingRowColors(True)
#         self.stats_table.setFont(QFont("Time Roman New", 10))
#         self.stats_dock.setWidget(self.stats_table)
#         self.addDockWidget(Qt.BottomDockWidgetArea, self.stats_dock)

#     def get_safe_date_range(self):
#         if not self.data.empty:
#             timestamp_col = self.column_cache.get("timestamp")
#             if timestamp_col and timestamp_col in self.data.columns:
#                 min_date = self.data[timestamp_col].min().date()
#                 max_date = self.data[timestamp_col].max().date()
#             elif isinstance(self.data.index, pd.DatetimeIndex):
#                 min_date = self.data.index.min().date()
#                 max_date = self.data.index.max().date()
#             else:
#                 return QDate.currentDate().addDays(-30), QDate.currentDate()
#             return QDate(min_date), QDate(max_date)
#         return QDate.currentDate().addDays(-30), QDate.currentDate()

#     # def update_statistics(self):
#     #     df_to_use = self.filtered_df if self.filtered_df is not None and not self.filtered_df.empty else self.data
#     #     if df_to_use is None or df_to_use.empty:
#     #         return
#     #     df = df_to_use.copy()
#     #     df.columns = df.columns.str.strip()
#     #     timestamp_col = self.column_cache.get("timestamp")
#     #     if timestamp_col and timestamp_col in df.columns:
#     #         df.loc[:, timestamp_col] = pd.to_datetime(df[timestamp_col], format='%d-%m-%Y %H:%M:%S', errors='coerce', dayfirst=True)
#     #         df.set_index(timestamp_col, inplace=True)
#     #     elif isinstance(df.index, pd.DatetimeIndex):
#     #         pass
#     #     else:
#     #         return
#     #     wind_speed_column = self.wind_speed_col.currentData() or self.wind_speed_col.currentText()
#     #     wind_dir_column = self.wind_dir_col.currentData() or self.wind_dir_col.currentText()
#     #     if wind_speed_column not in df.columns or wind_dir_column not in df.columns:
#     #         return
#     #     speed_data = df[wind_speed_column]
#     #     dir_data = df[wind_dir_column]
#     #     prevailing = pd.Series(dir_data).mode()
#     #     prevailing_wind = f"{prevailing.iloc[0]:.1f}°" if not prevailing.empty else "N/A"
#     #     data_period_start = df.index.min().strftime('%Y-%m-%d') if not df.empty else "N/A"
#     #     data_period_end = df.index.max().strftime('%Y-%m-%d') if not df.empty else "N/A"
#     #     stats = [
#     #         ("Mean Speed (m/s)", f"{speed_data.mean():.2f}"),
#     #         ("Max Speed (m/s)", f"{speed_data.max():.2f}"),
#     #         ("Std Dev (m/s)", f"{speed_data.std():.2f}"),
#     #         ("Prevailing Wind", prevailing_wind),
#     #         ("Data Period", f"{data_period_start} to {data_period_end}"),
#     #         ("Total Records", f"{len(df)}")
#     #     ]
#     #     self.stats_table.setRowCount(len(stats))
#     #     for row, (stat, value) in enumerate(stats):
#     #         self.stats_table.setItem(row, 0, QTableWidgetItem(str(stat)))
#     #         self.stats_table.setItem(row, 1, QTableWidgetItem(str(value)))
#     #     self.stats_table.resizeColumnsToContents()

#     def update_statistics(self):
#         df_to_use = self.filtered_df if self.filtered_df is not None and not self.filtered_df.empty else self.data
#         if df_to_use is None or df_to_use.empty:
#             return
        
#         df = df_to_use.copy()
#         df.columns = df.columns.str.strip()
        
#         timestamp_col = self.column_cache.get("timestamp")
#         if timestamp_col and timestamp_col in df.columns:
#             df.loc[:, timestamp_col] = pd.to_datetime(df[timestamp_col], format='%d-%m-%Y %H:%M:%S', errors='coerce')
#             df.set_index(timestamp_col, inplace=True)
#         elif isinstance(df.index, pd.DatetimeIndex):
#             pass
#         else:
#             return
        
#         wind_speed_column = self.wind_speed_col.currentData() or self.wind_speed_col.currentText()
#         wind_dir_column = self.wind_dir_col.currentData() or self.wind_dir_col.currentText()
        
#         if wind_speed_column not in df.columns or wind_dir_column not in df.columns:
#             return
        
#         # VECTORIZE: Process all data simultaneously
#         speed_data = pd.to_numeric(df[wind_speed_column], errors='coerce')
#         dir_data = pd.to_numeric(df[wind_dir_column], errors='coerce')
        
#         # VECTORIZE: Calculate all statistics at once
#         prevailing = dir_data.mode()
#         prevailing_wind = f"{prevailing.iloc[0]:.1f}°" if not prevailing.empty else "N/A"
        
#         data_period_start = df.index.min().strftime('%Y-%m-%d') if not df.empty else "N/A"
#         data_period_end = df.index.max().strftime('%Y-%m-%d') if not df.empty else "N/A"
        
#         # VECTORIZE: All statistical calculations in one pass
#         stats = [
#             ("Mean Speed (m/s)", f"{speed_data.mean():.2f}"),
#             ("Max Speed (m/s)", f"{speed_data.max():.2f}"),
#             ("Std Dev (m/s)", f"{speed_data.std():.2f}"),
#             ("Prevailing Wind", prevailing_wind),
#             ("Data Period", f"{data_period_start} to {data_period_end}"),
#             ("Total Records", f"{len(df)}")
#         ]
        
#         self.stats_table.setRowCount(len(stats))
#         for row, (stat, value) in enumerate(stats):
#             self.stats_table.setItem(row, 0, QTableWidgetItem(str(stat)))
#             self.stats_table.setItem(row, 1, QTableWidgetItem(str(value)))
#         self.stats_table.resizeColumnsToContents()

#     def update_summary(self):
#         df_to_use = self.filtered_df if self.filtered_df is not None and not self.filtered_df.empty else self.data
#         if df_to_use is None or df_to_use.empty:
#             return
#         power_col = self.column_cache.get("power")
#         if power_col and power_col in df_to_use.columns:
#             power_data = pd.to_numeric(df_to_use[power_col], errors='coerce').dropna()
#             if not power_data.empty:
#                 max_power = round(power_data.max(), 3)
#                 total_power = power_data.sum()
#                 active_power_sum = power_data[power_data > 0].sum()
#                 active_power_count = power_data[power_data > 0].count()
#                 reactive_power_sum = power_data[power_data < 0].sum()
#                 reactive_power_count = power_data[power_data < 0].count()
#                 rated_power = power_data.max()
#                 rated_power_col = self.column_cache.get("rated_power")
#                 if rated_power_col and rated_power_col in df_to_use.columns:
#                     try:
#                         rated_power = float(df_to_use[rated_power_col].max())
#                     except (ValueError, TypeError) as e:
#                         print(f"Error using rated_power column: {e}")
#                 total_possible_power = rated_power * len(df_to_use)
#                 plf = (total_power / total_possible_power) * 100 if total_possible_power > 0 else 0
#                 grid_availability = (active_power_count / len(df_to_use)) * 100 if len(df_to_use) > 0 else 0
#                 summary_stats = [
#                     ("Max Power (KW)", f"{max_power:.3f}"),
#                     ("Total Power", f"{total_power:.3f}"),
#                     ("Total Active Power", f"{active_power_sum:.3f} (samples: {active_power_count})"),
#                     ("Total Reactive Power", f"{reactive_power_sum:.3f} (samples: {reactive_power_count})"),
#                     ("PLF (%)", f"{plf:.2f}"),
#                     ("Grid Availability (%)", f"{grid_availability:.2f}")
#                 ]
#                 self.summary_table.setRowCount(len(summary_stats))
#                 for row, (metric, value) in enumerate(summary_stats):
#                     self.summary_table.setItem(row, 0, QTableWidgetItem(metric))
#                     self.summary_table.setItem(row, 1, QTableWidgetItem(value))
#                 self.summary_table.resizeColumnsToContents()

#     def get_filtered_data(self):
#         """Get filtered data based on current settings with improved error handling"""
#         try:
#             if self.data.empty:
#                 return pd.DataFrame()
            
#             # Initialize filtered_data
#             filtered_data = self.data
#             # Get timestamp column
#             timestamp_col = self.get_cached_columns("timestamp") or self._find_timestamp_column()
            
#             # # Apply date and time filters only if enabled
#             # if hasattr(self, 'enable_date_filter') and self.enable_date_filter.isChecked():
#             #     filtered_data = self.apply_date_filter(filtered_data, timestamp_col)
#             #     if filtered_data.empty:
#             #         print("Warning: Date filter resulted in empty dataset")
#             #         return filtered_data
#             # # Data type conversion
#             # self._convert_data_types(filtered_data)
#             # # Initialize removed data tracking
#             # self.removed_data = pd.DataFrame()
#             # # Apply power filtering for relevant plots
#             # if self._should_apply_power_filter():
#             #     filtered_data = self._apply_power_filter(filtered_data)
#             # # Apply sample size filtering
#             # if self.fix_sample_size.isChecked():
#             #     filtered_data = self._apply_sample_size_filter(filtered_data)
#             # self.filtered_df = filtered_data
#             # self.show_removed_data_table()
#             # return filtered_data

#             if hasattr(self, 'enable_date_filter') and self.enable_date_filter.isChecked():
#                 start_date = self.start_date_only.text()
#                 end_date = self.end_date_only.text()
                
#                 # VECTORIZE: Apply all date filters at once
#                 timestamp_col = self.get_cached_columns("timestamp")
#                 if timestamp_col:
#                     date_mask = pd.Series(True, index=filtered_data.index)
                    
#                     if start_date:
#                         date_mask &= (filtered_data[timestamp_col].dt.date >= 
#                                     pd.to_datetime(start_date, format='%d-%m-%Y').date())
#                     if end_date:
#                         date_mask &= (filtered_data[timestamp_col].dt.date <= 
#                                     pd.to_datetime(end_date, format='%d-%m-%Y').date())
                    
#                     filtered_data = filtered_data[date_mask]  # Single vectorized operation
            
#             # VECTORIZE: Power filtering
#             if self._should_apply_power_filter():
#                 power_col = self.column_cache.get("power")
#                 if power_col:
#                     # VECTORIZE: Filter all power values at once
#                     power_mask = pd.to_numeric(filtered_data[power_col], errors='coerce') > 0.1
#                     filtered_data = filtered_data[power_mask]
            
#             return filtered_data

#         except Exception as e:
#             self.handle_errors(f"Error filtering data: {str(e)}\n{traceback.format_exc()}")
#             return pd.DataFrame()
    
#     def apply_date_filter(self, df, timestamp_col):
#         """Enhanced date and time filters with proper datetime handling and error recovery"""
#         if not timestamp_col or timestamp_col not in df.columns:
#             print("Warning: No valid timestamp column found for filtering")
#             return df
#         original_count = len(df)
#         try:
#             # Ensure timestamp column is datetime
#             if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
#                 df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
#             # Remove rows with invalid timestamps
#             df = df.dropna(subset=[timestamp_col])
#             # Apply date filter only if date filtering is enabled
#             if hasattr(self, 'enable_date_filter') and self.enable_date_filter.isChecked():
#                 start_date = self.start_date_only.text().strip()
#                 end_date = self.end_date_only.text().strip()
#                 if start_date:
#                     try:
#                         start_dt = pd.to_datetime(start_date, format='%d-%m-%Y', errors='raise')
#                         df = df[df[timestamp_col].dt.date >= start_dt.date()]
#                     except ValueError:
#                         print(f"Invalid start date format: {start_date}. Expected DD-MM-YYYY")
#                 if end_date:
#                     try:
#                         end_dt = pd.to_datetime(end_date, format='%d-%m-%Y', errors='raise')
#                         df = df[df[timestamp_col].dt.date <= end_dt.date()]
#                     except ValueError:
#                         print(f"Invalid end date format: {end_date}. Expected DD-MM-YYYY")
#             # Apply time filter only if time filtering is enabled
#             if hasattr(self, 'enable_time_filter') and self.enable_time_filter.isChecked():
#                 start_time = self.start_time_only.text().strip()
#                 end_time = self.end_time_only.text().strip()

#                 if start_time:
#                     try:
#                         start_time_obj = pd.to_datetime(start_time, format='%H:%M').time()
#                         df = df[df[timestamp_col].dt.time >= start_time_obj]
#                     except ValueError:
#                         print(f"Invalid start time format: {start_time}. Expected HH:MM")
                
#                 if end_time:
#                     try:
#                         end_time_obj = pd.to_datetime(end_time, format='%H:%M').time()
#                         df = df[df[timestamp_col].dt.time <= end_time_obj]
#                     except ValueError:
#                         print(f"Invalid end time format: {end_time}. Expected HH:MM")
#         except Exception as e:
#             print(f"Date/time filter error: {e}")
#             return df  # Return original data if filtering fails
#         filtered_count = len(df)
#         if original_count != filtered_count:
#             print(f"Data filtered: {original_count} -> {filtered_count} rows")
#         return df
 
#     def _get_timestamp_column(self, df):
#         """Get the appropriate timestamp column"""
#         timestamp_col = self.column_cache.get("timestamp")
#         if timestamp_col and timestamp_col in df.columns:
#             return timestamp_col
#         elif isinstance(df.index, pd.DatetimeIndex):
#             timestamp_col = "Timestamp"
#             df.loc[:, "Timestamp"] = df.index
#             return timestamp_col
#         return None
    
#     def _convert_data_types(self, df):
#         """Convert data types for numeric columns"""
#         power_col = self.column_cache.get("power")
#         wind_speed_col = self.wind_speed_col.currentData() or self.wind_speed_col.currentText()
#         for col in [power_col, wind_speed_col]:
#             if col and col in df.columns:
#                 df.loc[:, col] = pd.to_numeric(df[col], errors='coerce')
#     def _should_apply_power_filter(self):
#         """Check if power filtering should be applied"""
#         power_related_plots = [
#             "power_curve", "actual_power_curve", "binned_power_curve"]
#         return (self.remove_negative_power.isChecked() and 
#                 self.selected_plot in power_related_plots)
#     def _apply_sample_size_filter(self, df):
#         """Apply sample size filtering for consistent intervals"""
#         timestamp_col = self.column_cache.get("timestamp")
#         if not timestamp_col or timestamp_col not in df.columns:
#             return df
        
#         fd = df.sort_values(by=timestamp_col)
#         fd['dt'] = fd[timestamp_col].diff().dt.total_seconds().fillna(0)
#         fd['block'] = (fd['dt'] != 600).cumsum()
        
#         spans = fd.groupby('block')[timestamp_col].agg(['min', 'max'])
#         spans['duration'] = (spans['max'] - spans['min']).dt.total_seconds()
#         good_blocks = spans[spans['duration'] >= 600].index
#         if not good_blocks.empty:
#             block_id = good_blocks.min()
#             return fd[fd['block'] == block_id].drop(columns=['dt', 'block'])
#         return df
    
#     def _apply_power_filter(self, df):
#         """Apply power filtering to remove negative power values"""
#         power_col = self.column_cache.get("power")
#         if not power_col or power_col not in df.columns:
#             return df
#         initial_count = len(df)
#         power_data = pd.to_numeric(df[power_col], errors='coerce')
#         valid_power_mask = power_data > 0.1
#         # Store removed data
#         removed_mask = ~valid_power_mask | power_data.isna()
#         if removed_mask.any():
#             self.removed_data = pd.concat([
#                 self.removed_data, 
#                 df[removed_mask]
#             ], ignore_index=True)
        
#         filtered_df = df[valid_power_mask]
#         removed_count = initial_count - len(filtered_df)
#         if removed_count > 0:
#             self.statusBar.showMessage(f"Removed {removed_count} records with negative/invalid power", 5000)
#         return filtered_df
    
#     def update_plot(self):
#         """Update the main plot with current settings"""
#         try:
#             start_time = time.time()
            
#             if self._should_skip_plot_update():
#                 return
#             # Cleanup and preparation
#             self._prepare_plot_update()
#             # Get filtered data
#             self.filtered_df = self.get_filtered_data()
#             # Execute plot function
#             if self.selected_plot and self.selected_plot in self._get_plot_functions():
#                 self._execute_plot_function()
#                 self._configure_plot_appearance()
#                 self._setup_plot_interactivity()
#             # Finalize plot
#             self.canvas.draw_idle()
#             self._update_ui_components()
#             # Show performance metrics
#             elapsed_time = time.time() - start_time
#             self.statusBar.showMessage(f"Plot updated in {elapsed_time:.3f} seconds", 3000)
            
#         except Exception as e:
#             self.handle_errors(f"Error updating plot: {str(e)}\n{traceback.format_exc()}")
    
#     def _should_skip_plot_update(self):
#         """Check if plot update should be skipped"""
#         if self.data is None or self.data.empty:
#             self.figure.clear()
#             ax = self.figure.add_subplot(111)
#             ax.text(0.5, 0.5, 'No data loaded', ha='center', va='center')
#             self.canvas.draw_idle()
#             return True
#         return False
    
#     def _prepare_plot_update(self):
#         """Prepare for plot update"""
#         plt.close('all')
#         gc.collect()
#         self.figure.clf()
    
#     def _get_plot_functions(self):
#         """Get dictionary of available plot functions"""
#         return {
#             "wind_rose": lambda: pl.plot_selected_graph(self, "wind_rose", self.column_cache),
#             "wind_speed_distribution": lambda: pl.plot_selected_graph(self, "wind_speed_distribution", self.column_cache),
#             "turbulence_intensity": lambda: pl.plot_selected_graph(self, "turbulence_intensity", self.column_cache),
#             "power_curve": lambda: pl.plot_selected_graph(self, "power_curve", self.column_cache),
#             "actual_power_curve": lambda: pl.plot_selected_graph(self, "actual_power_curve", self.column_cache),
#             "binned_power_curve": lambda: pl.plot_selected_graph(self, "binned_power_curve", self.column_cache),
#             "joint_distribution": lambda: pl.plot_selected_graph(self, "joint_distribution", self.column_cache),
#             "rotor_speed_graph": lambda: pl.plot_selected_graph(self, "rotor_speed_graph", self.column_cache),
#             "wind_frequency_histogram": lambda: pl.plot_selected_graph(self, "wind_frequency_histogram" ,self.column_cache),
#             "power_vs_temperature": lambda: pl.plot_selected_graph(self, "power_vs_temperature", self.column_cache),
#             "rotor_speed_vs_gearbox_temperature": lambda: pl.plot_selected_graph(self, "rotor_speed_vs_gearbox_temperature", self.column_cache),
#             "ambient_vs_nacelle_temperature": lambda: pl.plot_selected_graph(self, "ambient_vs_nacelle_temperature", self.column_cache),
#             "rotor_speed_vs_generator_speed": lambda: pl.plot_selected_graph(self, "rotor_speed_vs_generator_speed", self.column_cache),
#         }

#     def handle_canvas_click(self, event):
#         if event.inaxes:
#             clicked_on_artist = False
#             for artist in event.inaxes.get_children():
#                 contains, _ = artist.contains(event)
#                 if contains:
#                     clicked_on_artist = True
#                     break
#             if not clicked_on_artist:
#                 mplcursors.cursor().remove()
    
#     def _execute_plot_function(self):
#         """Execute the selected plot function"""
#         plot_functions = self._get_plot_functions()
#         plot_functions[self.selected_plot]()

#     def _configure_plot_appearance(self):
#         """Configure plot appearance settings"""
#         for ax in self.figure.get_axes():
#             ax.set_facecolor(self.background_color.currentText())
#             # Configure grid appearance based on background
#             if self.show_grid.isChecked():
#                 bg_color = self.background_color.currentText()
#                 if bg_color in ['white', 'lightgray']:
#                     ax.grid(True, color='gray', linestyle='-', alpha=0.3)
#                 elif bg_color == 'darkgray':
#                     ax.grid(True, color='lightgray', linestyle='-', alpha=0.5)
#                 elif bg_color == 'black':
#                     ax.grid(True, color='white', linestyle='-', alpha=0.3)
#                 else:
#                     ax.grid(True, color='gray', linestyle='-', alpha=0.3)

#     def _setup_plot_interactivity(self):
#         """Setup interactive features for the plot"""
#         for ax in self.figure.get_axes():
#             for line in ax.get_lines():
#                 cursor = mplcursors.cursor(line, hover=False)
#                 cursor.connect("add", self._format_cursor_annotation)
#             self.canvas.mpl_connect('button_press_event', self.handle_canvas_click)
    
#     def _format_cursor_annotation(self, sel):
#         """Format cursor annotation text"""
#         sel.annotation.set_text(f'{sel.artist.axes.get_xlabel()}: {sel.target[0]:.2f}\n{sel.artist.axes.get_ylabel()}: {sel.target[1]:.2f}') 
#         sel.annotation.get_bbox_patch().set(fc="white", alpha=0.85)
    
#     def _update_ui_components(self):
#         """Update UI components after plot update"""
#         self.update_statistics()
#         self.update_summary()
    
#     def set_data(self, df, file_name=None, turbine_name: Optional[str] = None) -> None:
#         """Set data for visualization with comprehensive validation"""
#         try:
#             # Validate input
#             if not self._validate_input_data(df):
#                 self._reset_data_state()
#                 return
#             # Set data attributes
#             self._set_data_attributes(df, file_name, turbine_name)
#             # Process data
#             self._populate_column_cache()
#             # Update UI
#             self._update_ui_after_data_load(file_name, turbine_name)
            
#         except Exception as e:
#             QMessageBox.critical(self, "Error", f"Failed to set data: {e}")
    
#     def _validate_input_data(self, df):
#         """Validate input data"""
#         if df is None or df.empty:
#             return False
#         if not isinstance(df, pd.DataFrame):
#             raise ValueError("Input must be a pandas DataFrame")
#         return True
    
#     def _reset_data_state(self):
#         """Reset data state when no valid data provided"""
#         self.data = pd.DataFrame()
#         self.file_name = None
#         self.turbine_id = None
#         self.setWindowTitle("Wind Data Analysis Tool")
    
#     def _set_data_attributes(self, df, file_name, turbine_name):
#         """Set data-related attributes"""
#         self.data = df
#         self.file_name = file_name
#         self.turbine_id = turbine_name
#         self.column_cache.clear()

#     def _update_ui_after_data_load(self, file_name, turbine_name):
#         """Update UI after data loading"""
#         self.update_plot_signal.emit()
        
#         # Update window title
#         if turbine_name:
#             self.setWindowTitle(f"Visualizing Turbine: {turbine_name}")
#         elif file_name:
#             self.setWindowTitle(f"Wind Data Analysis Tool - {file_name}")
#         else:
#             self.setWindowTitle("Wind Data Analysis Tool")

#     def export_plot(self):
#         file_name, _ = QFileDialog.getSaveFileName(self, "Export Plot", "", "PNG Files (*.png);;PDF Files (*.pdf)")
#         if file_name:
#             self.figure.savefig(file_name, bbox_inches='tight', dpi=300)
    
#     def generate_report(self):
#         generator = EnhancedReportGenerator(self)
#         generator.generate_report()
    
#     def export_data(self):
#         file_name, _ = QFileDialog.getSaveFileName(self, "Export Data", "", "CSV Files (*.csv)")
#         if file_name and self.data is not None:
#             self.data.to_csv(file_name)

#     def show_binned_power_curve_with_table(self):
#         self.selected_plot = "binned_power_curve"
        
#         # Setup table first if not exists
#         if not hasattr(self, 'bin_table_dock'):
#             self.bin_table_dock = QDockWidget("Bin Records", self)
#             self.bin_table_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)

#             self.bin_table = QTableWidget()
#             self.bin_table.setColumnCount(4)
#             self.bin_table.setHorizontalHeaderLabels(["Bin Range", "Mean Power", "Std Dev", "Count"])
#             self.bin_table.horizontalHeader().setStretchLastSection(True)
#             self.bin_table.setAlternatingRowColors(True)

#             bin_table_widget = QWidget()
#             bin_table_layout = QVBoxLayout(bin_table_widget)

#             export_button = QPushButton("Export Bin Data")
#             export_button.clicked.connect(lambda: self.export_bin_table(self.bin_table))

#             bin_table_layout.addWidget(self.bin_table)
#             bin_table_layout.addWidget(export_button)

#             self.bin_table_dock.setWidget(bin_table_widget)
#             self.addDockWidget(Qt.BottomDockWidgetArea, self.bin_table_dock)
#             self.bin_table_dock.setVisible(False)

#         # Update plot SYNCHRONOUSLY (direct call)
#         self.update_plot()
#         # Show table immediately after plot is ready
#         self.bin_table_dock.setVisible(True)
#         self.bin_table_dock.raise_()
#         # Show percentage bands dock if enabled
#         if hasattr(self, 'enable_percentage_bands') and self.enable_percentage_bands.isChecked():
#             self.percentage_bands_dock.setVisible(True)
#             self.percentage_bands_dock.raise_()
#         else:
#             self.percentage_bands_dock.setVisible(False)

#     def export_bin_table(self, table):
#         file_name, _ = QFileDialog.getSaveFileName(self, "Export Bin Data", "", "CSV Files (*.csv)")
#         if file_name:
#             data = []
#             for row in range(table.rowCount()):
#                 row_data = [table.item(row, col).text() for col in range(table.columnCount())]
#                 data.append(row_data)
#             df = pd.DataFrame(data, columns=["Bin Range", "Mean Power", "Std Dev", "Count"])
#             df.to_csv(file_name, index=False)
#             QMessageBox.information(self, "Success", f"Bin data exported to:\n{file_name}")

#     def show_removed_data_table(self):
#         if not hasattr(self, 'removed_data_dock') \
#            and self.remove_negative_power.isChecked()\
#            and self.removed_data is not None \
#            and not self.removed_data.empty:
#             self.removed_data_dock = QDockWidget("Removed Data", self)
#             self.removed_data_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
#             self.removed_data_table = QTableWidget()
#             self.removed_data_table.setColumnCount(len(self.removed_data.columns))
#             self.removed_data_table.setHorizontalHeaderLabels(self.removed_data.columns)
#             self.removed_data_table.setRowCount(len(self.removed_data))
#             for row in range(len(self.removed_data)):
#                 for col, value in enumerate(self.removed_data.iloc[row]):
#                     self.removed_data_table.setItem(row, col, QTableWidgetItem(str(value)))
#             self.removed_data_table.horizontalHeader().setStretchLastSection(True)
#             self.removed_data_table.setAlternatingRowColors(True)
#             removed_data_widget = QWidget()
#             removed_data_layout = QVBoxLayout(removed_data_widget)
#             removed_data_layout.addWidget(self.removed_data_table)
#             export_button = QPushButton("Export Removed Data")
#             export_button.clicked.connect(lambda: self.export_removed_data(self.removed_data_table))
#             removed_data_layout.addWidget(export_button)
#             self.removed_data_dock.setWidget(removed_data_widget)
#             self.addDockWidget(Qt.BottomDockWidgetArea, self.removed_data_dock)
#         if hasattr(self, 'removed_data_dock'):
#             visible = ((self.remove_negative_power.isChecked())
#                        and self.removed_data is not None
#                        and not self.removed_data.empty)
#             self.removed_data_dock.setVisible(visible)
#             if self.removed_data_dock.isVisible():
#                  self.removed_data_table.setRowCount(len(self.removed_data))
#                  for row in range(len(self.removed_data)):
#                      for col, value in enumerate(self.removed_data.iloc[row]):
#                          self.removed_data_table.setItem(row, col, QTableWidgetItem(str(value)))
#                  self.removed_data_table.resizeColumnsToContents()
    
#     def handle_standard_power_curve_toggle(self):
#         # Only upload client curve when checkbox is checked AND we don't have data yet
#         if self.show_standard_power_curve.isChecked() and not hasattr(self, "client_power_data"):
#             self.upload_client_power_curve()
        
#         # Always update plot (with or without client curve overlay)
#         self.update_plot_signal.emit()

#     def export_removed_data(self, table):
#         file_name, _ = QFileDialog.getSaveFileName(self, "Export Removed Data", "", "CSV Files (*.csv)")
#         if file_name:
#             data = []
#             headers = [table.horizontalHeaderItem(col).text() for col in range(table.columnCount())]
#             for row in range(table.rowCount()):
#                 row_data = [table.item(row, col).text() for col in range(table.columnCount())]
#                 data.append(row_data)
#             df = pd.DataFrame(data, columns=headers)
#             df.to_csv(file_name, index=False)
#             QMessageBox.information(self, "Success", f"Removed data exported to:\n{file_name}")

#     def upload_client_power_curve(self):
#         file_name, _ = QFileDialog.getOpenFileName(self, "Upload Client Power Curve", "", "Excel Files (*.xlsx);;CSV Files (*.csv)")
#         if file_name:
#             try:
#                 if file_name.endswith('.xlsx'):
#                     df = pd.read_excel(file_name)
#                 else:
#                     df = pd.read_csv(file_name)
#                 if 'wind_speed' not in df.columns or 'power' not in df.columns:
#                     raise ValueError("File must contain 'wind_speed' and 'power' columns.")
#                 df = df.sort_values('wind_speed')
#                 self.client_power_data = df
#                 self.standard_power_data = df
#                 min_ws = df['wind_speed'].min()
#                 max_ws = df['wind_speed'].max()
#                 self.client_power_interp = interp1d(df['wind_speed'], df['power'], kind='linear', fill_value='extrapolate')
#                 interp_ws = np.arange(min_ws, max_ws + 0.1, 0.1)
#                 interp_power = self.client_power_interp(interp_ws)
#                 self.interpolated_client_power = pd.DataFrame({'wind_speed': interp_ws, 'power': interp_power})
#                 tbl = self.standard_data_table
#                 tbl.setColumnCount(2)
#                 tbl.setHorizontalHeaderLabels(["wind_speed", "power"])
#                 tbl.setRowCount(len(df))
#                 for r, row in df.iterrows():
#                     tbl.setItem(r, 0, QTableWidgetItem(str(row['wind_speed'])))
#                     tbl.setItem(r, 1, QTableWidgetItem(str(row['power'])))
#                 self.standard_data_dock.setVisible(True)
#             except Exception as e:
#                 self.handle_errors(f"Error loading client power curve: {e}")

#     def show_wind_frequency_table(self):
#         if not hasattr(self, 'frequency_table_dock'):
#             self.frequency_table_dock = QDockWidget("Wind Frequency Data", self)
#             self.frequency_table_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)

#             self.frequency_table = QTableWidget()
#             self.frequency_table.setAlternatingRowColors(True)

#             freq_table_widget = QWidget()
#             freq_table_layout = QVBoxLayout(freq_table_widget)

#             export_button = QPushButton("Export Frequency Data")
#             export_button.clicked.connect(self.export_frequency_table)

#             freq_table_layout.addWidget(self.frequency_table)
#             freq_table_layout.addWidget(export_button)

#             self.frequency_table_dock.setWidget(freq_table_widget)
#             self.addDockWidget(Qt.BottomDockWidgetArea, self.frequency_table_dock)
        
#         self.frequency_table_dock.setVisible(True)
#         self.frequency_table_dock.raise_()

#     def _update_frequency_table(self):
#         if not hasattr(self, 'frequency_data'):
#             return
        
#         freq_data = self.frequency_data
        
#         # Set up table
#         self.frequency_table.setRowCount(len(freq_data.index))
#         self.frequency_table.setColumnCount(len(freq_data.columns) + 1)
        
#         headers = ["Direction"] + [str(col) for col in freq_data.columns]
#         self.frequency_table.setHorizontalHeaderLabels(headers)
        
#         # Fill table
#         for row, dir_bin in enumerate(freq_data.index):
#             self.frequency_table.setItem(row, 0, QTableWidgetItem(str(dir_bin)))
#             for col, ws_bin in enumerate(freq_data.columns):
#                 value = freq_data.loc[dir_bin, ws_bin]
#                 if hasattr(self, 'show_frequency_percentage') and self.show_frequency_percentage.isChecked():
#                     self.frequency_table.setItem(row, col + 1, QTableWidgetItem(f"{value:.2f}%"))
#                 else:
#                     self.frequency_table.setItem(row, col + 1, QTableWidgetItem(str(int(value))))

#     def export_frequency_table(self):
#         file_name, _ = QFileDialog.getSaveFileName(self, "Export Frequency Data", "", "CSV Files (*.csv)")
#         if file_name and hasattr(self, 'frequency_data'):
#             self.frequency_data.to_csv(file_name)
#             QMessageBox.information(self, "Success", f"Frequency data exported to:\n{file_name}")
    
#     def set_and_update_with_table(self, plot_name):
#         self.selected_plot = plot_name
#         self.update_plot_signal.emit()
#         if plot_name == "wind_frequency_histogram":
#             self.show_wind_frequency_table()
            
#     def export_percentage_bands(self):
#         file_name, _ = QFileDialog.getSaveFileName(self, "Export Percentage Bands Data", "", "CSV Files (*.csv)")
#         if file_name:
#             data = []
#             headers = [self.percentage_bands_table.horizontalHeaderItem(col).text() for col in range(self.percentage_bands_table.columnCount())]
#             for row in range(self.percentage_bands_table.rowCount()):
#                 row_data = [self.percentage_bands_table.item(row, col).text() for col in range(self.percentage_bands_table.columnCount())]
#                 data.append(row_data)
#             df = pd.DataFrame(data, columns=headers)
#             df.to_csv(file_name, index=False)
#             QMessageBox.information(self, "Success", f"Percentage bands data exported to:\n{file_name}")

#     def handle_errors(self, message: str):
#         QMessageBox.critical(self, "Error", message)
#         print(message)

#     def closeEvent(self, event):
#         plt.close('all')
#         gc.collect()
#         event.accept()

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
import pandas as pd
import numpy as np
import time, traceback, gc, mplcursors
from models import scada_utils as su
from utils.collapsible_prop import CollapsibleSection
from utils.datetime_utils import get_datetime_info
from views.visualization_components.report_gen import EnhancedReportGenerator
from . import plotting_logic as pl
from typing import Optional
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

class VisualizationWindow(QMainWindow):
    update_plot_signal = pyqtSignal()
    generate_report_signal = pyqtSignal()  # Define the signal for report generation

    def __init__(self, data=None, turbine_name=None, parent=None, project_id=None):
        super().__init__(parent)
        
        # Set window title with turbine name
        if turbine_name:
            self.setWindowTitle(f"Visualization Window: {turbine_name}")
        else:
            self.setWindowTitle("Wind Data Visualization Tool")
        self.setGeometry(100, 100, 1400, 800)
        self.setFont(QFont("Time New Roman", 10))

        # Initialize data attributes
        self.data = data if data is not None else pd.DataFrame()
        self.filtered_df = None
        self.selected_plot = None
        self.removed_data = None
        self.column_cache = {}
        self.standard_power_data = None
        self.client_power_data = None
        self.client_power_interp = None
        self.interpolated_client_power = None
        self.wind_speed_threshold = None
        self.wind_speed_threshold_history = []
            # Store project_id
        self.project_id = project_id

        # SDI: Independent window
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        # Initialize UI components FIRST
        self._init_ui_components()
        
        # Setup UI
        self.apply_styles()
        self.process_data()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.init_ui()
        
        # Process data AFTER UI is created
        if not self.data.empty:
            self._populate_column_cache()
        
        # Setup docks and connect signals
        self._setup_all_docks()
        self.connect_signals()
        # Initial plot setup
        self.figure.add_subplot(111).text(0.5, 0.5, 'No data loaded', ha='center', va='center')

    def _populate_column_cache(self):
        """Populate column cache without calling UI methods"""
        column_params = ["wind_speed", "nacelle_direction", "ambient_temp", "timestamp", 
            "power", "rotor_speed", "nacelle_temp", "gearbox_temp", 
            "generator_speed", "generator_temp" ]
        
        for param in column_params:
            matched_columns = su.find_matching_columns(self.data, param)
            self.column_cache[param] = matched_columns[0] if matched_columns else None

    def _init_ui_components(self):
        """Initialize all UI components"""
        # Create figure and canvas
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        
        # Initialize combo boxes
        self.wind_speed_col = QComboBox(self)
        self.wind_dir_col = QComboBox(self)
        self.temp_col = QComboBox(self)
               
        self.percentage_input = QLineEdit()
        self.percentage_input.setText("5.0")
        self.percentage_input.setEnabled(False)
        self.percentage_input.setStyleSheet("color: black; background-color: white;")
        # Initialize checkboxes
        self._init_checkboxes()
        # Initialize other components
        self.background_color = QComboBox()
        self.background_color.addItems(["white", "lightgray", "darkgray", "black"])
        
        self._init_windrose_components()
    
    def _init_checkboxes(self):
        """Initialize all checkbox components"""
        checkboxes = {
            'show_grid': "Show Grid",
            'show_legend': "Show Legend",
            'enable_iec_binning': "Enable IEC Binning",
            'show_std_dev': "Show Std Dev",
            'show_original_values': "Show Original Values",
            'remove_negative_power': "Remove Negative Power (≤ 0)",
            'show_standard_power_curve': "Show Site Based Power Curve",
            'enable_percentage_bands': "Enable ±n% Percentage Bands",
            'show_plus_percentage': "Show +n% Curve",
            'show_minus_percentage': "Show -n% Curve",
            'fix_sample_size': "Fix Sample Size = 600",
            'show_frequency_percentage': "Show Frequency as %"
        }

        for attr_name, text in checkboxes.items():
            setattr(self, attr_name, QCheckBox(text))
    
        # Set specific states
        self.show_grid.setChecked(True)
        self.show_plus_percentage.setChecked(False)
        self.show_plus_percentage.setVisible(False)
        self.show_minus_percentage.setChecked(False) 
        self.show_minus_percentage.setVisible(False)
        
    def _init_windrose_components(self):
        """Initialize windrose sector components"""
        self.windrose_checkboxes = {}
        self.selected_sectors = 16
        
        for sector in [8, 12, 16, 24, 36]:
            checkbox = QCheckBox(f"{sector:02d} Sectors")
            setattr(self, f'windrose_sectors_{sector:02d}', checkbox)
            self.windrose_checkboxes[sector] = checkbox
        
        self.windrose_sectors_16.setChecked(True)

    def _setup_all_docks(self):
        """Setup all dock widgets"""
        self.setup_command_center()
        self.setup_statistics_table()
        self._setup_summary_dock()
        self._setup_data_docks()
        self._setup_status_bar()
    
    def _setup_summary_dock(self):
        """Setup summary dock widget"""
        self.summary_dock = QDockWidget("Summary", self)
        self.summary_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(2)
        self.summary_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.summary_table.horizontalHeader().setStretchLastSection(True)
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.setFont(QFont("Time Roman New", 10))
        
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        summary_layout.addWidget(self.summary_table)
        self.summary_dock.setWidget(summary_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.summary_dock)

    def _setup_data_docks(self):
        """Setup data-related dock widgets"""
        dock_configs = [
            ("Standard Power Data", "standard_data_dock", "standard_data_table"),
            ("Deviation Data", "deviation_dock", "deviation_table"),
            ("Percentage Bands Data", "percentage_bands_dock", "percentage_bands_table")
        ]
        
        for title, dock_attr, table_attr in dock_configs:
            dock = QDockWidget(title, self)
            table = QTableWidget()
            
            if title == "Percentage Bands Data":
                widget = QWidget()
                layout = QVBoxLayout(widget)
                layout.addWidget(table)
                
                export_btn = QPushButton("Export Percentage Bands")
                export_btn.clicked.connect(self.export_percentage_bands)
                layout.addWidget(export_btn)
                dock.setWidget(widget)
            else:
                dock.setWidget(table)
            
            dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
            self.addDockWidget(Qt.RightDockWidgetArea, dock)
            dock.setVisible(False)
            
            setattr(self, dock_attr, dock)
            setattr(self, table_attr, table)

    def _setup_status_bar(self):
        """Setup status bar"""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
    
    def connect_signals(self):
        """Connect all UI signals to their handlers"""
        try:
            # Core signals
            signal_connections = [
                (self.update_plot_signal, self.update_plot),
                (self.generate_report_signal, self.generate_report),
                (self.background_color.currentIndexChanged, self.update_plot_signal.emit),
            ]
            # Checkbox signals
            checkbox_signals = [
                'enable_iec_binning', 'remove_negative_power', 'show_grid', 'show_legend',
                'show_std_dev', 'show_original_values', 'fix_sample_size',
                'show_plus_percentage', 'show_minus_percentage','show_frequency_percentage'
            ]
            for checkbox_name in checkbox_signals:
                checkbox = getattr(self, checkbox_name)
                signal_connections.append((checkbox.stateChanged, self.update_plot_signal.emit))
            # Special checkbox connections
            signal_connections.extend([
                (self.remove_negative_power.stateChanged, self.show_removed_data_table),
                (self.show_standard_power_curve.stateChanged, self.handle_standard_power_curve_toggle),
                (self.fix_sample_size.stateChanged, self.show_removed_data_table),
                (self.enable_percentage_bands.stateChanged, self.toggle_percentage_input),
                (self.percentage_input.textChanged, self.update_plot_signal.emit),
                (self.wind_speed_col.currentIndexChanged, self.update_plot_signal.emit),
                (self.wind_dir_col.currentIndexChanged, self.update_plot_signal.emit),
                (self.temp_col.currentIndexChanged, self.update_plot_signal.emit),
            ])
            
            # Connect all signals
            for signal, slot in signal_connections:
                signal.connect(slot)
            
            # Connect windrose sector signals
            self._connect_windrose_signals()
            
        except Exception as e:
            self.handle_errors(f"Error connecting signals: {str(e)}\n{traceback.format_exc()}")

    def _connect_windrose_signals(self):
        """Connect windrose sector checkbox signals"""
        for sector, checkbox in self.windrose_checkboxes.items():
            checkbox.stateChanged.connect(
                lambda state, cb=checkbox: self.on_windrose_sector_changed(cb)
            )
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f7f7f7; }
            QGroupBox { font-weight: bold; border: 2px solid #d3d3d3; border-radius: 8px; margin-top: 15px; padding-top: 10px; background-color: #ffffff;}
            QGroupBox::title {subcontrol-origin: margin; subcontrol-position: top left; padding: 4px 12px; background-color: #3498DB; color: white; border-radius: 4px; left: 10px; top: -8px;}
            QCheckBox, QRadioButton { spacing: 5px; font-size: 11px; max-width: 200px; border: none; background-color: transparent; margin: 5px; }
            QPushButton { background-color: #0078d7; color: white; border: none; padding: 6px 12px; border-radius: 4px; max-width: 180px; font-size: 11px;}
            QPushButton:hover { background-color: #005a9e; }
            QComboBox, QLineEdit { padding: 4px; border: 1px solid #ccc; border-radius: 4px; background-color: #ffffff; color: black; max-width: 150px; font-size: 11px;}  """)

    def update_turbine_title(self, turbine: str) -> None:
        self.setWindowTitle(f"Visualizing Turbine - {turbine}")

    # def process_data(self):
    #     if self.data.empty:
    #         self.populate_comboboxes()
    #         return
    #     try:
    #         timestamp_col = self.get_cached_columns("timestamp")
    #         if timestamp_col and timestamp_col in self.data.columns:
    #             self.data[timestamp_col] = pd.to_datetime(
    #                 self.data[timestamp_col], errors='coerce')
    #             self.data.dropna(subset=[timestamp_col], inplace=True)
    #         self.populate_comboboxes()
    #     except Exception as e:
    #         self.handle_errors(f"Error processing data:\n{e}\n\n{traceback.format_exc()}")

    def process_data(self):
        if self.data.empty:
            self.populate_comboboxes()
            return
        try:
            timestamp_col = self.get_cached_columns("timestamp")
            if timestamp_col and timestamp_col in self.data.columns:
                # FIX: Add format and dayfirst parameter
                self.data[timestamp_col] = pd.to_datetime(
                    self.data[timestamp_col], 
                    format='%d/%m/%Y %H:%M',
                    dayfirst=True,
                    errors='coerce'
                )
                self.data.dropna(subset=[timestamp_col], inplace=True)
            self.populate_comboboxes()
        except Exception as e:
            self.handle_errors(f"Error processing data:\n{e}\n\n{traceback.format_exc()}")


    def get_cached_columns(self, param):
        if param not in self.column_cache:
            matched_columns = su.find_matching_columns(self.data, param)
            self.column_cache[param] = matched_columns[0] if matched_columns else None
        return self.column_cache[param]
    
    def populate_comboboxes(self):
        self.wind_speed_col.clear()
        self.wind_dir_col.clear()
        self.temp_col.clear()
        if self.data.empty:
            return
        
        # Parameter display names mapping
        PARAMETER_DISPLAY_NAMES = {
            'wind_speed': 'Wind Speed (m/s)',
            'nacelle_direction': 'Wind Direction (°)',
        }
        
        def get_display_name(param_key):
            return PARAMETER_DISPLAY_NAMES.get(param_key, param_key.replace('_', ' ').title())
        
        wind_speed_cols = su.find_matching_columns(self.data, "wind_speed") or []
        wind_dir_cols = su.find_matching_columns(self.data, "nacelle_direction") or []
        ambient_temp_cols = su.find_matching_columns(self.data, "ambient_temp") or []
        
        # Add items with display names but store original column names as data
        for col in wind_speed_cols:
            self.wind_speed_col.addItem(get_display_name('wind_speed'), col)
        for col in wind_dir_cols:
            self.wind_dir_col.addItem(get_display_name('nacelle_direction'), col)
        for col in ambient_temp_cols:
            self.temp_col.addItem(get_display_name('ambient_temp'), col)

    def init_ui(self):
        splitter = QSplitter(Qt.Horizontal, self.central_widget)
        plot_panel = QWidget()
        plot_layout = QVBoxLayout(plot_panel)
        self.toolbar = NavigationToolbar(self.canvas, plot_panel)
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        splitter.addWidget(plot_panel)
        splitter.setSizes([350, 1050])
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.addWidget(splitter)
        self.central_widget.setLayout(main_layout)

    def create_data_selection_group(self):
        """Create the data selection UI group with optimized date handling and enable/disable checkboxes"""
        content_widget = QWidget()
        layout = QGridLayout(content_widget)
        layout.setVerticalSpacing(8)
        layout.setHorizontalSpacing(15)
        # Get date range from data - OPTIMIZED
        min_date, max_date, min_time, max_time, timestamp_col = get_datetime_info(self.data)
        # Create enable/disable checkboxes
        self.enable_date_filter = QCheckBox("Enable Date Filter")
        self.enable_date_filter.setChecked(True)  # Default enabled
        self.enable_date_filter.stateChanged.connect(self._toggle_date_filter)
        layout.addWidget(self.enable_date_filter, 0, 0, 1, 2)
        self.enable_time_filter = QCheckBox("Enable Time Filter")
        self.enable_time_filter.setChecked(False)  # Default disabled
        self.enable_time_filter.stateChanged.connect(self._toggle_time_filter)
        layout.addWidget(self.enable_time_filter, 1, 0, 1, 2)
        # Get date range from data - FIXED
        min_date, max_date, min_time, max_time, timestamp_col = get_datetime_info(self.data)
        # Use actual data dates or fallback
        min_date_str = min_date
        max_date_str = max_date
        min_time_str = min_time if min_time else "00:00"
        max_time_str = max_time if max_time else "23:59"
        # Date selection widgets
        self.start_date_label = QLabel("Start Date")
        layout.addWidget(self.start_date_label, 2, 0)
        self.start_date_only = QLineEdit(min_date_str)
        self.start_date_only.setPlaceholderText("DD-MM-YYYY")
        layout.addWidget(self.start_date_only, 2, 1)
        self.end_date_label = QLabel("End Date")
        layout.addWidget(self.end_date_label, 3, 0)
        self.end_date_only = QLineEdit(max_date_str)
        self.end_date_only.setPlaceholderText("DD-MM-YYYY")
        layout.addWidget(self.end_date_only, 3, 1)
        
        # Time selection widgets
        self.start_time_label = QLabel(f"From Time ({min_time_str}):")
        layout.addWidget(self.start_time_label, 4, 0)
        self.start_time_only = QLineEdit(min_time_str)
        self.start_time_only.setPlaceholderText("HH:MM")
        layout.addWidget(self.start_time_only, 4, 1)
        
        self.end_time_label = QLabel(f"To Time ({max_time_str}):")
        layout.addWidget(self.end_time_label, 5, 0)
        self.end_time_only = QLineEdit(max_time_str)
        self.end_time_only.setPlaceholderText("HH:MM")
        layout.addWidget(self.end_time_only, 5, 1)
        
        # Initially set time filter widgets visibility
        self._toggle_time_filter()
        
        # Background color
        layout.addWidget(QLabel("Background Color:"), 6, 0)
        layout.addWidget(self.background_color, 6, 1)
        # Wind parameters
        layout.addWidget(QLabel("Wind Speed:"), 7, 0, Qt.AlignLeft)
        layout.addWidget(self.wind_speed_col, 7, 1)
        layout.addWidget(QLabel("Wind Direction:"), 8, 0, Qt.AlignLeft)
        layout.addWidget(self.wind_dir_col, 8, 1)


        # Update button
        update_button = QPushButton("Update Plot")
        update_button.clicked.connect(self.update_plot_signal.emit)
        layout.addWidget(update_button, 10, 0, 1, 2, Qt.AlignCenter)
        # Fix sample size checkbox
        # layout.addWidget(self.fix_sample_size, 11, 0, 1, 2)
        section = CollapsibleSection("Data Selection and Filtering", content_widget, expanded=True)
        return section

    def _toggle_date_filter(self):
        """Toggle date filter widgets visibility and state"""
        enabled = self.enable_date_filter.isChecked()
        # Show/hide date widgets
        self.start_date_label.setVisible(enabled)
        self.start_date_only.setVisible(enabled)
        self.end_date_label.setVisible(enabled)
        self.end_date_only.setVisible(enabled)
        # Enable/disable date widgets
        self.start_date_label.setEnabled(enabled)
        self.start_date_only.setEnabled(enabled)
        self.end_date_label.setEnabled(enabled)
        self.end_date_only.setEnabled(enabled)
        # Update styling to show disabled state
        style = "" if enabled else "color: gray;"
        self.start_date_label.setStyleSheet(style)
        self.end_date_label.setStyleSheet(style)
 
    def _toggle_time_filter(self):
        """Toggle time filter widgets visibility and state"""
        enabled = self.enable_time_filter.isChecked()
        # Show/hide time widgets
        self.start_time_label.setVisible(enabled)
        self.start_time_only.setVisible(enabled)
        self.end_time_label.setVisible(enabled)
        self.end_time_only.setVisible(enabled)
        # Enable/disable time widgets
        self.start_time_label.setEnabled(enabled)
        self.start_time_only.setEnabled(enabled)
        self.end_time_label.setEnabled(enabled)
        self.end_time_only.setEnabled(enabled)
        
    def create_windrose_options_group(self):
        content_widget = QWidget()
        layout = QGridLayout(content_widget)
        layout.setVerticalSpacing(10)
        layout.setHorizontalSpacing(15)
        # Set default to 16 sectors
        self.windrose_sectors_16.setChecked(True)
        # Add to layout
        layout.addWidget(self.windrose_sectors_08, 0, 0)
        layout.addWidget(self.windrose_sectors_12, 0, 1)
        layout.addWidget(self.windrose_sectors_16, 1, 0)
        layout.addWidget(self.windrose_sectors_24, 1, 1)
        layout.addWidget(self.windrose_sectors_36, 2, 0)
        # Connect signals for mutual exclusivity
        self.windrose_sectors_08.stateChanged.connect(lambda: self.on_windrose_sector_changed(self.windrose_sectors_08))
        self.windrose_sectors_12.stateChanged.connect(lambda: self.on_windrose_sector_changed(self.windrose_sectors_12))
        self.windrose_sectors_16.stateChanged.connect(lambda: self.on_windrose_sector_changed(self.windrose_sectors_16))
        self.windrose_sectors_24.stateChanged.connect(lambda: self.on_windrose_sector_changed(self.windrose_sectors_24))
        self.windrose_sectors_36.stateChanged.connect(lambda: self.on_windrose_sector_changed(self.windrose_sectors_36))
        section = CollapsibleSection("Windrose Options", content_widget)
        return section

    def on_windrose_sector_changed(self, changed_checkbox):
        """Handle windrose sector selection with mutual exclusivity"""
        if not changed_checkbox.isChecked():
            # Prevent unchecking if no others are checked
            if not any(cb.isChecked() for cb in self.windrose_checkboxes.values()):
                changed_checkbox.setChecked(True)
            return
        
        # Uncheck all others and update selected sectors
        for sector, checkbox in self.windrose_checkboxes.items():
            if checkbox != changed_checkbox:
                checkbox.setChecked(False)
            elif checkbox.isChecked():
                self.selected_sectors = sector
        
        self.update_plot_signal.emit()
    
    def toggle_percentage_input(self):
        enabled = self.enable_percentage_bands.isChecked()
        
        self.percentage_input.setEnabled(enabled)
        self.show_plus_percentage.setEnabled(enabled)
        self.show_minus_percentage.setEnabled(enabled)
        
        # Show/hide the checkboxes
        self.show_plus_percentage.setVisible(enabled)
        self.show_minus_percentage.setVisible(enabled)
        
        self.update_plot_signal.emit()

    def ensure_exclusive_windrose_sector(self, changed_checkbox):
        if changed_checkbox.isChecked():
            for checkbox in [self.windrose_sectors_08, self.windrose_sectors_12, self.windrose_sectors_16, 
                            self.windrose_sectors_24, self.windrose_sectors_36]:
                if checkbox != changed_checkbox:
                    checkbox.setChecked(False)
            if changed_checkbox == self.windrose_sectors_08:
                self.selected_sectors = 8
            if changed_checkbox == self.windrose_sectors_12:
                self.selected_sectors = 12
            elif changed_checkbox == self.windrose_sectors_16:
                self.selected_sectors = 16
            elif changed_checkbox == self.windrose_sectors_24:
                self.selected_sectors = 24
            elif changed_checkbox == self.windrose_sectors_36:
                self.selected_sectors = 36
            self.update_plot_signal.emit()
        else:
            if not any(checkbox.isChecked() for checkbox in [self.windrose_sectors_08, self.windrose_sectors_12, self.windrose_sectors_16, self.windrose_sectors_24, 
                                                            self.windrose_sectors_36]):
                changed_checkbox.setChecked(True)
    
    def setup_command_center(self):
        self.command_center = QDockWidget("Command Center", self)
        self.command_center.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.command_center.setMinimumWidth(250)
        self.command_center.setMaximumWidth(350)

        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        # Data Selection Section
        data_selection_section = self.create_data_selection_group()
        scroll_layout.addWidget(data_selection_section)
        # Plot Options Section
        plot_options_section = self.create_plot_options_group()
        scroll_layout.addWidget(plot_options_section)
        # Windrose Options Section
        windrose_options_section = self.create_windrose_options_group()
        scroll_layout.addWidget(windrose_options_section)
        # Wind Analysis Section
        wind_content = QWidget()
        wind_layout = QVBoxLayout(wind_content)
        btn_wind_rose = QPushButton("Wind Rose")
        btn_wind_speed = QPushButton("Wind Speed Distribution")
        btn_turbulence = QPushButton("Turbulence Intensity")
        btn_wind_frequency = QPushButton("Wind Frequency Histogram")
        wind_layout.addWidget(btn_wind_rose)
        wind_layout.addWidget(btn_wind_speed)
        wind_layout.addWidget(btn_turbulence)
        wind_layout.addWidget(btn_wind_frequency)
        wind_section = CollapsibleSection("Wind Analysis", wind_content)
        scroll_layout.addWidget(wind_section)
        # Performance & Power Section
        power_content = QWidget()
        power_layout = QVBoxLayout(power_content)
        btn_power_curve = QPushButton("Site Based Power Curve")
        btn_actual_power_curve = QPushButton("Actual Power Curve")
        btn_binned_power_curve = QPushButton("Binned Power Curve")
        btn_rotor_speed = QPushButton("Rotor Speed Graph")
        btn_rotor_vs_gen = QPushButton("Rotor vs Generator Speed")
        power_layout.addWidget(btn_power_curve)
        power_layout.addWidget(btn_actual_power_curve)
        power_layout.addWidget(btn_binned_power_curve)
        power_layout.addWidget(btn_rotor_speed)
        power_layout.addWidget(btn_rotor_vs_gen)
        power_section = CollapsibleSection("Performance & Power", power_content)
        scroll_layout.addWidget(power_section)

        # Other Section
        other_content = QWidget()
        other_layout = QVBoxLayout(other_content)
        btn_joint = QPushButton("Joint Distribution")
        btn_generate_report = QPushButton("Generate Report")

        other_layout.addWidget(btn_joint)
        other_layout.addWidget(btn_generate_report)
        other_section = CollapsibleSection("Other", other_content)
        scroll_layout.addWidget(other_section)

        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        self.command_center.setWidget(scroll_area)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.command_center)

        btn_wind_rose.clicked.connect(lambda: self.set_and_update("wind_rose"))
        btn_wind_speed.clicked.connect(lambda: self.set_and_update("wind_speed_distribution"))
        btn_turbulence.clicked.connect(lambda: self.set_and_update("turbulence_intensity"))
        btn_wind_frequency.clicked.connect(lambda: self.set_and_update("wind_frequency_histogram"))
        btn_power_curve.clicked.connect(lambda: self.set_and_update("power_curve"))
        btn_actual_power_curve.clicked.connect(lambda: self.set_and_update("actual_power_curve"))
        btn_binned_power_curve.clicked.connect(self.show_binned_power_curve_with_table)
        btn_rotor_speed.clicked.connect(lambda: self.set_and_update("rotor_speed_graph"))
        btn_rotor_vs_gen.clicked.connect(lambda: self.set_and_update("rotor_speed_vs_generator_speed"))
        btn_joint.clicked.connect(lambda: self.set_and_update("joint_distribution"))
        btn_generate_report.clicked.connect(self.generate_report_signal.emit)
        btn_wind_frequency.clicked.connect(lambda: self.set_and_update_with_table("wind_frequency_histogram"))

    def _create_analysis_sections(self):
        """Create all analysis button sections"""
        sections = []
        
        # Wind Analysis Section
        wind_buttons = [
            ("Wind Rose", "wind_rose"),
            ("Wind Speed Distribution", "wind_speed_distribution"),
            ("Turbulence Intensity", "turbulence_intensity"),
            ("Wind Frequency", "wind_frequency_histogram")
        ]
        sections.append(self._create_button_section("Wind Analysis", wind_buttons))
        # Performance & Power Section
        power_buttons = [
            ("Site-Based Power Curve", "power_curve"),
            ("Actual Power Curve", "actual_power_curve"),
            ("Binned Power Curve", lambda: self.show_binned_power_curve_with_table()),
            ("Rotor Speed Graph", "rotor_speed_graph"),
            ("Rotor vs Generator Speed", "rotor_speed_vs_generator_speed")
        ]
        sections.append(self._create_button_section("Performance & Power", power_buttons))

        # Other Section
        other_buttons = [
            ("Joint Distribution", "joint_distribution"),
            ("Generate Report", lambda: self.generate_report_signal.emit())
        ]
        sections.append(self._create_button_section("Other", other_buttons))
        
        return sections

    def _create_button_section(self, title, buttons):
        """Create a collapsible section with buttons"""
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        for button_text, action in buttons:
            btn = QPushButton(button_text)
            if callable(action):
                btn.clicked.connect(action)
            else:
                btn.clicked.connect(lambda checked, plot=action: self.set_and_update(plot))
            layout.addWidget(btn)
        
        return CollapsibleSection(title, content_widget)
    
    def create_plot_options_group(self):
        """Create plot options control group"""
        content_widget = QWidget()
        layout = QGridLayout(content_widget)
        layout.setVerticalSpacing(8)
        layout.setHorizontalSpacing(10)
        # Row 1-2: Display options
        layout.addWidget(self.show_grid, 0, 0, 1, 2)
        layout.addWidget(self.show_legend, 1, 0, 1, 2)   
        # Row 3-4: IEC and std dev
        layout.addWidget(self.enable_iec_binning, 2, 0, 1, 2)
        layout.addWidget(self.remove_negative_power, 3, 0, 1, 2)
        layout.addWidget(self.show_std_dev, 4, 0, 1, 2)
        # Row 5: Original values and hourly avg
        layout.addWidget(self.show_original_values, 5, 0, 1, 2)
        layout.addWidget(self.show_frequency_percentage, 6, 0, 1, 2)
        # Row 7-9: Power curve options
        layout.addWidget(self.show_standard_power_curve, 7, 0, 1, 2)
        layout.addWidget(self.enable_percentage_bands, 8, 0, 1, 2)
        # Percentage input group
        pct_widget = QWidget()
        pct_layout = QHBoxLayout(pct_widget)
        pct_layout.setContentsMargins(0, 0, 0, 0)
        pct_layout.addWidget(QLabel("±"))
        pct_layout.addWidget(self.percentage_input)
        pct_layout.addWidget(QLabel("%"))
        layout.addWidget(pct_widget, 9, 0, 1, 2)
        # Row 10-11: Percentage band checkboxes
        layout.addWidget(self.show_plus_percentage, 10, 0, 1, 2)
        layout.addWidget(self.show_minus_percentage, 11, 0, 1, 2)
        return CollapsibleSection("Plot Options", content_widget, expanded=True)

    def set_and_update(self, plot_name):
        self.selected_plot = plot_name
        self.update_plot_signal.emit()

    def setup_statistics_table(self):
        self.stats_dock = QDockWidget("Statistics", self)
        self.stats_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Statistic", "Value"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.setFont(QFont("Time Roman New", 10))
        self.stats_dock.setWidget(self.stats_table)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.stats_dock)

    def get_safe_date_range(self):
        if not self.data.empty:
            timestamp_col = self.column_cache.get("timestamp")
            if timestamp_col and timestamp_col in self.data.columns:
                min_date = self.data[timestamp_col].min().date()
                max_date = self.data[timestamp_col].max().date()
            elif isinstance(self.data.index, pd.DatetimeIndex):
                min_date = self.data.index.min().date()
                max_date = self.data.index.max().date()
            else:
                return QDate.currentDate().addDays(-30), QDate.currentDate()
            return QDate(min_date), QDate(max_date)
        return QDate.currentDate().addDays(-30), QDate.currentDate()

    # def update_statistics(self):
    #     df_to_use = self.filtered_df if self.filtered_df is not None and not self.filtered_df.empty else self.data
    #     if df_to_use is None or df_to_use.empty:
    #         return
    #     df = df_to_use.copy()
    #     df.columns = df.columns.str.strip()
    #     timestamp_col = self.column_cache.get("timestamp")
    #     if timestamp_col and timestamp_col in df.columns:
    #         df.loc[:, timestamp_col] = pd.to_datetime(df[timestamp_col], format='%d-%m-%Y %H:%M:%S', errors='coerce', dayfirst=True)
    #         df.set_index(timestamp_col, inplace=True)
    #     elif isinstance(df.index, pd.DatetimeIndex):
    #         pass
    #     else:
    #         return
    #     wind_speed_column = self.wind_speed_col.currentData() or self.wind_speed_col.currentText()
    #     wind_dir_column = self.wind_dir_col.currentData() or self.wind_dir_col.currentText()
    #     if wind_speed_column not in df.columns or wind_dir_column not in df.columns:
    #         return
    #     speed_data = df[wind_speed_column]
    #     dir_data = df[wind_dir_column]
    #     prevailing = pd.Series(dir_data).mode()
    #     prevailing_wind = f"{prevailing.iloc[0]:.1f}°" if not prevailing.empty else "N/A"
    #     data_period_start = df.index.min().strftime('%Y-%m-%d') if not df.empty else "N/A"
    #     data_period_end = df.index.max().strftime('%Y-%m-%d') if not df.empty else "N/A"
    #     stats = [
    #         ("Mean Speed (m/s)", f"{speed_data.mean():.2f}"),
    #         ("Max Speed (m/s)", f"{speed_data.max():.2f}"),
    #         ("Std Dev (m/s)", f"{speed_data.std():.2f}"),
    #         ("Prevailing Wind", prevailing_wind),
    #         ("Data Period", f"{data_period_start} to {data_period_end}"),
    #         ("Total Records", f"{len(df)}")
    #     ]
    #     self.stats_table.setRowCount(len(stats))
    #     for row, (stat, value) in enumerate(stats):
    #         self.stats_table.setItem(row, 0, QTableWidgetItem(str(stat)))
    #         self.stats_table.setItem(row, 1, QTableWidgetItem(str(value)))
    #     self.stats_table.resizeColumnsToContents()

    def update_statistics(self):
        df_to_use = self.filtered_df if self.filtered_df is not None and not self.filtered_df.empty else self.data
        if df_to_use is None or df_to_use.empty:
            return
        
        df = df_to_use.copy()
        df.columns = df.columns.str.strip()
        
        timestamp_col = self.column_cache.get("timestamp")
        if timestamp_col and timestamp_col in df.columns:
            df.loc[:, timestamp_col] = pd.to_datetime(df[timestamp_col], format='%d-%m-%Y %H:%M:%S', errors='coerce')
            df.set_index(timestamp_col, inplace=True)
        elif isinstance(df.index, pd.DatetimeIndex):
            pass
        else:
            return
        
        wind_speed_column = self.wind_speed_col.currentData() or self.wind_speed_col.currentText()
        wind_dir_column = self.wind_dir_col.currentData() or self.wind_dir_col.currentText()
        
        if wind_speed_column not in df.columns or wind_dir_column not in df.columns:
            return
        
        # VECTORIZE: Process all data simultaneously
        speed_data = pd.to_numeric(df[wind_speed_column], errors='coerce')
        dir_data = pd.to_numeric(df[wind_dir_column], errors='coerce')
        
        # VECTORIZE: Calculate all statistics at once
        prevailing = dir_data.mode()
        prevailing_wind = f"{prevailing.iloc[0]:.1f}°" if not prevailing.empty else "N/A"
        
        data_period_start = df.index.min().strftime('%Y-%m-%d') if not df.empty else "N/A"
        data_period_end = df.index.max().strftime('%Y-%m-%d') if not df.empty else "N/A"
        
        # VECTORIZE: All statistical calculations in one pass
        stats = [
            ("Mean Speed (m/s)", f"{speed_data.mean():.2f}"),
            ("Max Speed (m/s)", f"{speed_data.max():.2f}"),
            ("Std Dev (m/s)", f"{speed_data.std():.2f}"),
            ("Prevailing Wind", prevailing_wind),
            ("Data Period", f"{data_period_start} to {data_period_end}"),
            ("Total Records", f"{len(df)}")
        ]
        
        self.stats_table.setRowCount(len(stats))
        for row, (stat, value) in enumerate(stats):
            self.stats_table.setItem(row, 0, QTableWidgetItem(str(stat)))
            self.stats_table.setItem(row, 1, QTableWidgetItem(str(value)))
        self.stats_table.resizeColumnsToContents()

    def update_summary(self):
        df_to_use = self.filtered_df if self.filtered_df is not None and not self.filtered_df.empty else self.data
        if df_to_use is None or df_to_use.empty:
            return
        power_col = self.column_cache.get("power")
        if power_col and power_col in df_to_use.columns:
            power_data = pd.to_numeric(df_to_use[power_col], errors='coerce').dropna()
            if not power_data.empty:
                max_power = round(power_data.max(), 3)
                total_power = power_data.sum()
                active_power_sum = power_data[power_data > 0].sum()
                active_power_count = power_data[power_data > 0].count()
                reactive_power_sum = power_data[power_data < 0].sum()
                reactive_power_count = power_data[power_data < 0].count()
                rated_power = power_data.max()
                rated_power_col = self.column_cache.get("rated_power")
                if rated_power_col and rated_power_col in df_to_use.columns:
                    try:
                        rated_power = float(df_to_use[rated_power_col].max())
                    except (ValueError, TypeError) as e:
                        print(f"Error using rated_power column: {e}")
                total_possible_power = rated_power * len(df_to_use)
                plf = (total_power / total_possible_power) * 100 if total_possible_power > 0 else 0
                grid_availability = (active_power_count / len(df_to_use)) * 100 if len(df_to_use) > 0 else 0
                summary_stats = [
                    ("Max Power (KW)", f"{max_power:.3f}"),
                    ("Total Power", f"{total_power:.3f}"),
                    ("Total Active Power", f"{active_power_sum:.3f} (samples: {active_power_count})"),
                    ("Total Reactive Power", f"{reactive_power_sum:.3f} (samples: {reactive_power_count})"),
                    ("PLF (%)", f"{plf:.2f}"),
                    ("Grid Availability (%)", f"{grid_availability:.2f}")
                ]
                self.summary_table.setRowCount(len(summary_stats))
                for row, (metric, value) in enumerate(summary_stats):
                    self.summary_table.setItem(row, 0, QTableWidgetItem(metric))
                    self.summary_table.setItem(row, 1, QTableWidgetItem(value))
                self.summary_table.resizeColumnsToContents()

    def get_filtered_data(self):
        """Get filtered data based on current settings with improved error handling"""
        try:
            if self.data.empty:
                return pd.DataFrame()
            
            # Initialize filtered_data
            filtered_data = self.data
            # Get timestamp column
            timestamp_col = self.get_cached_columns("timestamp") or self._find_timestamp_column()
            
            # # Apply date and time filters only if enabled
            # if hasattr(self, 'enable_date_filter') and self.enable_date_filter.isChecked():
            #     filtered_data = self.apply_date_filter(filtered_data, timestamp_col)
            #     if filtered_data.empty:
            #         print("Warning: Date filter resulted in empty dataset")
            #         return filtered_data
            # # Data type conversion
            # self._convert_data_types(filtered_data)
            # # Initialize removed data tracking
            # self.removed_data = pd.DataFrame()
            # # Apply power filtering for relevant plots
            # if self._should_apply_power_filter():
            #     filtered_data = self._apply_power_filter(filtered_data)
            # # Apply sample size filtering
            # if self.fix_sample_size.isChecked():
            #     filtered_data = self._apply_sample_size_filter(filtered_data)
            # self.filtered_df = filtered_data
            # self.show_removed_data_table()
            # return filtered_data

            if hasattr(self, 'enable_date_filter') and self.enable_date_filter.isChecked():
                start_date = self.start_date_only.text()
                end_date = self.end_date_only.text()
                
                # VECTORIZE: Apply all date filters at once
                timestamp_col = self.get_cached_columns("timestamp")
                if timestamp_col:
                    date_mask = pd.Series(True, index=filtered_data.index)
                    
                    if start_date:
                        date_mask &= (filtered_data[timestamp_col].dt.date >= 
                                    pd.to_datetime(start_date, format='%d-%m-%Y').date())
                    if end_date:
                        date_mask &= (filtered_data[timestamp_col].dt.date <= 
                                    pd.to_datetime(end_date, format='%d-%m-%Y').date())
                    
                    filtered_data = filtered_data[date_mask]  # Single vectorized operation
            
            # VECTORIZE: Power filtering
            if self._should_apply_power_filter():
                power_col = self.column_cache.get("power")
                if power_col:
                    # VECTORIZE: Filter all power values at once
                    power_mask = pd.to_numeric(filtered_data[power_col], errors='coerce') > 0.1
                    filtered_data = filtered_data[power_mask]
            
            return filtered_data

        except Exception as e:
            self.handle_errors(f"Error filtering data: {str(e)}\n{traceback.format_exc()}")
            return pd.DataFrame()
    
    def apply_date_filter(self, df, timestamp_col):
        """Enhanced date and time filters with proper datetime handling and error recovery"""
        if not timestamp_col or timestamp_col not in df.columns:
            print("Warning: No valid timestamp column found for filtering")
            return df
        original_count = len(df)
        try:
            # Ensure timestamp column is datetime
            if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
                df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
            # Remove rows with invalid timestamps
            df = df.dropna(subset=[timestamp_col])
            # Apply date filter only if date filtering is enabled
            if hasattr(self, 'enable_date_filter') and self.enable_date_filter.isChecked():
                start_date = self.start_date_only.text().strip()
                end_date = self.end_date_only.text().strip()
                if start_date:
                    try:
                        start_dt = pd.to_datetime(start_date, format='%d-%m-%Y', errors='raise')
                        df = df[df[timestamp_col].dt.date >= start_dt.date()]
                    except ValueError:
                        print(f"Invalid start date format: {start_date}. Expected DD-MM-YYYY")
                if end_date:
                    try:
                        end_dt = pd.to_datetime(end_date, format='%d-%m-%Y', errors='raise')
                        df = df[df[timestamp_col].dt.date <= end_dt.date()]
                    except ValueError:
                        print(f"Invalid end date format: {end_date}. Expected DD-MM-YYYY")
            # Apply time filter only if time filtering is enabled
            if hasattr(self, 'enable_time_filter') and self.enable_time_filter.isChecked():
                start_time = self.start_time_only.text().strip()
                end_time = self.end_time_only.text().strip()

                if start_time:
                    try:
                        start_time_obj = pd.to_datetime(start_time, format='%H:%M').time()
                        df = df[df[timestamp_col].dt.time >= start_time_obj]
                    except ValueError:
                        print(f"Invalid start time format: {start_time}. Expected HH:MM")
                
                if end_time:
                    try:
                        end_time_obj = pd.to_datetime(end_time, format='%H:%M').time()
                        df = df[df[timestamp_col].dt.time <= end_time_obj]
                    except ValueError:
                        print(f"Invalid end time format: {end_time}. Expected HH:MM")
        except Exception as e:
            print(f"Date/time filter error: {e}")
            return df  # Return original data if filtering fails
        filtered_count = len(df)
        if original_count != filtered_count:
            print(f"Data filtered: {original_count} -> {filtered_count} rows")
        return df
 
    def _get_timestamp_column(self, df):
        """Get the appropriate timestamp column"""
        timestamp_col = self.column_cache.get("timestamp")
        if timestamp_col and timestamp_col in df.columns:
            return timestamp_col
        elif isinstance(df.index, pd.DatetimeIndex):
            timestamp_col = "Timestamp"
            df.loc[:, "Timestamp"] = df.index
            return timestamp_col
        return None
    
    def _convert_data_types(self, df):
        """Convert data types for numeric columns"""
        power_col = self.column_cache.get("power")
        wind_speed_col = self.wind_speed_col.currentData() or self.wind_speed_col.currentText()
        for col in [power_col, wind_speed_col]:
            if col and col in df.columns:
                df.loc[:, col] = pd.to_numeric(df[col], errors='coerce')
    def _should_apply_power_filter(self):
        """Check if power filtering should be applied"""
        power_related_plots = [
            "power_curve", "actual_power_curve", "binned_power_curve"]
        return (self.remove_negative_power.isChecked() and 
                self.selected_plot in power_related_plots)
    def _apply_sample_size_filter(self, df):
        """Apply sample size filtering for consistent intervals"""
        timestamp_col = self.column_cache.get("timestamp")
        if not timestamp_col or timestamp_col not in df.columns:
            return df
        
        fd = df.sort_values(by=timestamp_col)
        fd['dt'] = fd[timestamp_col].diff().dt.total_seconds().fillna(0)
        fd['block'] = (fd['dt'] != 600).cumsum()
        
        spans = fd.groupby('block')[timestamp_col].agg(['min', 'max'])
        spans['duration'] = (spans['max'] - spans['min']).dt.total_seconds()
        good_blocks = spans[spans['duration'] >= 600].index
        if not good_blocks.empty:
            block_id = good_blocks.min()
            return fd[fd['block'] == block_id].drop(columns=['dt', 'block'])
        return df
    
    def _apply_power_filter(self, df):
        """Apply power filtering to remove negative power values"""
        power_col = self.column_cache.get("power")
        if not power_col or power_col not in df.columns:
            return df
        initial_count = len(df)
        power_data = pd.to_numeric(df[power_col], errors='coerce')
        valid_power_mask = power_data > 0.1
        # Store removed data
        removed_mask = ~valid_power_mask | power_data.isna()
        if removed_mask.any():
            self.removed_data = pd.concat([
                self.removed_data, 
                df[removed_mask]
            ], ignore_index=True)
        
        filtered_df = df[valid_power_mask]
        removed_count = initial_count - len(filtered_df)
        if removed_count > 0:
            self.statusBar.showMessage(f"Removed {removed_count} records with negative/invalid power", 5000)
        return filtered_df
    
    def update_plot(self):
        """Update the main plot with current settings"""
        try:
            start_time = time.time()
            
            if self._should_skip_plot_update():
                return
            # Cleanup and preparation
            self._prepare_plot_update()
            # Get filtered data
            self.filtered_df = self.get_filtered_data()
            # Execute plot function
            if self.selected_plot and self.selected_plot in self._get_plot_functions():
                self._execute_plot_function()
                self._configure_plot_appearance()
                self._setup_plot_interactivity()
            # Finalize plot
            self.canvas.draw_idle()
            self._update_ui_components()
            # Show performance metrics
            elapsed_time = time.time() - start_time
            self.statusBar.showMessage(f"Plot updated in {elapsed_time:.3f} seconds", 3000)
            
        except Exception as e:
            self.handle_errors(f"Error updating plot: {str(e)}\n{traceback.format_exc()}")
    
    def _should_skip_plot_update(self):
        """Check if plot update should be skipped"""
        if self.data is None or self.data.empty:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No data loaded', ha='center', va='center')
            self.canvas.draw_idle()
            return True
        return False
    
    def _prepare_plot_update(self):
        """Prepare for plot update"""
        plt.close('all')
        gc.collect()
        self.figure.clf()
    
    def _get_plot_functions(self):
        """Get dictionary of available plot functions"""
        return {
            "wind_rose": lambda: pl.plot_selected_graph(self, "wind_rose", self.column_cache),
            "wind_speed_distribution": lambda: pl.plot_selected_graph(self, "wind_speed_distribution", self.column_cache),
            "turbulence_intensity": lambda: pl.plot_selected_graph(self, "turbulence_intensity", self.column_cache),
            "power_curve": lambda: pl.plot_selected_graph(self, "power_curve", self.column_cache),
            "actual_power_curve": lambda: pl.plot_selected_graph(self, "actual_power_curve", self.column_cache),
            "binned_power_curve": lambda: pl.plot_selected_graph(self, "binned_power_curve", self.column_cache),
            "joint_distribution": lambda: pl.plot_selected_graph(self, "joint_distribution", self.column_cache),
            "rotor_speed_graph": lambda: pl.plot_selected_graph(self, "rotor_speed_graph", self.column_cache),
            "wind_frequency_histogram": lambda: pl.plot_selected_graph(self, "wind_frequency_histogram" ,self.column_cache),
            "power_vs_temperature": lambda: pl.plot_selected_graph(self, "power_vs_temperature", self.column_cache),
            "rotor_speed_vs_gearbox_temperature": lambda: pl.plot_selected_graph(self, "rotor_speed_vs_gearbox_temperature", self.column_cache),
            "ambient_vs_nacelle_temperature": lambda: pl.plot_selected_graph(self, "ambient_vs_nacelle_temperature", self.column_cache),
            "rotor_speed_vs_generator_speed": lambda: pl.plot_selected_graph(self, "rotor_speed_vs_generator_speed", self.column_cache),
        }

    def handle_canvas_click(self, event):
        if event.inaxes:
            clicked_on_artist = False
            for artist in event.inaxes.get_children():
                contains, _ = artist.contains(event)
                if contains:
                    clicked_on_artist = True
                    break
            if not clicked_on_artist:
                mplcursors.cursor().remove()
    
    def _execute_plot_function(self):
        """Execute the selected plot function"""
        plot_functions = self._get_plot_functions()
        plot_functions[self.selected_plot]()

    def _configure_plot_appearance(self):
        """Configure plot appearance settings"""
        for ax in self.figure.get_axes():
            ax.set_facecolor(self.background_color.currentText())
            # Configure grid appearance based on background
            if self.show_grid.isChecked():
                bg_color = self.background_color.currentText()
                if bg_color in ['white', 'lightgray']:
                    ax.grid(True, color='gray', linestyle='-', alpha=0.3)
                elif bg_color == 'darkgray':
                    ax.grid(True, color='lightgray', linestyle='-', alpha=0.5)
                elif bg_color == 'black':
                    ax.grid(True, color='white', linestyle='-', alpha=0.3)
                else:
                    ax.grid(True, color='gray', linestyle='-', alpha=0.3)

    def _setup_plot_interactivity(self):
        """Setup interactive features for the plot"""
        for ax in self.figure.get_axes():
            for line in ax.get_lines():
                cursor = mplcursors.cursor(line, hover=False)
                cursor.connect("add", self._format_cursor_annotation)
            self.canvas.mpl_connect('button_press_event', self.handle_canvas_click)
    
    def _format_cursor_annotation(self, sel):
        """Format cursor annotation text"""
        sel.annotation.set_text(f'{sel.artist.axes.get_xlabel()}: {sel.target[0]:.2f}\n{sel.artist.axes.get_ylabel()}: {sel.target[1]:.2f}') 
        sel.annotation.get_bbox_patch().set(fc="white", alpha=0.85)
    
    def _update_ui_components(self):
        """Update UI components after plot update"""
        self.update_statistics()
        self.update_summary()
    
    def set_data(self, df, file_name=None, turbine_name: Optional[str] = None) -> None:
        """Set data for visualization with comprehensive validation"""
        try:
            # Validate input
            if not self._validate_input_data(df):
                self._reset_data_state()
                return
            # Set data attributes
            self._set_data_attributes(df, file_name, turbine_name)
            # Process data
            self._populate_column_cache()
            # Update UI
            self._update_ui_after_data_load(file_name, turbine_name)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set data: {e}")
    
    def _validate_input_data(self, df):
        """Validate input data"""
        if df is None or df.empty:
            return False
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        return True
    
    def _reset_data_state(self):
        """Reset data state when no valid data provided"""
        self.data = pd.DataFrame()
        self.file_name = None
        self.turbine_id = None
        self.setWindowTitle("Wind Data Analysis Tool")
    
    def _set_data_attributes(self, df, file_name, turbine_name):
        """Set data-related attributes"""
        self.data = df
        self.file_name = file_name
        self.turbine_id = turbine_name
        self.column_cache.clear()

    def _update_ui_after_data_load(self, file_name, turbine_name):
        """Update UI after data loading"""
        self.update_plot_signal.emit()
        
        # Update window title
        if turbine_name:
            self.setWindowTitle(f"Visualizing Turbine: {turbine_name}")
        elif file_name:
            self.setWindowTitle(f"Wind Data Analysis Tool - {file_name}")
        else:
            self.setWindowTitle("Wind Data Analysis Tool")

    def export_plot(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Plot", "", "PNG Files (*.png);;PDF Files (*.pdf)")
        if file_name:
            self.figure.savefig(file_name, bbox_inches='tight', dpi=300)
    
    def generate_report(self):
        generator = EnhancedReportGenerator(self)
        generator.generate_report()
    
    def export_data(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Data", "", "CSV Files (*.csv)")
        if file_name and self.data is not None:
            self.data.to_csv(file_name)

    def show_binned_power_curve_with_table(self):
        self.selected_plot = "binned_power_curve"
        
        # Setup table first if not exists
        if not hasattr(self, 'bin_table_dock'):
            self.bin_table_dock = QDockWidget("Bin Records", self)
            self.bin_table_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)

            self.bin_table = QTableWidget()
            self.bin_table.setColumnCount(4)
            self.bin_table.setHorizontalHeaderLabels(["Bin Range", "Mean Power", "Std Dev", "Count"])
            self.bin_table.horizontalHeader().setStretchLastSection(True)
            self.bin_table.setAlternatingRowColors(True)

            bin_table_widget = QWidget()
            bin_table_layout = QVBoxLayout(bin_table_widget)

            export_button = QPushButton("Export Bin Data")
            export_button.clicked.connect(lambda: self.export_bin_table(self.bin_table))

            bin_table_layout.addWidget(self.bin_table)
            bin_table_layout.addWidget(export_button)

            self.bin_table_dock.setWidget(bin_table_widget)
            self.addDockWidget(Qt.BottomDockWidgetArea, self.bin_table_dock)
            self.bin_table_dock.setVisible(False)

        # Update plot SYNCHRONOUSLY (direct call)
        self.update_plot()
        # Show table immediately after plot is ready
        self.bin_table_dock.setVisible(True)
        self.bin_table_dock.raise_()
        # Show percentage bands dock if enabled
        if hasattr(self, 'enable_percentage_bands') and self.enable_percentage_bands.isChecked():
            self.percentage_bands_dock.setVisible(True)
            self.percentage_bands_dock.raise_()
        else:
            self.percentage_bands_dock.setVisible(False)

    def export_bin_table(self, table):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Bin Data", "", "CSV Files (*.csv)")
        if file_name:
            data = []
            for row in range(table.rowCount()):
                row_data = [table.item(row, col).text() for col in range(table.columnCount())]
                data.append(row_data)
            df = pd.DataFrame(data, columns=["Bin Range", "Mean Power", "Std Dev", "Count"])
            df.to_csv(file_name, index=False)
            QMessageBox.information(self, "Success", f"Bin data exported to:\n{file_name}")

    def show_removed_data_table(self):
        if not hasattr(self, 'removed_data_dock') \
           and self.remove_negative_power.isChecked()\
           and self.removed_data is not None \
           and not self.removed_data.empty:
            self.removed_data_dock = QDockWidget("Removed Data", self)
            self.removed_data_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
            self.removed_data_table = QTableWidget()
            self.removed_data_table.setColumnCount(len(self.removed_data.columns))
            self.removed_data_table.setHorizontalHeaderLabels(self.removed_data.columns)
            self.removed_data_table.setRowCount(len(self.removed_data))
            for row in range(len(self.removed_data)):
                for col, value in enumerate(self.removed_data.iloc[row]):
                    self.removed_data_table.setItem(row, col, QTableWidgetItem(str(value)))
            self.removed_data_table.horizontalHeader().setStretchLastSection(True)
            self.removed_data_table.setAlternatingRowColors(True)
            removed_data_widget = QWidget()
            removed_data_layout = QVBoxLayout(removed_data_widget)
            removed_data_layout.addWidget(self.removed_data_table)
            export_button = QPushButton("Export Removed Data")
            export_button.clicked.connect(lambda: self.export_removed_data(self.removed_data_table))
            removed_data_layout.addWidget(export_button)
            self.removed_data_dock.setWidget(removed_data_widget)
            self.addDockWidget(Qt.BottomDockWidgetArea, self.removed_data_dock)
        if hasattr(self, 'removed_data_dock'):
            visible = ((self.remove_negative_power.isChecked())
                       and self.removed_data is not None
                       and not self.removed_data.empty)
            self.removed_data_dock.setVisible(visible)
            if self.removed_data_dock.isVisible():
                 self.removed_data_table.setRowCount(len(self.removed_data))
                 for row in range(len(self.removed_data)):
                     for col, value in enumerate(self.removed_data.iloc[row]):
                         self.removed_data_table.setItem(row, col, QTableWidgetItem(str(value)))
                 self.removed_data_table.resizeColumnsToContents()
    
    def handle_standard_power_curve_toggle(self):
        # Only upload client curve when checkbox is checked AND we don't have data yet
        if self.show_standard_power_curve.isChecked() and not hasattr(self, "client_power_data"):
            self.upload_client_power_curve()
        
        # Always update plot (with or without client curve overlay)
        self.update_plot_signal.emit()

    def export_removed_data(self, table):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Removed Data", "", "CSV Files (*.csv)")
        if file_name:
            data = []
            headers = [table.horizontalHeaderItem(col).text() for col in range(table.columnCount())]
            for row in range(table.rowCount()):
                row_data = [table.item(row, col).text() for col in range(table.columnCount())]
                data.append(row_data)
            df = pd.DataFrame(data, columns=headers)
            df.to_csv(file_name, index=False)
            QMessageBox.information(self, "Success", f"Removed data exported to:\n{file_name}")

    def upload_client_power_curve(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Upload Site Power Curve", "", "Excel Files (*.xlsx);;CSV Files (*.csv)")
        if file_name:
            try:
                if file_name.endswith('.xlsx'):
                    df = pd.read_excel(file_name)
                else:
                    df = pd.read_csv(file_name)
                if 'wind_speed' not in df.columns or 'power' not in df.columns:
                    raise ValueError("File must contain 'wind_speed' and 'power' columns.")
                df = df.sort_values('wind_speed')
                self.client_power_data = df
                self.standard_power_data = df
                min_ws = df['wind_speed'].min()
                max_ws = df['wind_speed'].max()
                self.client_power_interp = interp1d(df['wind_speed'], df['power'], kind='linear', fill_value='extrapolate')
                interp_ws = np.arange(min_ws, max_ws + 0.1, 0.1)
                interp_power = self.client_power_interp(interp_ws)
                self.interpolated_client_power = pd.DataFrame({'wind_speed': interp_ws, 'power': interp_power})
                tbl = self.standard_data_table
                tbl.setColumnCount(2)
                tbl.setHorizontalHeaderLabels(["wind_speed", "power"])
                tbl.setRowCount(len(df))
                for r, row in df.iterrows():
                    tbl.setItem(r, 0, QTableWidgetItem(str(row['wind_speed'])))
                    tbl.setItem(r, 1, QTableWidgetItem(str(row['power'])))
                self.standard_data_dock.setVisible(True)
            except Exception as e:
                self.handle_errors(f"Error loading client power curve: {e}")

    def show_wind_frequency_table(self):
        if not hasattr(self, 'frequency_table_dock'):
            self.frequency_table_dock = QDockWidget("Wind Frequency Data", self)
            self.frequency_table_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)

            self.frequency_table = QTableWidget()
            self.frequency_table.setAlternatingRowColors(True)

            freq_table_widget = QWidget()
            freq_table_layout = QVBoxLayout(freq_table_widget)

            export_button = QPushButton("Export Frequency Data")
            export_button.clicked.connect(self.export_frequency_table)

            freq_table_layout.addWidget(self.frequency_table)
            freq_table_layout.addWidget(export_button)

            self.frequency_table_dock.setWidget(freq_table_widget)
            self.addDockWidget(Qt.BottomDockWidgetArea, self.frequency_table_dock)
        
        self.frequency_table_dock.setVisible(True)
        self.frequency_table_dock.raise_()

    def _update_frequency_table(self):
        if not hasattr(self, 'frequency_data'):
            return
        
        freq_data = self.frequency_data
        
        # Set up table
        self.frequency_table.setRowCount(len(freq_data.index))
        self.frequency_table.setColumnCount(len(freq_data.columns) + 1)
        
        headers = ["Direction"] + [str(col) for col in freq_data.columns]
        self.frequency_table.setHorizontalHeaderLabels(headers)
        
        # Fill table
        for row, dir_bin in enumerate(freq_data.index):
            self.frequency_table.setItem(row, 0, QTableWidgetItem(str(dir_bin)))
            for col, ws_bin in enumerate(freq_data.columns):
                value = freq_data.loc[dir_bin, ws_bin]
                if hasattr(self, 'show_frequency_percentage') and self.show_frequency_percentage.isChecked():
                    self.frequency_table.setItem(row, col + 1, QTableWidgetItem(f"{value:.2f}%"))
                else:
                    self.frequency_table.setItem(row, col + 1, QTableWidgetItem(str(int(value))))

    def export_frequency_table(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Frequency Data", "", "CSV Files (*.csv)")
        if file_name and hasattr(self, 'frequency_data'):
            self.frequency_data.to_csv(file_name)
            QMessageBox.information(self, "Success", f"Frequency data exported to:\n{file_name}")
    
    def set_and_update_with_table(self, plot_name):
        self.selected_plot = plot_name
        self.update_plot_signal.emit()
        if plot_name == "wind_frequency_histogram":
            self.show_wind_frequency_table()
            
    def export_percentage_bands(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Percentage Bands Data", "", "CSV Files (*.csv)")
        if file_name:
            data = []
            headers = [self.percentage_bands_table.horizontalHeaderItem(col).text() for col in range(self.percentage_bands_table.columnCount())]
            for row in range(self.percentage_bands_table.rowCount()):
                row_data = [self.percentage_bands_table.item(row, col).text() for col in range(self.percentage_bands_table.columnCount())]
                data.append(row_data)
            df = pd.DataFrame(data, columns=headers)
            df.to_csv(file_name, index=False)
            QMessageBox.information(self, "Success", f"Percentage bands data exported to:\n{file_name}")

    def handle_errors(self, message: str):
        QMessageBox.critical(self, "Error", message)
        print(message)

    def closeEvent(self, event):
        plt.close('all')
        gc.collect()
        event.accept()