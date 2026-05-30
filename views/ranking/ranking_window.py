import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from utils.column_cache_utility import get_cached_column, populate_column_cache
from views.ranking.ranking import TurbineRanker
from functools import lru_cache
from utils.collapsible_prop import CollapsibleSection
from utils.plot_helpers import apply_legend, apply_grid, format_axes, handle_layout
from views.visualization_components import plotting_logic as pl

Title = "Wind Turbine Comparative Performance Analysis"

# Parameter display names mapping
PARAMETER_DISPLAY_NAMES = {
    'timestamp': 'Timestamp',
    'power': 'Power (kW)',
    'wind_speed': 'Wind Speed (m/s)',
    'rotor_speed': 'Rotor Speed (RPM)',
    'nacelle_direction': 'Wind Direction (°)',
    'generator_speed': 'Generator Speed (RPM)',
    'ambient_temp': 'Ambient Temperature (°C)',
}

def get_display_name(param_key):
    """Get user-friendly display name for parameter"""
    return PARAMETER_DISPLAY_NAMES.get(param_key, param_key.replace('_', ' ').title())

class RankingResultsDialog(QDialog):
    def __init__(self, ranked_data: pd.DataFrame, turbine_id_col: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ranking Results")
        self.setGeometry(100, 100, 600, 400)
        layout = QVBoxLayout()
        self.ranking_table = QTableWidget(len(ranked_data), 3)
        self.ranking_table.setHorizontalHeaderLabels(["Turbine ID", "Composite Score", "Rank"])
        self.ranking_table.setStyleSheet("QTableWidget { font-size: 12px; }")
        
        for i, (_, row) in enumerate(ranked_data.iterrows()):
            
            # Try both possible column names
            composite_score = row.get('CompositeScore', row.get('iec_performance_index', 0))
            self.ranking_table.setItem(i, 0, QTableWidgetItem(str(row[turbine_id_col])))
            self.ranking_table.setItem(i, 1, QTableWidgetItem(f"{composite_score:.2f}"))
            self.ranking_table.setItem(i, 2, QTableWidgetItem(str(row['Rank'])))
        layout.addWidget(self.ranking_table)
        close_button = QPushButton("Close")
        close_button.setStyleSheet("QPushButton { padding: 8px; font-size: 12px; }")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        self.setLayout(layout)
    
class RankingWindow(QMainWindow):
    def __init__(self, data: pd.DataFrame, parent=None, project_id = None):
        super().__init__(parent)
        self.setWindowTitle(Title)
        self.setGeometry(100, 100, 1400, 900)
        self.data = data
        self.filtered_data = None
        self._filter_cache = {}
        self.ranked_data = None
        self.current_ranking_results = None
        self.project_id = project_id
        # Initialize column cache
        self.column_cache = populate_column_cache(data)
        self.init_columns()
        self.apply_styles()
        self.initUI()

    def apply_styles(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(44, 62, 80))
        self.setPalette(palette)

        self.setStyleSheet(self.styleSheet() + """
            QDockWidget {
                background-color: #34495E;
                color: #ECF0F1;
                titlebar-close-icon: url(close.png);
                titlebar-normal-icon: url(float.png);
                font-size: 12px;
            }
            QDockWidget::title {
                background-color: #2C3E50;
                color: #ECF0F1;
                padding: 6px;
                border: 1px solid #5D6D7E;
                font-weight: bold;
            }
            QDockWidget::close-button, QDockWidget::float-button {
                background-color: #3498DB;
                border: none;
                border-radius: 3px;
                padding: 2px;
            }
            QDockWidget::close-button:hover, QDockWidget::float-button:hover {
                background-color: #2980B9;
            }
        """)
    
    def init_columns(self):
        """Initialize required columns using column cache"""
        # Required parameters
        required_params = ['power', 'wind_speed', 'rotor_speed']
        
        # Get cached columns
        self.timestamp_col = get_cached_column('timestamp', self.data)
        self.power_col = get_cached_column('power', self.data)
        self.wind_speed_col = get_cached_column('wind_speed', self.data)
        self.rotor_speed_col = get_cached_column('rotor_speed', self.data)
        
        # Validate required columns exist
        missing_params = []
        if not self.timestamp_col:
            missing_params.append('timestamp')
        if not self.power_col:
            missing_params.append('power')
        if not self.wind_speed_col:
            missing_params.append('wind_speed')
        if not self.rotor_speed_col:
            missing_params.append('rotor_speed')
        
        if missing_params:
            raise ValueError(f"Required columns not found: {missing_params}")
        
        # Find turbine ID column
        self.turbine_id_col = get_cached_column('turbine_id', self.data)
        if not self.turbine_id_col:
            # Fallback: look for any column that might be turbine ID
            possible_turbine_cols = [col for col in self.data.columns 
                                   if any(term in col.lower() for term in ['turbine', 'wtg', 'unit', 'id'])]
            if possible_turbine_cols:
                self.turbine_id_col = possible_turbine_cols[0]
            else:
                raise ValueError("Turbine ID column not found")
        
        # Build KPI columns list with only required parameters
        self.kpi_columns = []
        for param in required_params:
            col = get_cached_column(param, self.data)
            if col:
                self.kpi_columns.append(col)
        
        # Get unique turbines and date range
        self.turbines = sorted(self.data[self.turbine_id_col].unique().tolist())
        self.data[self.timestamp_col] = pd.to_datetime(self.data[self.timestamp_col], format='mixed')
        self.min_date = self.data[self.timestamp_col].min().date()
        self.max_date = self.data[self.timestamp_col].max().date()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left Sidebar (Command Center) - 30% width
        left_sidebar = self.create_left_sidebar()
        left_sidebar.setMaximumWidth(350)
        
        # Right Area (Plot only) - 70% width
        viz_widget = self.create_center_widget()
        
        # Add to main layout: 30% left, 70% right
        main_layout.addWidget(left_sidebar, stretch=30)
        main_layout.addWidget(viz_widget, stretch=70)

        # Create dockable bottom area (like visualization window)
        self._setup_bottom_docks()

        # Default selections
        if self.kpi_columns:
            if hasattr(self, 'power_col') and self.power_col in self.kpi_checkboxes:
                self.kpi_checkboxes[self.power_col].setChecked(True)
    

    def _setup_bottom_docks(self):
        """Setup dockable bottom area with rankings, stats, and analysis"""
        
        # 1. Rankings Dock (40% of bottom area)
        self.rankings_dock = QDockWidget("Performance Rankings", self)
        self.rankings_dock.setFeatures(
            QDockWidget.DockWidgetMovable | 
            QDockWidget.DockWidgetFloatable
        )
        rankings_widget = self._create_rankings_dock_widget()
        self.rankings_dock.setWidget(rankings_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.rankings_dock)
        
        # 2. Statistics Dock (30% of bottom area)
        self.stats_dock = QDockWidget("Quick Statistics", self)
        self.stats_dock.setFeatures(
            QDockWidget.DockWidgetMovable | 
            QDockWidget.DockWidgetFloatable
        )
        stats_widget = self._create_stats_dock_widget()
        self.stats_dock.setWidget(stats_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.stats_dock)
        
        # Arrange docks side by side
        self.setCorner(Qt.BottomLeftCorner, Qt.BottomDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner, Qt.BottomDockWidgetArea)
        
        # Set initial sizes (proportional widths: 40%, 30%, 30%)
        self.resizeDocks(
            [self.rankings_dock, self.stats_dock],
            [400, 300, 300],
            Qt.Horizontal
        )

    
    def _create_rankings_dock_widget(self):
        """Create rankings table widget for dock"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
              
        # Rankings Table
        self.ranking_table = QTableWidget(0, 5)
        self.ranking_table.setHorizontalHeaderLabels([
            "Rank", "Turbine", "Power (kW)", "Capacity %", "Performance"
        ])
        self.ranking_table.horizontalHeader().setStretchLastSection(True)
        self.ranking_table.setAlternatingRowColors(True)
        self.ranking_table.setStyleSheet("""
            QTableWidget {
                background-color: #34495E;
                color: #ECF0F1;
                gridline-color: #5D6D7E;
                font-size: 11px;
                border: 1px solid #5D6D7E;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:alternate {
                background-color: #2C3E50;
            }
            QHeaderView::section {
                background-color: #2C3E50;
                color: #ECF0F1;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #5D6D7E;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.ranking_table)
        
        return widget

    def _create_actions_dock_widget(self):
        """Create actions widget for dock"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(6)
        
        # Create action buttons
        self.plot_button = QPushButton("📊 Update Plot")
        self.rank_button = QPushButton("🏆 Rank Turbines")
        self.aep_button = QPushButton("⚡ Calculate AEP")
        self.export_button = QPushButton("💾 Export Data")
        
        # Connect signals
        self.plot_button.clicked.connect(self.update_visualization)
        self.rank_button.clicked.connect(self.rank_by_generation)
        self.aep_button.clicked.connect(self.calculate_aep)
        self.export_button.clicked.connect(self.export_data)
        
        # Style buttons
        button_style = """
            QPushButton {
                font-size: 11px;
                padding: 8px;
                background-color: #3498DB;
                color: white;
                border-radius: 4px;
                text-align: left;
                padding-left: 12px;
            }
            QPushButton:hover { 
                background-color: #2980B9; 
            }
            QPushButton:pressed {
                background-color: #21618C;
            }
        """
        
        for btn in [self.plot_button, self.rank_button, self.aep_button, self.export_button]:
            btn.setStyleSheet(button_style)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        return widget

    def _create_stats_dock_widget(self):
        """Create statistics widget for dock"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        self.stats_labels = {
            "total_turbines": QLabel("Total Turbines: 0"),
            "total_generation": QLabel("Total Generation: 0 kWh"),
            "avg_capacity": QLabel("Avg Capacity Factor: 0%"),
            "top_performer": QLabel("Top Performer: N/A"),
            "analysis_count": QLabel("Analysis Results: 0")
        }
        
        for label in self.stats_labels.values():
            label.setStyleSheet("color: #ECF0F1; font-size: 11px; padding: 3px;")
            layout.addWidget(label)
        
        layout.addStretch()
        
        return widget

    def _add_kpi_label_inside_graph(self, ax, selected_kpis):
        """Add KPI name inside graph area instead of Y-axis"""
        # Remove Y-axis label
        ax.set_ylabel("")
        
        # Get display names for selected KPIs
        kpi_names = []
        for kpi in selected_kpis:
            param_name = self._get_param_for_column(kpi)
            display_name = get_display_name(param_name) if param_name else kpi
            kpi_names.append(display_name)
        
        # Add text annotation inside graph
        kpi_text = ", ".join(kpi_names)
        ax.text(0.02, 0.98, kpi_text, transform=ax.transAxes,
                fontsize=11, fontweight='bold', verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8, edgecolor='gray'))
            
    def create_left_sidebar(self):
        """Create left control sidebar with actions"""
        left_sidebar = QWidget()
        left_sidebar.setMaximumWidth(350)
        left_sidebar.setStyleSheet("""
            QWidget {
                background-color: #2C3E50;
            }
        """)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #2C3E50;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        
        # Add collapsible sections
        scroll_layout.addWidget(self._create_turbine_selection_section())
        scroll_layout.addWidget(self._create_time_filters_section())
        scroll_layout.addWidget(self._create_kpi_selection_section())
        scroll_layout.addWidget(self._create_actions_section())  # NEW: Actions in left panel
        # scroll_layout.addWidget(self._create_analysis_options_section())
        scroll_layout.addWidget(self._create_visualization_settings_section())
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        
        left_layout = QVBoxLayout(left_sidebar)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(scroll_area)
        return left_sidebar

    def _create_actions_section(self):
        """Create actions section for left panel"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(6)
        
        # Create action buttons
        self.plot_button = QPushButton("📊 Update Plot")
        self.rank_button = QPushButton("🏆 Rank Turbines")
        self.aep_button = QPushButton("⚡ Calculate AEP")
        self.export_button = QPushButton("💾 Export Data")
        
        # Connect signals
        self.plot_button.clicked.connect(self.update_visualization)
        self.rank_button.clicked.connect(self.rank_by_generation)
        self.aep_button.clicked.connect(self.calculate_aep)
        self.export_button.clicked.connect(self.export_data)
        
        # Style buttons
        button_style = """
            QPushButton {
                font-size: 11px;
                padding: 8px;
                background-color: #3498DB;
                color: white;
                border-radius: 4px;
                text-align: left;
                padding-left: 12px;
            }
            QPushButton:hover { 
                background-color: #2980B9; 
            }
            QPushButton:pressed {
                background-color: #21618C;
            }
        """
        
        for btn in [self.plot_button, self.rank_button, self.aep_button, self.export_button]:
            btn.setStyleSheet(button_style)
            layout.addWidget(btn)
        
        return CollapsibleSection("Actions", content, expanded=True)

    def _create_turbine_selection_section(self):
        """Create turbine selection with checkboxes only"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(8)
        
        # Quick select buttons
        controls = QHBoxLayout()
        self.select_all_turbines_btn = QPushButton("Select All")
        self.clear_all_turbines_btn = QPushButton("Clear All")
        self.select_all_turbines_btn.clicked.connect(self.select_all_turbines)
        self.clear_all_turbines_btn.clicked.connect(self.clear_all_turbines)
        controls.addWidget(self.select_all_turbines_btn)
        controls.addWidget(self.clear_all_turbines_btn)
        layout.addLayout(controls)
        
        # Turbines list with checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(250)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #5D6D7E;
                background-color: #34495E;
            }
        """)
        scroll_widget = QWidget()
        turbine_layout = QVBoxLayout(scroll_widget)
        turbine_layout.setSpacing(4)
        turbine_layout.setContentsMargins(5, 5, 5, 5)
        
        self.turbine_checkboxes = {}
        
        # Create checkbox for each turbine
        for turbine in self.turbines:
            cb = QCheckBox(str(turbine))
            cb.setStyleSheet("color: #ECF0F1; font-size: 11px; padding: 3px;")
            self.turbine_checkboxes[turbine] = cb
            turbine_layout.addWidget(cb)
        
        turbine_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        return CollapsibleSection("Turbine Selection", content, expanded=True)


    def _add_turbine_checkbox(self, turbine, checked=True):
        """Add a turbine checkbox to the list"""
        if turbine in self.turbine_checkboxes:
            return  # Already exists
        
        cb_widget = QWidget()
        cb_layout = QHBoxLayout(cb_widget)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        cb_layout.setSpacing(5)
        
        cb = QCheckBox(str(turbine))
        cb.setChecked(checked)
        cb.setStyleSheet("color: #ECF0F1; font-size: 11px;")
        
        remove_btn = QPushButton("✕")
        remove_btn.setMaximumWidth(25)
        remove_btn.setMaximumHeight(20)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 2px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #C0392B; }
        """)
        remove_btn.clicked.connect(lambda: self._remove_turbine_checkbox(turbine))
        
        cb_layout.addWidget(cb)
        cb_layout.addStretch()
        cb_layout.addWidget(remove_btn)
        
        self.turbine_checkboxes[turbine] = cb
        self.turbine_checkbox_widgets[turbine] = cb_widget
        self.turbine_checkbox_layout.addWidget(cb_widget)

    def _on_turbine_selected_from_dropdown(self, index):
        """Handle turbine selection from dropdown"""
        if index <= 0:  # Skip "-- Select Turbine --"
            return
        
        turbine = self.turbines[index - 1]
        
        # Add checkbox if not already present
        if turbine not in self.turbine_checkboxes:
            self._add_turbine_checkbox(turbine, checked=True)
        else:
            # If exists, just check it
            self.turbine_checkboxes[turbine].setChecked(True)
        
        # Reset dropdown
        self.turbine_dropdown.setCurrentIndex(0)

    def _remove_turbine_checkbox(self, turbine):
        """Remove turbine checkbox from list"""
        if turbine in self.turbine_checkboxes:
            # Remove widget
            widget = self.turbine_checkbox_widgets[turbine]
            self.turbine_checkbox_layout.removeWidget(widget)
            widget.deleteLater()
            
            # Remove from tracking
            del self.turbine_checkboxes[turbine]
            del self.turbine_checkbox_widgets[turbine]


    def _create_time_filters_section(self):
        content = QWidget()
        layout = QGridLayout(content)
        layout.setVerticalSpacing(8)
        
        # Enable/disable checkbox
        self.enable_date_filter = QCheckBox("Enable Date Filter")
        self.enable_date_filter.setChecked(True)
        self.enable_date_filter.stateChanged.connect(self._toggle_date_filter)
        layout.addWidget(self.enable_date_filter, 0, 0, 1, 2)
        
        # Date widgets
        self.start_date_label = QLabel("From:")
        layout.addWidget(self.start_date_label, 1, 0)
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.fromString(str(self.min_date), "yyyy-MM-dd"))
        self.start_date.setCalendarPopup(True)
        layout.addWidget(self.start_date, 1, 1)
        
        self.end_date_label = QLabel("To:")
        layout.addWidget(self.end_date_label, 2, 0)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.fromString(str(self.max_date), "yyyy-MM-dd"))
        self.end_date.setCalendarPopup(True)
        layout.addWidget(self.end_date, 2, 1)
        
        # Interval
        layout.addWidget(QLabel("Interval:"), 3, 0)
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["None", "Hourly", "Daily", "Weekly", "Monthly"])
        layout.addWidget(self.interval_combo, 3, 1)
        
        return CollapsibleSection("Time Filters", content, expanded=True)
    
    def _toggle_date_filter(self):
        enabled = self.enable_date_filter.isChecked()
        self.start_date_label.setEnabled(enabled)
        self.start_date.setEnabled(enabled)
        self.end_date_label.setEnabled(enabled)
        self.end_date.setEnabled(enabled)
    
    def _create_kpi_selection_section(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        
        controls = QHBoxLayout()
        self.select_all_kpis_btn = QPushButton("Select All")
        self.clear_all_kpis_btn = QPushButton("Clear All")
        self.select_all_kpis_btn.clicked.connect(self.select_all_kpis)
        self.clear_all_kpis_btn.clicked.connect(self.clear_all_kpis)
        controls.addWidget(self.select_all_kpis_btn)
        controls.addWidget(self.clear_all_kpis_btn)
        layout.addLayout(controls)
        
        kpi_grid = QGridLayout()
        self.kpi_checkboxes = {}
        for i, col in enumerate(self.kpi_columns):
            param_name = self._get_param_for_column(col)
            display_name = get_display_name(param_name) if param_name else col
            cb = QCheckBox(display_name)
            cb.setToolTip(f"Column: {col}")
            self.kpi_checkboxes[col] = cb
            kpi_grid.addWidget(cb, i//2, i%2)
        layout.addLayout(kpi_grid)
        
        return CollapsibleSection("Parameters", content, expanded=True)

    def create_center_widget(self):
        """Create center visualization widget"""
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(5, 5, 5, 5)
        center_layout.setSpacing(5)
        
        viz_group = QGroupBox("Performance Visualization")
        viz_group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                color: #ECF0F1;
                border: 2px solid #5D6D7E;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 12px;
                background-color: #34495E;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
            }
        """)
        viz_layout = QVBoxLayout()
        viz_layout.setSpacing(5)
        
        self.viz_canvas = FigureCanvas(plt.Figure(figsize=(14, 8)))
        self.viz_canvas.setStyleSheet("background-color: white;")
        
        from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
        self.viz_toolbar = NavigationToolbar(self.viz_canvas, self)
        self.viz_toolbar.setStyleSheet("""
            QToolBar {
                background-color: #34495E;
                border: 1px solid #5D6D7E;
                spacing: 3px;
            }
        """)
        
        viz_layout.addWidget(self.viz_toolbar)
        viz_layout.addWidget(self.viz_canvas)
        
        viz_group.setLayout(viz_layout)
        center_layout.addWidget(viz_group)
        return center_widget

    
    def create_rankings_widget(self):
        """Create rankings table widget for bottom-left area"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Header with title and update button
        header_layout = QHBoxLayout()
        header_label = QLabel("🏆 Performance Rankings")
        header_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #ECF0F1;")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        update_rankings_btn = QPushButton("🔄 Update")
        update_rankings_btn.setMaximumWidth(100)
        update_rankings_btn.clicked.connect(self.update_ranking)
        update_rankings_btn.setStyleSheet("""
            QPushButton {
                font-size: 10px;
                padding: 5px;
                background-color: #3498DB;
                color: white;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #2980B9; }
        """)
        header_layout.addWidget(update_rankings_btn)
        
        layout.addLayout(header_layout)
        
        # Rankings Table
        self.ranking_table = QTableWidget(0, 5)
        self.ranking_table.setHorizontalHeaderLabels([
            "Rank", "Turbine", "Power (kW)", "Capacity %", "Performance"
        ])
        self.ranking_table.horizontalHeader().setStretchLastSection(True)
        self.ranking_table.setAlternatingRowColors(True)
        self.ranking_table.setStyleSheet("""
            QTableWidget {
                background-color: #34495E;
                color: #ECF0F1;
                gridline-color: #5D6D7E;
                font-size: 11px;
                border: 1px solid #5D6D7E;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:alternate {
                background-color: #2C3E50;
            }
            QHeaderView::section {
                background-color: #2C3E50;
                color: #ECF0F1;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #5D6D7E;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.ranking_table)
        
        return widget
    
    def create_stats_actions_panel(self):
        """Create stats and actions panel for bottom-right area"""
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(5, 5, 5, 5)
        panel_layout.setSpacing(8)
        
        # 1. Quick Statistics
        stats_group = QGroupBox("📊 Quick Statistics")
        stats_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
                font-weight: bold;
                color: #ECF0F1;
                border: 1px solid #5D6D7E;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(3)
        
        self.stats_labels = {
            "total_turbines": QLabel("Total Turbines: 0"),
            "total_generation": QLabel("Total Generation: 0 kWh"),
            "avg_capacity": QLabel("Avg Capacity Factor: 0%"),
            "top_performer": QLabel("Top Performer: N/A"),
            "analysis_count": QLabel("Analysis Results: 0")
        }
        
        for label in self.stats_labels.values():
            label.setStyleSheet("color: #ECF0F1; font-size: 10px; padding: 2px;")
            stats_layout.addWidget(label)
        
        stats_group.setLayout(stats_layout)
        panel_layout.addWidget(stats_group)
        
        # 2. Action Buttons
        actions_group = QGroupBox("⚡ Actions")
        actions_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
                font-weight: bold;
                color: #ECF0F1;
                border: 1px solid #5D6D7E;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(5)
        
        # Create action buttons
        self.plot_button = QPushButton("📊 Update Plot")
        self.rank_button = QPushButton("🏆 Rank Turbines")
        self.aep_button = QPushButton("⚡ Calculate AEP")
        self.export_button = QPushButton("💾 Export Data")
        
        # Connect signals
        self.plot_button.clicked.connect(self.update_visualization)
        self.rank_button.clicked.connect(self.rank_by_generation)
        self.aep_button.clicked.connect(self.calculate_aep)
        self.export_button.clicked.connect(self.export_data)
        
        # Style buttons
        button_style = """
            QPushButton {
                font-size: 11px;
                padding: 8px;
                background-color: #3498DB;
                color: white;
                border-radius: 4px;
                text-align: left;
                padding-left: 12px;
            }
            QPushButton:hover { 
                background-color: #2980B9; 
            }
            QPushButton:pressed {
                background-color: #21618C;
            }
        """
        
        for btn in [self.plot_button, self.rank_button, self.aep_button, self.export_button]:
            btn.setStyleSheet(button_style)
            actions_layout.addWidget(btn)
        
        actions_group.setLayout(actions_layout)
        panel_layout.addWidget(actions_group)
        
        # 3. Analysis Results
        results_group = QGroupBox("🔍 Analysis Results")
        results_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
                font-weight: bold;
                color: #ECF0F1;
                border: 1px solid #5D6D7E;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        results_layout = QVBoxLayout()
        results_layout.setSpacing(5)
        
        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Metric", "Value", "Unit"])
        self.results_table.setMaximumHeight(100)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setStyleSheet("""
            QTableWidget {
                background-color: #34495E;
                color: #ECF0F1;
                gridline-color: #5D6D7E;
                font-size: 10px;
                border: 1px solid #5D6D7E;
            }
            QHeaderView::section {
                background-color: #2C3E50;
                color: #ECF0F1;
                font-weight: bold;
                padding: 4px;
                font-size: 10px;
            }
        """)
        results_layout.addWidget(self.results_table)
        
        self.run_analysis_button = QPushButton("🔬 Run Analysis")
        self.run_analysis_button.clicked.connect(self.run_analysis)
        self.run_analysis_button.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                padding: 6px;
                background-color: #E74C3C;
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #C0392B; }
        """)
        results_layout.addWidget(self.run_analysis_button)
        
        results_group.setLayout(results_layout)
        panel_layout.addWidget(results_group)
        
        panel_layout.addStretch()
        
        return panel

    def update_visualization(self):
        """Update visualization using ranking and plotting logic"""
        selected_turbines = [t for t, cb in self.turbine_checkboxes.items() if cb.isChecked()]
        selected_kpis = [k for k, cb in self.kpi_checkboxes.items() if cb.isChecked()]
        
        if not selected_turbines:
            self._show_canvas_message("Please select at least one turbine")
            return
        
        if not selected_kpis:
            self._show_canvas_message("Please select at least one KPI")
            return
        
        filtered_data = self.get_filtered_data()
        if filtered_data.empty:
            self._show_canvas_message("No data available for selected filters", "lightcoral")
            return
        
        # Filter data for selected turbines
        turbine_data = filtered_data[filtered_data[self.turbine_id_col].isin(selected_turbines)]
        
        if turbine_data.empty:
            self._show_canvas_message("No data for selected turbines", "lightcoral")
            return
        
        self.viz_canvas.figure.clear()
        fig = self.viz_canvas.figure
        ax = fig.add_subplot(111)
        chart_type = self.chart_type_combo.currentText()
        
        try:
            # Create ranker instance
            ranker = TurbineRanker(turbine_data, id_col=self.turbine_id_col, date_col=self.timestamp_col)
            
            # Check if cumulative view is enabled
            is_cumulative = hasattr(self, 'show_cumulative') and self.show_cumulative.isChecked()
            
            # Plot based on chart type
            if chart_type == "Bar Chart":
                if is_cumulative:
                    self.plot_cumulative_bar_chart(turbine_data, selected_turbines, selected_kpis, ax)
                else:
                    ranker.plot_bar_graph(turbine_data, selected_turbines, selected_kpis, ax)
            
            elif chart_type == "Line Chart":
                if is_cumulative:
                    self.plot_cumulative_line_chart(turbine_data, selected_turbines, selected_kpis, ax)
                else:
                    ranker.plot_trend_line(turbine_data, selected_turbines, selected_kpis, ax)
            
            elif chart_type == "Spline Chart":
                show_pct = hasattr(self, 'show_percentage') and self.show_percentage.isChecked()
                ranker.plot_spline_trend_line(turbine_data, selected_turbines, selected_kpis, ax, percentage=show_pct)
            
            elif chart_type == "Efficiency Trends":
                self.plot_efficiency_trends(turbine_data, selected_turbines, ax)
            elif chart_type == "Comparative Power Curve":
                self.plot_comparative_power_curve(turbine_data, selected_turbines, ax)

            
            # Apply grid if enabled
            if hasattr(self, 'show_grid') and self.show_grid.isChecked():
                ax.grid(True, alpha=0.3, linestyle='--', color='gray')
            
            fig.tight_layout()
            
        except Exception as e:
            import traceback
            error_msg = f"Error creating visualization:\n{str(e)}\n{traceback.format_exc()}"
            print(error_msg)  # Debug print
            self._show_canvas_message(f"Error: {str(e)}", "lightyellow")
            return
        
        self.viz_canvas.draw()

    def plot_cumulative_line_chart(self, data, turbines, kpis, ax):
        """Plot cumulative line chart over time"""
        from utils.plot_helpers import insert_nans_at_time_gaps
        
        turbine_data = data[data[self.turbine_id_col].isin(turbines)]
        if turbine_data.empty:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            return
        
        for turbine in turbines:
            turb_data = turbine_data[turbine_data[self.turbine_id_col] == turbine].sort_values(self.timestamp_col)
            if turb_data.empty:
                continue
            for kpi in kpis:
                if kpi in turb_data.columns:
                    cumulative = turb_data[kpi].cumsum()
                    # Create temp df with cumulative values
                    temp_df = pd.DataFrame({
                        self.timestamp_col: turb_data[self.timestamp_col],
                        'cumulative': cumulative
                    })
                    # Insert NaNs at gaps
                    temp_df = insert_nans_at_time_gaps(temp_df, self.timestamp_col, max_gap_hours=24)
                    ax.plot(temp_df[self.timestamp_col], temp_df['cumulative'], label=f"{turbine} - {kpi}", linewidth=2)


    def plot_efficiency_trends(self, data, turbines, ax):
        """Plot efficiency trends over time"""
        if not turbines:
            ax.text(0.5, 0.5, "No turbines selected", ha='center', va='center')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            return
        
        if not self.power_col or not self.wind_speed_col:
            ax.text(0.5, 0.5, "Power or wind speed column not found", ha='center', va='center')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            return
        
        ranker = TurbineRanker(data, id_col=self.turbine_id_col, date_col=self.timestamp_col)
        efficiency_data = ranker.calculate_efficiency_metrics(self.power_col, self.wind_speed_col)
        
        if 'capacity_factor' not in efficiency_data.columns:
            ax.text(0.5, 0.5, "Efficiency metrics not available", ha='center', va='center')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            return
        
        for turbine in turbines:
            turbine_eff = efficiency_data[efficiency_data[self.turbine_id_col] == turbine]
            if not turbine_eff.empty:
                ax.plot(turbine_eff[self.timestamp_col], turbine_eff['capacity_factor'], 
                        label=f"{turbine}", linewidth=2)
        
        ax.set_title("Capacity Factor Trends", fontweight='bold', fontsize=12)
        ax.set_xlabel("Time", fontweight='bold', fontsize=11)
        ax.set_ylabel("Capacity Factor (%)", fontweight='bold', fontsize=11)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    
    def rank_by_generation(self):
        selected_turbines = [turbine for turbine, cb in self.turbine_checkboxes.items() if cb.isChecked()]
        
        if not selected_turbines:
            QMessageBox.warning(self, "No Turbines", "Please select at least one turbine.")
            return
        
        if not hasattr(self, 'power_col'):
            QMessageBox.warning(self, "No Power Data", "No power column found in the data.")
            return
        
        filtered_data = self.get_filtered_data()
        turbine_data = filtered_data[filtered_data[self.turbine_id_col].isin(selected_turbines)]
        
        ranker = TurbineRanker(turbine_data, id_col=self.turbine_id_col, date_col=self.timestamp_col)
        ranking_results = ranker.rank_by_power_generation(self.power_col)
        
        self.ranking_table.setRowCount(len(ranking_results))
        for i, (_, row) in enumerate(ranking_results.iterrows()):
            self.ranking_table.setItem(i, 0, QTableWidgetItem(str(row['rank'])))
            self.ranking_table.setItem(i, 1, QTableWidgetItem(str(row[self.turbine_id_col])))
            self.ranking_table.setItem(i, 2, QTableWidgetItem(f"{row['total_generation']:.1f}"))
            self.ranking_table.setItem(i, 3, QTableWidgetItem(f"{row['capacity_factor']:.1f}"))
            self.ranking_table.setItem(i, 4, QTableWidgetItem(f"{row['iec_performance_index']:.2f}"))
        
        self.update_quick_stats(ranking_results)
        self.current_ranking_results = ranking_results
        QMessageBox.information(self, "Success", "Turbines ranked by IEC power generation standards.")


    # Fix calculate_aep to use existing attribute:
    def calculate_aep(self):
        selected_turbines = [turbine for turbine, cb in self.turbine_checkboxes.items() if cb.isChecked()]
        
        if not selected_turbines:
            QMessageBox.warning(self, "No Turbines", "Please select at least one turbine.")
            return
    
        if not self.power_col or not self.wind_speed_col:
            QMessageBox.warning(self, "Missing Data", "Power and wind speed columns required for AEP calculation.")
            return
    
        filtered_data = self.get_filtered_data()
        turbine_data = filtered_data[filtered_data[self.turbine_id_col].isin(selected_turbines)]
    
        if turbine_data.empty:
            QMessageBox.warning(self, "No Data", "No data available for selected turbines.")
            return
    
        ranker = TurbineRanker(turbine_data, id_col=self.turbine_id_col, date_col=self.timestamp_col)
        aep_results = ranker.calculate_annual_energy_production(self.power_col, self.wind_speed_col)
        
        self.show_aep_results(aep_results)
    
    def run_analysis(self):
        if not any(cb.isChecked() for cb in self.analysis_checkboxes.values()):
            QMessageBox.warning(self, "No Analysis", "Please select analysis options.")
            return
        
        selected_kpis = [k for k, cb in self.kpi_checkboxes.items() if cb.isChecked()]
        if not selected_kpis:
            QMessageBox.warning(self, "No KPIs", "Please select KPIs for analysis.")
            return
        
        filtered_data = self.get_filtered_data()
        if filtered_data.empty:
            QMessageBox.warning(self, "No Data", "No data available for selected filters.")
            return
            
        ranker = TurbineRanker(filtered_data, id_col=self.turbine_id_col, date_col=self.timestamp_col)
        results = {}
        
        if self.analysis_checkboxes["efficiency"].isChecked():
            # Use existing attributes
            if self.power_col and self.wind_speed_col:
                results['efficiency'] = ranker.calculate_efficiency_metrics(self.power_col, self.wind_speed_col)
        
        if self.analysis_checkboxes["anomalies"].isChecked():
            results['anomalies'] = ranker.detect_anomalies(selected_kpis)
        
        if self.analysis_checkboxes["statistics"].isChecked():
            results['statistics'] = ranker.get_performance_statistics(selected_kpis)
        
        if self.analysis_checkboxes["seasonal"].isChecked():
            selected_turbines = [t for t, cb in self.turbine_checkboxes.items() if cb.isChecked()]
            if selected_turbines:
                seasonal_results = []
                for turbine in selected_turbines:
                    seasonal_data = ranker.get_seasonal_performance(turbine, selected_kpis)
                    seasonal_results.append(seasonal_data)
                results['seasonal'] = pd.concat(seasonal_results, ignore_index=True)
        
        self.show_analysis_results(results)
    
    def get_filtered_data(self):
        interval_type = self.interval_combo.currentText()
        cache_key = (self.enable_date_filter.isChecked(), 
                     self.start_date.date().toPyDate() if self.enable_date_filter.isChecked() else None,
                     self.end_date.date().toPyDate() if self.enable_date_filter.isChecked() else None,
                     interval_type)
        
        if cache_key in self._filter_cache:
            return self._filter_cache[cache_key]
        
        df = self.data
        
        # Only apply date filter if enabled
        if self.enable_date_filter.isChecked():
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            date_mask = (df[self.timestamp_col].dt.date >= start_date) & (df[self.timestamp_col].dt.date <= end_date)
            filtered_df = df[date_mask].copy()
        else:
            filtered_df = df.copy()
        
        if interval_type != "None":
            ranker = TurbineRanker(filtered_df, id_col=self.turbine_id_col, date_col=self.timestamp_col)
            filtered_df = ranker.filter_by_time_interval(interval_type.lower())
        
        self._filter_cache[cache_key] = filtered_df
        return filtered_df

    def update_quick_stats(self, ranking_results):
        total_turbines = len(ranking_results)
        total_generation = ranking_results['total_generation'].sum()
        avg_capacity = ranking_results['capacity_factor'].mean()
        top_performer = ranking_results.iloc[0][self.turbine_id_col] if not ranking_results.empty else "N/A"
        
        self.stats_labels["total_turbines"].setText(f"Total Turbines: {total_turbines}")
        self.stats_labels["total_generation"].setText(f"Total Generation: {total_generation:.1f} kWh")
        self.stats_labels["avg_capacity"].setText(f"Avg Capacity Factor: {avg_capacity:.1f}%")
        self.stats_labels["top_performer"].setText(f"Top Performer: {top_performer}")

    def plot_power_curve(self, data, turbines, ax):
        if not hasattr(self, 'power_col'):
            ax.text(0.5, 0.5, "Power column not detected", ha='center', va='center')
            return
        
        wind_cols = [col for col in self.kpi_columns if 'wind' in col.lower() and 'speed' in col.lower()]
        if not wind_cols:
            ax.text(0.5, 0.5, "Wind speed column not found", ha='center', va='center')
            return
        
        ranker = TurbineRanker(data, id_col=self.turbine_id_col, date_col=self.timestamp_col)
        power_curve_data = ranker.get_iec_power_curve(self.power_col, wind_cols[0])
        
        for turbine in turbines:
            turbine_curve = power_curve_data[power_curve_data['turbine_id'] == turbine]
            if not turbine_curve.empty:
                ax.plot(turbine_curve['wind_speed_center'], turbine_curve['mean_power'], 
                        'o-', label=f"{turbine}", alpha=0.7)
        
        format_axes(ax, "Wind Speed (m/s)", "", "IEC Power Curves")
        # Add KPI label inside
        ax.text(0.02, 0.98, "Power (kW)", transform=ax.transAxes,
                fontsize=10, fontweight='bold', verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.85, edgecolor='#3498DB'))

        ax.legend()
        ax.grid(True, alpha=0.3)       

        
    def plot_efficiency_trends(self, data, turbines, ax):
        """Plot efficiency trends over time"""
        if not turbines:
            ax.text(0.5, 0.5, "No turbines selected", ha='center', va='center')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            return
        
        if not self.power_col or not self.wind_speed_col:
            ax.text(0.5, 0.5, "Power or wind speed column not found", ha='center', va='center')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            return
        
        ranker = TurbineRanker(data, id_col=self.turbine_id_col, date_col=self.timestamp_col)
        efficiency_data = ranker.calculate_efficiency_metrics(self.power_col, self.wind_speed_col)
        
        if 'capacity_factor' not in efficiency_data.columns:
            ax.text(0.5, 0.5, "Efficiency metrics not available", ha='center', va='center')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            return
        
        # Import the helper function
        from utils.plot_helpers import insert_nans_at_time_gaps
        
        for turbine in turbines:
            turbine_eff = efficiency_data[efficiency_data[self.turbine_id_col] == turbine]
            if not turbine_eff.empty:
                # Insert NaNs at time gaps to break line connections
                turbine_eff = insert_nans_at_time_gaps(turbine_eff, self.timestamp_col, max_gap_hours=24)
                ax.plot(turbine_eff[self.timestamp_col], turbine_eff['capacity_factor'], 
                        label=f"{turbine}", linewidth=2)

    
    def _get_param_for_column(self, col):
        """Get parameter name for a column"""
        if not hasattr(self, '_col_to_param'):
            self._col_to_param = {}
            for param in ['timestamp', 'power', 'wind_speed', 'rotor_speed']:
                cached_col = get_cached_column(param, self.data)
                if cached_col:
                    self._col_to_param[cached_col] = param
        return self._col_to_param.get(col)
    
    
    def _create_visualization_settings_section(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        
        chart_layout = QHBoxLayout()
        chart_layout.addWidget(QLabel("Chart Type:"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems([
            "Bar Chart", "Line Chart", "Spline Chart", 
           "Efficiency Trends","Comparative Power Curve"
        ])
        chart_layout.addWidget(self.chart_type_combo)
        layout.addLayout(chart_layout)
        
        self.show_percentage = QCheckBox("Show Percentage")
        self.show_grid = QCheckBox("Show Grid")
        self.show_grid.setChecked(True)
        self.show_cumulative = QCheckBox("Show Cumulative View")
        self.show_cumulative.setChecked(False)
        self.enable_iec_binning = QCheckBox("Enable IEC Binning (0.5 m/s)")  # ADD THIS
        self.enable_iec_binning.setChecked(True)                              # ADD THIS
        
        layout.addWidget(self.show_percentage)
        layout.addWidget(self.show_grid)
        layout.addWidget(self.show_cumulative)
        layout.addWidget(self.enable_iec_binning)    
        
        return CollapsibleSection("Visualization Settings", content, expanded=True)

    
    # Add helper method for canvas messages (eliminates duplication):
    def _show_canvas_message(self, message, facecolor="lightgray"):
        """Display a message on the canvas"""
        self.viz_canvas.figure.clear()
        ax = self.viz_canvas.figure.add_subplot(111)
        ax.text(0.5, 0.5, message, ha='center', va='center', fontsize=14,
                bbox=dict(boxstyle="round,pad=0.3", facecolor=facecolor))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        self.viz_canvas.draw()
    
    def select_all_turbines(self):
        for cb in self.turbine_checkboxes.values():
            cb.setChecked(True)

    def clear_all_turbines(self):
        for cb in self.turbine_checkboxes.values():
            cb.setChecked(False)

    def select_all_kpis(self):
        for cb in self.kpi_checkboxes.values():
            cb.setChecked(True)

    def clear_all_kpis(self):
        for cb in self.kpi_checkboxes.values():
            cb.setChecked(False)

    def update_ranking(self):
        if hasattr(self, 'current_ranking_results'):
            self.rank_by_generation()
        else:
            QMessageBox.information(self, "No Data", "Generate rankings first.")

    def export_data(self):
        if hasattr(self, 'current_ranking_results'):
            file_name, _ = QFileDialog.getSaveFileName(self, "Export Data", "", "CSV Files (*.csv)")
            if file_name:
                self.current_ranking_results.to_csv(file_name, index=False)
                QMessageBox.information(self, "Success", "Data exported successfully.")

    def show_aep_results(self, aep_results):
        dialog = AEPResultsDialog(aep_results, self)
        dialog.exec_()

    def show_analysis_results(self, results):
        dialog = AnalysisResultsDialog(results, self)
        dialog.exec_()
    
    def plot_cumulative_bar_chart(self, data, turbines, kpis, ax):
        """Plot cumulative bar chart for selected turbines and KPIs"""
        turbine_data = data[data[self.turbine_id_col].isin(turbines)]
        if turbine_data.empty:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            return
        
        # Calculate cumulative sums
        cumulative_data = turbine_data.groupby(self.turbine_id_col)[kpis].sum()
        
        if cumulative_data.empty:
            ax.text(0.5, 0.5, "No data to plot", ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            return
        
        cumulative_data.plot(kind='bar', ax=ax, color=plt.cm.Paired(np.arange(len(cumulative_data))))
        ax.set_xlabel("Turbine", fontweight='bold', fontsize=11)
        ax.set_ylabel("Cumulative Value", fontweight='bold', fontsize=11)
        ax.set_title("Cumulative KPIs by Turbine", fontweight='bold', fontsize=12)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
        ax.legend(fontsize=9)
    
    def plot_comparative_power_curve(self, data, turbines, ax):
        """Plot comparative power curves"""
        if not self.power_col or not self.wind_speed_col:
            ax.text(0.5, 0.5, "Power or wind speed column not found", ha='center', va='center')
            return
    
        enable_iec = hasattr(self, 'enable_iec_binning') and self.enable_iec_binning.isChecked() if hasattr(self, 'enable_iec_binning') else True
        
        ranker = TurbineRanker(data, id_col=self.turbine_id_col, date_col=self.timestamp_col)
        ranker.plot_comparative_power_curve(
            data, turbines, 
            self.power_col, self.wind_speed_col, 
            ax, enable_iec_binning=enable_iec
        )



class AEPResultsDialog(QDialog):
    def __init__(self, aep_data: pd.DataFrame, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Annual Energy Production Results")
        self.setGeometry(100, 100, 900, 600)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        table = QTableWidget(len(aep_data), 7)
        table.setHorizontalHeaderLabels([
            "Rank", "Turbine", "AEP (kWh)", "Capacity %", 
            "Wind Speed", "Measured Energy", "Period (hrs)"
        ])
        table.setStyleSheet("QTableWidget { font-size: 12px; }")
        
        for i, (_, row) in enumerate(aep_data.iterrows()):
            table.setItem(i, 0, QTableWidgetItem(str(row['aep_rank'])))
            table.setItem(i, 1, QTableWidgetItem(str(row['turbine_id'])))
            table.setItem(i, 2, QTableWidgetItem(f"{row['annual_energy_production']:.1f}"))
            table.setItem(i, 3, QTableWidgetItem(f"{row['capacity_factor']:.2f}"))
            table.setItem(i, 4, QTableWidgetItem(f"{row['mean_wind_speed']:.2f}"))
            table.setItem(i, 5, QTableWidgetItem(f"{row['measured_energy']:.1f}"))
            table.setItem(i, 6, QTableWidgetItem(f"{row['measurement_period_hours']:.1f}"))
        
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton { 
                font-size: 12px; 
                padding: 8px; 
                background-color: #2196F3; 
                color: white; 
                border-radius: 4px;
            }
            QPushButton:hover { 
                background-color: #1976D2;
            }
        """)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)

class AnalysisResultsDialog(QDialog):
    def __init__(self, results: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analysis Results")
        self.setGeometry(100, 100, 1000, 700)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        from PyQt5.QtWidgets import QTabWidget
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("QTabWidget { font-size: 12px; }")
        
        for analysis_type, data in results.items():
            if isinstance(data, pd.DataFrame) and not data.empty:
                tab = QWidget()
                tab_layout = QVBoxLayout()
                
                table = QTableWidget()
                table.setRowCount(len(data))
                table.setColumnCount(len(data.columns))
                table.setHorizontalHeaderLabels(data.columns.tolist())
                table.setStyleSheet("QTableWidget { font-size: 12px; }")
                
                for i, (_, row) in enumerate(data.iterrows()):
                    for j, value in enumerate(row):
                        table.setItem(i, j, QTableWidgetItem(str(value)))
                
                table.resizeColumnsToContents()
                tab_layout.addWidget(table)
                tab.setLayout(tab_layout)
                tab_widget.addTab(tab, analysis_type.title())
        
        layout.addWidget(tab_widget)
        
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton { 
                font-size: 12px; 
                padding: 8px; 
                background-color: #2196F3; 
                color: white; 
                border-radius: 4px;
            }
            QPushButton:hover { 
                background-color: #1976D2;
            }
        """)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)

    def calculate_wind_power_relationship(data: pd.DataFrame, power_col: str, wind_speed_col: str) -> pd.DataFrame:
        data = data.copy()
        data['theoretical_power'] = 0.5 * 1.225 * (data[wind_speed_col] ** 3) * 0.4
        data['power_efficiency'] = data[power_col] / data['theoretical_power']
        data['power_loss'] = data['theoretical_power'] - data[power_col]
        return data

    def get_turbine_availability(data: pd.DataFrame, turbine_id_col: str, power_col: str) -> pd.DataFrame:
        availability_data = []
        
        for turbine_id in data[turbine_id_col].unique():
            turbine_data = data[data[turbine_id_col] == turbine_id]
            total_records = len(turbine_data)
            available_records = len(turbine_data[turbine_data[power_col] > 0])
            availability = (available_records / total_records) * 100 if total_records > 0 else 0
            
            availability_data.append({
                'turbine_id': turbine_id,
                'availability_percentage': availability,
                'total_records': total_records,
                'available_records': available_records
            })
        
        return pd.DataFrame(availability_data)