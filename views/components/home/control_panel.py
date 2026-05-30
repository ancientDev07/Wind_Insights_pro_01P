# views/components/home/command_center.py
import os
import logging
from typing import Optional
import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from controllers.central_set_datamanger import CentralizedDataManager
from controllers.database.database_manager import DatabaseManager
from utils.window_manager import WindowManager
from views.components.data_table_components.data_table_module import DataTableModule
from views.farm_analysis.farm_analysis_window import FarmAnalysisWindow
from views.ranking.ranking_window import RankingWindow
# from views.time_series.Time_series_comp import TimeSeriesAnalysisWindow
from views.time_series.time_series_launcher import open_timeseries
from views.visualization_components.power_curve_window import PowerCurveWindow
from views.visualization_components.temperature_comp import TemperatureAnalysisWindow
from views.visualization_components.visualization_window import VisualizationWindow

class ControlPanel(QWidget):
    visualization_requested = pyqtSignal(object)

    def __init__(self, parent: Optional[QWidget] = None, file_handler: Optional[object] = None) -> None:
        super().__init__(parent)
        self.file_handler = file_handler
        self.current_data: Optional[pd.DataFrame] = None
        self.full_data: Optional[pd.DataFrame] = None # Full dataset for analysis
        self.data_table_module = DataTableModule()
        self.window_manager = WindowManager()

        # ADD THESE LINES:
        self.db_manager = DatabaseManager()
        self.project_id = None

        # Initialize analysis and visualization windows
        self.viz_window: Optional[VisualizationWindow] = None
        # self.timeseries_window: Optional[TimeSeriesAnalysisWindow] = None
        self.temperature_analysis: Optional[TemperatureAnalysisWindow] = None
        self.ranking_window: Optional[RankingWindow] = None

        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        self.status_label = QLabel("No file uploaded")

        # Maintain a history log (to be shown in a popup when needed)
        self.history_log = []

        if self.file_handler:
            print("DEBUG: Connecting file_handler signals")
            self.file_handler.signals.turbine_ids_available.connect(self.populate_turbine_dropdown)
            self.file_handler.signals.turbine_data_loaded.connect(
                lambda data: self.handle_data_loaded(data, is_turbine_specific=True)
            )
            self.file_handler.signals.clustering_completed.connect(self.handle_clustering_completed)
            self.file_handler.signals.status_update.connect(self.update_status)
            self.file_handler.signals.error_occurred.connect(self.handle_error)
        self.initUI()

    def initUI(self) -> None:
        """Initializes the UI with categorized options in group boxes."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        icon_size = QSize(48, 48)  # Professional icon size

        # -------------------------
        # Additional Controls Area
        # -------------------------
        # Turbine Selection
        turbine_layout = QHBoxLayout()
        turbine_label = QLabel("Turbine:")
        self.turbine_combo = QComboBox()
        self.turbine_combo.setMinimumWidth(150)
        self.turbine_combo.currentIndexChanged.connect(self.load_turbine_data)
        turbine_layout.addWidget(turbine_label)
        turbine_layout.addWidget(self.turbine_combo)
        turbine_layout.addStretch()
        main_layout.addLayout(turbine_layout)


        # Status Area
        status_layout = QVBoxLayout()
        status_layout.addWidget(self.progress_bar)
        status_layout.addWidget(self.status_label)
        main_layout.addLayout(status_layout)

        # ============
        # Data Group
        # ============
        data_group = QGroupBox("Data Correction")
        data_layout = QGridLayout()
        data_layout.setSpacing(10)

        # Replace Data Button (moved here, styled as QToolButton)
        self.replace_data_button = QToolButton()
        self.replace_data_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.replace_data_button.setIcon(self._load_icon("replace.png"))  # Fixed typo: was self.replace_button
        self.replace_data_button.setText("Replace Data")
        self.replace_data_button.setIconSize(icon_size)
        self.replace_data_button.clicked.connect(self.replace_data)
        self.replace_data_button.setEnabled(False)
        data_layout.addWidget(self.replace_data_button, 0, 0)  

        data_group.setLayout(data_layout)
        main_layout.addWidget(data_group)

        # ============
        # View Group
        # ============
        view_group = QGroupBox("View")
        view_layout = QGridLayout()
        view_layout.setSpacing(10)
        # Map View Button
        self.map_button = QToolButton()
        self.map_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.map_button.setIcon(self._load_icon("map.png"))
        self.map_button.setText("Map")
        self.map_button.setIconSize(icon_size)
        self.map_button.clicked.connect(self.toggle_map_view)
        self.map_button.setEnabled(False)
        view_layout.addWidget(self.map_button, 0, 0)
        
        # Dashboard
        self.dashboard_button = QToolButton()
        self.dashboard_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.dashboard_button.setIcon(self._load_icon("dashboard.png"))
        self.dashboard_button.setText("Dashboard")
        self.dashboard_button.setIconSize(icon_size)
        self.dashboard_button.clicked.connect(self.show_dashboard)
        self.dashboard_button.setEnabled(False)
        view_layout.addWidget(self.dashboard_button, 0, 1)

        view_group.setLayout(view_layout)
        main_layout.addWidget(view_group)

        
        # ============
        # Analytics Group
        # ============
        analytics_group = QGroupBox("Analytics")
        analytics_layout = QGridLayout()
        analytics_layout.setSpacing(10)

        # Time Series Analysis Button
        self.timeseries_button = QToolButton()
        self.timeseries_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.timeseries_button.setIcon(self._load_icon("timeseries.png"))
        self.timeseries_button.setText("TimeSeries")
        self.timeseries_button.setIconSize(icon_size)
        self.timeseries_button.clicked.connect(self.open_timeseries_analysis)
        self.timeseries_button.setEnabled(False)
        analytics_layout.addWidget(self.timeseries_button, 0, 0)

        # temperature analysis Analysis Button
        self.temperature_button = QToolButton()
        self.temperature_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.temperature_button.setIcon(self._load_icon("temperature.png"))
        self.temperature_button.setText("Temprature")
        self.temperature_button.setIconSize(icon_size)
        self.temperature_button.clicked.connect(self.open_temperature_analysis)
        self.temperature_button.setEnabled(False)
        analytics_layout.addWidget(self.temperature_button, 0, 1)

        analytics_group.setLayout(analytics_layout)
        main_layout.addWidget(analytics_group)

        # ===============
        # Visualization Group
        # ===============
        viz_group = QGroupBox("Visualization")
        viz_layout = QGridLayout()
        viz_layout.setSpacing(10)

        # Visualization Button
        self.visualize_button = QToolButton()
        self.visualize_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.visualize_button.setIcon(self._load_icon("visualization.png"))
        self.visualize_button.setText("Viz")
        self.visualize_button.setIconSize(icon_size)
        self.visualize_button.clicked.connect(self.open_visualization)
        self.visualize_button.setEnabled(False)
        viz_layout.addWidget(self.visualize_button, 0, 0)
        
        # power curve window
        self.power_button = QToolButton()
        self.power_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.power_button.setIcon(self._load_icon("power.png"))
        self.power_button.setText("PowerCurve")
        self.power_button.setIconSize(icon_size)
        self.power_button.clicked.connect(self.open_power)
        self.power_button.setEnabled(False)
        viz_layout.addWidget(self.power_button, 0, 1)
        
        viz_group.setLayout(viz_layout)
        main_layout.addWidget(viz_group)
    
        # ============
        # AI View Group
        # ============
        ai_ins_group = QGroupBox("AI Insights")
        ai_ins_layout = QGridLayout()
        ai_ins_layout.setSpacing(10)

        # AI View Button
        self.ai_button = QToolButton()
        self.ai_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.ai_button.setIcon(self._load_icon("analysis.png"))
        self.ai_button.setText("AI Ins")
        self.ai_button.setIconSize(icon_size)
        self.ai_button.clicked.connect(self.open_ai_insights)
        self.ai_button.setEnabled(False)
        ai_ins_layout.addWidget(self.ai_button, 0, 0)
        
        # AI insights Button
        self.ai_in_button = QToolButton()
        self.ai_in_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.ai_in_button.setIcon(self._load_icon("ai_chat.png"))
        self.ai_in_button.setText("AI Chat")
        self.ai_in_button.setIconSize(icon_size)
        self.ai_in_button.clicked.connect(self.open_ai_chat)
        self.ai_in_button.setEnabled(False)
        ai_ins_layout.addWidget(self.ai_in_button, 0, 1)

        ai_ins_group.setLayout(ai_ins_layout)
        main_layout.addWidget(ai_ins_group)

        # ============
        # Reports Group
        # ============
        report_group = QGroupBox("Reports")
        report_layout = QGridLayout()
        report_layout.setSpacing(10)

        # Time Series Analysis Button
        self.report_button = QToolButton()
        self.report_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.report_button.setIcon(self._load_icon("wind_farm.png"))
        self.report_button.setText("Wind_Farm Report")
        self.report_button.setIconSize(icon_size)
        self.report_button.clicked.connect(self.open_farm_analysis)
        self.report_button.setEnabled(False)
        report_layout.addWidget(self.report_button, 0, 0)

        # ranking Data Button (New)
        self.ranking_button = QToolButton()
        self.ranking_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.ranking_button.setIcon(self._load_icon("ranking.png"))
        self.ranking_button.setText("Ranking")
        self.ranking_button.setIconSize(icon_size)
        self.ranking_button.clicked.connect(self.ranking_data)
        self.ranking_button.setEnabled(False)
        report_layout.addWidget(self.ranking_button, 0, 1)

        report_group.setLayout(report_layout)
        main_layout.addWidget(report_group)

        self.setLayout(main_layout)
       # --- Stylesheet ---
        self.setStyleSheet("""
            QWidget {
                background-color: #34495E; color: #ECF0F1; font-size: 12px;}
            QGroupBox {
                border: 1px solid #2C3E50; margin-top: 10px;}
            QGroupBox::title {
                subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px;}
            QToolButton {
                background-color: transparent; border: none;}
            QToolButton:hover {
                background-color: #3E5871; }
            QComboBox { padding: 2px;
            }
            QLabel {
                font-weight: bold;
            }""")

    def _load_icon(self, icon_filename: str) -> QIcon:

        # Adjust path: from this file (located in views/components/home/) move up four levels.
        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
        )
        icon_path = os.path.join(project_root, "resources", "control_icons", icon_filename)
        if not os.path.exists(icon_path):
            logging.warning("Icon file not found: %s", icon_path)
            return QIcon()  # Return an empty icon if file not found
        return QIcon(icon_path)

    def ranking_data(self):
        if self.project_id is None:
            QMessageBox.warning(self, "No Project", "No project loaded.")
            return
        
        # Load full data if not already loaded
        if self.full_data is None or self.full_data.empty:
            try:
                self.full_data = self.db_manager.get_all_turbines_data(self.project_id)
                print(f"DEBUG: Loaded full_data with shape {self.full_data.shape}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load data:\n{str(e)}")
                return
        
        if self.full_data is not None and not self.full_data.empty:
            try:
                self.ranking_window = RankingWindow(self.full_data, parent=self, project_id=self.project_id)
                self.ranking_window.show()
            except Exception as e:
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Error", f"Failed to open ranking window:\n{str(e)}")
        else:
            QMessageBox.warning(self, "No Data", "No data available for ranking.")

    def open_visualization(self):
        """SDI: Open visualization window"""
        try:
            if hasattr(self, 'current_data') and self.current_data is not None:
                turbine_name = self.turbine_combo.currentText()
                params = CentralizedDataManager.get_standard_params(self.turbine_combo, self)
                params['project_id'] = self.project_id
                
                viz_window = self.window_manager.get_or_create(
                    turbine_name,
                    'visualization',
                    VisualizationWindow,
                    self.current_data,
                    **params
                )
                viz_window.show()
            else:
                QMessageBox.warning(self, "Warning", "No data available")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open: {str(e)}")

    def open_power(self):
        """SDI: Open power curve window"""
        try:
            if hasattr(self, 'current_data') and self.current_data is not None:
                turbine_name = self.turbine_combo.currentText()
                params = CentralizedDataManager.get_standard_params(self.turbine_combo, self)
                params['project_id'] = self.project_id
                
                power_window = self.window_manager.get_or_create(
                    turbine_name,
                    'power_curve',
                    PowerCurveWindow,
                    self.current_data,
                    **params
                )
                power_window.show()
            else:
                QMessageBox.warning(self, "Warning", "No data available")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open: {str(e)}")

    def open_temperature_analysis(self):
        """SDI: Open temperature analysis window"""
        try:
            if self.current_data is not None:
                turbine_name = self.turbine_combo.currentText()
                params = CentralizedDataManager.get_standard_params(self.turbine_combo, self)
                params['project_id'] = self.project_id
                
                temp_window = self.window_manager.get_or_create(
                    turbine_name,
                    'temperature',
                    TemperatureAnalysisWindow,
                    self.current_data,
                    **params
                )
                temp_window.show()
            else:
                QMessageBox.warning(self, "Warning", "Please select a turbine first")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open: {str(e)}")


    def open_timeseries_analysis(self):
        """Open Time Series Analysis in the default browser via Dash."""
        if self.current_data is None or self.current_data.empty:
            QMessageBox.warning(self, "Warning", "Please load data first.")
            return
        try:
            turbine_name = self.turbine_combo.currentText() or "Unknown"
            open_timeseries(
                data=self.current_data,
                turbine_name=turbine_name,
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Time Series:\n{str(e)}")
 
    
    def update_status(self, message: str) -> None:
        """Update the status label and manage progress bar visibility."""
        self.status_label.setText(message)
        if "Loading" in message or "Processing" in message:
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.progress_bar.show()
        else:
            self.progress_bar.hide()

    def handle_error(self, error_message: str) -> None:
        """Display an error message in the status area and log history."""
        self.status_label.setText(f"Error: {error_message}")
        self.progress_bar.hide()

    def handle_data_loaded(self, data: pd.DataFrame, is_turbine_specific: bool = False) -> bool:
        """Handle data loaded event"""
        print(f"DEBUG: handle_data_loaded called with data shape: {data.shape if data is not None else 'None'}")
        
        try:
            if data is None or data.empty:
                self._set_buttons_enabled(False)
                return False
                
            self.current_data = data
            if not is_turbine_specific:
                self.full_data = data
                
            rows, cols = data.shape
            message = f"Turbine data loaded: {rows} rows, {cols} columns"
            self.status_label.setText(message)
            self._set_buttons_enabled(True)
            
            # Get main window
            main_window = self.window()
            
            # CRITICAL: Update central_widget which contains the data table
            if hasattr(main_window, 'central_widget'):
                print(f"DEBUG: Calling central_widget.update_data_table with {rows} rows")
                main_window.central_widget.refresh_dashboard()
                main_window.central_widget.update_data_table(data)
                print("DEBUG: central_widget.update_data_table called")
            
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
            
            return True
            
        except Exception as e:
            print(f"DEBUG ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False


    def handle_clustering_completed(self, turbine_files: dict) -> None:
        """Update turbine selection based on clustering results."""
        self.turbine_combo.clear()
        self.turbine_combo.addItems(turbine_files.keys())


    def load_turbine_data(self):
        turbine = self.turbine_combo.currentText()
        print(f"DEBUG: load_turbine_data called for turbine: {turbine}")
        if turbine and self.file_handler:
            self.file_handler.load_turbine_data(turbine)
    
    def populate_turbine_dropdown(self, turbine_ids):
        """Populate dropdown with turbine IDs"""
        self.turbine_combo.clear()
        self.turbine_combo.addItems(turbine_ids)


    # -----------------------
    # New Functionality Stubs
    # -----------------------

    def load_from_database(self, project_id: int):
        """Load project data from database - OPTIMIZED"""
        try:
            self.project_id = project_id
            self.progress_bar.show()
            self.progress_bar.setRange(0, 0)
            self.status_label.setText("Loading from database...")
            QApplication.processEvents()
            
            # Check if table exists
            table_name = f"ProjectData_{project_id}"  # FIX: Correct table name format
            cursor = self.db_manager.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
                [table_name]
            )
            
            if not cursor.fetchone():
                self.progress_bar.hide()
                self.status_label.setText("No data in database")
                QMessageBox.warning(
                    self, 
                    "No Data", 
                    "This project has no data in the database.\n\nPlease upload data first."
                )
                return
            
            # Get turbine list
            turbines = self.db_manager.get_turbines(project_id)
            
            if not turbines:
                self.progress_bar.hide()
                QMessageBox.warning(self, "No Data", "No turbine data found.")
                return
            
            # Populate dropdown
            self.turbine_combo.blockSignals(True)
            self.turbine_combo.clear()
            self.turbine_combo.addItems(turbines)
            self.turbine_combo.blockSignals(False)
            
            # Load first turbine for display
            self.current_data = self.db_manager.get_turbine_data(project_id, turbines[0])
            
            # FIX: Load ALL turbines data for ranking
            self.full_data = self.db_manager.get_all_turbines_data(project_id)
            print(f"DEBUG: full_data columns: {list(self.full_data.columns)}")
            print(f"DEBUG: full_data shape: {self.full_data.shape}")
            
            # Update UI
            if self.data_table_module:
                self.data_table_module.update_data_table(self.current_data)
            
            if hasattr(self.parent(), 'central_widget'):
                self.parent().central_widget.update_data_table(self.current_data)
            
            self.progress_bar.hide()
            self.status_label.setText(f"Loaded {len(turbines)} turbines from database")
            self._set_buttons_enabled(True)
            
        except Exception as e:
            self.progress_bar.hide()
            self.status_label.setText("Failed to load data")
            QMessageBox.critical(self, "Error", f"Failed to load from database: {str(e)}")
    
    def toggle_map_view(self):
        """Toggle between table and map view"""
        main_window = self.window()
        if hasattr(main_window, 'central_widget'):
            main_window.central_widget.toggle_view()
    
    def show_dashboard(self):
        main_window = self.window()
        if hasattr(main_window, 'central_widget'):
            main_window.central_widget.show_dashboard()

    def _set_buttons_enabled(self, enabled: bool) -> None:
        """Helper to enable/disable analysis buttons."""
        self.visualize_button.setEnabled(enabled)
        self.ranking_button.setEnabled(enabled)
        self.timeseries_button.setEnabled(enabled)
        self.temperature_button.setEnabled(enabled)
        self.power_button.setEnabled(enabled)
        self.map_button.setEnabled(enabled)
        self.dashboard_button.setEnabled(enabled)
        self.replace_data_button.setEnabled(enabled)
        self.ai_in_button.setEnabled(enabled)
        self.ai_button.setEnabled(enabled)
        self.report_button.setEnabled(enabled)


    def open_settings(self) -> None:
        """Open application settings/preferences (not implemented)."""
        QMessageBox.information(self, "Not Implemented", "Settings functionality is not implemented yet.")


    def replace_data(self):
        if self.project_id is None:
            QMessageBox.warning(self, "No Project", "No project loaded.")
            return

        reply = QMessageBox.warning(
            self, "Replace Data",
            "This will permanently delete all existing SCADA data for this project and replace it.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel
        )
        if reply != QMessageBox.Yes:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select New Data File", "",
            "Data Files (*.csv *.xlsx *.xls);;All Files (*)"
        )
        if not file_path:
            return

        try:
            self.progress_bar.show()
            self.progress_bar.setRange(0, 0)
            self.status_label.setText("Replacing data...")
            QApplication.processEvents()

            turbines = self.db_manager.replace_project_data(self.project_id, file_path)

            # 1. Close all stale analysis windows (they hold old data references)
            self.window_manager.close_all()

            # 2. Re-sync file_handler so dropdown → load_turbine_data() works with new data
            if self.file_handler:
                self.file_handler.set_project_id(self.project_id)
            else:
                # fallback: manually repopulate dropdown and load data
                self.turbine_combo.blockSignals(True)
                self.turbine_combo.clear()
                self.turbine_combo.addItems(turbines)
                self.turbine_combo.blockSignals(False)
                self.current_data = self.db_manager.get_turbine_data(self.project_id, turbines[0])
                self.full_data = self.db_manager.get_all_turbines_data(self.project_id)

                main_window = self.window()
                if hasattr(main_window, 'central_widget'):
                    main_window.central_widget.update_data_table(self.current_data)
                    main_window.central_widget.refresh_dashboard()

            self.progress_bar.hide()
            self.status_label.setText(f"✅ Data replaced — {len(turbines)} turbine(s) loaded")

        except Exception as e:
            self.progress_bar.hide()
            self.status_label.setText("Failed to replace data")
            QMessageBox.critical(self, "Error", f"Failed to replace data:\n{str(e)}")

    def open_ai_insights(self):
        if self.current_data is None or self.current_data.empty:
            QMessageBox.warning(self, "No Data", "Please load turbine data first.")
            return
        from views.ai_insights.ai_insights_window import AIInsightsWindow
        turbine_name = self.turbine_combo.currentText()
        column_cache = {}
        if self.viz_window and hasattr(self.viz_window, 'column_cache'):
            column_cache = self.viz_window.column_cache
        win = AIInsightsWindow(
            self.current_data,
            turbine_name=turbine_name,
            parent=self,
            project_id=self.project_id
        )
        self.window_manager.get_or_create(turbine_name, 'ai_insights',
                                          AIInsightsWindow,
                                          self.current_data,
                                          turbine_name=turbine_name,
                                          project_id=self.project_id)
        win.show()

    def open_ai_chat(self):
        from views.ai_insights.chat_panel import ChatPanel        
        turbine_name = self.turbine_combo.currentText() if self.current_data is not None else ""
        win = ChatPanel(data=self.current_data, turbine_name=turbine_name,
                        project_id=self.project_id, parent=self)
        win.show()

    def open_farm_analysis(self):
        if self.project_id is None:
            QMessageBox.warning(self, "No Project", "No project loaded.")
            return
        try:
            farm_window = FarmAnalysisWindow(project_id=self.project_id, parent=self)
            self.window_manager.get_or_create(
                f"farm_{self.project_id}",
                'farm_analysis',
                FarmAnalysisWindow,
                project_id=self.project_id
            )
            farm_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Farm Analysis:\n{str(e)}")