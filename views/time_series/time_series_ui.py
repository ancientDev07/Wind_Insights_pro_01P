from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import pyqtgraph as pg
from utils.collapsible_prop import CollapsibleSection

class TimeSeriesUI:
    def setup_ui(self, main_window):
        """Setup the complete UI for Time Series Analysis"""
        main_window.setGeometry(100, 100, 1400, 900)
        main_window.setFont(QFont("Times New Roman", 10))
        
        self.create_menu_bar(main_window)
        
        central_widget = QWidget()
        main_window.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left Sidebar (30% width)
        left_sidebar = self.create_left_sidebar()
        left_sidebar.setMaximumWidth(350)
        
        # Center Widget (70% width)
        center_widget = self.create_central_widget(main_window)
        
        main_layout.addWidget(left_sidebar, stretch=30)
        main_layout.addWidget(center_widget, stretch=70)

        # Bottom dockable statistics
        self._setup_bottom_dock(main_window)
        
        main_window.statusBar().showMessage("Ready - Select parameters and click Plot")
        self.apply_theme(main_window)

    def apply_theme(self, main_window):
        """Apply Wind Data Insight Pro theme"""
        main_window.setStyleSheet("""
            QMainWindow { background-color: #2C3E50; color: #ECF0F1; }
            QWidget { background-color: #2C3E50; color: #ECF0F1; }
            QGroupBox { 
                font-weight: bold; border: 1px solid #5D6D7E; 
                border-radius: 5px; margin-top: 10px; padding-top: 15px;
                background-color: #34495E; color: #ECF0F1;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 8px;
                background-color: #3498DB;
                color: white;
                border-radius: 4px;
            }
            QPushButton { 
                background-color: #3498DB; color: white; border: none; 
                padding: 8px 12px; border-radius: 4px; font-size: 11px;
            }
            QPushButton:hover { background-color: #2980B9; }
            QPushButton:pressed { background-color: #21618C; }
            QCheckBox { spacing: 5px; color: #ECF0F1; font-size: 11px; }
            QLabel { color: #ECF0F1; font-size: 11px; }
            QComboBox, QLineEdit { 
                background-color: #34495E; color: #ECF0F1; 
                border: 1px solid #5D6D7E; border-radius: 3px; padding: 5px;
            }
            QScrollArea { border: none; background-color: #2C3E50; }
            QTableWidget {
                background-color: #34495E; color: #ECF0F1;
                gridline-color: #5D6D7E; font-size: 11px;
                border: 1px solid #5D6D7E;
            }
            QHeaderView::section {
                background-color: #2C3E50; color: #ECF0F1;
                font-weight: bold; padding: 6px; border: 1px solid #5D6D7E;
            }
            QDockWidget {
                background-color: #34495E; color: #ECF0F1;
                font-size: 12px;
            }
            QDockWidget::title {
                background-color: #2C3E50; color: #ECF0F1;
                padding: 6px; border: 1px solid #5D6D7E;
                font-weight: bold;
            }
            QStatusBar { background-color: #34495E; color: #ECF0F1; }
        """)
    
    def create_menu_bar(self, main_window):
        """Create menu bar with File, View, and Analysis menus"""
        menubar = main_window.menuBar()
        
        file_menu = menubar.addMenu('File')
        self.export_plot_action = file_menu.addAction('Export Plot')
        self.export_plot_action.setShortcut('Ctrl+E')
        self.export_data_action = file_menu.addAction('Export Data')
        self.export_data_action.setShortcut('Ctrl+Shift+E')
        
        view_menu = menubar.addMenu('View')
        self.reset_action = view_menu.addAction('Reset View')
        self.reset_action.setShortcut('Ctrl+R')
        self.clear_action = view_menu.addAction('Clear Plot')
        self.clear_action.setShortcut('Ctrl+L')
        
        analysis_menu = menubar.addMenu('Analysis')
        self.plot_action = analysis_menu.addAction('Plot Data')
        self.plot_action.setShortcut('Ctrl+P')
    
    # def create_left_sidebar(self):
    #     """Create left control sidebar"""
    #     left_sidebar = QWidget()
    #     left_sidebar.setMaximumWidth(350)
    #     left_sidebar.setStyleSheet("QWidget { background-color: #2C3E50; }")
        
    #     scroll_area = QScrollArea()
    #     scroll_area.setWidgetResizable(True)
    #     scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #2C3E50; }")
        
    #     scroll_widget = QWidget()
    #     scroll_layout = QVBoxLayout(scroll_widget)
    #     scroll_layout.setSpacing(10)
    #     scroll_layout.setContentsMargins(5, 5, 5, 5)
        
    #     # Add collapsible sections
    #     scroll_layout.addWidget(self._create_filter_section())
    #     scroll_layout.addWidget(self._create_parameter_section())
    #     scroll_layout.addWidget(self._create_actions_section())
    #     scroll_layout.addWidget(self._create_plot_options_section())
        
    #     scroll_layout.addStretch()
    #     scroll_widget.setLayout(scroll_layout)
    #     scroll_area.setWidget(scroll_widget)
        
    #     left_layout = QVBoxLayout(left_sidebar)
    #     left_layout.setContentsMargins(0, 0, 0, 0)
    #     left_layout.addWidget(scroll_area)
    #     return left_sidebar
    
    def create_left_sidebar(self):
        """Create left control sidebar"""
        left_sidebar = QWidget()
        left_sidebar.setMaximumWidth(350)
        left_sidebar.setStyleSheet("QWidget { background-color: #2C3E50; }")
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #2C3E50; }")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        
        # Time window controls (NEW - moved from central)
        # scroll_layout.addWidget(self._create_time_window_section())
        time_window_section = self._create_time_window_section()
        scroll_layout.addWidget(time_window_section)

        # Add collapsible sections
        scroll_layout.addWidget(self._create_filter_section())
        scroll_layout.addWidget(self._create_parameter_section())
        scroll_layout.addWidget(self._create_actions_section())
        scroll_layout.addWidget(self._create_plot_options_section())
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        
        left_layout = QVBoxLayout(left_sidebar)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(scroll_area)
        return left_sidebar

    def _create_time_window_section(self):
        """Create time window controls section"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(6)
        
        layout.addWidget(QLabel("Time Window:"))
        
        self.window_combo = QComboBox()
        self.window_combo.setStyleSheet("QComboBox { background-color: #34495E; color: #ECF0F1; border: 1px solid #5D6D7E; padding: 5px; }")

        self.window_combo.addItems(["6 Hours", "12 Hours", "24 Hours", "3 Days", "7 Days", "1 Month", "Full Dataset"])
        self.window_combo.setCurrentText("24 Hours")
        layout.addWidget(self.window_combo)
        
        layout.addWidget(QLabel("Position:"))
        self.window_slider = QSlider(Qt.Horizontal)
        self.window_slider.setStyleSheet("QSlider { background-color: #34495E; } QSlider::groove:horizontal { background: #5D6D7E; height: 8px; } QSlider::handle:horizontal { background: #3498DB; width: 18px; margin: -5px 0; }")

        self.window_slider.setMinimum(0)
        self.window_slider.setMaximum(100)
        self.window_slider.setValue(0)
        self.window_slider.setEnabled(False)
        layout.addWidget(self.window_slider)
        
        self.window_position_label = QLabel("Start: -- | End: --")
        self.window_position_label.setStyleSheet("QLabel { color: #ECF0F1; font-size: 10px; }")

        self.window_position_label.setWordWrap(True)
        layout.addWidget(self.window_position_label)
        
        return CollapsibleSection("Time Window", content, expanded=True)

    
    def _create_filter_section(self):
        """Create filter options section"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(8)
        
        self.enable_600s_filter = QCheckBox("600s Cycle Only")
        self.enable_date_filter = QCheckBox("Enable Date Filter")
        self.enable_date_filter.setChecked(True)
        
        date_layout1 = QHBoxLayout()
        date_layout1.addWidget(QLabel("Start Date:"))
        self.start_date_only = QLineEdit()
        self.start_date_only.setPlaceholderText("DD-MM-YYYY")
        date_layout1.addWidget(self.start_date_only)
        
        date_layout2 = QHBoxLayout()
        date_layout2.addWidget(QLabel("End Date:"))
        self.end_date_only = QLineEdit()
        self.end_date_only.setPlaceholderText("DD-MM-YYYY")
        date_layout2.addWidget(self.end_date_only)
        
        self.enable_time_filter = QCheckBox("Enable Time Filter")
        
        time_layout1 = QHBoxLayout()
        time_layout1.addWidget(QLabel("Start Time:"))
        self.start_time_only = QLineEdit()
        self.start_time_only.setPlaceholderText("HH:MM")
        time_layout1.addWidget(self.start_time_only)
        
        time_layout2 = QHBoxLayout()
        time_layout2.addWidget(QLabel("End Time:"))
        self.end_time_only = QLineEdit()
        self.end_time_only.setPlaceholderText("HH:MM")
        time_layout2.addWidget(self.end_time_only)
        
        layout.addWidget(self.enable_600s_filter)
        layout.addWidget(self.enable_date_filter)
        layout.addLayout(date_layout1)
        layout.addLayout(date_layout2)
        layout.addWidget(self.enable_time_filter)
        layout.addLayout(time_layout1)
        layout.addLayout(time_layout2)
        
        return CollapsibleSection("Filter Options", content, expanded=True)
    
    def _create_parameter_section(self):
        """Create parameter selection section"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(8)
        
        # Power Group
        self.power_group = QGroupBox("⚡ Power")
        power_layout = QVBoxLayout(self.power_group)
        self.power_full_cb = QCheckBox("Power (kW)")
        self.power_active_cb = QCheckBox("Active Power (kW)")
        self.power_reactive_cb = QCheckBox("Reactive Power (kW)")
        power_layout.addWidget(self.power_full_cb)
        power_layout.addWidget(self.power_active_cb)
        power_layout.addWidget(self.power_reactive_cb)
        
        # Speed Group
        self.speed_group = QGroupBox("💨 Speed")
        speed_layout = QVBoxLayout(self.speed_group)
        self.wind_speed_cb = QCheckBox("Wind Speed (m/s)")
        self.rotor_speed_cb = QCheckBox("Rotor Speed (rpm)")
        self.yaw_speed_cb = QCheckBox("Nacelle Angle (deg/s)")
        self.nacelle_direction_cb = QCheckBox("Wind Direction (deg)")
        speed_layout.addWidget(self.wind_speed_cb)
        speed_layout.addWidget(self.rotor_speed_cb)
        speed_layout.addWidget(self.yaw_speed_cb)
        speed_layout.addWidget(self.nacelle_direction_cb)
        
        # Electrical Group
        self.electrical_group = QGroupBox("🔌 Electrical")
        electrical_layout = QVBoxLayout(self.electrical_group)
        self.voltage_phase_a_cb = QCheckBox("Voltage Phase A (V)")
        self.voltage_phase_b_cb = QCheckBox("Voltage Phase B (V)")
        self.voltage_phase_c_cb = QCheckBox("Voltage Phase C (V)")
        self.frequency_cb = QCheckBox("Frequency (Hz)")
        electrical_layout.addWidget(self.voltage_phase_a_cb)
        electrical_layout.addWidget(self.voltage_phase_b_cb)
        electrical_layout.addWidget(self.voltage_phase_c_cb)
        electrical_layout.addWidget(self.frequency_cb)
        
        layout.addWidget(self.power_group)
        layout.addWidget(self.speed_group)
        layout.addWidget(self.electrical_group)
        
        return CollapsibleSection("Parameters", content, expanded=True)
    
    def _create_actions_section(self):
        """Create actions section"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(6)
        
        self.plot_btn = QPushButton("📊 Plot")
        self.reset_btn = QPushButton("🔄 Reset")
        self.clear_btn = QPushButton("🗑️ Clear")
        self.export_btn = QPushButton("💾 Export Data")
        
        button_style = """
            QPushButton {
                font-size: 11px; padding: 8px;
                background-color: #3498DB; color: white;
                border-radius: 4px; text-align: left;
                padding-left: 12px;
            }
            QPushButton:hover { background-color: #2980B9; }
            QPushButton:pressed { background-color: #21618C; }
        """
        
        self.plot_btn.setStyleSheet(button_style)
        self.reset_btn.setStyleSheet(button_style.replace("#3498DB", "#E74C3C").replace("#2980B9", "#C0392B"))
        self.clear_btn.setStyleSheet(button_style.replace("#3498DB", "#7F8C8D").replace("#2980B9", "#5D6D7E"))
        self.export_btn.setStyleSheet(button_style)
        
        layout.addWidget(self.plot_btn)
        layout.addWidget(self.reset_btn)
        layout.addWidget(self.clear_btn)
        layout.addWidget(self.export_btn)
        
        return CollapsibleSection("Actions", content, expanded=True)
    
    def _create_plot_options_section(self):
        """Create plot options section"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(6)
        
        self.show_grid = QCheckBox("Show Grid")
        self.show_legend = QCheckBox("Show Legend")
        self.show_markers = QCheckBox("Show Markers")
        
        layout.addWidget(self.show_grid)
        layout.addWidget(self.show_legend)
        layout.addWidget(self.show_markers)
        
        return CollapsibleSection("Plot Options", content, expanded=True)
    
    def create_central_widget(self, main_window):
        """Create central widget with plot area"""
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(5, 5, 5, 5)
        central_layout.setSpacing(5)
        
        # Plotly web view (no time window controls here)
        viz_group = QGroupBox("Time Series Visualization")
        viz_group.setStyleSheet("""
            QGroupBox {
                font-size: 13px; font-weight: bold;
                color: #ECF0F1; border: 2px solid #5D6D7E;
                border-radius: 5px; margin-top: 10px;
                padding-top: 12px; background-color: #34495E;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px; padding: 0 8px;
            }
        """)
        viz_layout = QVBoxLayout(viz_group)
        viz_layout.setSpacing(5)
        
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        self.ts_plot = QWebEngineView()
        self.ts_plot.setMinimumHeight(400)
        
        viz_layout.addWidget(self.ts_plot)
        viz_group.setLayout(viz_layout)
        central_layout.addWidget(viz_group)
        
        return central_widget

    
    def _setup_bottom_dock(self, main_window):
        """Setup dockable bottom statistics panel"""
        self.stats_dock = QDockWidget("Statistics", main_window)
        self.stats_dock.setFeatures(
            QDockWidget.DockWidgetMovable | 
            QDockWidget.DockWidgetFloatable
        )
        
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(5, 5, 5, 5)
        stats_layout.setSpacing(5)
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(5)
        self.stats_table.setHorizontalHeaderLabels(["Parameter", "Mean", "Std", "Min", "Max"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.setStyleSheet("""
            QTableWidget {
                background-color: #34495E; color: #ECF0F1;
                gridline-color: #5D6D7E; font-size: 11px;
                border: 1px solid #5D6D7E;
            }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:alternate { background-color: #2C3E50; }
            QHeaderView::section {
                background-color: #2C3E50; color: #ECF0F1;
                font-weight: bold; padding: 6px;
                border: 1px solid #5D6D7E; font-size: 11px;
            }
        """)
        
        stats_layout.addWidget(self.stats_table)
        self.stats_dock.setWidget(stats_widget)
        main_window.addDockWidget(Qt.BottomDockWidgetArea, self.stats_dock)
        self.stats_dock.setVisible(True)