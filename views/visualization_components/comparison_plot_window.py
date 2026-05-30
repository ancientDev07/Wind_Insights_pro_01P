from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from utils.collapsible_prop import CollapsibleSection
from utils.datetime_utils import get_datetime_info
from . import plotting_logic as pl
from . import power_curve_logic as pcl

class ComparisonPlotWindow(QMainWindow):
    """Dynamic windrose + power curve comparison with sector-based filtering"""
    
    def __init__(self, data=None, turbine_name=None, parent=None, project_id=None):
        super().__init__(parent)
        self.setWindowTitle(f"Windrose-Power Curve Comparison - {turbine_name}" if turbine_name else "Comparison Plot")
        self.setGeometry(100, 100, 1600, 900)
        
        # Data attributes
        self.data = data if data is not None else pd.DataFrame()
        self.turbine_name = turbine_name
        self.project_id = project_id
        self.column_cache = {}
        self.filtered_df = None
        self.client_power_data = None
        self.client_power_interp = None
        self.ad_reference_data = None
        self.ad_corrected_data = None
        self.rho_site = None
        
        # Sector filtering state
        self.selected_sector = None
        self.sector_bounds = {}  # {sector_id: (min_dir, max_dir)}
        self.full_data = None  # Cache unfiltered data
        self.sector_data_cache = {}  # {sector_id: filtered_df}
        
        # UI state
        self.current_windrose_sectors = 16
        
        # Window setup
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        # Load data
        if self.project_id:
            self._load_files_from_database()
        
        if not self.data.empty:
            self._populate_column_cache()
            self.process_data()
            self.full_data = self.data.copy()
        
        # Initialize UI
        self._init_ui_components()
        self.apply_styles()
        self.init_ui()
        self._setup_docks()
        self._connect_signals()
        
        # Initial plot
        if not self.data.empty:
            self.update_comparison_plot()
    
    def _populate_column_cache(self):
        """Populate column cache for common parameters"""
        import models.scada_utils as su
        params = ["wind_speed", "power", "nacelle_direction", "timestamp"]
        for param in params:
            matched = su.find_matching_columns(self.data, param)
            self.column_cache[param] = matched[0] if matched else None
    
    def process_data(self):
        """Convert timestamp to datetime"""
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
        """Get column name from cache"""
        if param not in self.column_cache:
            import models.scada_utils as su
            matched_columns = su.find_matching_columns(self.data, param)
            self.column_cache[param] = matched_columns[0] if matched_columns else None
        return self.column_cache[param]
    
    def _init_ui_components(self):
        """Initialize UI components"""
        self.figure = Figure(figsize=(14, 8))
        self.canvas = FigureCanvas(self.figure)
        
        # Checkboxes
        self.show_grid = QCheckBox("Show Grid")
        self.show_grid.setChecked(True)
        self.show_legend = QCheckBox("Show Legend")
        self.show_legend.setChecked(True)
        self.show_standard_power_curve = QCheckBox("Show Client Power Curve")
        self.enable_iec_binning = QCheckBox("Enable IEC Binning")
        self.remove_negative_power = QCheckBox("Remove Negative Power (≤ 0)")
        self.show_original_values = QCheckBox("Show Original Values")
        
        # Windrose config
        self.windrose_sectors_group = QButtonGroup()
        self.windrose_8 = QRadioButton("8 Sectors")
        self.windrose_12 = QRadioButton("12 Sectors")
        self.windrose_16 = QRadioButton("16 Sectors")
        self.windrose_24 = QRadioButton("24 Sectors")
        self.windrose_36 = QRadioButton("36 Sectors")
        self.windrose_16.setChecked(True)
        
        self.windrose_sectors_group.addButton(self.windrose_8, 8)
        self.windrose_sectors_group.addButton(self.windrose_12, 12)
        self.windrose_sectors_group.addButton(self.windrose_16, 16)
        self.windrose_sectors_group.addButton(self.windrose_24, 24)
        self.windrose_sectors_group.addButton(self.windrose_36, 36)
        
        # Sector info label
        self.sector_info_label = QLabel("No sector selected")
        self.sector_info_label.setStyleSheet("color: #0078d7; font-weight: bold;")
        
        # Background color
        self.background_color = QComboBox()
        self.background_color.addItems(["white", "lightgray", "darkgray", "black"])
        
        # Action buttons
        self.clear_sector_btn = QPushButton("Clear Sector Filter")
        self.clear_sector_btn.setEnabled(False)
        self.export_plot_btn = QPushButton("Export Plot")
        self.export_sector_data_btn = QPushButton("Export Sector Data")
    
    def apply_styles(self):
        """Apply stylesheet"""
        self.setStyleSheet("""
            QMainWindow { background-color: #f7f7f7; }
            QGroupBox { font-weight: bold; border: 2px solid #d3d3d3; border-radius: 8px; 
                       margin-top: 15px; padding-top: 10px; background-color: #ffffff;}
            QGroupBox::title {subcontrol-origin: margin; subcontrol-position: top left; 
                             padding: 4px 12px; background-color: #3498DB; color: white; 
                             border-radius: 4px; left: 10px; top: -8px;}
            QCheckBox, QRadioButton { spacing: 5px; font-size: 11px; }
            QPushButton { background-color: #0078d7; color: white; border: none; 
                         padding: 6px 12px; border-radius: 4px; font-size: 11px;}
            QPushButton:hover { background-color: #005a9e; }
            QPushButton:disabled { background-color: #ccc; }
            QComboBox { padding: 4px; border: 1px solid #ccc; border-radius: 4px; 
                       background-color: #ffffff; color: black; font-size: 11px;}
        """)
    
    def init_ui(self):
        """Setup main UI layout with dual subplots"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Plot panel with dual axes
        plot_panel = QWidget()
        plot_layout = QVBoxLayout(plot_panel)
        self.toolbar = NavigationToolbar(self.canvas, plot_panel)
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        
        splitter.addWidget(plot_panel)
        splitter.setSizes([1200, 400])
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(splitter)
    
    def _setup_docks(self):
        """Setup dock widgets"""
        self._setup_command_center()
        self._setup_sector_info_dock()
        self._setup_statistics_dock()
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
    
    def _setup_command_center(self):
        """Setup command center dock"""
        self.command_center = QDockWidget("Command Center", self)
        self.command_center.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.command_center.setMinimumWidth(280)
        self.command_center.setMaximumWidth(350)
        
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Data selection
        scroll_layout.addWidget(self._create_data_selection_group())
        
        # Windrose options
        scroll_layout.addWidget(self._create_windrose_options_group())
        
        # Plot options
        scroll_layout.addWidget(self._create_plot_options_group())
        
        # Actions
        scroll_layout.addWidget(self._create_actions_group())
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        self.command_center.setWidget(scroll_area)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.command_center)
    
    def _create_data_selection_group(self):
        """Create data selection group"""
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
        
        self.start_time_label = QLabel("From Time:")
        layout.addWidget(self.start_time_label, 4, 0)
        self.start_time_only = QLineEdit(min_time)
        layout.addWidget(self.start_time_only, 4, 1)
        
        self.end_time_label = QLabel("To Time:")
        layout.addWidget(self.end_time_label, 5, 0)
        self.end_time_only = QLineEdit(max_time)
        layout.addWidget(self.end_time_only, 5, 1)
        
        self._toggle_time_filter()
        
        layout.addWidget(QLabel("Background:"), 6, 0)
        layout.addWidget(self.background_color, 6, 1)
        
        return CollapsibleSection("Data Selection", content, expanded=True)
    
    def _create_windrose_options_group(self):
        """Create windrose configuration group"""
        content = QWidget()
        layout = QGridLayout(content)
        layout.setVerticalSpacing(8)
        
        layout.addWidget(QLabel("Windrose Sectors:"), 0, 0, 1, 2)
        layout.addWidget(self.windrose_8, 1, 0)
        layout.addWidget(self.windrose_12, 1, 1)
        layout.addWidget(self.windrose_16, 2, 0)
        layout.addWidget(self.windrose_24, 2, 1)
        layout.addWidget(self.windrose_36, 3, 0)
        
        return CollapsibleSection("Windrose Config", content, expanded=True)
    
    def _create_plot_options_group(self):
        """Create plot options group"""
        content = QWidget()
        layout = QVBoxLayout(content)
        
        layout.addWidget(self.show_grid)
        layout.addWidget(self.show_legend)
        layout.addWidget(self.enable_iec_binning)
        layout.addWidget(self.remove_negative_power)
        layout.addWidget(self.show_original_values)
        layout.addWidget(self.show_standard_power_curve)
        
        return CollapsibleSection("Plot Options", content, expanded=True)
    
    def _create_actions_group(self):
        """Create actions group"""
        content = QWidget()
        layout = QVBoxLayout(content)
        
        layout.addWidget(QLabel("Sector Info:"))
        layout.addWidget(self.sector_info_label)
        layout.addWidget(self.clear_sector_btn)
        layout.addWidget(self.export_plot_btn)
        layout.addWidget(self.export_sector_data_btn)
        
        return CollapsibleSection("Actions", content, expanded=True)
    
    def _setup_sector_info_dock(self):
        """Setup sector information dock"""
        self.sector_info_dock = QDockWidget("Sector Statistics", self)
        self.sector_info_table = QTableWidget()
        self.sector_info_table.setColumnCount(2)
        self.sector_info_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.sector_info_table.horizontalHeader().setStretchLastSection(True)
        self.sector_info_table.setAlternatingRowColors(True)
        self.sector_info_dock.setWidget(self.sector_info_table)
        self.addDockWidget(Qt.RightDockWidgetArea, self.sector_info_dock)
    
    def _setup_statistics_dock(self):
        """Setup full dataset statistics dock"""
        self.stats_dock = QDockWidget("Full Data Statistics", self)
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.setAlternatingRowColors(True)
        self.stats_dock.setWidget(self.stats_table)
        self.addDockWidget(Qt.RightDockWidgetArea, self.stats_dock)
        self.tabifyDockWidget(self.sector_info_dock, self.stats_dock)
    
    def _toggle_date_filter(self):
        """Toggle date filter visibility"""
        enabled = self.enable_date_filter.isChecked()
        for w in [self.start_date_label, self.start_date_only, self.end_date_label, self.end_date_only]:
            w.setVisible(enabled)
            w.setEnabled(enabled)
    
    def _toggle_time_filter(self):
        """Toggle time filter visibility"""
        enabled = self.enable_time_filter.isChecked()
        for w in [self.start_time_label, self.start_time_only, self.end_time_label, self.end_time_only]:
            w.setVisible(enabled)
            w.setEnabled(enabled)
    
    def _connect_signals(self):
        """Connect all signals"""
        # Windrose sector changes
        self.windrose_8.toggled.connect(lambda: self._on_sector_config_changed(8))
        self.windrose_12.toggled.connect(lambda: self._on_sector_config_changed(12))
        self.windrose_16.toggled.connect(lambda: self._on_sector_config_changed(16))
        self.windrose_24.toggled.connect(lambda: self._on_sector_config_changed(24))
        self.windrose_36.toggled.connect(lambda: self._on_sector_config_changed(36))
        
        # Plot options
        self.show_grid.stateChanged.connect(self.update_comparison_plot)
        self.show_legend.stateChanged.connect(self.update_comparison_plot)
        self.enable_iec_binning.stateChanged.connect(self.update_comparison_plot)
        self.remove_negative_power.stateChanged.connect(self.update_comparison_plot)
        self.show_standard_power_curve.stateChanged.connect(self.update_comparison_plot)
        self.background_color.currentIndexChanged.connect(self.update_comparison_plot)
        
        # Data filters
        self.start_date_only.editingFinished.connect(self.update_comparison_plot)
        self.end_date_only.editingFinished.connect(self.update_comparison_plot)
        self.start_time_only.editingFinished.connect(self.update_comparison_plot)
        self.end_time_only.editingFinished.connect(self.update_comparison_plot)
        
        # Actions
        self.clear_sector_btn.clicked.connect(self.clear_sector_filter)
        self.export_plot_btn.clicked.connect(self._export_plot)
        self.export_sector_data_btn.clicked.connect(self._export_sector_data)
        
        # Canvas click events
        self.canvas.mpl_connect('pick_event', self.on_windrose_bar_clicked)
    
    def _on_sector_config_changed(self, num_sectors):
        """Handle windrose sector configuration change"""
        if num_sectors != self.current_windrose_sectors:
            self.current_windrose_sectors = num_sectors
            self.selected_sector = None
            self.sector_bounds.clear()
            self.sector_data_cache.clear()
            self.update_comparison_plot()
    
    def get_filtered_data(self):
        """Get filtered data based on date/time filters"""
        df = self.full_data.copy()
        
        timestamp_col = self.get_cached_columns("timestamp")
        if not timestamp_col or timestamp_col not in df.columns:
            return df
        
        try:
            # Date filtering
            if self.enable_date_filter.isChecked():
                start_date = pd.to_datetime(self.start_date_only.text(), format='%d-%m-%Y')
                end_date = pd.to_datetime(self.end_date_only.text(), format='%d-%m-%Y')
                df = df[(df[timestamp_col] >= start_date) & (df[timestamp_col] <= end_date)]
            
            # Time filtering
            if self.enable_time_filter.isChecked():
                start_time = pd.to_datetime(self.start_time_only.text(), format='%H:%M').time()
                end_time = pd.to_datetime(self.end_time_only.text(), format='%H:%M').time()
                df['_time'] = df[timestamp_col].dt.time
                df = df[(df['_time'] >= start_time) & (df['_time'] <= end_time)]
                df.drop('_time', axis=1, inplace=True)
        except Exception as e:
            print(f"Error applying filters: {e}")
        
        return df
    
    def update_comparison_plot(self):
        """Update windrose and power curve plots"""
        try:
            if self.data.empty or not self.column_cache.get("wind_speed"):
                return
            
            self.figure.clear()
            
            # Get filtered data
            filtered_df = self.get_filtered_data()
            if filtered_df.empty:
                self.handle_errors("No data matches current filters")
                return
            
            # Create subplots: windrose on left, power curve on right
            gs = self.figure.add_gridspec(1, 2, width_ratios=[1, 1.2], wspace=0.3)
            
            # Windrose subplot
            self.ax_windrose = self.figure.add_subplot(gs[0])
            self._plot_windrose(filtered_df, self.ax_windrose)
            
            # Power curve subplot (either full or filtered by sector)
            self.ax_powerc = self.figure.add_subplot(gs[1])
            pc_data = self.sector_data_cache.get(self.selected_sector, filtered_df) \
                     if self.selected_sector else filtered_df
            self._plot_power_curve(pc_data, self.ax_powerc)
            
            self._configure_plot_appearance()
            self.canvas.draw_idle()
            self._update_statistics(filtered_df)
            
        except Exception as e:
            self.handle_errors(f"Error updating plots: {str(e)}")
    
    # def _plot_windrose(self, data, ax):
    #     """Plot windrose with pick event support"""
    #     wind_speed_col = self.column_cache.get("wind_speed")
    #     wind_dir_col = self.column_cache.get("nacelle_direction")
        
    #     if not wind_speed_col or not wind_dir_col:
    #         return
        
    #     speed_data = pd.to_numeric(data[wind_speed_col], errors='coerce')
    #     dir_data = pd.to_numeric(data[wind_dir_col], errors='coerce')
        
    #     # Validate data
    #     valid_mask = ~(speed_data.isna() | dir_data.isna())
    #     speed_clean = speed_data[valid_mask].values
    #     dir_clean = dir_data[valid_mask].values
        
    #     if len(speed_clean) == 0:
    #         self.handle_errors("No valid windrose data")
    #         return
        
    #     max_speed = np.max(speed_clean)
    #     if max_speed == 0:
    #         return
        
    #     # Windrose configuration
    #     from windrose import WindroseAxes
        
    #     bin_edges = np.arange(0, max_speed + 0.5, 0.5)
    #     cmap = plt.get_cmap("viridis")
        
    #     # Clear and recreate windrose on given axes
    #     ax.clear()
    #     windrose_ax = WindroseAxes(ax, fig=self.figure)
    #     windrose_ax.bar(dir_clean, speed_clean, bins=bin_edges, 
    #                    nsector=self.current_windrose_sectors, cmap=cmap, normed=True)
        
    #     # Configure windrose
    #     windrose_ax.set_theta_zero_location('N')
    #     windrose_ax.set_theta_direction(-1)
        
    #     # Set sector ticks
    #     tick_angles = np.linspace(0, 2 * np.pi, self.current_windrose_sectors + 1)[:-1]
    #     tick_degrees = np.linspace(0, 360, self.current_windrose_sectors, endpoint=False)
    #     windrose_ax.set_xticks(tick_angles)
    #     windrose_ax.set_xticklabels([f"{int(deg)}°" for deg in tick_degrees], fontsize=9)
        
    #     windrose_ax.set_title("Wind Direction Distribution", fontsize=11, fontweight='bold')
        
    #     # Store sector bounds for later filtering
    #     self._calculate_sector_bounds()
        
    #     # Make bars pickable
    #     for bar in windrose_ax.containers[0]:
    #         bar.set_picker(True)
    #         bar.set_pickradius(5)
        
    #     if self.show_legend.isChecked():
    #         windrose_ax.legend(loc='upper left', fontsize=9)
    
    def _plot_windrose(self, data, ax):
        """Plot windrose with pick event support"""
        wind_speed_col = self.column_cache.get("wind_speed")
        wind_dir_col = self.column_cache.get("nacelle_direction")
        
        if not wind_speed_col or not wind_dir_col:
            return
        
        speed_data = pd.to_numeric(data[wind_speed_col], errors='coerce')
        dir_data = pd.to_numeric(data[wind_dir_col], errors='coerce')
        
        # Validate data
        valid_mask = ~(speed_data.isna() | dir_data.isna())
        speed_clean = speed_data[valid_mask].values
        dir_clean = dir_data[valid_mask].values
        
        if len(speed_clean) == 0:
            self.handle_errors("No valid windrose data")
            return
        
        max_speed = np.max(speed_clean)
        if max_speed == 0:
            return
        
        # Windrose configuration
        from windrose import WindroseAxes
        
        bin_edges = np.arange(0, max_speed + 0.5, 0.5)
        cmap = plt.get_cmap("viridis")
        
        # Create windrose using WindroseAxes
        ax.clear()
        windrose_ax = WindroseAxes.from_ax(ax=ax, fig=self.figure)
        bars = windrose_ax.bar(dir_clean, speed_clean, bins=bin_edges, 
                       nsector=self.current_windrose_sectors, cmap=cmap, normed=True)
        
        # Configure windrose
        windrose_ax.set_theta_zero_location('N')
        windrose_ax.set_theta_direction(-1)
        
        # Set sector ticks
        tick_angles = np.linspace(0, 2 * np.pi, self.current_windrose_sectors + 1)[:-1]
        tick_degrees = np.linspace(0, 360, self.current_windrose_sectors, endpoint=False)
        windrose_ax.set_xticks(tick_angles)
        windrose_ax.set_xticklabels([f"{int(deg)}°" for deg in tick_degrees], fontsize=9)
        
        windrose_ax.set_title("Wind Direction Distribution", fontsize=11, fontweight='bold')
        
        # Store sector bounds for later filtering
        self._calculate_sector_bounds()
        
        # Make bars pickable for sector clicking
        for container in windrose_ax.containers:
            for patch in container.patches:
                patch.set_picker(True)
                patch.set_pickradius(5)
        
        if self.show_legend.isChecked():
            windrose_ax.legend(loc='upper left', fontsize=9)

    
    def _calculate_sector_bounds(self):
        """Calculate direction bounds for each sector"""
        self.sector_bounds.clear()
        sector_width = 360 / self.current_windrose_sectors
        
        for sector_id in range(self.current_windrose_sectors):
            min_dir = (sector_id * sector_width - sector_width / 2) % 360
            max_dir = min_dir + sector_width
            self.sector_bounds[sector_id] = (min_dir, max_dir)
    
    def on_windrose_bar_clicked(self, event):
        """Handle windrose bar click event"""
        if event.artist is None or not hasattr(self, 'ax_windrose'):
            return
        
        # Get the clicked patch
        clicked_patch = event.artist
        
        # Find which sector was clicked by checking the patch's theta position
        # Each patch has a theta attribute representing its angular position
        if hasattr(clicked_patch, 'theta'):
            theta_deg = np.degrees(clicked_patch.theta) % 360
            
            # Calculate which sector this corresponds to
            sector_width = 360 / self.current_windrose_sectors
            sector_id = int((theta_deg + sector_width / 2) / sector_width) % self.current_windrose_sectors
            
            self._apply_sector_filter(sector_id)
    
    def _apply_sector_filter(self, sector_id):
        """Apply directional sector filter and update power curve"""
        self.selected_sector = sector_id
        
        # Calculate direction bounds
        sector_width = 360 / self.current_windrose_sectors
        min_dir = (sector_id * sector_width - sector_width / 2) % 360
        max_dir = min_dir + sector_width
        
        # Filter data for this sector
        direction_col = self.column_cache.get("nacelle_direction")
        if not direction_col:
            return
        
        filtered_df = self.get_filtered_data()
        dir_data = pd.to_numeric(filtered_df[direction_col], errors='coerce')
        
        # Handle wraparound (e.g., 350-10 degrees)
        if max_dir > 360:
            mask = (dir_data >= min_dir) | (dir_data < (max_dir - 360))
        else:
            mask = (dir_data >= min_dir) & (dir_data < max_dir)
        
        sector_filtered = filtered_df[mask]
        
        # Cache and update
        self.sector_data_cache[sector_id] = sector_filtered
        
        # Update UI
        count = len(sector_filtered)
        self.sector_info_label.setText(
            f"Sector {sector_id} ({min_dir:.0f}°-{max_dir:.0f}°): {count} records"
        )
        self.clear_sector_btn.setEnabled(True)
        self.export_sector_data_btn.setEnabled(True)
        
        # Update sector statistics table
        self._update_sector_statistics(sector_filtered)
        
        # Refresh plots
        self.update_comparison_plot()
    
    def clear_sector_filter(self):
        """Clear sector filter and show all data"""
        self.selected_sector = None
        self.sector_data_cache.clear()
        self.sector_info_label.setText("No sector selected")
        self.clear_sector_btn.setEnabled(False)
        self.export_sector_data_btn.setEnabled(False)
        self.sector_info_table.setRowCount(0)
        self.update_comparison_plot()
    
    def _plot_power_curve(self, data, ax):
        """Plot power curve for current data (full or sector-filtered)"""
        wind_speed_col = self.column_cache.get("wind_speed")
        power_col = self.column_cache.get("power")
        
        if not wind_speed_col or not power_col:
            return
        
        speed_data = pd.to_numeric(data[wind_speed_col], errors='coerce')
        power_data = pd.to_numeric(data[power_col], errors='coerce')
        
        df = pd.DataFrame({'wind_speed': speed_data, 'power': power_data}).dropna()
        
        if self.remove_negative_power.isChecked():
            df = df[df['power'] > 0]
        
        if df.empty:
            ax.text(0.5, 0.5, 'No valid power data', ha='center', va='center', 
                   transform=ax.transAxes)
            return
        
        # Scatter plot
        scatter = ax.scatter(df['wind_speed'], df['power'], 
                            c=df['power'], cmap='viridis', 
                            s=20, alpha=0.6, label="Power Data")
        cbar = self.figure.colorbar(scatter, ax=ax)
        cbar.set_label('Power (kW)', rotation=270, labelpad=15)
        
        # Binned overlay if enabled
        if self.enable_iec_binning.isChecked():
            self._add_binned_curve_overlay(ax, df)
        
        # Client power curve overlay
        if self.show_standard_power_curve.isChecked() and self.client_power_interp:
            min_ws = df['wind_speed'].min()
            max_ws = df['wind_speed'].max()
            x_plot = np.linspace(min_ws, max_ws, 200)
            y_plot = self.client_power_interp(x_plot)
            ax.plot(x_plot, y_plot, 'r-', linewidth=2.5, label='Client Power Curve', zorder=10)
        
        ax.set_xlabel("Wind Speed (m/s)", fontsize=10)
        ax.set_ylabel("Power (kW)", fontsize=10)
        title = f"Power Curve"
        if self.selected_sector is not None:
            title += f" - Sector {self.selected_sector}"
        ax.set_title(title, fontsize=11, fontweight='bold')
        
        if self.show_legend.isChecked():
            ax.legend(loc='best', fontsize=9)
        
        ax.grid(True, alpha=0.3)
    
    def _add_binned_curve_overlay(self, ax, df):
        """Add binned power curve overlay"""
        from utils.binning_utils import get_bins, bin_data
        
        bin_width = 1
        enable_iec = self.enable_iec_binning.isChecked()
        bins = get_bins(df['wind_speed'].max(), enable_iec, bin_width)
        df['bin'] = bin_data(df, 'wind_speed', bins)
        
        binned = df.groupby('bin', observed=True).agg({
            'wind_speed': 'mean',
            'power': 'mean'
        }).dropna()
        
        if not binned.empty:
            ax.plot(binned['wind_speed'], binned['power'], 
                   'b--', linewidth=2, marker='o', markersize=5,
                   label='Binned Curve', zorder=5, alpha=0.7)
    
    def _configure_plot_appearance(self):
        """Configure plot appearance"""
        bg_color = self.background_color.currentText()
        for ax in self.figure.get_axes():
            ax.set_facecolor(bg_color)
            if self.show_grid.isChecked():
                grid_color = 'white' if bg_color == 'black' else 'gray'
                ax.grid(True, color=grid_color, linestyle='-', alpha=0.3)
    
    def _update_statistics(self, data):
        """Update full dataset statistics"""
        wind_speed_col = self.column_cache.get("wind_speed")
        power_col = self.column_cache.get("power")
        wind_dir_col = self.column_cache.get("nacelle_direction")
        
        if not wind_speed_col:
            return
        
        ws_data = pd.to_numeric(data[wind_speed_col], errors='coerce').dropna()
        
        stats = [
            ("Total Records", f"{len(data)}"),
            ("Mean Wind Speed (m/s)", f"{ws_data.mean():.2f}"),
            ("Max Wind Speed (m/s)", f"{ws_data.max():.2f}"),
            ("Std Dev (m/s)", f"{ws_data.std():.2f}"),
        ]
        
        if power_col:
            power_data = pd.to_numeric(data[power_col], errors='coerce').dropna()
            stats.extend([
                ("Mean Power (kW)", f"{power_data.mean():.2f}"),
                ("Max Power (kW)", f"{power_data.max():.2f}"),
            ])
        
        if wind_dir_col:
            dir_data = pd.to_numeric(data[wind_dir_col], errors='coerce').dropna()
            stats.append(("Prevailing Direction (°)", f"{dir_data.mode().values[0]:.0f}"))
        
        self.stats_table.setRowCount(len(stats))
        for row, (metric, value) in enumerate(stats):
            self.stats_table.setItem(row, 0, QTableWidgetItem(metric))
            self.stats_table.setItem(row, 1, QTableWidgetItem(value))
        self.stats_table.resizeColumnsToContents()
    
    def _update_sector_statistics(self, data):
        """Update sector-specific statistics"""
        if data.empty:
            return
        
        wind_speed_col = self.column_cache.get("wind_speed")
        power_col = self.column_cache.get("power")
        
        stats = [
            ("Records in Sector", f"{len(data)}"),
            ("% of Total", f"{len(data)/len(self.full_data)*100:.1f}%"),
        ]
        
        if wind_speed_col:
            ws_data = pd.to_numeric(data[wind_speed_col], errors='coerce').dropna()
            stats.extend([
                ("Mean WS (m/s)", f"{ws_data.mean():.2f}"),
                ("Max WS (m/s)", f"{ws_data.max():.2f}"),
            ])
        
        if power_col:
            power_data = pd.to_numeric(data[power_col], errors='coerce').dropna()
            stats.extend([
                ("Mean Power (kW)", f"{power_data.mean():.2f}"),
                ("Max Power (kW)", f"{power_data.max():.2f}"),
            ])
        
        self.sector_info_table.setRowCount(len(stats))
        for row, (metric, value) in enumerate(stats):
            self.sector_info_table.setItem(row, 0, QTableWidgetItem(metric))
            self.sector_info_table.setItem(row, 1, QTableWidgetItem(value))
        self.sector_info_table.resizeColumnsToContents()
    
    def _export_plot(self):
        """Export comparison plot"""
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Export Plot", "", "PNG (*.png);;PDF (*.pdf)")
        if file_name:
            self.figure.savefig(file_name, bbox_inches='tight', dpi=300)
            self.statusBar.showMessage(f"Plot exported: {file_name}")
    
    def _export_sector_data(self):
        """Export sector-filtered data"""
        if not self.selected_sector:
            QMessageBox.warning(self, "Warning", "No sector selected")
            return
        
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Export Sector Data", "", "CSV (*.csv)")
        if file_name and self.selected_sector in self.sector_data_cache:
            self.sector_data_cache[self.selected_sector].to_csv(file_name, index=False)
            self.statusBar.showMessage(f"Sector data exported: {file_name}")
    
    def _load_files_from_database(self):
        """Load data from database"""
        from controllers.database.database_manager import DatabaseManager
        try:
            db = DatabaseManager()
            ad_df = db.get_ad_reference_data(self.project_id)
            if not ad_df.empty:
                self.ad_reference_data = ad_df
                self.client_power_data = ad_df
                self.client_power_interp = interp1d(
                    ad_df['wind_speed'], ad_df['power'],
                    kind='linear', fill_value='extrapolate')
            db.close()
        except Exception as e:
            print(f"Error loading from database: {e}")
    
    def handle_errors(self, msg):
        """Handle and display errors"""
        print(f"Error: {msg}")
        self.statusBar.showMessage(msg)
    
    def set_data(self, data, column_cache=None):
        """Set data for comparison"""
        self.data = data
        self.full_data = data.copy()
        if column_cache:
            self.column_cache = column_cache
        elif not self.data.empty:
            self._populate_column_cache()
        self.update_comparison_plot()
    
    def closeEvent(self, event):
        event.accept()