from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import mplcursors
from models import scada_utils as su
from utils import datetime_utils as dtu

class CollapsibleSidebar(QFrame):
    """Collapsible sidebar widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        self.collapsed = False
        self.normal_width = 350
        self.collapsed_width = 30
        
        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        
        # Toggle button
        self.toggle_btn = QPushButton("◀")
        self.toggle_btn.setMaximumWidth(20)
        self.toggle_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        
        self.main_layout.addWidget(self.content_widget)
        self.main_layout.addWidget(self.toggle_btn)
        
        self.setMinimumWidth(self.normal_width)
        self.setMaximumWidth(self.normal_width)
    
    def toggle_sidebar(self):
        """Toggle sidebar collapse/expand"""
        if self.collapsed:
            self.expand_sidebar()
        else:
            self.collapse_sidebar()
    
    def collapse_sidebar(self):
        """Collapse sidebar"""
        self.collapsed = True
        self.content_widget.hide()
        self.toggle_btn.setText("▶")
        self.setMinimumWidth(self.collapsed_width)
        self.setMaximumWidth(self.collapsed_width)
    
    def expand_sidebar(self):
        """Expand sidebar"""
        self.collapsed = False
        self.content_widget.show()
        self.toggle_btn.setText("◀")
        self.setMinimumWidth(self.normal_width)
        self.setMaximumWidth(self.normal_width)
        
# 2. Fix the InteractiveMarker class to include color
class InteractiveMarker:
    def __init__(self, x, y, label, timestamp, color='red'):
        self.x = x
        self.y = y
        self.label = label
        self.timestamp = timestamp
        self.color = color
        self.artist = None

class TemperatureAnalysisWindow(QMainWindow):
    def __init__(self, data=None, turbine_name=None, parent=None, project_id=None):
        super().__init__(parent)
        # Set window title with turbine name (same as VisualizationWindow)
        if turbine_name:
            self.setWindowTitle(f"Temperature Analysis Tool: {turbine_name}")
        else:
            self.setWindowTitle("Temperature Analysis Tool")
    
        self.setGeometry(100, 100, 1400, 800)
        self.setMinimumSize(1200, 700)
        self.setFont(QFont("Times Roman New", 10))
        
        # Data
        # self.data = data.copy() if data is not None else pd.DataFrame()
        self.data = data if data is not None else pd.DataFrame()
        self.filtered_data = None
        self.column_cache = {}
        self.markers = []  # Store interactive markers
        self.project_id = project_id
        
        # Initialize column cache
        self.init_column_cache()
        # SDI: Independent window
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Initialize temp_checkboxes dictionary
        self.temp_checkboxes = {}
        # Temperature tags from scada_utils
        self.temp_categories = [
            'generator_temp', 'bearing_temp', 'gearbox_temp', 'ambient_temp', 
            'cabinet_temp', 'motor_temp', 'nacelle_temp'
        ]
        
        self.power_column = self.column_cache.get('power')
        
        self.apply_styles()
        self.init_ui()

    def apply_styles(self):
        """Apply Wind Data Insight Pro compatible theme styles"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(44, 62, 80))  # Match main app background
        self.setPalette(palette)
        
        self.setStyleSheet("""
            QMainWindow { 
                background-color: #2C3E50; 
                color: #ECF0F1;
            }
            QGroupBox { 
                font-weight: bold; 
                border: 1px solid #B0B0B0; 
                border-radius: 3px; 
                margin-top: 10px; 
                padding-top: 15px;
                background-color: #34495E;
                color: #ECF0F1;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                subcontrol-position: top left; 
                padding: 0 5px;
                color: #ECF0F1;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton { 
                background-color: #0078d7; 
                color: white; 
                border: none; 
                padding: 6px 12px; 
                border-radius: 4px; 
                font-weight: 500;
            }
            QPushButton:hover { 
                background-color: #005a9e; 
            }
            QPushButton:pressed { 
                background-color: #004578; 
            }
            QComboBox, QLineEdit { 
                padding: 4px; 
                border: 1px solid #ccc; 
                border-radius: 4px; 
                background-color: #ffffff; 
                color: black;
                selection-background-color: #e6f3ff; 
                selection-color: black;
            }
            QCheckBox { 
                spacing: 5px; 
                color: #ECF0F1;
                font-size: 14px;
            }
            QRadioButton {
                spacing: 5px;
                color: #ECF0F1;
                font-size: 14px;
            }
            QLabel {
                color: #ECF0F1;
                font-size: 14px;
            }
            QListWidget {
                gridline-color: lightgray; 
                selection-background-color: lightblue; 
                selection-color: black;
                background-color: white;
                alternate-background-color: #f9f9f9;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: lightblue;
                color: black;
            }
            QTextEdit {
                background-color: white;
                color: black;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px;
            }
            QScrollArea {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #34495E;
            }
            QFrame {
                background-color: #34495E;
                border: 1px solid #B0B0B0;
            }
            QMenuBar {
                background-color: #34495E;
                color: #ECF0F1;
                font-size: 12px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #005a9e;
            }
            QMenu {
                background-color: #34495E;
                color: #ECF0F1;
                border: 1px solid #B0B0B0;
            }
            QMenu::item:selected {
                background-color: #005a9e;
            } """)
    
    def init_column_cache(self):
        """Initialize column cache using scada_utils"""
        if self.data.empty:
            return
        # Cache all relevant parameters using scada_utils
        params_to_cache = ['power', 'wind_speed', 'timestamp']
        
        # Add all temperature-related parameters from scada_utils
        temp_params = ['generator_temp', 'bearing_temp', 'gearbox_temp', 'ambient_temp', 
                    'cabinet_temp', 'motor_temp', 'nacelle_temp']
        params_to_cache.extend(temp_params)
    
        for param in params_to_cache:
            matched_cols = su.find_matching_columns(self.data, param)
            self.column_cache[param] = matched_cols[0] if matched_cols else None
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create sidebar first
        self.sidebar = CollapsibleSidebar()
        self.sidebar.normal_width = 300
        self.sidebar.setMaximumWidth(300)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Main splitter with 3 sections: left sidebar, plot, right panel
        self.main_splitter = QSplitter(Qt.Horizontal)
        central_widget.setLayout(QHBoxLayout())
        central_widget.layout().addWidget(self.main_splitter)
        
        # Add sidebar content (filters only)
        self.create_sidebar_content()
        self.main_splitter.addWidget(self.sidebar)
        
        # Plot area
        self.create_plot_area()
        self.main_splitter.addWidget(self.plot_widget)
        
        # Right panel for temperature tags and insights
        self.create_right_panel()
        self.main_splitter.addWidget(self.right_panel)
        
        # Set splitter sizes (20% sidebar, 60% plot, 20% right panel)
        self.main_splitter.setSizes([300, 800, 300])


    def create_menu_bar(self):
        """Create professional menu bar"""
        menubar = self.menuBar()
        # File Menu
        file_menu = menubar.addMenu('File')
        export_action = file_menu.addAction('Export Plot')
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.show_export_dialog)
        export_data_action = file_menu.addAction('Export Data')
        export_data_action.setShortcut('Ctrl+Shift+E')
        export_data_action.triggered.connect(self.export_data)
        file_menu.addSeparator()
        reset_action = file_menu.addAction('Reset View')
        reset_action.setShortcut('Ctrl+R')
        reset_action.triggered.connect(self.reset_view)

        # Analysis Menu
        analysis_menu = menubar.addMenu('Analysis')
        insights_action = analysis_menu.addAction('Generate Insights')
        insights_action.setShortcut('Ctrl+I')
        insights_action.triggered.connect(self.generate_insights)
        report_action = analysis_menu.addAction('Generate Report')
        report_action.setShortcut('Ctrl+G')
        report_action.triggered.connect(self.generate_report)
        anomaly_action = analysis_menu.addAction('Detect Anomalies')
        anomaly_action.setShortcut('Ctrl+A')
        anomaly_action.triggered.connect(self.detect_anomalies)
        
        # View Menu
        view_menu = menubar.addMenu('View')
        self.markers_action = view_menu.addAction('Show Interactive Markers')
        self.markers_action.setCheckable(True)
        self.markers_action.setShortcut('Ctrl+M')
        self.markers_action.triggered.connect(self.toggle_markers_dock)
        
        sidebar_action = view_menu.addAction('Toggle Sidebar')
        sidebar_action.setShortcut('Ctrl+B')
        # Use lambda to safely call sidebar toggle
        sidebar_action.triggered.connect(lambda: self.sidebar.toggle_sidebar() if hasattr(self, 'sidebar') else None)

    def create_sidebar_content(self):
        """Optimized sidebar with modern layout"""
        layout = self.sidebar.content_layout
        layout.setSpacing(8)
        
        # Date Filter Group
        date_group = QGroupBox("📅 Date Filter")
        date_layout = QVBoxLayout(date_group)
        date_layout.setSpacing(8)

        self.enable_date_filter = QCheckBox("Enable Date Filter")
        date_layout.addWidget(self.enable_date_filter)
        
        # Get date range from data - OPTIMIZED
        min_date, max_date, min_time, max_time, timestamp_col = self.get_datetime_info_from_dataset()
        
        date_grid = QGridLayout()
        date_grid.addWidget(QLabel(f"From ({min_date}):"), 0, 0)
        self.start_date_only = QLineEdit(min_date)
        date_grid.addWidget(self.start_date_only, 0, 1)
        
        date_grid.addWidget(QLabel(f"To ({max_date}):"), 1, 0)
        self.end_date_only = QLineEdit(max_date)
        date_grid.addWidget(self.end_date_only, 1, 1)
        
        date_layout.addLayout(date_grid)
        layout.addWidget(date_group)

        # Time Filter Group
        time_filter_group = QGroupBox("⏰ Time Filter")
        time_filter_layout = QVBoxLayout(time_filter_group)
        time_filter_layout.setSpacing(8)

        self.enable_time_filter = QCheckBox("Enable Time Filter")
        time_filter_layout.addWidget(self.enable_time_filter)

        time_grid = QGridLayout()
        time_grid.setSpacing(6)
        time_grid.addWidget(QLabel("From:"), 0, 0)
        self.start_time_only = QLineEdit()
        self.start_time_only.setPlaceholderText("HH:MM")
        time_grid.addWidget(self.start_time_only, 0, 1)
        time_grid.addWidget(QLabel("To:"), 1, 0)
        self.end_time_only = QLineEdit()
        self.end_time_only.setPlaceholderText("HH:MM")
        time_grid.addWidget(self.end_time_only, 1, 1)
        time_filter_layout.addLayout(time_grid)
        layout.addWidget(time_filter_group)

        # Time Aggregation Group - Fixed
        time_agg_group = QGroupBox("📊 Time Aggregation")
        time_agg_layout = QVBoxLayout(time_agg_group)
        time_agg_layout.setSpacing(6)
        
        self.time_group = QButtonGroup()
        self.raw_radio = QRadioButton("Raw Data")
        self.hourly_radio = QRadioButton("Hourly Average")
        self.daily_radio = QRadioButton("Daily Average")
        self.weekly_radio = QRadioButton("Weekly Average")
        self.monthly_radio = QRadioButton("Monthly Average")
        self.raw_radio.setChecked(True)

        for radio in [self.raw_radio, self.hourly_radio, self.daily_radio, self.weekly_radio, self.monthly_radio]:
            self.time_group.addButton(radio)
            radio.toggled.connect(self.on_time_aggregation_changed)
            time_agg_layout.addWidget(radio)

        layout.addWidget(time_agg_group)

        # Temperature Zones Group
        zone_group = QGroupBox("⚠️ Temperature Zones")
        zone_layout = QGridLayout(zone_group)
        zone_layout.setSpacing(8)
        
        zone_layout.addWidget(QLabel("Normal:"), 0, 0)
        self.normal_zone_input = QLineEdit("60")
        zone_layout.addWidget(self.normal_zone_input, 0, 1)
        
        zone_layout.addWidget(QLabel("Critical:"), 0, 2)
        self.critical_zone_input = QLineEdit("80")
        zone_layout.addWidget(self.critical_zone_input, 0, 3)
        
        self.enable_zones = QCheckBox("Enable Temperature Zones")
        self.enable_zones.setChecked(True)
        zone_layout.addWidget(self.enable_zones, 1, 0, 1, 4)
        
        layout.addWidget(zone_group)
        
        # Analysis Options Group
        options_group = QGroupBox("🔧 Analysis Options")
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(8)
        
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Chart Type:"))
        self.graph_type_combo = QComboBox()
        self.graph_type_combo.addItems(["Line", "Bar", "Scatter"])
        type_layout.addWidget(self.graph_type_combo)
        options_layout.addLayout(type_layout)
        
        options_grid = QGridLayout()
        options_grid.setSpacing(6)
        
        self.show_markers = QCheckBox("Show Markers")
        self.show_legend = QCheckBox("Show Legend")
        self.show_legend.setChecked(True)
        self.show_power = QCheckBox("Show Power")
        self.enable_anomaly = QCheckBox("Detect Anomalies")
        
        options_grid.addWidget(self.show_markers, 0, 0)
        options_grid.addWidget(self.show_legend, 0, 1)
        options_grid.addWidget(self.show_power, 1, 0)
        options_grid.addWidget(self.enable_anomaly, 1, 1)
        
        options_layout.addLayout(options_grid)
        layout.addWidget(options_group)
        
        layout.addStretch()

    def create_right_panel(self):
        """Create right panel with temperature tags and insights"""
        self.right_panel = QWidget()
        self.right_panel.setMinimumWidth(300)
        self.right_panel.setMaximumWidth(350)
        
        layout = QVBoxLayout(self.right_panel)
        layout.setSpacing(10)
        
        # Temperature Tags Section
        temp_group = QGroupBox("🌡️ Temperature Tags")
        temp_layout = QVBoxLayout(temp_group)
        
        # Search box
        self.tag_search = QLineEdit()
        self.tag_search.setPlaceholderText("Search tags...")
        self.tag_search.textChanged.connect(self.filter_tags)
        temp_layout.addWidget(self.tag_search)
        
        # Tags list with proper scrolling
        self.tags_list = QListWidget()
        self.tags_list.setMaximumHeight(400)
        self.tags_list.setSelectionMode(QListWidget.MultiSelection)
        
        # Initialize temp_checkboxes dictionary
        self.temp_checkboxes = {}

        # Display names mapping
        display_names = {
            'generator_temp': 'Generator Temperature',
            'bearing_temp': 'Bearing Temperature',
            'gearbox_temp': 'Gearbox Temperature',
            'ambient_temp': 'Ambient Temperature',
            'cabinet_temp': 'Cabinet Temperature',
            'motor_temp': 'Motor Temperature',
            'nacelle_temp': 'Nacelle Temperature'
        }
        
        # # Populate tags
        # scada_temp_tags = {
        #     "T_GEN_1_Avg": "Generator Winding 1",
        #     "T_GEN_2_Avg": "Generator Winding 2", 
        #     "AI_In_TbGenWinding3Temp_Avg": "Generator Winding 3",
        #     "T_BEAR_A_Avg": "Generator Bearing A",
        #     "T_BEAR_B_Avg": "Generator Bearing B",
        #     "T_BEAR_SHAFT_Avg": "Shaft Bearing",
        #     "T_GEAR_Avg": "Gear Box Oil",
        #     "T_GEAR_BEAR_Avg": "Gear Box Bearing",
        #     "AI_In_TbGbxBearingFastShaftB_Avg": "Gear Box Highspeed Shaft",
        #     "AI_In_TbGbxIntermedBrgTempA_Avg": "Gear Box Intermediate Shaft A",
        #     "AI_In_TbGbxIntermedBrgTempB_Avg": "Gear Box Intermediate Shaft B",
        #     "T_AMB_Avg": "Ambient Temperature",
        #     "T_NAC_Avg": "Nacelle Temperature",
        #     "AI_In_TbOutsideTemp1_Avg": "Outside Ambient",
        #     "T_GEN_COOL_Avg": "Generator Cooler",
        #     "AI_In_MotorTempA1_Avg": "Pitch Motor A1",
        #     "AI_In_MotorTempA2_Avg": "Pitch Motor A2", 
        #     "AI_In_MotorTempA3_Avg": "Pitch Motor A3",
        #     "T_HUB_Avg": "Hub Temperature",
        #     "AI_In_DtaDownTowerCabinetTemp_Avg": "Bottom Cabinet",
        #     "AI_In_MVTrafoWindingVTemp_Avg": "Trafo Winding V",
        #     "AI_In_MVTrafoWindingWTemp_Avg": "Trafo Winding W",
        #     "AI_In_TbSlipringTemperature_Avg": "Slipring Temperature"
        # }
        
        self.tag_items = {}
        for category in self.temp_categories:
            matched_cols = su.find_matching_columns(self.data, category)
            for col in matched_cols:
                if col not in self.tag_items:  # Avoid duplicates
                    display_name = f"{display_names.get(category, category)} ({col})"
                    item = QListWidgetItem(display_name)
                    item.setData(Qt.UserRole, col)
                    item.setCheckState(Qt.Unchecked)
                    self.tags_list.addItem(item)
                    self.tag_items[col] = item
                    
                    self.temp_checkboxes[col] = type('MockCheckbox', (), {
                        'isChecked': lambda item=item: item.checkState() == Qt.Checked
                    })()
        
        temp_layout.addWidget(self.tags_list)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("All")
        clear_all_btn = QPushButton("Clear")
        plot_btn = QPushButton("Plot")
        
        select_all_btn.clicked.connect(self.select_all_tags)
        clear_all_btn.clicked.connect(self.clear_all_tags)
        plot_btn.clicked.connect(self.update_plot)
        
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(clear_all_btn)
        btn_layout.addWidget(plot_btn)
        temp_layout.addLayout(btn_layout)
        
        layout.addWidget(temp_group)
        
        # Insights Dock
        self.create_insights_dock()
        layout.addWidget(self.insights_dock)
        
        layout.addStretch()

    def create_plot_area(self):
        """Create plot area with enhanced features"""
        self.plot_widget = QWidget()
        layout = QVBoxLayout(self.plot_widget)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(12, 8), facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self.plot_widget)
        
        # Connect click events for interactive markers
        self.canvas.mpl_connect('button_press_event', self.on_plot_click)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # Initialize plot
        self.update_plot()
    
    def calculate_temperature_statistics(self, tag_data):
        """Calculate comprehensive temperature statistics"""
        if tag_data.empty:
            return None
        
        stats = {
            'mean': tag_data.mean(),
            'median': tag_data.median(),
            'std': tag_data.std(),
            'min': tag_data.min(),
            'max': tag_data.max(),
            'range': tag_data.max() - tag_data.min(),
            'q25': tag_data.quantile(0.25),
            'q75': tag_data.quantile(0.75),
            'iqr': tag_data.quantile(0.75) - tag_data.quantile(0.25)
        }
        return stats
    
    def on_plot_click(self, event):
        """Handle plot click events for adding markers"""
        if event.inaxes and event.button == 3:  # Right click
            # Get timestamp from x-coordinate
            try:
                timestamp = mdates.num2date(event.xdata)
                label, ok = QInputDialog.getText(self, 'Add Marker', 'Enter marker label:')
                
                if ok and label:
                    marker = InteractiveMarker(event.xdata, event.ydata, label, timestamp)
                    self.markers.append(marker)
                    self.update_markers_list()
                    self.update_plot()
            except:
                pass
    
    def update_markers_list(self):
        """Update the markers list widget"""
        self.markers_list.clear()
        for i, marker in enumerate(self.markers):
            item_text = f"{marker.label} - {marker.timestamp.strftime('%Y-%m-%d %H:%M')}"
            item = QListWidgetItem(item_text)
            self.markers_list.addItem(item)
    
    def clear_markers(self):
        """Clear all markers"""
        self.markers.clear()
        self.markers_list.clear()
        self.update_plot()
    
    # 2. Fix get_selected_view method
    def get_selected_view(self):
        """Get selected time view with proper aggregation"""
        if hasattr(self, 'raw_radio') and self.raw_radio.isChecked():
            return "Raw Data"
        elif hasattr(self, 'hourly_radio') and self.hourly_radio.isChecked():
            return "Hourly"
        elif hasattr(self, 'daily_radio') and self.daily_radio.isChecked():
            return "Daily"
        elif hasattr(self, 'weekly_radio') and self.weekly_radio.isChecked():
            return "Weekly"
        elif hasattr(self, 'monthly_radio') and self.monthly_radio.isChecked():
            return "Monthly"
        return "Raw Data"
        
    def prepare_data(self):
        """Fixed data preparation with proper time aggregation - passes complete data"""
        if self.data.empty:
            return None
        
        timestamp_col = self.column_cache.get('timestamp')
        
        # Handle timestamp column
        if not timestamp_col:
            # Check if index is datetime
            if isinstance(self.data.index, pd.DatetimeIndex):
                df = self.data.copy()
                df.reset_index(inplace=True)
                timestamp_col = df.columns[0]  # First column should be the index
            else:
                # Try to find any datetime column
                datetime_cols = []
                for col in self.data.columns:
                    if 'time' in col.lower() or 'date' in col.lower():
                        try:
                            pd.to_datetime(self.data[col].iloc[:100], errors='coerce')
                            datetime_cols.append(col)
                        except:
                            continue
                
                if datetime_cols:
                    timestamp_col = datetime_cols[0]
                else:
                    # Create a dummy timestamp column based on actual data length
                    df = self.data.copy()
                    df['timestamp'] = pd.date_range(start='2023-01-01', periods=len(df), freq='10min')
                    timestamp_col = 'timestamp'
        else:
            df = self.data.copy()
        
        # Convert timestamp column to datetime
        try:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
        except:
            print(f"Error converting {timestamp_col} to datetime")
            return None
        
        # Remove rows with invalid timestamps
        df = df.dropna(subset=[timestamp_col])
        if df.empty:
            return None
        
        # Sort by timestamp to ensure proper ordering
        df = df.sort_values(by=timestamp_col)
        
        # Apply date/time filters BEFORE aggregation
        df = self.apply_date_filter(df, timestamp_col)
        
        # Time aggregation - work with complete filtered data
        view = self.get_selected_view()
        if view != "Raw Data":
            # Set timestamp as index for resampling
            df = df.set_index(timestamp_col)
            
            # Define proper aggregation methods
            agg_methods = {
                "Hourly Average": 'h',
                "Daily Average": 'D', 
                "Weekly Average": 'W',
                "Monthly Average": 'ME'
            }
            
            if view in agg_methods:
                try:
                    # Resample using mean for numeric columns - keep all data points
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        df_resampled = df[numeric_cols].resample(agg_methods[view]).mean()
                        # Don't drop NaN rows - keep all time periods
                        df_resampled = df_resampled.reset_index()
                        df = df_resampled
                except Exception as e:
                    print(f"Resampling error: {e}")
                    # Fallback to original data
                    df = df.reset_index()
        
        return df

    def update_plot(self):
        """Enhanced plot update with better data handling and date/time display"""
        if not hasattr(self, 'figure'):
            return
        
        self.figure.clear()
        
        # Get selected tags using the new method
        selected_tags = self.get_selected_tags()
        
        if not selected_tags:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Select temperature tags to display\nRight-click to add markers', 
                    ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_facecolor('#f7f7f7')
            self.canvas.draw()
            return
        
        df = self.prepare_data()
        if df is None or df.empty:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'No data available for plotting', ha='center', va='center', 
                    transform=ax.transAxes, fontsize=12)
            self.canvas.draw()
            return
        
        # Create subplots
        show_power = hasattr(self, 'show_power') and self.show_power.isChecked() and self.power_column
        if show_power:
            ax1 = self.figure.add_subplot(111)
            ax2 = ax1.twinx()
        else:
            ax1 = self.figure.add_subplot(111)
            ax2 = None
        
        # Find timestamp column
        timestamp_col = 'timestamp'
        if timestamp_col not in df.columns:
            timestamp_col = df.columns[0]  # Use first column as fallback
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
        
        graph_type = self.graph_type_combo.currentText() if hasattr(self, 'graph_type_combo') else "Line"
        
        # Plot temperature data
        temp_lines = []
        anomaly_points = []
        
        for i, tag in enumerate(selected_tags):
            if tag not in df.columns:
                print(f"Tag {tag} not found in data columns")
                continue
            
            # Convert to numeric and handle NaN values properly
            temp_series = pd.to_numeric(df[tag], errors='coerce')
            
            # Get corresponding timestamps for valid data points
            valid_mask = ~temp_series.isna()
            if not valid_mask.any():
                print(f"No valid data for tag {tag}")
                continue
            
            valid_temp = temp_series[valid_mask]
            valid_timestamps = df.loc[valid_mask, timestamp_col]
            
            # Ensure timestamps are datetime
            if not pd.api.types.is_datetime64_any_dtype(valid_timestamps):
                try:
                    valid_timestamps = pd.to_datetime(valid_timestamps)
                except:
                    print(f"Cannot convert timestamps to datetime for tag {tag}")
                    continue
            
            # Sort by timestamp to ensure proper line plotting
            sort_idx = valid_timestamps.argsort()
            valid_timestamps = valid_timestamps.iloc[sort_idx]
            valid_temp = valid_temp.iloc[sort_idx]
            
            # Anomaly detection
            if hasattr(self, 'enable_anomaly') and self.enable_anomaly.isChecked():
                try:
                    mean_temp = valid_temp.mean()
                    std_temp = valid_temp.std()
                    if std_temp > 0:  # Avoid division by zero
                        threshold = 3 * std_temp
                        anomaly_mask = abs(valid_temp - mean_temp) > threshold
                        if anomaly_mask.any():
                            anomaly_temp = valid_temp[anomaly_mask]
                            anomaly_timestamps = valid_timestamps[anomaly_mask]
                            anomaly_points.extend(list(zip(anomaly_timestamps, anomaly_temp)))
                except Exception as e:
                    print(f"Anomaly detection error for {tag}: {e}")
            
            # Plot based on graph type
            try:
                if graph_type == "Bar":
                    bars = ax1.bar(valid_timestamps, valid_temp, 
                                color=colors[i % len(colors)], alpha=0.7, 
                                label=self.get_tag_display_name(tag), width=0.8)
                    temp_lines.extend(bars)
                elif graph_type == "Scatter":
                    scatter = ax1.scatter(valid_timestamps, valid_temp, 
                                        c=colors[i % len(colors)], alpha=0.7,
                                        label=self.get_tag_display_name(tag), s=30)
                    temp_lines.append(scatter)
                else:  # Line
                    line_style = '-o' if (hasattr(self, 'show_markers') and self.show_markers.isChecked()) else '-'
                    marker_size = 3 if (hasattr(self, 'show_markers') and self.show_markers.isChecked()) else 0
                    
                    line = ax1.plot(valid_timestamps, valid_temp, line_style, 
                                color=colors[i % len(colors)], 
                                label=self.get_tag_display_name(tag), markersize=marker_size, 
                                alpha=0.8, linewidth=2)
                    temp_lines.extend(line)
            except Exception as e:
                print(f"Plotting error for tag {tag}: {e}")
                continue
        
        # Plot anomalies
        if anomaly_points:
            try:
                anomaly_x, anomaly_y = zip(*anomaly_points)
                ax1.scatter(anomaly_x, anomaly_y, color='red', s=100, marker='X', 
                        label='Anomalies', zorder=5, alpha=0.8)
            except Exception as e:
                print(f"Anomaly plotting error: {e}")
        
        # Plot power data if requested
        if ax2 and self.power_column and self.power_column in df.columns:
            try:
                power_data = pd.to_numeric(df[self.power_column], errors='coerce')
                valid_power_mask = ~power_data.isna()
                if valid_power_mask.any():
                    valid_power = power_data[valid_power_mask]
                    valid_power_timestamps = df.loc[valid_power_mask, timestamp_col]
                    
                    # Sort power data by timestamp
                    sort_idx = valid_power_timestamps.argsort()
                    valid_power_timestamps = valid_power_timestamps.iloc[sort_idx]
                    valid_power = valid_power.iloc[sort_idx]
                    
                    ax2.plot(valid_power_timestamps, valid_power, 'k-', alpha=0.4, 
                            linewidth=1.5, label='Power')
            except Exception as e:
                print(f"Power plotting error: {e}")
        
        # Zone highlighting
        if hasattr(self, 'enable_zones') and self.enable_zones.isChecked():
            try:
                normal_zone = float(self.normal_zone_input.text())
                critical_zone = float(self.critical_zone_input.text())
                
                ax1.axhline(y=normal_zone, color='green', linestyle='--', alpha=0.8, linewidth=2, 
                        label=f'Normal ({normal_zone}°C)')
                ax1.axhline(y=critical_zone, color='red', linestyle='--', alpha=0.8, linewidth=2, 
                        label=f'Critical ({critical_zone}°C)')
                
                # Fill zones
                y_min, y_max = ax1.get_ylim()
                ax1.fill_between(ax1.get_xlim(), y_min, normal_zone, alpha=0.2, color='green')
                ax1.fill_between(ax1.get_xlim(), normal_zone, critical_zone, alpha=0.2, color='yellow')
                ax1.fill_between(ax1.get_xlim(), critical_zone, y_max, alpha=0.2, color='red')
            except ValueError as e:
                print(f"Zone highlighting error: {e}")
        
        # Add interactive markers
        for marker in self.markers:
            try:
                ax1.plot(marker.x, marker.y, 'o', color=marker.color, markersize=8)
                ax1.annotate(marker.label, (marker.x, marker.y), xytext=(5, 5), 
                            textcoords='offset points', fontsize=8, 
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
            except Exception as e:
                print(f"Marker plotting error: {e}")
        
        # Format axes
        ax1.set_xlabel('Date/Time', fontweight='bold')
        ax1.set_ylabel('Temperature (°C)', color='blue', fontweight='bold')
        ax1.tick_params(axis='y', labelcolor='blue')
        
        if ax2:
            ax2.set_ylabel('Power (kW)', color='red', fontweight='bold')
            ax2.tick_params(axis='y', labelcolor='red')
        
        # Enhanced time axis formatting
        if len(df) > 0:
            try:
                self.format_time_axis(ax1, df[timestamp_col])
            except Exception as e:
                print(f"Time axis formatting error: {e}")
        
        # Legend
        if hasattr(self, 'show_legend') and self.show_legend.isChecked():
            try:
                lines1, labels1 = ax1.get_legend_handles_labels()
                if ax2:
                    lines2, labels2 = ax2.get_legend_handles_labels()
                    lines1.extend(lines2)
                    labels1.extend(labels2)
                
                if lines1:  # Only add legend if there are lines to show
                    ax1.legend(lines1, labels1, loc='upper left', bbox_to_anchor=(1.02, 1), 
                            frameon=True, fancybox=True, shadow=True)
            except Exception as e:
                print(f"Legend error: {e}")
        
        # Grid and styling
        ax1.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax1.set_facecolor('#f9f9f9')
        
        # Enhanced title with data information
        view = self.get_selected_view()
        selected_count = len(selected_tags)
        data_points = len(df)
        anomaly_count = len(anomaly_points)
        
        # Add date range to title
        if len(df) > 0:
            try:
                date_range = f"{df[timestamp_col].min().strftime('%Y-%m-%d')} to {df[timestamp_col].max().strftime('%Y-%m-%d')}"
                title_text = f'Temperature Analysis - {view} | {graph_type}\n{date_range} | {selected_count} tags, {data_points} points'
            except:
                title_text = f'Temperature Analysis - {view} | {graph_type}\n{selected_count} tags, {data_points} points'
        else:
            title_text = f'Temperature Analysis - {view} | {graph_type}\n{selected_count} tags, {data_points} points'
        
        if anomaly_count > 0:
            title_text += f', {anomaly_count} anomalies'
        
        ax1.set_title(title_text, fontweight='bold', pad=20)
        
        # Add tooltips for line charts
        if graph_type == "Line" and temp_lines:
            try:
                self.add_enhanced_tooltips(ax1, temp_lines)
            except Exception as e:
                print(f"Tooltip error: {e}")
        
        self.figure.tight_layout()
        self.canvas.draw()

    def format_time_axis(self, ax, timestamps):
        """Enhanced time axis formatting with proper date/time display"""
        if len(timestamps) < 2:
            return
        
        # Ensure timestamps are sorted
        timestamps = timestamps.sort_values()
        time_range = timestamps.max() - timestamps.min()
        
        # More detailed time formatting based on data range
        if time_range <= pd.Timedelta(hours=6):
            # Very short range - show hour:minute
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
            ax.xaxis.set_minor_locator(mdates.MinuteLocator(interval=30))
        elif time_range <= pd.Timedelta(hours=24):
            # Single day - show hour:minute
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
            ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
        elif time_range <= pd.Timedelta(days=7):
            # Week - show month/day hour:minute
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d\n%H:%M'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
        elif time_range <= pd.Timedelta(days=30):
            # Month - show month/day
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
            ax.xaxis.set_minor_locator(mdates.DayLocator(interval=1))
        elif time_range <= pd.Timedelta(days=90):
            # Quarter - show month/day
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            ax.xaxis.set_minor_locator(mdates.DayLocator(interval=1))
        else:
            # Long range - show year-month
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
            ax.xaxis.set_minor_locator(mdates.WeekdayLocator(interval=1))
        
        # Rotate labels for better readability
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add grid for better readability
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.grid(True, which='minor', alpha=0.1, linestyle=':', linewidth=0.3)
        
    def add_enhanced_tooltips(self, ax, lines):
        """Enhanced interactive tooltips with proper date/time display"""
        try:
            cursor = mplcursors.cursor(lines, hover=True)
            cursor.connect("add", lambda sel: sel.annotation.set_text(
                f'Tag: {sel.artist.get_label()}\n'
                f'Date/Time: {mdates.num2date(sel.target[0]).strftime("%Y-%m-%d %H:%M:%S")}\n'
                f'Temperature: {sel.target[1]:.2f}°C'
            ))
            cursor.connect("add", lambda sel: sel.annotation.get_bbox_patch().set(
                facecolor='white', alpha=0.9, edgecolor='black'
            ))
        except Exception as e:
            print(f"Tooltip error: {e}")
            pass
    
    def get_tag_display_name(self, tag):
        """Get display name for SCADA tag"""
        scada_display_names = {
            "T_GEN_1_Avg": "Gen Winding 1",
            "T_GEN_2_Avg": "Gen Winding 2",
            "AI_In_TbGenWinding3Temp_Avg": "Gen Winding 3",
            "T_BEAR_A_Avg": "Gen Bearing A",
            "T_BEAR_B_Avg": "Gen Bearing B", 
            "T_BEAR_SHAFT_Avg": "Shaft Bearing",
            "T_GEAR_Avg": "Gearbox Oil",
            "T_GEAR_BEAR_Avg": "Gearbox Bearing",
            "AI_In_TbGbxBearingFastShaftB_Avg": "GB HS Shaft",
            "AI_In_TbGbxIntermedBrgTempA_Avg": "GB IS A",
            "AI_In_TbGbxIntermedBrgTempB_Avg": "GB IS B",
            "T_AMB_Avg": "Ambient",
            "T_NAC_Avg": "Nacelle",
            "AI_In_TbOutsideTemp1_Avg": "Outside",
            "T_GEN_COOL_Avg": "Gen Cooler",
            "AI_In_MotorTempA1_Avg": "Motor A1",
            "AI_In_MotorTempA2_Avg": "Motor A2",
            "AI_In_MotorTempA3_Avg": "Motor A3",
            "T_HUB_Avg": "Hub",
            "AI_In_DtaDownTowerCabinetTemp_Avg": "Cabinet",
            "AI_In_MVTrafoWindingVTemp_Avg": "Trafo V",
            "AI_In_MVTrafoWindingWTemp_Avg": "Trafo W",
            "AI_In_TbSlipringTemperature_Avg": "Slipring"
        }
        return scada_display_names.get(tag, tag.replace('_', ' ').title())
    
    def export_plot(self, format_type):
        """Export plot to file"""
        file_filter = f"{format_type.upper()} Files (*.{format_type})"
        file_path, _ = QFileDialog.getSaveFileName(self, f"Export {format_type.upper()}", "", file_filter)
        
        if file_path:
            try:
                self.figure.savefig(file_path, format=format_type, dpi=300, bbox_inches='tight', 
                                   facecolor='white', edgecolor='none')
                QMessageBox.information(self, "Success", f"Plot exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
    
    def export_data(self):
        """Export current data to CSV"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Data", "", "CSV Files (*.csv)")
        
        if file_path:
            try:
                df = self.prepare_data()
                if df is not None:
                    # Export selected columns with markers info
                    selected_tags = [tag for tag, cb in self.temp_checkboxes.items() if cb.isChecked()]
                    export_cols = ['timestamp'] + selected_tags
                    if self.power_column:
                        export_cols.append(self.power_column)
                    export_cols = [col for col in export_cols if col in df.columns]
                    
                    export_df = df[export_cols].copy()
                    
                    # Add markers information
                    if self.markers:
                        markers_info = pd.DataFrame([
                            {'timestamp': m.timestamp, 'marker_label': m.label, 'marker_value': m.y}
                            for m in self.markers
                        ])
                        export_df.to_csv(file_path, index=False)
                        # Save markers separately
                        markers_file = file_path.replace('.csv', '_markers.csv')
                        markers_info.to_csv(markers_file, index=False)
                        QMessageBox.information(self, "Success", 
                                              f"Data exported to {file_path}\nMarkers exported to {markers_file}")
                    else:
                        export_df.to_csv(file_path, index=False)
                        QMessageBox.information(self, "Success", f"Data exported to {file_path}")
                else:
                    QMessageBox.warning(self, "Warning", "No data to export")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")
    
    def set_data(self, data):
        """Set new data and reinitialize"""
        self.data = data.copy() if data is not None else pd.DataFrame()
        self.init_column_cache()
        self.power_column = self.column_cache.get('power')
        
        # Clear existing checkboxes safely
        try:
            for cb in list(self.temp_checkboxes.values()):
                if hasattr(cb, 'setParent'):
                    cb.setParent(None)
                elif hasattr(cb, 'deleteLater'):
                    cb.deleteLater()
        except:
            pass
        
        self.temp_checkboxes.clear()
        
        # Recreate sidebar content
        if hasattr(self, 'sidebar'):
            # Clear and recreate content
            for i in reversed(range(self.sidebar.content_layout.count())):
                item = self.sidebar.content_layout.itemAt(i)
                if item.widget():
                    item.widget().setParent(None)
            self.create_sidebar_content()
        
        self.update_plot()

    # code for helper function
    def get_selected_view(self):
        """Get selected time view with proper aggregation"""
        if hasattr(self, 'raw_radio') and self.raw_radio.isChecked():
            return "Raw Data"
        elif hasattr(self, 'hourly_radio') and self.hourly_radio.isChecked():
            return "Hourly Average"
        elif hasattr(self, 'daily_radio') and self.daily_radio.isChecked():
            return "Daily Average"
        elif hasattr(self, 'weekly_radio') and self.weekly_radio.isChecked():
            return "Weekly Average"
        elif hasattr(self, 'monthly_radio') and self.monthly_radio.isChecked():
            return "Monthly Average"
        else:
            return "Raw Data"
        
    def apply_date_filter(self, df, timestamp_col):
        """Enhanced date and time filters with proper datetime handling"""
        original_count = len(df)
        
        # Date filter
        if hasattr(self, 'enable_date_filter') and self.enable_date_filter.isChecked():
            try:
                start_date = self.start_date_only.text().strip()
                end_date = self.end_date_only.text().strip()
                
                if start_date:
                    start_dt = pd.to_datetime(start_date, format='%d-%m-%Y', errors='coerce')
                    df = df[df[timestamp_col] >= start_dt]
                if end_date:
                    end_dt = pd.to_datetime(end_date,format='%d-%m-%Y', errors='coerce') + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                    df = df[df[timestamp_col] <= end_dt]
            except Exception as e:
                print(f"Date filter error: {e}")
        
        # Time filter
        if hasattr(self, 'enable_time_filter') and self.enable_time_filter.isChecked():
            try:
                start_time = self.start_time_only.text().strip()
                end_time = self.end_time_only.text().strip()
                
                if start_time:
                    start_time_obj = pd.to_datetime(start_time, format='%H:%M').time()
                    df = df[df[timestamp_col].dt.time >= start_time_obj]
                if end_time:
                    end_time_obj = pd.to_datetime(end_time, format='%H:%M').time()
                    df = df[df[timestamp_col].dt.time <= end_time_obj]
            except Exception as e:
                print(f"Time filter error: {e}")
        
        filtered_count = len(df)
        if original_count != filtered_count:
            print(f"Data filtered: {original_count} -> {filtered_count} rows")
        
        return df
            
    def set_quick_date_range(self, days=None, hours=None):
        """Set quick date range for filtering"""
        if not hasattr(self, 'enable_datetime_filter'):
            return
        
        # Get current max date from data
        timestamp_col = self.column_cache.get('timestamp')
        if not timestamp_col or timestamp_col not in self.data.columns:
            return
        
        try:
            max_date = pd.to_datetime(self.data[timestamp_col]).max()
            
            if hours:
                start_date = max_date - pd.Timedelta(hours=hours)
            elif days:
                start_date = max_date - pd.Timedelta(days=days)
            else:
                return
            
            self.start_date_input.setText(start_date.strftime('%Y-%m-%d %H:%M'))
            self.end_date_input.setText(max_date.strftime('%Y-%m-%d %H:%M'))
            self.enable_datetime_filter.setChecked(True)
            
        except Exception as e:
            print(f"Error setting date range: {e}")
    
    def reset_view(self):
        """Reset all view settings to default"""
        # Reset radio buttons
        if hasattr(self, 'raw_radio'):
            self.raw_radio.setChecked(True)
        
        # Reset date filters
        if hasattr(self, 'enable_datetime_filter'):
            self.enable_datetime_filter.setChecked(False)
            self.start_date_input.clear()
            self.end_date_input.clear()
        
        # Reset graph type
        if hasattr(self, 'graph_type_combo'):
            self.graph_type_combo.setCurrentText("Line Chart")
        
        # Reset zones
        if hasattr(self, 'normal_zone_input'):
            self.normal_zone_input.setText("60")
            self.critical_zone_input.setText("80")
        
        # Clear markers
        self.clear_markers()
        
        # Update plot
        self.update_plot()
    
    def create_markers_dock(self):
        """Create optimized markers dock"""
        self.markers_dock = QDockWidget("Interactive Markers", self)
        self.markers_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        
        markers_widget = QWidget()
        markers_layout = QVBoxLayout(markers_widget)
        
        # Use QListWidget instead of QTableWidget for better performance
        self.markers_list = QListWidget()
        markers_layout.addWidget(self.markers_list)
        
        # Compact controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(5)
        
        add_btn = QPushButton("Add")
        add_btn.setMaximumHeight(25)
        add_btn.clicked.connect(self.add_manual_marker)
        
        remove_btn = QPushButton("Remove")
        remove_btn.setMaximumHeight(25)
        remove_btn.clicked.connect(self.remove_selected_marker)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setMaximumHeight(25)
        clear_btn.clicked.connect(self.clear_markers)
        
        controls_layout.addWidget(add_btn)
        controls_layout.addWidget(remove_btn)
        controls_layout.addWidget(clear_btn)
        markers_layout.addLayout(controls_layout)
        
        self.markers_dock.setWidget(markers_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.markers_dock)
        self.markers_dock.setVisible(False)

    # 6. Add missing marker management methods
    def remove_selected_marker(self):
        """Remove selected marker"""
        current_row = self.markers_list.currentRow()
        if current_row >= 0 and current_row < len(self.markers):
            self.markers.pop(current_row)
            self.update_markers_list()
            self.update_plot()

    def update_markers_list(self):
        """Update markers list efficiently"""
        if not hasattr(self, 'markers_list'):
            return
        
        self.markers_list.clear()
        for marker in self.markers:
            item_text = f"{marker.label} - {marker.timestamp.strftime('%Y-%m-%d %H:%M')}"
            self.markers_list.addItem(item_text)


    def toggle_markers_dock(self):
        """Toggle markers dock visibility safely"""
        if hasattr(self, 'markers_dock') and self.markers_dock is not None:
            visible = not self.markers_dock.isVisible()
            self.markers_dock.setVisible(visible)
            if hasattr(self, 'markers_action'):
                self.markers_action.setChecked(visible)
            
            if visible:
                # Adjust main splitter to accommodate dock
                self.main_splitter.setSizes([250, 1050])  # Reduce plot area slightly
            else:
                # Restore full plot area
                self.main_splitter.setSizes([300, 1300])
        else:
            QMessageBox.information(self, "Not Available", "Markers feature is not available in this version.")
        
    def show_export_dialog(self):
        """Show export options dialog"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Export Options")
        layout = QVBoxLayout(dialog)
        
        # Export type selection
        type_combo = QComboBox()
        type_combo.addItems(["PNG (High Quality)", "PDF (Vector)", "SVG (Scalable)", "CSV (Data)"])
        layout.addWidget(type_combo)
        
        # Buttons
        btn_layout = QHBoxLayout()
        export_btn = QPushButton("Export")
        cancel_btn = QPushButton("Cancel")
        
        export_btn.clicked.connect(lambda: self.handle_export_dialog(type_combo.currentText(), dialog))
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec_()

    def handle_export_dialog(self, export_type, dialog):
        """Handle export from dialog"""
        if "PNG" in export_type:
            self.export_plot("png")
        elif "PDF" in export_type:
            self.export_plot("pdf")
        elif "SVG" in export_type:
            self.export_plot("svg")
        elif "CSV" in export_type:
            self.export_data()
        dialog.accept()

    def generate_insights(self):
        """Generate temperature insights"""
        selected_tags = self.get_selected_tags()
        if not selected_tags:
            self.insights_text.setText("Please select temperature tags first.")
            return
        
        df = self.prepare_data()
        if df is None:
            self.insights_text.setText("No data available for analysis.")
            return
        
        insights = []
        for tag in selected_tags:
            if tag in df.columns:
                temp_data = pd.to_numeric(df[tag], errors='coerce').dropna()
                if not temp_data.empty:
                    stats = self.calculate_temperature_statistics(temp_data)
                    display_name = self.get_tag_display_name(tag)
                    
                    insights.append(f"📊 {display_name}:")
                    insights.append(f"  • Average: {stats['mean']:.1f}°C")
                    insights.append(f"  • Range: {stats['min']:.1f}°C - {stats['max']:.1f}°C")
                    
                    if stats['max'] > 80:
                        insights.append(f"  ⚠️ High temperature detected!")
                    insights.append("")
        
        self.insights_text.setText("\n".join(insights))

    def generate_report(self):
        """Generate comprehensive report"""
        QMessageBox.information(self, "Report Generation", "Report generation feature coming soon!")

    def detect_anomalies(self):
        """Toggle anomaly detection"""
        if hasattr(self, 'enable_anomaly'):
            self.enable_anomaly.setChecked(not self.enable_anomaly.isChecked())
            self.update_plot()
    
    def detect_temperature_anomalies(self, tag_data, method='iqr'):
        """Enhanced anomaly detection"""
        if tag_data.empty:
            return pd.Series(dtype=bool)
        
        if method == 'iqr':
            Q1 = tag_data.quantile(0.25)
            Q3 = tag_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            anomalies = (tag_data < lower_bound) | (tag_data > upper_bound)
        else:  # z-score method
            mean_temp = tag_data.mean()
            std_temp = tag_data.std()
            z_scores = np.abs((tag_data - mean_temp) / std_temp)
            anomalies = z_scores > 3
        
        return anomalies
    
    def generate_temperature_trends(self, df, tag):
        """Generate temperature trends analysis"""
        if tag not in df.columns:
            return None
        
        tag_data = pd.to_numeric(df[tag], errors='coerce').dropna()
        if tag_data.empty:
            return None
        
        timestamp_col = 'timestamp' if 'timestamp' in df.columns else df.index
        
        # Calculate rolling statistics
        window = min(24, len(tag_data) // 10)  # Adaptive window size
        if window < 2:
            window = 2
        
        trends = {
            'rolling_mean': tag_data.rolling(window=window).mean(),
            'rolling_std': tag_data.rolling(window=window).std(),
            'trend_direction': 'stable'
        }
        
        # Determine trend direction
        if len(tag_data) > 10:
            first_half = tag_data[:len(tag_data)//2].mean()
            second_half = tag_data[len(tag_data)//2:].mean()
            
            if second_half > first_half * 1.05:
                trends['trend_direction'] = 'increasing'
            elif second_half < first_half * 0.95:
                trends['trend_direction'] = 'decreasing'
        
        return trends
    
    def add_manual_marker(self):
        """Add marker manually"""
        label, ok = QInputDialog.getText(self, 'Add Marker', 'Enter marker label:')
        if ok and label:
            # Add at center of current view
            ax = self.figure.get_axes()[0] if self.figure.get_axes() else None
            if ax:
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()
                x_center = (xlim[0] + xlim[1]) / 2
                y_center = (ylim[0] + ylim[1]) / 2
                
                marker = InteractiveMarker(x_center, y_center, label, datetime.now())
                self.markers.append(marker)
                self.update_markers_table()
                self.update_plot()

    def change_marker_color(self):
        """Change selected marker color"""
        current_row = self.markers_table.currentRow()
        if current_row >= 0 and current_row < len(self.markers):
            color = QColorDialog.getColor()
            if color.isValid():
                # Store color in marker (extend InteractiveMarker class if needed)
                self.update_plot()

    def update_markers_table(self):
        """Update markers table"""
        if not hasattr(self, 'markers_table'):
            return
            
        self.markers_table.setRowCount(len(self.markers))
        for i, marker in enumerate(self.markers):
            self.markers_table.setItem(i, 0, QTableWidgetItem(marker.label))
            self.markers_table.setItem(i, 1, QTableWidgetItem(marker.timestamp.strftime('%Y-%m-%d %H:%M')))
            self.markers_table.setItem(i, 2, QTableWidgetItem(f"{marker.y:.2f}"))
            self.markers_table.setItem(i, 3, QTableWidgetItem("Red"))  # Default color
    
    def on_tag_selection_changed(self):
        """Handle tag selection changes with auto-update"""
        if hasattr(self, 'auto_update') and self.auto_update.isChecked():
            self.update_plot()
    
    def add_auto_update_to_sidebar(self):
        """Add auto-update option to sidebar"""
        self.auto_update = QCheckBox("Auto Update")
        self.auto_update.setChecked(True)
        self.auto_update.setStyleSheet("QCheckBox { font-size: 8pt; }")
        
        # Add to options group if it exists
        if hasattr(self, 'options_group'):
            self.options_group.layout().addWidget(self.auto_update)
    
    # 5. Add missing signal handler
    def on_time_aggregation_changed(self):
        """Handle time aggregation radio button changes"""
        if self.sender().isChecked():
            self.update_plot()

    def get_selected_tags(self):
        """Get selected temperature tags from the list widget"""
        if not hasattr(self, 'tags_list'):
            return []
        
        selected = []
        for i in range(self.tags_list.count()):
            item = self.tags_list.item(i)
            if item.checkState() == Qt.Checked:
                scada_tag = item.data(Qt.UserRole)
                selected.append(scada_tag)
        return selected
    
    def select_all_tags(self):
        """Select all visible tags"""
        if not hasattr(self, 'tags_list'):
            return
        for i in range(self.tags_list.count()):
            item = self.tags_list.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.Checked)

    def clear_all_tags(self):
        """Clear all tag selections"""
        if not hasattr(self, 'tags_list'):
            return
        for i in range(self.tags_list.count()):
            item = self.tags_list.item(i)
            item.setCheckState(Qt.Unchecked)

    def filter_tags(self, text):
        """Filter tags based on search text"""
        if not hasattr(self, 'tags_list'):
            return
        for i in range(self.tags_list.count()):
            item = self.tags_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def create_insights_dock(self):
        """Create insights dock widget"""
        self.insights_dock = QGroupBox("🔍 Insights")
        layout = QVBoxLayout(self.insights_dock)
        
        # Insights text area
        self.insights_text = QTextEdit()
        self.insights_text.setMaximumHeight(200)
        self.insights_text.setReadOnly(True)
        self.insights_text.setPlaceholderText("Select tags and click 'Generate Insights' to see analysis...")
        layout.addWidget(self.insights_text)
        
        # Generate button
        generate_btn = QPushButton("Generate Insights")
        generate_btn.clicked.connect(self.generate_insights)
        layout.addWidget(generate_btn)

    def get_datetime_info_from_dataset(self):
        return dtu.get_datetime_info(self.data)
    
    def closeEvent(self, event):
        event.accept()