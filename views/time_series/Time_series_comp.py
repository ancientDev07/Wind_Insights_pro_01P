# import numpy as np
# from datetime import timedelta
# from PyQt5.QtWidgets import *
# from PyQt5.QtCore import *
# import pandas as pd
# import pyqtgraph as pg
# from matplotlib.backends.backend_pdf import PdfPages
# import matplotlib.pyplot as plt
# from models import scada_utils as su
# from utils import datetime_utils as dtu
# from views.time_series.time_series_logic import TSAnalysisEngine
# from views.time_series.time_series_ui import TimeSeriesUI
# from utils import column_cache_utility as ccu
# from PyQt5.QtWebEngineWidgets import QWebEngineView
# from views.time_series.plotly_engine import PlotlyTimeSeriesEngine

# # REPLACE existing imports with:
# import numpy as np
# from datetime import timedelta
# from PyQt5.QtWidgets import *
# from PyQt5.QtCore import *
# from PyQt5.QtGui import *
# import pandas as pd
# from matplotlib.backends.backend_pdf import PdfPages
# import matplotlib.pyplot as plt
# from models import scada_utils as su
# from utils import datetime_utils as dtu
# from views.time_series import shared_store
# from views.time_series.time_series_logic import TSAnalysisEngine
# from views.time_series.time_series_ui import TimeSeriesUI
# from utils import column_cache_utility as ccu
# from PyQt5.QtWebEngineWidgets import QWebEngineView

# from views.time_series import dash_app


# class TimeSeriesAnalysisWindow(QMainWindow):
#     # def __init__(self, data=None, turbine_name=None, parent=None, project_id = None):
#     #     super().__init__(parent)
#     #     self.data = data if data is not None else pd.DataFrame()
#     #     self.turbine_name = turbine_name
#     #     # self.filtered_data = None
#     #     self.filtered_data = pd.DataFrame()
#     #     self.column_cache = {}
#     #     self.project_id = project_id
#     #     self.current_window_hours = 24
#     #     self.window_start_index = 0
#     #     self.total_data_points = 0
#     #     self.selected_params_cache = []
#     #     self.full_data_cache = None    
        
#     #     # Set window title
#     #     self.setWindowTitle(f"Time Series Analysis: {turbine_name}" if turbine_name else "Time Series Analysis - Wind Data Insight Pro")
        
#     #     # Setup UI and engine
#     #     self.ui = TimeSeriesUI()
#     #     self.ui.setup_ui(self)
#     #     self.ui.ts_plot._legends = []  # Initialize legend tracking
        
#     #     self.engine = TSAnalysisEngine()
#     #     self.plotly_engine = PlotlyTimeSeriesEngine()

#     #             # SDI: Independent window
#     #     self.setWindowFlags(Qt.Window)
#     #     self.setAttribute(Qt.WA_DeleteOnClose)
#     #     # Connect signals
#     #     self._connect_signals()
        
#     #     # Initialize data display
#     #     self._initialize_data_display()

#     def __init__(self, data=None, turbine_name=None, parent=None, project_id=None):
#         super().__init__(parent)
#         self.data = data if data is not None else pd.DataFrame()
#         self.turbine_name = turbine_name
#         self.filtered_data = pd.DataFrame()
#         self.column_cache = {}
#         self.project_id = project_id
#         self.current_window_hours = 24
#         self.window_start_index = 0
#         self.total_data_points = 0
#         self.selected_params_cache = []
#         self.full_data_cache = None

#         # Unique key for this window instance
#         self._turbine_key = f"{turbine_name}_{id(self)}"

#         self.setWindowTitle(
#             f"Time Series Analysis: {turbine_name}" if turbine_name
#             else "Time Series Analysis - Wind Data Insight Pro"
#         )

#         self.ui = TimeSeriesUI()
#         self.ui.setup_ui(self)
#         self.ui.ts_plot._legends = []

#         self.engine = TSAnalysisEngine()

#         # Start single shared Dash server (no-op if already running)
#         dash_app.start_server()

#         self.setWindowFlags(Qt.Window)
#         self.setAttribute(Qt.WA_DeleteOnClose)
#         self._connect_signals()
#         self._initialize_data_display()

#     # Update the set_data method:
#     def set_data(self, data, turbine_name=None):
#         """Set new data and refresh UI"""
#         self.data = data if data is not None else pd.DataFrame()
#         self.turbine_name = turbine_name
#         self.filtered_data = None

#         # Update window title
#         if turbine_name:
#             self.setWindowTitle(f"Time Series Analysis: {turbine_name}")
#         else:
#             self.setWindowTitle("Time Series Analysis - Wind Data Insight Pro")

#         # Initialize data display using helper method
#         self._initialize_data_display()
    
#     def _initialize_data_display(self):
#         """Helper method to initialize data display after setting data"""
#         if not self.data.empty:
#             self._setup_data_display()
#         else:
#             self._clear_data_display()

#     # def _setup_data_display(self):
#     #     """Setup display with populated data"""
#     #     self._populate_column_cache()
#     #     self.populate_data_tree()
#     #     min_date, max_date, _, _, _ = self.get_datetime_info_from_dataset()
#     #     self.ui.start_date_only.setText(min_date)
#     #     self.ui.end_date_only.setText(max_date)
#     #     self.statusBar().showMessage(f"Data loaded: {len(self.data)} rows, {len(self.data.columns)} columns")

#     def _setup_data_display(self):
#         """Setup display with populated data"""
#         self._populate_column_cache()
#         self.populate_data_tree()
#         datetime_info = self.get_datetime_info_from_dataset()
#         self.ui.start_date_only.setText(datetime_info['min_date'])
#         self.ui.end_date_only.setText(datetime_info['max_date'])
#         self.statusBar().showMessage(f"Data loaded: {len(self.data)} rows, {len(self.data.columns)} columns")
#         print(f"DEBUG: Set dates - start: {datetime_info['min_date']}, end: {datetime_info['max_date']}")

    
#     def _clear_data_display(self):
#         """Clear display when no data"""
#         self.filtered_data = pd.DataFrame()
#         self.statusBar().showMessage("No data available")
#         self.ui.ts_plot.setHtml("<html><body style='background:#2C3E50'></body></html>")
#         self.ui.stats_table.clearContents()
#         self.ui.stats_table.setRowCount(0)

#     def _apply_sample_size_filter(self, df):
#         """Apply sample size filtering for consistent 600s intervals, keeping all valid data"""
#         timestamp_col = self.column_cache.get("timestamp")
#         if not timestamp_col or timestamp_col not in df.columns:
#             self.statusBar().showMessage("No timestamp column found for 600s interval filter")
#             return df
        
#         fd = df.sort_values(by=timestamp_col)
#         fd['dt'] = fd[timestamp_col].diff().dt.total_seconds().fillna(0)
        
#         # Keep only rows where dt == 600 (or first row where dt == 0)
#         fd = fd[(fd['dt'] == 600) | (fd['dt'] == 0)]
        
#         if fd.empty:
#             self.statusBar().showMessage("No data with consistent 600s intervals found")
        
#         return fd.drop(columns=['dt'])
    
#     def _setup_viewport_rendering(self):
#         """Setup window-based rendering with time window controls"""
#         self.full_data_cache = None
#         self.current_window_hours = 24  # Default 24-hour window
#         self.window_start_index = 0
#         self.total_data_points = 0
    
#     # def apply_filters(self):
#     #     """Apply date, time, and 600s cycle filters"""
#     #     if self.data.empty:
#     #         self.filtered_data = pd.DataFrame()
#     #         self.statusBar().showMessage("No data available")
#     #         return
        
#     #     timestamp_col = ccu.column_cache.get_column('timestamp', self.data)
#     #     if not timestamp_col or timestamp_col not in self.data.columns:
#     #         self.filtered_data = self.data
#     #         self.statusBar().showMessage("No timestamp column found")
#     #         return
        
#     #     df = self.data.copy()
#     #     df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
        
#     #     if df[timestamp_col].isna().all():
#     #         self.filtered_data = df
#     #         self.statusBar().showMessage("Invalid timestamp data")
#     #         return
        
#     #     # Apply filters sequentially
#     #     df = self._apply_600s_filter(df, timestamp_col)
#     #     if df is None:
#     #         return
        
#     #     df = self._apply_date_filter(df, timestamp_col)
#     #     if df is None:
#     #         return
        
#     #     df = self._apply_time_filter(df, timestamp_col)
#     #     if df is None:
#     #         return
        
#     #     self.filtered_data = df
#     #     if df.empty:
#     #         self.statusBar().showMessage("No data remains after filtering")

#     def apply_filters(self):
#         """Apply date, time, and 600s cycle filters"""
#         if self.data.empty:
#             self.filtered_data = pd.DataFrame()
#             self.statusBar().showMessage("No data available")
#             print("DEBUG: Data is empty")
#             return
        
#         print(f"DEBUG: Initial data rows: {len(self.data)}")
        
#         timestamp_col = ccu.column_cache.get_column('timestamp', self.data)
#         if not timestamp_col or timestamp_col not in self.data.columns:
#             self.filtered_data = self.data
#             self.statusBar().showMessage("No timestamp column found")
#             print(f"DEBUG: Timestamp col not found. Available cols: {self.data.columns.tolist()}")
#             return
        
#         df = self.data.copy()
#         df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
        
#         if df[timestamp_col].isna().all():
#             self.filtered_data = df
#             self.statusBar().showMessage("Invalid timestamp data")
#             print("DEBUG: All timestamps are NaT")
#             return
        
#         print(f"DEBUG: After timestamp parse: {len(df)} rows")
        
#         # Apply filters sequentially
#         df = self._apply_600s_filter(df, timestamp_col)
#         if df is None:
#             print("DEBUG: 600s filter returned None")
#             return
#         print(f"DEBUG: After 600s filter: {len(df)} rows")
        
#         df = self._apply_date_filter(df, timestamp_col)
#         if df is None:
#             print("DEBUG: Date filter returned None")
#             return
#         print(f"DEBUG: After date filter: {len(df)} rows")
        
#         df = self._apply_time_filter(df, timestamp_col)
#         if df is None:
#             print("DEBUG: Time filter returned None")
#             return
#         print(f"DEBUG: After time filter: {len(df)} rows")
        
#         self.filtered_data = df
#         if df.empty:
#             self.statusBar().showMessage("No data remains after filtering")
#             print("DEBUG: Final filtered data is empty")
#         else:
#             self.statusBar().showMessage(f"Filtered: {len(df)} rows")
#             print(f"DEBUG: Final filtered data: {len(df)} rows")

    
#     def _apply_600s_filter(self, df, timestamp_col):
#         """Apply 600s cycle filter"""
#         if not self.ui.enable_600s_filter.isChecked():
#             return df
        
#         if 'Count' not in df.columns:
#             self.statusBar().showMessage("Count column not found")
#             self.filtered_data = pd.DataFrame()
#             return None
        
#         df = df[df['Count'] == 600]
#         if df.empty:
#             self.statusBar().showMessage("No data with Count == 600")
#             self.filtered_data = pd.DataFrame()
#             return None
        
#         return df

#     # def _apply_date_filter(self, df, timestamp_col):
#     #     """Apply date range filter"""
#     #     if not self.ui.enable_date_filter.isChecked():
#     #         return df
        
#     #     start_date_str = self.ui.start_date_only.text().strip()
#     #     end_date_str = self.ui.end_date_only.text().strip()
        
#     #     if start_date_str:
#     #         start_dt = pd.to_datetime(start_date_str, format='%d-%m-%Y', errors='coerce')
#     #         if pd.isna(start_dt):
#     #             self.statusBar().showMessage("Invalid start date format (DD-MM-YYYY)")
#     #             return None
#     #         df = df[df[timestamp_col] >= start_dt]
        
#     #     if end_date_str:
#     #         end_dt = pd.to_datetime(end_date_str, format='%d-%m-%Y', errors='coerce') + pd.Timedelta(days=1)
#     #         if pd.isna(end_dt):
#     #             self.statusBar().showMessage("Invalid end date format (DD-MM-YYYY)")
#     #             return None
#     #         df = df[df[timestamp_col] <= end_dt]
        
#     #     return df

#     def _apply_date_filter(self, df, timestamp_col):
#         """Apply date range filter"""
#         if not self.ui.enable_date_filter.isChecked():
#             return df
        
#         start_date_str = self.ui.start_date_only.text().strip()
#         end_date_str = self.ui.end_date_only.text().strip()
        
#         print(f"DEBUG: Date filter - start: '{start_date_str}', end: '{end_date_str}'")
        
#         if not start_date_str and not end_date_str:
#             print("DEBUG: No date range specified, skipping date filter")
#             return df
        
#         if start_date_str:
#             try:
#                 start_dt = pd.to_datetime(start_date_str, format='%d-%m-%Y', errors='coerce')
#                 if pd.isna(start_dt):
#                     self.statusBar().showMessage("Invalid start date format (DD-MM-YYYY)")
#                     print(f"DEBUG: Invalid start date: {start_date_str}")
#                     return df
#                 df = df[df[timestamp_col] >= start_dt]
#                 print(f"DEBUG: After start date filter: {len(df)} rows")
#             except Exception as e:
#                 print(f"DEBUG: Start date filter error: {e}")
#                 return df
        
#         if end_date_str:
#             try:
#                 end_dt = pd.to_datetime(end_date_str, format='%d-%m-%Y', errors='coerce') + pd.Timedelta(days=1)
#                 if pd.isna(end_dt):
#                     self.statusBar().showMessage("Invalid end date format (DD-MM-YYYY)")
#                     print(f"DEBUG: Invalid end date: {end_date_str}")
#                     return df
#                 df = df[df[timestamp_col] <= end_dt]
#                 print(f"DEBUG: After end date filter: {len(df)} rows")
#             except Exception as e:
#                 print(f"DEBUG: End date filter error: {e}")
#                 return df
        
#         return df

    
#     def _apply_time_filter(self, df, timestamp_col):
#         """Apply time range filter"""
#         if not self.ui.enable_time_filter.isChecked():
#             return df
        
#         start_time_str = self.ui.start_time_only.text().strip()
#         end_time_str = self.ui.end_time_only.text().strip()
        
#         if start_time_str:
#             start_time_obj = pd.to_datetime(start_time_str, format='%H:%M', errors='coerce')
#             if pd.isna(start_time_obj):
#                 self.statusBar().showMessage("Invalid start time format (HH:MM)")
#                 return None
#             df = df[df[timestamp_col].dt.time >= start_time_obj.time()]
        
#         if end_time_str:
#             end_time_obj = pd.to_datetime(end_time_str, format='%H:%M', errors='coerce')
#             if pd.isna(end_time_obj):
#                 self.statusBar().showMessage("Invalid end time format (HH:MM)")
#                 return None
#             df = df[df[timestamp_col].dt.time <= end_time_obj.time()]
        
#         return df

        
#     def _populate_column_cache(self):
#         """Populate column cache using scada_utils with simplified mapping"""
#         if self.data.empty:
#             return
            
#         # Simplified parameter mapping
#         param_mapping = {
#             'Power': 'power',
#             'Wind Speed': 'wind_speed',
#             'Rotor Speed': 'rotor_speed',
#             'Yaw Speed': 'yaw_speed',
#             'Nacelle Direction': 'nacelle_direction',
#             'Timestamp': 'timestamp',
#             'Voltage Phase A': 'voltage_phase_a',
#             'Voltage Phase B': 'voltage_phase_b',
#             'Voltage Phase C': 'voltage_phase_c',
#             'Frequency': 'frequency'
#         }
        
#         # Use dictionary comprehension for cleaner code
#         self.column_cache = {
#             display_name: (lambda matched: matched[0] if matched else None)(
#                 su.find_matching_columns(self.data, param_key)
#             )
#             for display_name, param_key in param_mapping.items()
#         }
    
#     def populate_data_tree(self):
#         """Populate power and speed groups with checkboxes"""
#         if self.data.empty:
#             return
        
#         power_col = self.column_cache.get('Power')
#         if power_col:
#             self.ui.power_full_cb.setProperty('column', power_col)
#             self.ui.power_full_cb.setProperty('param_key', 'power')
#             self.ui.power_full_cb.setProperty('power_type', 'full')
#             self.ui.power_active_cb.setProperty('column', power_col)
#             self.ui.power_active_cb.setProperty('param_key', 'power')
#             self.ui.power_active_cb.setProperty('power_type', 'active')
#             self.ui.power_reactive_cb.setProperty('column', power_col)
#             self.ui.power_reactive_cb.setProperty('param_key', 'power')
#             self.ui.power_reactive_cb.setProperty('power_type', 'reactive')
        
#         wind_speed_col = self.column_cache.get('Wind Speed')
#         if wind_speed_col:
#             self.ui.wind_speed_cb.setProperty('column', wind_speed_col)
#             self.ui.wind_speed_cb.setProperty('param_key', 'wind_speed')
        
#         rotor_speed_col = self.column_cache.get('Rotor Speed')
#         if rotor_speed_col:
#             self.ui.rotor_speed_cb.setProperty('column', rotor_speed_col)
#             self.ui.rotor_speed_cb.setProperty('param_key', 'rotor_speed')
        
#         yaw_speed_col = self.column_cache.get('Yaw Speed')
#         if yaw_speed_col:
#             self.ui.yaw_speed_cb.setProperty('column', yaw_speed_col)
#             self.ui.yaw_speed_cb.setProperty('param_key', 'yaw_speed')
        
#         nacelle_direction_col = self.column_cache.get('Nacelle Direction')
#         if nacelle_direction_col:
#             self.ui.nacelle_direction_cb.setProperty('column', nacelle_direction_col)
#             self.ui.nacelle_direction_cb.setProperty('param_key', 'nacelle_direction')

#         voltage_phase_a_col = self.column_cache.get('Voltage Phase A')
#         if voltage_phase_a_col:
#             self.ui.voltage_phase_a_cb.setProperty('column', voltage_phase_a_col)
#             self.ui.voltage_phase_a_cb.setProperty('param_key', 'voltage_phase_a')

#         voltage_phase_b_col = self.column_cache.get('Voltage Phase B')
#         if voltage_phase_b_col:
#             self.ui.voltage_phase_b_cb.setProperty('column', voltage_phase_b_col)
#             self.ui.voltage_phase_b_cb.setProperty('param_key', 'voltage_phase_b')

#         voltage_phase_c_col = self.column_cache.get('Voltage Phase C')
#         if voltage_phase_c_col:
#             self.ui.voltage_phase_c_cb.setProperty('column', voltage_phase_c_col)
#             self.ui.voltage_phase_c_cb.setProperty('param_key', 'voltage_phase_c')
        
#         frequency_col = self.column_cache.get('Frequency')
#         if frequency_col:
#             self.ui.frequency_cb.setProperty('column', frequency_col)
#             self.ui.frequency_cb.setProperty('param_key', 'frequency')
    
#     def analyze_data(self):
#         """Analyze selected data"""
#         if self.data.empty:
#             QMessageBox.warning(self, "No Data", "No data available for analysis")
#             return
            
#         selected_params = self.get_selected_parameters()
#         if not selected_params:
#             QMessageBox.warning(self, "No Selection", "Please select at least one parameter")
#             return
            
#         self.apply_filters()
#         if self.filtered_data.empty:
#             QMessageBox.warning(self, "No Data", "No data available after filtering")
#             return
            
#         self.engine.start_analysis(self.filtered_data)
#         self.engine.analysis_finished.connect(self.on_analysis_finished)
    
#     def get_selected_parameters(self):
#         """Get selected parameters using a mapping approach"""
#         parameter_mapping = [
#             (self.ui.power_full_cb, 'power', 'full', 'Power (kW)'),
#             (self.ui.power_active_cb, 'power', 'active', 'Active Power (kW)'),
#             (self.ui.power_reactive_cb, 'power', 'reactive', 'Reactive Power (kW)'),
#             (self.ui.wind_speed_cb, 'wind_speed', None, 'Wind Speed (m/s)'),
#             (self.ui.rotor_speed_cb, 'rotor_speed', None, 'Rotor Speed (rpm)'),
#             (self.ui.yaw_speed_cb, 'yaw_speed', None, 'Nacelle Angle (deg/s)'),
#             (self.ui.nacelle_direction_cb, 'nacelle_direction', None, 'Wind Direction (deg)'),
#             (self.ui.voltage_phase_a_cb, 'voltage_phase_a', None, 'Voltage Phase A (V)'),
#             (self.ui.voltage_phase_b_cb, 'voltage_phase_b', None, 'Voltage Phase B (V)'),
#             (self.ui.voltage_phase_c_cb, 'voltage_phase_c', None, 'Voltage Phase C (V)'),
#             (self.ui.frequency_cb, 'frequency', None, 'Frequency (Hz)')
#         ]
        
#         selected = []
#         for checkbox, param_key, power_type, display in parameter_mapping:
#             if checkbox.isChecked():
#                 col = checkbox.property('column')
#                 if col:
#                     selected.append({
#                         'column': col,
#                         'param_key': param_key,
#                         'power_type': power_type,
#                         'display': display
#                     })
        
#         return selected
    
#     def _apply_window_aggregation(self, data, timestamp_col, window_size, selected_params):
#         """Apply window-based aggregation preserving min/max/mean for accuracy"""
#         agg_data = data.copy()
#         agg_data[timestamp_col] = pd.to_datetime(agg_data[timestamp_col], errors='coerce')
#         agg_data = agg_data.sort_values(timestamp_col)
        
#         # Group by window and aggregate
#         agg_dict = {timestamp_col: 'first'}
#         for param in selected_params:
#             col = param['column']
#             if col in agg_data.columns:
#                 # Keep min, max, and mean to preserve trends and extremes
#                 agg_dict[col] = lambda x: x.iloc[len(x)//2] if len(x) > 0 else np.nan
        
#         # Create window groups
#         agg_data['_window'] = (agg_data.index // window_size)
#         result = agg_data.groupby('_window').agg(agg_dict).reset_index(drop=True)
        
#         return result
    
#     # def plot_time_series(self, selected_params):
#     #     """Initialize full dataset and render first window"""
#     #     if self.filtered_data is None or self.filtered_data.empty or not selected_params:
#     #         self.statusBar().showMessage("No data or parameters selected for plotting")
#     #         return
        
#     #     timestamp_col = ccu.column_cache.get_column('timestamp', self.filtered_data)
#     #     if not timestamp_col or timestamp_col not in self.filtered_data.columns:
#     #         self.statusBar().showMessage("No timestamp column found")
#     #         return
        
#     #     timestamps = pd.to_datetime(self.filtered_data[timestamp_col], errors='coerce')
#     #     if timestamps.isna().all():
#     #         self.statusBar().showMessage("Invalid timestamp data")
#     #         return
        
#     #     # Cache full dataset
#     #     self.full_data_cache = self.filtered_data.copy()
#     #     self.selected_params_cache = selected_params
#     #     self.total_data_points = len(self.full_data_cache)
        
#     #     # Enable slider
#     #     self.ui.window_slider.setEnabled(True)
#     #     self.ui.window_slider.setValue(0)
        
#     #     # Render first window
#     #     self._render_current_window()

#     # def _render_current_window(self):
#     #     """Render data for current time window at full resolution"""
#     #     if self.full_data_cache is None or self.full_data_cache.empty:
#     #         return
        
#     #     if not hasattr(self, 'selected_params_cache') or not self.selected_params_cache:
#     #         return
        
#     #     timestamp_col = ccu.column_cache.get_column('timestamp', self.full_data_cache)
#     #     timestamps = pd.to_datetime(self.full_data_cache[timestamp_col], errors='coerce')
        
#     #     # Calculate window data
#     #     if self.current_window_hours is None:
#     #         # Full dataset
#     #         window_data = self.full_data_cache
#     #         window_timestamps = timestamps
#     #     else:
#     #         # Time-based window
#     #         window_start_time = timestamps.iloc[self.window_start_index] if self.window_start_index < len(timestamps) else timestamps.min()
#     #         window_end_time = window_start_time + timedelta(hours=self.current_window_hours)
            
#     #         mask = (timestamps >= window_start_time) & (timestamps <= window_end_time)
#     #         window_data = self.full_data_cache[mask]
#     #         window_timestamps = timestamps[mask]
        
#     #     if window_data.empty:
#     #         self.statusBar().showMessage("No data in current window")
#     #         return
        
#     #     # Clear and redraw
#     #     self.ui.ts_plot.clear()
#     #     if hasattr(self.ui.ts_plot, 'plotItem') and self.ui.ts_plot.plotItem.legend is not None:
#     #         self.ui.ts_plot.plotItem.legend.scene().removeItem(self.ui.ts_plot.plotItem.legend)
#     #         self.ui.ts_plot.plotItem.legend = None
        
#     #     try:
#     #         pg.setConfigOptions(useOpenGL=True)
#     #     except:
#     #         pass
        
#     #     # Plot all parameters in window
#     #     for param in self.selected_params_cache:
#     #         col = param['column']
#     #         param_key = param['param_key']
#     #         power_type = param['power_type']
            
#     #         if col not in window_data.columns:
#     #             continue
            
#     #         if param_key == 'power':
#     #             self.engine.plot_power(window_data, col, power_type, self.ui.ts_plot, self.ui.show_markers.isChecked())
#     #         elif param_key == 'wind_speed':
#     #             self.engine.plot_wind_speed(window_data, col, self.ui.ts_plot, self.ui.show_markers.isChecked())
#     #         elif param_key == 'rotor_speed':
#     #             self.engine.plot_rotor_speed(window_data, col, self.ui.ts_plot, self.ui.show_markers.isChecked())
#     #         elif param_key == 'yaw_speed':
#     #             self.engine.plot_yaw_speed(window_data, col, self.ui.ts_plot, self.ui.show_markers.isChecked())
#     #         elif param_key == 'nacelle_direction':
#     #             self.engine.plot_nacelle_direction(window_data, col, self.ui.ts_plot, self.ui.show_markers.isChecked())
#     #         elif param_key == 'voltage_phase_a':
#     #             self.engine.plot_voltage_phase_a(window_data, col, self.ui.ts_plot, self.ui.show_markers.isChecked())
#     #         elif param_key == 'voltage_phase_b':
#     #             self.engine.plot_voltage_phase_b(window_data, col, self.ui.ts_plot, self.ui.show_markers.isChecked())
#     #         elif param_key == 'voltage_phase_c':
#     #             self.engine.plot_voltage_phase_c(window_data, col, self.ui.ts_plot, self.ui.show_markers.isChecked())
#     #         elif param_key == 'frequency':
#     #             self.engine.plot_frequency(window_data, col, self.ui.ts_plot, self.ui.show_markers.isChecked())
        
#     #     # Format axes
#     #     if len(window_timestamps) > 0:
#     #         axis = self.ui.ts_plot.getAxis('bottom')
#     #         start_date = window_timestamps.min().date()
#     #         end_date = window_timestamps.max().date()
#     #         if start_date == end_date:
#     #             tick_times = window_timestamps[::max(1, len(window_timestamps)//12)]
#     #             axis.setTicks([[(t.timestamp(), t.strftime('%H:%M')) for t in tick_times]])
#     #             axis.setLabel("Time (HH:MM)", color='white')
#     #         else:
#     #             tick_times = window_timestamps[::max(1, len(window_timestamps)//10)]
#     #             axis.setTicks([[(t.timestamp(), t.strftime('%m-%d\n%H:%M')) for t in tick_times]])
#     #             axis.setLabel("Date/Time", color='white')
        
#     #     self.ui.ts_plot.getAxis('left').setLabel("Value", color='white')
#     #     self.ui.ts_plot.setBackground('k')
#     #     self.ui.ts_plot.getAxis('bottom').setPen(pg.mkPen('w', width=1))
#     #     self.ui.ts_plot.getAxis('left').setPen(pg.mkPen('w', width=1))
        
#     #     if self.ui.show_legend.isChecked():
#     #         self.ui.ts_plot.addLegend(offset=(10, 10))
        
#     #     self.ui.ts_plot.showGrid(x=self.ui.show_grid.isChecked(), y=self.ui.show_grid.isChecked(), alpha=0.3)
        
#     #     # Update position label
#     #     if len(window_timestamps) > 0:
#     #         start_str = window_timestamps.min().strftime('%Y-%m-%d %H:%M')
#     #         end_str = window_timestamps.max().strftime('%Y-%m-%d %H:%M')
#     #         self.ui.window_position_label.setText(f"Start: {start_str} | End: {end_str}")
        
#     #     self.statusBar().showMessage(
#     #         f"Window: {len(window_data)} points | Full dataset: {self.total_data_points} points"
#     #     )

#     def plot_time_series(self, selected_params):
#         """Initialize full dataset and render first window"""
#         if self.filtered_data is None or self.filtered_data.empty or not selected_params:
#             self.statusBar().showMessage("No data or parameters selected")
#             return
        
#         timestamp_col = ccu.column_cache.get_column('timestamp', self.filtered_data)
#         if not timestamp_col or timestamp_col not in self.filtered_data.columns:
#             self.statusBar().showMessage("No timestamp column found")
#             return
        
#         timestamps = pd.to_datetime(self.filtered_data[timestamp_col], errors='coerce')
#         if timestamps.isna().all():
#             self.statusBar().showMessage("Invalid timestamp data")
#             return
        
#         # Cache full dataset
#         self.full_data_cache = self.filtered_data.copy()
#         self.selected_params_cache = selected_params
#         self.total_data_points = len(self.full_data_cache)
        
#         # Enable slider
#         self.ui.window_slider.setEnabled(True)
#         self.ui.window_slider.setMinimum(0)
#         self.ui.window_slider.setMaximum(1000)   # finer than 100 steps
#         self.ui.window_slider.setSingleStep(1)
#         self.ui.window_slider.setValue(0)
        
#         # Render first window
#         self._render_current_window()

    
#     # def _render_current_window(self):
#     #     """Render data for current time window using Plotly + TSAnalysisEngine"""
#     #     if self.full_data_cache is None or self.full_data_cache.empty:
#     #         return
        
#     #     if not self.selected_params_cache:
#     #         return
        
#     #     timestamp_col = ccu.column_cache.get_column('timestamp', self.full_data_cache)
#     #     if not timestamp_col:
#     #         return
        
#     #     timestamps = pd.to_datetime(self.full_data_cache[timestamp_col], errors='coerce')
        
#     #     # Calculate window data
#     #     if self.current_window_hours is None:
#     #         window_data = self.full_data_cache.copy()
#     #         window_timestamps = timestamps.copy()
#     #     else:
#     #         if self.window_start_index >= len(timestamps):
#     #             self.window_start_index = 0
            
#     #         window_start_time = timestamps.iloc[self.window_start_index]
#     #         window_end_time = window_start_time + pd.Timedelta(hours=self.current_window_hours)
            
#     #         mask = (timestamps >= window_start_time) & (timestamps <= window_end_time)
#     #         window_data = self.full_data_cache[mask].copy()
#     #         window_timestamps = timestamps[mask].copy()
        
#     #     if window_data.empty:
#     #         self.statusBar().showMessage("No data in current window")
#     #         return
        
#     #     # Generate Plotly HTML using TSAnalysisEngine
#     #     html = self.plotly_engine.create_html(
#     #         window_data,
#     #         timestamp_col,
#     #         self.selected_params_cache,
#     #         self.engine,  # Pass engine for data extraction
#     #         show_grid=self.ui.show_grid.isChecked(),
#     #         show_legend=self.ui.show_legend.isChecked()
#     #     )
        
#     #     # Load into QWebEngineView
#     #     self.ui.ts_plot.setHtml(html, QUrl("qrc:/"))
        
#     #     # Update position label
#     #     if len(window_timestamps) > 0:
#     #         start_str = window_timestamps.min().strftime('%Y-%m-%d %H:%M')
#     #         end_str = window_timestamps.max().strftime('%Y-%m-%d %H:%M')
#     #         self.ui.window_position_label.setText(f"Start: {start_str} | End: {end_str}")
        
#     #     self.statusBar().showMessage(
#     #         f"Window: {len(window_data)} points (full resolution) | Total: {self.total_data_points} points"
#     #     )

    
#     def _render_current_window(self):
#         """Push window data to shared store and point WebView at Dash"""
#         if self.full_data_cache is None or self.full_data_cache.empty:
#             return
#         if not self.selected_params_cache:
#             return

#         timestamp_col = ccu.column_cache.get_column("timestamp", self.full_data_cache)
#         if not timestamp_col:
#             return

#         timestamps = pd.to_datetime(self.full_data_cache[timestamp_col], errors="coerce")

#         # Calculate window slice
#         if self.current_window_hours is None:
#             window_data = self.full_data_cache.copy()
#             window_timestamps = timestamps.copy()
#         else:
#             if self.window_start_index >= len(timestamps):
#                 self.window_start_index = 0
#             window_start_time = timestamps.iloc[self.window_start_index]
#             window_end_time   = window_start_time + pd.Timedelta(hours=self.current_window_hours)
#             mask = (timestamps >= window_start_time) & (timestamps <= window_end_time)
#             window_data       = self.full_data_cache[mask].copy()
#             window_timestamps = timestamps[mask].copy()

#         if window_data.empty:
#             self.statusBar().showMessage("No data in current window")
#             return

#         # Push to shared store
#         shared_store.stores[self._turbine_key] = {
#             "data":          window_data.reset_index(drop=True),
#             "params":        self.selected_params_cache,
#             "timestamp_col": timestamp_col,
#         }

#         # Load Dash page with this window's turbine key
#         url = QUrl(f"http://127.0.0.1:8050/?turbine={self._turbine_key}")
#         self.ui.ts_plot.setUrl(url)

#         # Update position label
#         if len(window_timestamps) > 0:
#             start_str = window_timestamps.min().strftime("%Y-%m-%d %H:%M")
#             end_str   = window_timestamps.max().strftime("%Y-%m-%d %H:%M")
#             self.ui.window_position_label.setText(f"Start: {start_str} | End: {end_str}")

#         self.statusBar().showMessage(
#             f"Window: {len(window_data)} points | Total: {self.total_data_points} points"
#         )
    
#     def on_analysis_finished(self, data, statistics):
#         """Handle analysis results and update statistics table"""
#         self.filtered_data = data
#         self.plot_time_series(self.get_selected_parameters())
        
#         # Update statistics table
#         self.ui.stats_table.clearContents()
#         self.ui.stats_table.setRowCount(0)
        
#         if statistics:
#             # Count unique parameters (those ending with '_mean')
#             unique_params = [key.replace('_mean', '') for key in statistics.keys() if key.endswith('_mean')]
#             self.ui.stats_table.setRowCount(len(unique_params))
            
#             for row, param_name in enumerate(unique_params):
#                 self.ui.stats_table.setItem(row, 0, QTableWidgetItem(param_name))
#                 self.ui.stats_table.setItem(row, 1, QTableWidgetItem(f"{statistics.get(f'{param_name}_mean', 0):.2f}"))
#                 self.ui.stats_table.setItem(row, 2, QTableWidgetItem(f"{statistics.get(f'{param_name}_std', 0):.2f}"))
#                 self.ui.stats_table.setItem(row, 3, QTableWidgetItem(f"{statistics.get(f'{param_name}_min', 0):.2f}"))
#                 self.ui.stats_table.setItem(row, 4, QTableWidgetItem(f"{statistics.get(f'{param_name}_max', 0):.2f}"))
        
#         self.statusBar().showMessage("Analysis completed")

#     # Add signal connection helper:
#     # def _connect_signals(self):
#     #     """Connect all UI signals"""
#     #     self.ui.plot_btn.clicked.connect(self.analyze_data)
#     #     self.ui.reset_btn.clicked.connect(self.reset_view)
#     #     self.ui.clear_btn.clicked.connect(self.clear_plot)
#     #     self.ui.show_legend.toggled.connect(self.update_plot)
#     #     self.ui.show_grid.toggled.connect(self.update_plot)
#     #     self.ui.show_markers.toggled.connect(self.update_plot)
#     #    # Connect menu actions instead of buttons
#     #     self.ui.export_data_action.triggered.connect(self.export_plotted_data)
#     #     self.ui.export_plot_action.triggered.connect(self.export_report)

#     #     self.ui.window_combo.currentTextChanged.connect(self._on_window_size_changed)
#     #     self.ui.window_slider.valueChanged.connect(self._on_window_position_changed)
    
#     def _connect_signals(self):
#         """Connect all UI signals"""
#         self.ui.plot_btn.clicked.connect(self.analyze_data)
#         self.ui.reset_btn.clicked.connect(self.reset_view)
#         self.ui.clear_btn.clicked.connect(self.clear_plot)
#         self.ui.show_legend.toggled.connect(self.update_plot)
#         self.ui.show_grid.toggled.connect(self.update_plot)
#         self.ui.window_combo.currentTextChanged.connect(self._on_window_size_changed)
#         self.ui.window_slider.valueChanged.connect(self._on_window_position_changed)
#         self.ui.export_data_action.triggered.connect(self.export_plotted_data)
#         self.ui.export_plot_action.triggered.connect(self.export_report)

    
#     def _on_window_size_changed(self, window_text):
#         """Handle time window size change"""
#         window_map = {
#             "6 Hours": 6,
#             "12 Hours": 12,
#             "24 Hours": 24,
#             "3 Days": 72,
#             "7 Days": 168,
#             "1 Month": 720,
#             "Full Dataset": None
#         }
#         self.current_window_hours = window_map.get(window_text, 24)
#         self._render_current_window()

#     # REPLACE _on_window_position_changed

#     def _on_window_position_changed(self, value):
#         if self.full_data_cache is None or self.full_data_cache.empty:
#             return

#         timestamp_col = ccu.column_cache.get_column('timestamp', self.full_data_cache)
#         if not timestamp_col:
#             return

#         timestamps = pd.to_datetime(
#             self.full_data_cache[timestamp_col], errors='coerce'
#         ).dropna().sort_values()

#         if timestamps.empty:
#             return

#         if self.current_window_hours is None:
#             self.window_start_index = 0
#         else:
#             total_hours = (timestamps.max() - timestamps.min()).total_seconds() / 3600
#             max_start_hours = max(0.0, total_hours - self.current_window_hours)
#             start_offset_hours = (value / 1000.0) * max_start_hours   # 0-1000 range
#             window_start_time = timestamps.min() + pd.Timedelta(hours=start_offset_hours)
#             # idxmax on boolean returns label; use searchsorted for positional index
#             pos = int(np.searchsorted(timestamps.values, window_start_time))
#             # self.window_start_index = timestamps.index[min(pos, len(timestamps) - 1)]
#             self.window_start_index = min(pos, len(timestamps) - 1)

#         self._render_current_window()


#     def clear_plot(self):
#         """Clear the plot"""
#         self.ui.ts_plot.setHtml("<html><body style='background:#2C3E50'></body></html>")

#     def reset_view(self):
#         """Reset all selections"""
#         self.ui.enable_600s_filter.setChecked(False)
#         self.ui.enable_date_filter.setChecked(True)
#         self.ui.enable_time_filter.setChecked(False)
#         self.ui.power_full_cb.setChecked(False)
#         self.ui.power_active_cb.setChecked(False)
#         self.ui.power_reactive_cb.setChecked(False)
#         self.ui.wind_speed_cb.setChecked(False)
#         self.ui.rotor_speed_cb.setChecked(False)
#         self.ui.yaw_speed_cb.setChecked(False)
#         self.ui.nacelle_direction_cb.setChecked(False)
        
#         datetime_info = self.get_datetime_info_from_dataset()
#         self.ui.start_date_only.setText(datetime_info['min_date'])
#         self.ui.end_date_only.setText(datetime_info['max_date'])
#         self.ui.start_time_only.clear()
#         self.ui.end_time_only.clear()
        
#         self.ui.ts_plot.setHtml("<html><body style='background:#2C3E50'></body></html>")

    
#     def export_plotted_data(self):
#         """Export the currently plotted data to CSV or Excel"""
#         if not self._validate_export_data():
#             return
        
#         selected_params = self.get_selected_parameters()
#         if not selected_params:
#             QMessageBox.warning(self, "Export Failed", "No parameters selected")
#             return
        
#         file_path = self._get_export_file_path(selected_params, "Data")
#         if not file_path:
#             return
        
#         try:
#             export_df = self._prepare_export_dataframe(selected_params)
#             self._save_export_file(export_df, file_path)
#             QMessageBox.information(self, "Export Successful", f"Data exported to {file_path}")
#             self.statusBar().showMessage(f"Exported: {len(export_df)} rows, {len(export_df.columns)} columns")
#         except Exception as e:
#             QMessageBox.critical(self, "Export Failed", f"Error: {str(e)}")
#             self.statusBar().showMessage(f"Export failed: {str(e)}")

#     def _validate_export_data(self):
#         """Validate data before export"""
#         if self.filtered_data is None or self.filtered_data.empty:
#             QMessageBox.warning(self, "Export Failed", "No data to export")
#             return False
#         return True

#     def _get_export_file_path(self, selected_params, file_type):
#         """Get file path from user"""
#         param_names = [p['display'].replace(' ', '_').replace('(', '').replace(')', '') for p in selected_params]
#         default_filename = f"TimeSeries_{'_'.join(param_names[:3])}"
        
#         file_path, file_type_selected = QFileDialog.getSaveFileName(
#             self, f"Export {file_type}", default_filename,
#             "CSV Files (*.csv);;Excel Files (*.xlsx)"
#         )
#         return file_path

#     def _prepare_export_dataframe(self, selected_params):
#         """Prepare dataframe for export"""
#         timestamp_col = ccu.column_cache.get_column('timestamp', self.filtered_data)
#         selected_columns = [p['column'] for p in selected_params]
#         export_cols = [timestamp_col] + selected_columns
#         export_df = self.filtered_data[export_cols].copy()
        
#         column_rename = {p['column']: p['display'] for p in selected_params}
#         export_df = export_df.rename(columns=column_rename)
        
#         if len(selected_columns) > 1:
#             numeric_cols = []
#             for p in selected_params:
#                 display_name = p['display']
#                 if display_name in export_df.columns:
#                     export_df[display_name] = pd.to_numeric(export_df[display_name], errors='coerce')
#                     numeric_cols.append(display_name)
#             if numeric_cols:
#                 export_df['Total_Sum'] = export_df[numeric_cols].sum(axis=1, skipna=True)
        
#         return export_df

#     def _save_export_file(self, df, file_path):
#         """Save dataframe to file"""
#         if file_path.endswith('.csv'):
#             df.to_csv(file_path, index=False)
#         else:
#             df.to_excel(file_path, index=False, sheet_name="TimeSeries_Data")

    
#     def export_report(self):
#         """Export a report including the graph and the summary/statistics table."""
#         if self.filtered_data is None or self.filtered_data.empty:
#             QMessageBox.warning(self, "Export Failed", "No data to export.")
#             return

#         # Get selected parameters
#         selected_params = self.get_selected_parameters()
#         if not selected_params:
#             QMessageBox.warning(self, "Export Failed", "No parameters selected.")
#             return

#         # Get timestamp column
#         timestamp_col = ccu.column_cache.get_column('timestamp', self.filtered_data)
#         if not timestamp_col:
#             QMessageBox.warning(self, "Export Failed", "No timestamp column found.")
#             return

#         # Create filename with selected parameter names
#         param_names = [param['display'].replace(' ', '_').replace('(', '').replace(')', '') for param in selected_params]
#         default_filename = f"Report_{'_'.join(param_names[:3])}"
        
#         # Ask user for PDF file path
#         options = QFileDialog.Options()
#         file_path, _ = QFileDialog.getSaveFileName(
#             self,
#             "Export Report",
#             default_filename,
#             "PDF Files (*.pdf)",
#             options=options
#         )
#         if not file_path:
#             return

#         try:
#             selected_columns = [param['column'] for param in selected_params]
#             timestamps = pd.to_datetime(self.filtered_data[timestamp_col], errors='coerce')
            
#             # Create the plot
#             fig, ax = plt.subplots(figsize=(12, 6))
            
#             for param in selected_params:
#                 col = param['column']
#                 display_name = param['display']
#                 if col in self.filtered_data.columns:
#                     values = pd.to_numeric(self.filtered_data[col], errors='coerce')
#                     ax.plot(timestamps, values, label=display_name, linewidth=2)
            
#             ax.set_title(f"Time Series Analysis: {', '.join([p['display'] for p in selected_params])}", 
#                         fontsize=14, fontweight='bold')
#             ax.set_xlabel("Time", fontsize=12)
#             ax.set_ylabel("Values", fontsize=12)
#             ax.legend()
#             ax.grid(True, alpha=0.3)
#             plt.xticks(rotation=45)
#             plt.tight_layout()

#             # Prepare summary statistics
#             summary_data = {}
#             for param in selected_params:
#                 col = param['column']
#                 display_name = param['display']
#                 if col in self.filtered_data.columns:
#                     values = pd.to_numeric(self.filtered_data[col], errors='coerce').dropna()
#                     if not values.empty:
#                         summary_data[display_name] = {
#                             'Mean': values.mean(),
#                             'Std': values.std(),
#                             'Min': values.min(),
#                             'Max': values.max(),
#                             'Count': len(values)
#                         }
            
#             summary_df = pd.DataFrame(summary_data).T

#             # Export to PDF
#             with PdfPages(file_path) as pdf:
#                 # Save the plot
#                 pdf.savefig(fig, bbox_inches='tight')
#                 plt.close(fig)

#                 # Create statistics table page
#                 if not summary_df.empty:
#                     fig2, ax2 = plt.subplots(figsize=(10, max(4, len(summary_df) * 0.5 + 2)))
#                     ax2.axis('off')
                    
#                     table = ax2.table(
#                         cellText=summary_df.round(3).values,
#                         colLabels=summary_df.columns,
#                         rowLabels=summary_df.index,
#                         cellLoc='center',
#                         loc='center'
#                     )
#                     table.auto_set_font_size(False)
#                     table.set_fontsize(9)
#                     table.scale(1.2, 1.8)
                    
#                     # Style the table
#                     for i in range(len(summary_df.columns)):
#                         table[(0, i)].set_facecolor('#3498DB')
#                         table[(0, i)].set_text_props(weight='bold', color='white')
                    
#                     ax2.set_title("Summary Statistics", fontsize=14, fontweight='bold', pad=20)
#                     pdf.savefig(fig2, bbox_inches='tight')
#                     plt.close(fig2)

#             QMessageBox.information(self, "Export Successful", f"Report exported to {file_path}")
#             self.statusBar().showMessage(f"Report exported with {len(selected_params)} parameters")
            
#         except Exception as e:
#             QMessageBox.critical(self, "Export Failed", f"Error during report export: {str(e)}")
#             self.statusBar().showMessage(f"Report export failed: {str(e)}")
    
#     # def get_datetime_info_from_dataset(self):
#     #     """Get datetime info using datetime_utils"""
#     #     if hasattr(self, 'data') and not self.data.empty:
#     #         return dtu.get_datetime_info(self.data)
#     #     return "", "", "", "", None
#     def get_datetime_info_from_dataset(self):
#         """Get datetime info as dictionary"""
#         if hasattr(self, 'data') and not self.data.empty:
#             min_date, max_date, min_time, max_time, col = dtu.get_datetime_info(self.data)
#             return {
#                 'min_date': min_date,
#                 'max_date': max_date,
#                 'min_time': min_time,
#                 'max_time': max_time,
#                 'timestamp_col': col
#             }
#         return {
#             'min_date': "",
#             'max_date': "",
#             'min_time': "",
#             'max_time': "",
#             'timestamp_col': None
#         }

    
#     def update_plot(self):
#         """Update plot when view options change"""
#         selected_params = self.get_selected_parameters()
#         if selected_params and not self.filtered_data.empty:
#             self.plot_time_series(selected_params)

#     # def closeEvent(self, event):
#     #     """Handle window close event"""
#     #     event.accept()  # Allow window to close
#     def closeEvent(self, event):
#         """Cleanup store entry on window close"""
#         shared_store.stores.pop(self._turbine_key, None)
#         event.accept()

# # views/time_series/Time_series_comp.py
# import sys
# import os
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# import pandas as pd
# from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout
# from PyQt5.QtCore import Qt, QUrl
# from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings

# import dash_app
# from utils import column_cache_utility as ccu
# from models import scada_utils as su


# class TimeSeriesAnalysisWindow(QMainWindow):
#     """Minimal launcher — full UI lives in Dash."""

#     def __init__(self, data=None, turbine_name=None, parent=None, project_id=None):
#         super().__init__(parent)
#         self.turbine_name = turbine_name or "Unknown"
#         self._turbine_key = f"{self.turbine_name}_{id(self)}"

#         self.setWindowTitle(f"Time Series — {self.turbine_name}")
#         self.setWindowFlags(Qt.Window)
#         self.setAttribute(Qt.WA_DeleteOnClose)
#         self.resize(1400, 900)

#         # Push data to Dash store
#         if data is not None and not data.empty:
#             self._push_data(data)

#         # Start server (no-op if running)
#         dash_app.start_server()

#         # Minimal PyQt5 window — just a full-screen browser
#         self._browser = QWebEngineView()
#         settings = self._browser.settings()
#         settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
#         settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

#         central = QWidget()
#         layout  = QVBoxLayout(central)
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.addWidget(self._browser)
#         self.setCentralWidget(central)

#         self._browser.setUrl(QUrl(f"http://127.0.0.1:8050/?turbine={self._turbine_key}"))

#     def _push_data(self, data: pd.DataFrame):
#         """Detect columns and push raw data to dash_app.stores."""
#         timestamp_col = ccu.column_cache.get_column("timestamp", data)

#         # Build column map using scada_utils
#         param_keys = [
#             "power", "wind_speed", "rotor_speed", "yaw_speed",
#             "nacelle_direction", "voltage_phase_a", "voltage_phase_b",
#             "voltage_phase_c", "frequency",
#         ]
#         column_map = {}
#         for key in param_keys:
#             matched = su.find_matching_columns(data, key)
#             if matched:
#                 column_map[key] = matched[0]

#         dash_app.stores[self._turbine_key] = {
#             "raw_data":      data,
#             "timestamp_col": timestamp_col,
#             "turbine_name":  self.turbine_name,
#             "column_map":    column_map,
#         }

#     def set_data(self, data, turbine_name=None):
#         """Called if data updates after window is open."""
#         if turbine_name:
#             self.turbine_name = turbine_name
#         if data is not None and not data.empty:
#             self._push_data(data)
#         self._browser.reload()

#     def closeEvent(self, event):
#         dash_app.stores.pop(self._turbine_key, None)
#         event.accept()

import webbrowser

from models import scada_utils as su
from utils import column_cache_utility as ccu
from views.time_series import dash_app

def open_timeseries(data, turbine_name):
    key = f"{turbine_name}_{id(data)}"
    timestamp_col = ccu.column_cache.get_column("timestamp", data)
    column_map = {k: su.find_matching_columns(data, k)[0]
                  for k in ["power","wind_speed","rotor_speed","yaw_speed",
                             "nacelle_direction","voltage_phase_a",
                             "voltage_phase_b","voltage_phase_c","frequency"]
                  if su.find_matching_columns(data, k)}
    dash_app.stores[key] = {
        "raw_data": data,
        "timestamp_col": timestamp_col,
        "turbine_name": turbine_name,
        "column_map": column_map,
    }
    dash_app.start_server()
    webbrowser.open(f"http://127.0.0.1:8050/?turbine={key}")