from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
import pandas as pd
import numpy as np
import traceback
from scipy.interpolate import interp1d
from utils.collapsible_prop import CollapsibleSection
from utils.datetime_utils import get_datetime_info
from . import plotting_logic as pl
from . import power_curve_logic as pcl

class PowerCurveWindow(QMainWindow):

    def __init__(self, data=None, turbine_name=None, parent=None, project_id=None):
        super().__init__(parent)
        self.setWindowTitle(f"Power Curve Analysis - {turbine_name}" if turbine_name else "Power Curve Analysis")
        self.setGeometry(150, 150, 1400, 800)
        
        self.data = data if data is not None else pd.DataFrame()
        self.turbine_name = turbine_name
        self.project_id = project_id  # NEW
        self.column_cache = {}
        self.filtered_df = None
        self.client_power_data = None
        self.client_power_interp = None
        self.interpolated_client_power = None
        self.removed_data = None
        self.selected_plot = None
        self.standard_power_data = None
        self.current_plot_type = None
        self.coordinate_data = None
        self.ad_reference_data = None
        self.ad_corrected_data = None
        self.rho_site = None  # ADD THIS LINE
        
        # NEW: Auto-load files from database
        if self.project_id:
            self._load_files_from_database()
        
        if not self.data.empty:
            self._populate_column_cache()
            self.process_data()

                # SDI: Independent window
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self._init_ui_components()
        self.apply_styles()
        self.init_ui()
        self._setup_docks()
        self._connect_signals()
    
    def _populate_column_cache(self):
        import models.scada_utils as su
        params = ["wind_speed", "power", "timestamp"]
        for param in params:
            matched = su.find_matching_columns(self.data, param)
            self.column_cache[param] = matched[0] if matched else None
    
    def process_data(self):
        """Same as VisualizationWindow - convert timestamp to datetime"""
        if self.data.empty:
            return
        try:
            timestamp_col = self.get_cached_columns("timestamp")
            if timestamp_col and timestamp_col in self.data.columns:
                self.data[timestamp_col] = pd.to_datetime(
                    self.data[timestamp_col], errors='coerce')
                self.data.dropna(subset=[timestamp_col], inplace=True)
        except Exception as e:
            self.handle_errors(f"Error processing data: {e}")

    def get_cached_columns(self, param):
        """Same as VisualizationWindow"""
        if param not in self.column_cache:
            import models.scada_utils as su
            matched_columns = su.find_matching_columns(self.data, param)
            self.column_cache[param] = matched_columns[0] if matched_columns else None
        return self.column_cache[param]

    def _should_apply_power_filter(self):
        """Check if power filtering should be applied"""
        power_related_plots = ["power_curve", "actual_power_curve", "binned_power_curve"]
        return (self.remove_negative_power.isChecked() and 
                self.selected_plot in power_related_plots)

    def get_filtered_data(self):
        """Call VisualizationWindow's filtering logic directly"""
        from .visualization_window import VisualizationWindow
        self.selected_plot = self.current_plot_type
        return VisualizationWindow.get_filtered_data(self)
    
    def  _init_ui_components(self):
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        
        self.show_legend = QCheckBox("Show Legend")
        self.show_legend.setChecked(True)
        self.show_grid = QCheckBox("Show Grid")
        self.show_grid.setChecked(True)
        self.show_standard_power_curve = QCheckBox("Show Site Curve")
        self.show_original_values = QCheckBox("Show Original Values")
        self.show_average_line = QCheckBox("Show Average Line")
        self.enable_iec_binning = QCheckBox("Enable IEC Binning")
        self.remove_negative_power = QCheckBox("Remove Negative Power (≤ 0)")
        self.fix_sample_size = QCheckBox("Fix Sample Size = 600")
        self.show_binned_overlay = QCheckBox("Show Binned Curve Overlay")

        # Air density Dorrection
        self.enable_air_density_correction = QCheckBox("Apply Air Density Correction")
        self.show_calculated_ad = QCheckBox("Show Calculated AD (ρ_site)")
        self.show_reference_ad = QCheckBox("Show Reference AD (ρ=1.225)")
        self.show_ad_corrected_curve = QCheckBox("Show AD Corrected Curve")

        self.background_color = QComboBox()
        self.background_color.addItems(["white", "lightgray", "darkgray", "black"])
        self.bin_width = type('obj', (object,), {'value': lambda self: 1})()

        # Store AD corrected data
        self.ad_corrected_data = None
    
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f7f7f7; }
            QGroupBox { font-weight: bold; border: 2px solid #d3d3d3; border-radius: 8px; 
                       margin-top: 15px; padding-top: 10px; background-color: #ffffff;}
            QGroupBox::title {subcontrol-origin: margin; subcontrol-position: top left; 
                             padding: 4px 12px; background-color: #3498DB; color: white; 
                             border-radius: 4px; left: 10px; top: -8px;}
            QCheckBox { spacing: 5px; font-size: 11px; }
            QPushButton { background-color: #0078d7; color: white; border: none; 
                         padding: 6px 12px; border-radius: 4px; font-size: 11px;}
            QPushButton:hover { background-color: #005a9e; }
            QComboBox, QLineEdit { padding: 4px; border: 1px solid #ccc; border-radius: 4px; 
                                  background-color: #ffffff; color: black; font-size: 11px;}
        """)
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        splitter = QSplitter(Qt.Horizontal)
        
        plot_panel = QWidget()
        plot_layout = QVBoxLayout(plot_panel)
        self.toolbar = NavigationToolbar(self.canvas, plot_panel)
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        
        splitter.addWidget(plot_panel)
        splitter.setSizes([1050, 350])
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(splitter)
    
    def _setup_docks(self):
        self._setup_command_center()
        self._setup_statistics_dock()
        self._setup_ad_data_dock()  # Add this line
        self._setup_bin_table_dock()
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
    
    def _setup_command_center(self):
        self.command_center = QDockWidget("Command Center", self)
        self.command_center.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.command_center.setMinimumWidth(250)
        self.command_center.setMaximumWidth(350)
        
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        scroll_layout.addWidget(self._create_data_selection_group())
        scroll_layout.addWidget(self._create_plot_options_group())
        scroll_layout.addWidget(self._create_power_curve_types_group())
        scroll_layout.addWidget(self._create_actions_group())
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        self.command_center.setWidget(scroll_area)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.command_center)
    
    def _create_data_selection_group(self):
        content = QWidget()
        layout = QGridLayout(content)
        layout.setVerticalSpacing(8)
        
        min_date, max_date, min_time, max_time, _ = get_datetime_info(self.data)
        
        self.enable_date_filter = QCheckBox("Enable Date Filter")
        self.enable_date_filter.setChecked(True)
        self.enable_date_filter.stateChanged.connect(self._toggle_date_filter)
        layout.addWidget(self.enable_date_filter, 0, 0, 1, 2)
        
        self.start_date_label = QLabel("Start Date")
        layout.addWidget(self.start_date_label, 1, 0)
        self.start_date_only = QLineEdit(min_date)
        layout.addWidget(self.start_date_only, 1, 1)
        
        self.end_date_label = QLabel("End Date")
        layout.addWidget(self.end_date_label, 2, 0)
        self.end_date_only = QLineEdit(max_date)
        layout.addWidget(self.end_date_only, 2, 1)
        
        self.enable_time_filter = QCheckBox("Enable Time Filter")
        self.enable_time_filter.setChecked(False)
        self.enable_time_filter.stateChanged.connect(self._toggle_time_filter)
        layout.addWidget(self.enable_time_filter, 3, 0, 1, 2)
        
        self.start_time_label = QLabel(f"From Time:")
        layout.addWidget(self.start_time_label, 4, 0)
        self.start_time_only = QLineEdit(min_time)
        layout.addWidget(self.start_time_only, 4, 1)
        
        self.end_time_label = QLabel(f"To Time:")
        layout.addWidget(self.end_time_label, 5, 0)
        self.end_time_only = QLineEdit(max_time)
        layout.addWidget(self.end_time_only, 5, 1)
        
        self._toggle_time_filter()
        
        layout.addWidget(QLabel("Background:"), 6, 0)
        layout.addWidget(self.background_color, 6, 1)
        
        return CollapsibleSection("Data Selection and Filtering", content, expanded=True)
    
    def _toggle_date_filter(self):
        enabled = self.enable_date_filter.isChecked()
        for w in [self.start_date_label, self.start_date_only, self.end_date_label, self.end_date_only]:
            w.setVisible(enabled)
            w.setEnabled(enabled)
    
    def _toggle_time_filter(self):
        enabled = self.enable_time_filter.isChecked()
        for w in [self.start_time_label, self.start_time_only, self.end_time_label, self.end_time_only]:
            w.setVisible(enabled)
            w.setEnabled(enabled)
    
    def _create_plot_options_group(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        
        layout.addWidget(self.show_grid)
        layout.addWidget(self.show_legend)
        layout.addWidget(self.enable_iec_binning)
        layout.addWidget(self.remove_negative_power)
        layout.addWidget(self.show_binned_overlay)
        layout.addWidget(self.show_average_line)
        layout.addWidget(self.show_original_values)
        layout.addWidget(self.show_standard_power_curve)

        # Air Density Correction Options
        layout.addWidget(self.enable_air_density_correction)
        # NEW: Add radio-style toggles
        self.show_calculated_ad = QCheckBox(f"Show Calculated AD (ρ_site)")
        self.show_reference_ad = QCheckBox("Show Reference AD (ρ=1.225)")
        layout.addWidget(self.show_calculated_ad)
        layout.addWidget(self.show_reference_ad)
        # Hide initially
        self.show_calculated_ad.setVisible(False)
        self.show_reference_ad.setVisible(False)
        layout.addWidget(self.show_ad_corrected_curve)
        
        return CollapsibleSection("Plot Options", content, expanded=True)
    
    def _create_power_curve_types_group(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        
        self.btn_actual_pc = QPushButton("Actual Power Curve")
        self.btn_binned_pc = QPushButton("Binned Power Curve")
        self.btn_client_pc = QPushButton("Site Power Curve")
        
        layout.addWidget(self.btn_actual_pc)
        layout.addWidget(self.btn_binned_pc)
        layout.addWidget(self.btn_client_pc)
        
        return CollapsibleSection("Power Curve Types", content)
    
    def _create_actions_group(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Existing buttons
        self.export_plot_btn = QPushButton("Export Plot")
        self.export_data_btn = QPushButton("Export Data")
        
        layout.addWidget(self.export_plot_btn)
        layout.addWidget(self.export_data_btn)
        
        return CollapsibleSection("Actions", content)
    
    def _setup_statistics_dock(self):
        self.stats_dock = QDockWidget("Statistics", self)
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.setAlternatingRowColors(True)
        self.stats_dock.setWidget(self.stats_table)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.stats_dock)
    
    def _setup_bin_table_dock(self):
        self.bin_table_dock = QDockWidget("Bin Records", self)
        self.bin_table = QTableWidget()
        self.bin_table.setColumnCount(5)
        self.bin_table.setHorizontalHeaderLabels(["Bin Range", "Mean Power",  "Min", "Max", "Count"])
        self.bin_table.horizontalHeader().setStretchLastSection(True)
        self.bin_table.setAlternatingRowColors(True)
        
        bin_widget = QWidget()
        bin_layout = QVBoxLayout(bin_widget)
        bin_layout.addWidget(self.bin_table)
        
        export_btn = QPushButton("Export Bin Data")
        export_btn.clicked.connect(self._export_bin_data)
        bin_layout.addWidget(export_btn)
        
        self.bin_table_dock.setWidget(bin_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.bin_table_dock)
        self.bin_table_dock.setVisible(False)

    def _setup_ad_data_dock(self):
        self.ad_data_dock = QDockWidget("AD Corrected Data", self)
        self.ad_data_table = QTableWidget()
        self.ad_data_table.setColumnCount(2)
        self.ad_data_table.setHorizontalHeaderLabels(["Wind Speed (m/s)", "Power (kW)"])
        self.ad_data_table.horizontalHeader().setStretchLastSection(True)
        self.ad_data_table.setAlternatingRowColors(True)
        self.ad_data_dock.setWidget(self.ad_data_table)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.ad_data_dock)
        self.tabifyDockWidget(self.stats_dock, self.ad_data_dock)
        self.ad_data_dock.setVisible(False)
    
    def _connect_signals(self):
        self.btn_actual_pc.clicked.connect(lambda: self._plot_curve("actual_power_curve"))
        self.btn_binned_pc.clicked.connect(lambda: self._plot_curve("binned_power_curve"))
        self.btn_client_pc.clicked.connect(lambda: self._plot_curve("power_curve"))
        
        self.show_grid.stateChanged.connect(self.update_plot)
        self.show_legend.stateChanged.connect(self.update_plot)
        self.enable_iec_binning.stateChanged.connect(self.update_plot)
        self.remove_negative_power.stateChanged.connect(self.update_plot)
        self.fix_sample_size.stateChanged.connect(self.update_plot)
        self.show_average_line.stateChanged.connect(self.update_plot)
        self.show_standard_power_curve.stateChanged.connect(self._handle_client_curve_toggle)
        self.background_color.currentIndexChanged.connect(self.update_plot)
        self.show_binned_overlay.stateChanged.connect(self.update_plot)
        # New upload buttons
        self.enable_air_density_correction.stateChanged.connect(self._handle_ad_correction)
        
        # Air density correction signal
        self.show_ad_corrected_curve.stateChanged.connect(self.update_plot)
        self.show_calculated_ad.stateChanged.connect(self.update_plot)
        self.show_reference_ad.stateChanged.connect(self.update_plot)

        self.export_plot_btn.clicked.connect(self._export_plot)
        self.export_data_btn.clicked.connect(self._export_data)
    
    def _handle_client_curve_toggle(self):
        # Check if data already loaded from database
        if self.show_standard_power_curve.isChecked():
            if not self.client_power_interp:
                # No data loaded, prompt user to upload
                reply = QMessageBox.question(
                    self, 
                    "Site Power Curve", 
                    "No Site power curve found in database.\nWould you like to upload one?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.upload_client_power_curve()
                else:
                    self.show_standard_power_curve.setChecked(False)
                    return
        self.update_plot()
    
    # def _handle_ad_correction(self):
    #     if self.enable_air_density_correction.isChecked():
    #         # Validations
    #         if self.client_power_data is None or self.client_power_data.empty:
    #             QMessageBox.warning(self, "Warning", "No AD reference curve found in database.")
    #             self.enable_air_density_correction.setChecked(False)
    #             return
            
    #         if self.coordinate_data is None:
    #             QMessageBox.warning(self, "Warning", "No coordinate data found in database.\nPlease recreate the project with coordinate file.")
    #             self.enable_air_density_correction.setChecked(False)
    #             return
            
    #         if self.coordinate_data.empty:
    #             QMessageBox.warning(self, "Warning", "Coordinate data is empty.")
    #             self.enable_air_density_correction.setChecked(False)
    #             return
            
    #         if self.data is None or self.data.empty:
    #             QMessageBox.warning(self, "Warning", "No turbine data loaded.")
    #             self.enable_air_density_correction.setChecked(False)
    #             return
            
    #         try:
    #             turbine_map, _ = self._build_turbine_lookup(self.coordinate_data)
                
    #             if turbine_map is None:
    #                 QMessageBox.warning(self, "Warning", "Failed to parse coordinate file.")
    #                 self.enable_air_density_correction.setChecked(False)
    #                 return
                
    #             turbine_obj = self._find_turbine_data(turbine_map, self.turbine_name)
                
    #             if turbine_obj is None:
    #                 available = list(turbine_map.keys())[:10]
    #                 QMessageBox.warning(self, "Warning", f"Turbine '{self.turbine_name}' not found.\nAvailable: {available}")
    #                 self.enable_air_density_correction.setChecked(False)
    #                 return
                
    #             elevation = turbine_obj['elevation']
    #             hub_height = turbine_obj['hub_height']
                
    #             from views.visualization_components import air_density_correction as adc
    #             T_hub_avg = adc.get_t_hub_average(self.data, None)
    #             rho_site = adc.calculate_air_density(elevation, hub_height, T_hub_avg)
                
    #             self.ad_corrected_data = adc.normalize_wind_speed_power(self.client_power_data, rho_site)
                
    #             self._populate_ad_table()
    #             self.ad_data_dock.setVisible(True)
                
    #             QMessageBox.information(
    #                 self, "Success", 
    #                 f"AD Correction Applied\n"
    #                 f"Turbine: {turbine_obj['wtg_id']}\n"
    #                 f"Elevation: {elevation}m\n"
    #                 f"Hub Height: {hub_height}m\n"
    #                 f"T_hub: {T_hub_avg:.2f}°C\n"
    #                 f"ρ_site: {rho_site:.3f} kg/m³"
    #             )
                
    #         except Exception as e:
    #             import traceback
    #             traceback.print_exc()
    #             QMessageBox.critical(self, "Error", f"AD correction failed: {e}")
    #             self.enable_air_density_correction.setChecked(False)
    #     else:
    #         if hasattr(self, 'ad_data_dock'):
    #             self.ad_data_dock.setVisible(False)
        
    #     self.update_plot()

    # def _handle_ad_correction(self):
    #     if self.enable_air_density_correction.isChecked():
    #         # Validations
    #         if self.client_power_data is None or self.client_power_data.empty:
    #             QMessageBox.warning(self, "Warning", "No AD reference curve found in database.")
    #             self.enable_air_density_correction.setChecked(False)
    #             return
            
    #         if self.coordinate_data is None:
    #             QMessageBox.warning(self, "Warning", "No coordinate data found in database.\nPlease recreate the project with coordinate file.")
    #             self.enable_air_density_correction.setChecked(False)
    #             return
            
    #         if self.coordinate_data.empty:
    #             QMessageBox.warning(self, "Warning", "Coordinate data is empty.")
    #             self.enable_air_density_correction.setChecked(False)
    #             return
            
    #         if self.data is None or self.data.empty:
    #             QMessageBox.warning(self, "Warning", "No turbine data loaded.")
    #             self.enable_air_density_correction.setChecked(False)
    #             return
            
    #         try:
    #             turbine_map, _ = self._build_turbine_lookup(self.coordinate_data)
                
    #             if turbine_map is None:
    #                 QMessageBox.warning(self, "Warning", "Failed to parse coordinate file.")
    #                 self.enable_air_density_correction.setChecked(False)
    #                 return
                
    #             turbine_obj = self._find_turbine_data(turbine_map, self.turbine_name)
                
    #             if turbine_obj is None:
    #                 available = list(turbine_map.keys())[:10]
    #                 QMessageBox.warning(self, "Warning", f"Turbine '{self.turbine_name}' not found.\nAvailable: {available}")
    #                 self.enable_air_density_correction.setChecked(False)
    #                 return
                
    #             elevation = turbine_obj['elevation']
    #             hub_height = turbine_obj['hub_height']
                
    #             from views.visualization_components import air_density_correction as adc
    #             T_hub_avg = adc.get_t_hub_average(self.data, None)
    #             rho_site = adc.calculate_air_density(elevation, hub_height, T_hub_avg)
                
    #             self.ad_corrected_data = adc.normalize_wind_speed_power(self.client_power_data, rho_site)
    #             # Update checkbox labels with calculated value
    #             self.show_calculated_ad.setText(f"Show Calculated AD (ρ={self.rho_site:.3f})")
    #             self.show_calculated_ad.setVisible(True)
    #             self.show_reference_ad.setVisible(True)
                
    #             self._populate_ad_table()
    #             self.ad_data_dock.setVisible(True)
                
    #             QMessageBox.information(
    #                 self, "Success", 
    #                 f"AD Correction Applied\n"
    #                 f"Turbine: {turbine_obj['wtg_id']}\n"
    #                 f"Elevation: {elevation}m\n"
    #                 f"Hub Height: {hub_height}m\n"
    #                 f"T_hub: {T_hub_avg:.2f}°C\n"
    #                 f"ρ_site: {rho_site:.3f} kg/m³"
    #             )
                
    #         except Exception as e:
    #             import traceback
    #             traceback.print_exc()
    #             QMessageBox.critical(self, "Error", f"AD correction failed: {e}")
    #             self.enable_air_density_correction.setChecked(False)
    #             self.show_calculated_ad.setVisible(False)
    #             self.show_reference_ad.setVisible(False)
    #     else:
    #         self.show_calculated_ad.setVisible(False)
    #         self.show_reference_ad.setVisible(False)
    #         if hasattr(self, 'ad_data_dock'):
    #             self.ad_data_dock.setVisible(False)
        
    #     self.update_plot()
    
    def _handle_ad_correction(self):
        if self.enable_air_density_correction.isChecked():
            # Validations
            if self.ad_reference_data is None or self.ad_reference_data.empty:
                QMessageBox.warning(self, "Warning", "No AD reference curve found in database.")
                self.enable_air_density_correction.setChecked(False)
                return
            
            if self.coordinate_data is None:
                QMessageBox.warning(self, "Warning", "No coordinate data found in database.\nPlease recreate the project with coordinate file.")
                self.enable_air_density_correction.setChecked(False)
                return
            
            if self.coordinate_data.empty:
                QMessageBox.warning(self, "Warning", "Coordinate data is empty.")
                self.enable_air_density_correction.setChecked(False)
                return
            
            if self.data is None or self.data.empty:
                QMessageBox.warning(self, "Warning", "No turbine data loaded.")
                self.enable_air_density_correction.setChecked(False)
                return
            
            try:
                turbine_map, _ = self._build_turbine_lookup(self.coordinate_data)
                
                if turbine_map is None:
                    QMessageBox.warning(self, "Warning", "Failed to parse coordinate file.")
                    self.enable_air_density_correction.setChecked(False)
                    return
                
                turbine_obj = self._find_turbine_data(turbine_map, self.turbine_name)
                
                if turbine_obj is None:
                    available = list(turbine_map.keys())[:10]
                    QMessageBox.warning(self, "Warning", f"Turbine '{self.turbine_name}' not found.\nAvailable: {available}")
                    self.enable_air_density_correction.setChecked(False)
                    return
                
                elevation = turbine_obj['elevation']
                hub_height = turbine_obj['hub_height']
                
                from views.visualization_components import air_density_correction as adc
                T_hub_avg = adc.get_t_hub_average(self.data, None)
                self.rho_site = adc.calculate_air_density(elevation, hub_height, T_hub_avg)
                
                self.ad_corrected_data = adc.normalize_wind_speed_power(self.ad_reference_data, self.rho_site)
                
                # Update checkbox labels and show them
                self.show_calculated_ad.setText(f"Show Calculated AD (ρ={self.rho_site:.3f})")
                self.show_calculated_ad.setVisible(True)
                self.show_reference_ad.setVisible(True)
                
                self._populate_ad_table()
                self.ad_data_dock.setVisible(True)
                
                QMessageBox.information(
                    self, "Success", 
                    f"AD Correction Applied\n"
                    f"Turbine: {turbine_obj['wtg_id']}\n"
                    f"Elevation: {elevation}m\n"
                    f"Hub Height: {hub_height}m\n"
                    f"T_hub: {T_hub_avg:.2f}°C\n"
                    f"ρ_site: {self.rho_site:.3f} kg/m³"
                )
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Error", f"AD correction failed: {e}")
                self.enable_air_density_correction.setChecked(False)
                self.show_calculated_ad.setVisible(False)
                self.show_reference_ad.setVisible(False)
        else:
            self.show_calculated_ad.setVisible(False)
            self.show_reference_ad.setVisible(False)
            if hasattr(self, 'ad_data_dock'):
                self.ad_data_dock.setVisible(False)
        
        self.update_plot()

    def _plot_curve(self, plot_type):
        self.current_plot_type = plot_type
        self.bin_table_dock.setVisible(False)
        self.update_plot()
        
        if plot_type == "binned_power_curve":
            self.bin_table_dock.setVisible(True)
            self.bin_table_dock.raise_()
    
    # def update_plot(self):
    #     """Main update function - calls plotting_logic functions directly"""
    #     try:
    #         if self.data.empty or not hasattr(self, 'current_plot_type') or not self.current_plot_type:
    #             return
            
    #         self.filtered_df = self.get_filtered_data()
            
    #         # Plot main curve (this clears and draws)
    #         success = pl.plot_selected_graph(self, self.current_plot_type, self.column_cache)
            
    #         if not success or not self.figure.get_axes():
    #             return
            
    #         ax = self.figure.get_axes()[0]
            
    #         # Add overlays WITHOUT triggering redraws
    #         if self.current_plot_type == "actual_power_curve":
    #             if self.show_binned_overlay.isChecked():
    #                 pcl.overlay_binned_curve(ax, self.filtered_df, 
    #                                         self.enable_iec_binning.isChecked(), False)
                
    #             if self.show_average_line.isChecked():
    #                 pcl.overlay_average_line(ax, self.filtered_df,
    #                                         self.enable_iec_binning.isChecked(), False)
            
    #         if (self.show_ad_corrected_curve.isChecked() or self.superimpose_ad_curve.isChecked()) and \
    #            hasattr(self, 'ad_corrected_data') and self.ad_corrected_data is not None:
    #             ax.plot(self.ad_corrected_data['wind_speed_normalized'], 
    #                    self.ad_corrected_data['power_corrected'],
    #                    'g--', linewidth=2.5, label='AD Corrected Curve', zorder=10)
            
    #         # Show calculated AD curve
    #         if self.show_calculated_ad.isChecked() and hasattr(self, 'ad_corrected_data') and self.ad_corrected_data is not None:
    #             ax.plot(self.ad_corrected_data['wind_speed_normalized'], 
    #                 self.ad_corrected_data['power_corrected'],
    #                 'g--', linewidth=2.5, label=f'AD Corrected (ρ={self.rho_site:.3f})', zorder=10)
            
    #         # Show reference AD curve (original Site curve at ρ=1.225)
    #         if self.show_reference_ad.isChecked() and self.client_power_data is not None:
    #             ax.plot(self.client_power_data['wind_speed'], 
    #                 self.client_power_data['power'],
    #                 'b--', linewidth=2.5, label='Reference AD (ρ=1.225)', zorder=9)
            
    #         # Update legend once if needed
    #         if self.show_legend.isChecked():
    #             ax.legend()
            
    #         self._configure_plot_appearance()
    #         self.canvas.draw_idle()
    #         self._update_statistics()
            
    #     except Exception as e:
    #         self.handle_errors(f"Error updating plot: {str(e)}")

    
    def update_plot(self):
        """Main update function"""
        try:
            if self.data.empty or not hasattr(self, 'current_plot_type') or not self.current_plot_type:
                return
            
            self.filtered_df = self.get_filtered_data()
            
            success = pl.plot_selected_graph(self, self.current_plot_type, self.column_cache)
            
            if not success or not self.figure.get_axes():
                return
            
            ax = self.figure.get_axes()[0]
            
            if self.current_plot_type == "actual_power_curve":
                if self.show_binned_overlay.isChecked():
                    pcl.overlay_binned_curve(ax, self.filtered_df, 
                                            self.enable_iec_binning.isChecked(), False)
                
                if self.show_average_line.isChecked():
                    pcl.overlay_average_line(ax, self.filtered_df,
                                            self.enable_iec_binning.isChecked(), False)
            
            # Show calculated AD curve
            if self.show_calculated_ad.isChecked() and hasattr(self, 'ad_corrected_data') and self.ad_corrected_data is not None:
                ax.plot(self.ad_corrected_data['wind_speed_normalized'], 
                       self.ad_corrected_data['power_corrected'],
                       'g--', linewidth=2.5, label=f'AD Corrected (ρ={self.rho_site:.3f})', zorder=10)
            
            # Show reference AD curve (from AD reference file at ρ=1.225)
            if self.show_reference_ad.isChecked() and self.ad_reference_data is not None:
                ax.plot(self.ad_reference_data['wind_speed'], 
                       self.ad_reference_data['power'],
                       'b--', linewidth=2.5, label='Reference AD (ρ=1.225)', zorder=9)
            
            if self.show_legend.isChecked():
                ax.legend()
            
            self._configure_plot_appearance()
            self.canvas.draw_idle()
            self._update_statistics()
            
        except Exception as e:
            self.handle_errors(f"Error updating plot: {str(e)}")
    
    def _configure_plot_appearance(self):
        for ax in self.figure.get_axes():
            ax.set_facecolor(self.background_color.currentText())
            if self.show_grid.isChecked():
                bg = self.background_color.currentText()
                grid_color = 'white' if bg == 'black' else 'gray'
                ax.grid(True, color=grid_color, linestyle='-', alpha=0.3)
    
    def _update_statistics(self):
        if self.filtered_df is None or self.filtered_df.empty:
            return
        
        power_col = self.column_cache.get("power")
        ws_col = self.column_cache.get("wind_speed")
        
        if not power_col or not ws_col:
            return
        
        power_data = pd.to_numeric(self.filtered_df[power_col], errors='coerce').dropna()
        ws_data = pd.to_numeric(self.filtered_df[ws_col], errors='coerce').dropna()
        
        stats = [
            ("Total Records", f"{len(self.filtered_df)}"),
            ("Mean Power (kW)", f"{power_data.mean():.2f}"),
            ("Max Power (kW)", f"{power_data.max():.2f}"),
            ("Mean Wind Speed (m/s)", f"{ws_data.mean():.2f}"),
            ("Max Wind Speed (m/s)", f"{ws_data.max():.2f}"),
        ]
        
        self.stats_table.setRowCount(len(stats))
        for row, (metric, value) in enumerate(stats):
            self.stats_table.setItem(row, 0, QTableWidgetItem(metric))
            self.stats_table.setItem(row, 1, QTableWidgetItem(value))
        self.stats_table.resizeColumnsToContents()
    
    def upload_client_power_curve(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Upload Site Power Curve", 
                                                 "", "Excel Files (*.xlsx);;CSV Files (*.csv)")
        if not file_name:
            return
        
        try:
            if file_name.endswith('.xlsx'):
                df = pd.read_excel(file_name)
            else:
                df = pd.read_csv(file_name)
            
            if 'wind_speed' not in df.columns or 'power' not in df.columns:
                raise ValueError("File must contain 'wind_speed' and 'power' columns")
            
            df = df.sort_values('wind_speed')
            self.client_power_data = df
            self.standard_power_data = df
            
            min_ws = df['wind_speed'].min()
            max_ws = df['wind_speed'].max()
            self.client_power_interp = interp1d(df['wind_speed'], df['power'], 
                                               kind='linear', fill_value='extrapolate')
            
            interp_ws = np.arange(min_ws, max_ws + 0.1, 0.1)
            interp_power = self.client_power_interp(interp_ws)
            self.interpolated_client_power = pd.DataFrame({
                'wind_speed': interp_ws, 
                'power': interp_power
            })
            
            QMessageBox.information(self, "Success", "Site power curve loaded successfully!")
            self.update_plot()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading Site power curve: {e}")
    
    def _export_plot(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Plot", "", "PNG (*.png);;PDF (*.pdf)")
        if file_name:
            self.figure.savefig(file_name, bbox_inches='tight', dpi=300)
            QMessageBox.information(self, "Success", f"Plot exported to:\n{file_name}")
    
    def _export_data(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Data", "", "CSV (*.csv)")
        if file_name and self.filtered_df is not None:
            self.filtered_df.to_csv(file_name, index=False)
            QMessageBox.information(self, "Success", f"Data exported to:\n{file_name}")
    
    def _export_bin_data(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Bin Data", "", "CSV (*.csv)")
        if file_name:
            data = []
            for row in range(self.bin_table.rowCount()):
                row_data = [self.bin_table.item(row, col).text() for col in range(self.bin_table.columnCount())]
                data.append(row_data)
            df = pd.DataFrame(data, columns=["Bin Range", "Mean Power", "Min", "Max", "Count"])
            df.to_csv(file_name, index=False)
            QMessageBox.information(self, "Success", f"Bin data exported!")
    
    def handle_errors(self, msg):
        print(f"Error: {msg}")
        QMessageBox.warning(self, "Warning", msg)
    
    def set_data(self, data, column_cache=None):
        self.data = data
        if column_cache:
            self.column_cache = column_cache
        elif not self.data.empty:
            self._populate_column_cache()
        if hasattr(self, 'current_plot_type') and self.current_plot_type:
            self.update_plot()

    def _overlay_binned_curve(self):
        """Overlay binned curve on existing actual power curve plot"""
        if not self.figure.get_axes():
            return
        
        ax = self.figure.get_axes()[0]
        pcl.overlay_binned_curve(ax, self.filtered_df, 
                                self.enable_iec_binning.isChecked(),
                                self.show_legend.isChecked())
    def _overlay_average_line(self):
        """Overlay average power line on actual power curve"""
        if not self.figure.get_axes():
            return
        
        ax = self.figure.get_axes()[0]
        pcl.overlay_average_line(ax, self.filtered_df,
                                self.enable_iec_binning.isChecked(),
                                self.show_legend.isChecked())
        

    def _populate_ad_table(self):
        """Populate AD corrected data table"""
        self.ad_data_table.setRowCount(len(self.ad_corrected_data))
        for row, (ws, pwr) in enumerate(zip(
            self.ad_corrected_data['wind_speed_normalized'], 
            self.ad_corrected_data['power_corrected']
        )):
            self.ad_data_table.setItem(row, 0, QTableWidgetItem(f"{ws:.2f}"))
            self.ad_data_table.setItem(row, 1, QTableWidgetItem(f"{pwr:.2f}"))
        self.ad_data_table.resizeColumnsToContents()

    def _overlay_ad_corrected_curve(self):
        if not self.figure.get_axes() or self.ad_corrected_data is None:
            return
        
        ax = self.figure.get_axes()[0]
        ax.plot(self.ad_corrected_data['wind_speed_normalized'], 
                self.ad_corrected_data['power_corrected'],
                'g--', linewidth=2.5, label='AD Corrected Curve', zorder=10)
        
        if self.show_legend.isChecked():
            ax.legend(loc='best')

    # load from database:

    # def _load_files_from_database(self):
    #     """Auto-load coordinate and AD files from database"""
    #     from controllers.database.database_manager import DatabaseManager
        
    #     print(f"\n{'='*50}")
    #     print(f"DEBUG: PowerCurveWindow.project_id = {self.project_id}")
    #     print(f"{'='*50}")
        
    #     try:
    #         db = DatabaseManager()
            
    #         # CHECK 1: What projects exist?
    #         cursor = db.connection.execute("SELECT project_id, project_name FROM Projects")
    #         projects = cursor.fetchall()
    #         print(f"✓ Projects in database: {projects}")
            
    #         # CHECK 2: What coordinate data exists?
    #         cursor = db.connection.execute("SELECT project_id, COUNT(*) FROM CoordinateData GROUP BY project_id")
    #         coord_data = cursor.fetchall()
    #         print(f"✓ CoordinateData by project_id: {coord_data}")
            
    #         # CHECK 3: What AD data exists?
    #         cursor = db.connection.execute("SELECT project_id, COUNT(*) FROM ADReferenceData GROUP BY project_id")
    #         ad_data = cursor.fetchall()
    #         print(f"✓ ADReferenceData by project_id: {ad_data}")
            
    #         # CHECK 4: Try to load with current project_id
    #         print(f"\n--- Attempting to load with project_id={self.project_id} ---")
            
    #         coord_df = db.get_coordinate_data(self.project_id)
    #         print(f"Coordinate query result: {len(coord_df)} rows")
            
    #         ad_df = db.get_ad_reference_data(self.project_id)
    #         print(f"AD reference query result: {len(ad_df)} rows")
            
    #         print(f"{'='*50}\n")
            
    #         # Rest of your existing code...
    #         if not coord_df.empty:
    #             self.coordinate_data = coord_df
    #             print(f"✓ Loaded {len(coord_df)} turbine coordinates")
    #         else:
    #             print("⚠ No coordinate data found")
            
    #         if not ad_df.empty:
    #             self.client_power_data = ad_df
    #             self.standard_power_data = ad_df
                
    #             from scipy.interpolate import interp1d
    #             self.client_power_interp = interp1d(
    #                 ad_df['wind_speed'], ad_df['power'],
    #                 kind='linear', fill_value='extrapolate'
    #             )
    #             print(f"✓ Loaded AD reference curve ({len(ad_df)} points)")
    #         else:
    #             print("⚠ No AD reference data found")
            
    #         db.close()
    #     except Exception as e:
    #         import traceback
    #         print(f"✗ Error: {e}")
    #         traceback.print_exc()

    def _load_files_from_database(self):
        """Auto-load coordinate and AD files from database"""
        from controllers.database.database_manager import DatabaseManager
        
        try:
            db = DatabaseManager()
            
            # Load coordinate data
            coord_df = db.get_coordinate_data(self.project_id)
            if not coord_df.empty:
                self.coordinate_data = coord_df
            
            # Load AD reference data (separate from Site power curve)
            ad_df = db.get_ad_reference_data(self.project_id)
            if not ad_df.empty:
                self.ad_reference_data = ad_df
            
            db.close()
        except Exception as e:
            print(f"Error loading files from database: {e}")
        
    def _build_turbine_lookup(self, coord_df):
        """Build HashMap for O(1) turbine lookup"""
        import models.scada_utils as su
        
        # Normalize columns
        coord_df.columns = coord_df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Find required columns
        wtg_cols = su.find_matching_columns(coord_df, 'turbine_id')
        elev_cols = su.find_matching_columns(coord_df, 'elevation')
        hub_cols = su.find_matching_columns(coord_df, 'hub_height')
        
        if not (wtg_cols and elev_cols and hub_cols):
            return None, None
        
        wtg_col = wtg_cols[0]
        elev_col = elev_cols[0]
        hub_col = hub_cols[0]
        
        # Build HashMap: {turbine_id: {elevation, hub_height, ...}}
        turbine_map = {}
        
        for _, row in coord_df.iterrows():
            wtg_id = str(row[wtg_col]).strip()
            
            turbine_map[wtg_id] = {
                'wtg_id': wtg_id,
                'elevation': float(row[elev_col]),
                'hub_height': float(row[hub_col])
            }
        
        return turbine_map, None

    
    # def _find_turbine_data(self, turbine_lookup, target_id):
    #     print(f"DEBUG: Searching for: {target_id}")
    #     print(f"DEBUG: Available keys sample: {list(turbine_lookup.keys())[:10]}")
        
    #     # Try exact matches
    #     for key in [target_id, target_id.lower(), target_id.upper()]:
    #         if key in turbine_lookup:
    #             print(f"DEBUG: Found exact match: {key}")
    #             return turbine_lookup[key]
        
    #     # Try partial matches
    #     import re
    #     target_num = re.findall(r'\d+', target_id)
    #     if target_num:
    #         if target_num[-1] in turbine_lookup:
    #             print(f"DEBUG: Found number match: {target_num[-1]}")
    #             return turbine_lookup[target_num[-1]]
        
    #     print(f"DEBUG: No match found for {target_id}")
    #     return None
    
    def _find_turbine_data(self, turbine_map, target_id):
        """O(1) lookup with fallback strategies"""
        target_id = str(target_id).strip()
        
        # Strategy 1: Direct match
        if target_id in turbine_map:
            return turbine_map[target_id]
        
        # Strategy 2: Case-insensitive match
        target_lower = target_id.lower()
        for key, value in turbine_map.items():
            if key.lower() == target_lower:
                return value
        
        # Strategy 3: Partial match (e.g., "329" matches "Tut-329")
        import re
        target_num = re.findall(r'\d+', target_id)
        if target_num:
            num = target_num[-1]
            for key, value in turbine_map.items():
                if num in key:
                    return value
        
        return None
    
    def _populate_ad_table(self):
        self.ad_data_table.setRowCount(len(self.ad_corrected_data))
        for row, (ws, pwr) in enumerate(zip(self.ad_corrected_data['wind_speed_normalized'], self.ad_corrected_data['power_corrected'])):
            self.ad_data_table.setItem(row, 0, QTableWidgetItem(f"{ws:.2f}"))
            self.ad_data_table.setItem(row, 1, QTableWidgetItem(f"{pwr:.2f}"))
        self.ad_data_table.resizeColumnsToContents()

    def closeEvent(self, event):
        event.accept()