from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QDate
import pyqtgraph as pg
import numpy as np
import pandas as pd
import datetime

class CustomGraphDialog(QMainWindow):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Custom-Multi Graph")
        self.setMinimumSize(1100, 700)
        # Store data (assumed to be a pandas DataFrame)
        self.data = data.copy() if data is not None else pd.DataFrame()
        self.filtered_df = None  # Placeholder for filtered data if needed
        self.axis_mode = "Two_axis"
        self.init_ui()
        # 15. UPDATE INIT_UI METHOD - Replace the existing init_ui method structure
    def init_ui(self):
        """Enhanced UI initialization"""
        # Create central widget and set layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        # Main Content Area
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.main_layout.addWidget(content_widget)
        # Setup command dock with all groups
        self.setup_command_dock()
        # Enhanced PyQtGraph Plot Widget
        self.pg_widget = pg.PlotWidget()
        self.pg_widget.setBackground('w')
        self.pg_widget.setMinimumSize(600, 400)
        content_layout.addWidget(self.pg_widget, stretch=1)

    def create_enhanced_plot_options_group(self):
        """Create enhanced plotting options group"""
        plot_group = QGroupBox("Advanced Plotting Options")
        plot_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        plot_layout = QGridLayout(plot_group)
        plot_layout.setContentsMargins(5, 5, 5, 5)
        plot_layout.setHorizontalSpacing(5)
        plot_layout.setVerticalSpacing(5)
        # Primary plot options
        plot_type_label = QLabel("Plot Type:")
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["Scatter", "Line", "Scatter+Line", "Bar", "Histogram", "Area"])
        color_label = QLabel("Primary Color:")
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Blue", "Red", "Green", "Purple", "Orange", "Teal", "Pink", "Brown"])
        # Secondary plot options (for four-axis mode) - FIX: Properly initialize as instance attributes
        self.secondary_color_label = QLabel("Secondary Color:")
        self.secondary_color_combo = QComboBox()
        self.secondary_color_combo.addItems(["Red", "Blue", "Green", "Purple", "Orange", "Teal", "Pink", "Brown"])
        self.secondary_color_combo.setCurrentText("Red")
        marker_label = QLabel("Marker:")
        self.marker_combo = QComboBox()
        self.marker_combo.addItems(["Circle", "Square", "Triangle", "Diamond", "Cross", "Plus", "Star", "None"])
        
        size_label = QLabel("Size:")
        self.size_spin = QDoubleSpinBox()
        self.size_spin.setRange(1, 30)
        self.size_spin.setValue(8)
        self.size_spin.setSingleStep(0.5)
        # Grid options
        self.show_grid = QCheckBox("Show Grid")
        self.show_grid.setChecked(True)
        # Transparency
        alpha_label = QLabel("Transparency:")
        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.1, 1.0)
        self.alpha_spin.setValue(0.8)
        self.alpha_spin.setSingleStep(0.1)
        plot_layout.addWidget(plot_type_label, 0, 0)
        plot_layout.addWidget(self.plot_type_combo, 0, 1)
        plot_layout.addWidget(color_label, 1, 0)
        plot_layout.addWidget(self.color_combo, 1, 1)
        plot_layout.addWidget(self.secondary_color_label, 2, 0)
        plot_layout.addWidget(self.secondary_color_combo, 2, 1)
        plot_layout.addWidget(marker_label, 3, 0)
        plot_layout.addWidget(self.marker_combo, 3, 1)
        plot_layout.addWidget(size_label, 4, 0)
        plot_layout.addWidget(self.size_spin, 4, 1)
        plot_layout.addWidget(self.show_grid, 5, 0)
        plot_layout.addWidget(alpha_label, 6, 0)
        plot_layout.addWidget(self.alpha_spin, 6, 1)
        return plot_group
    
    def create_data_selection_group(self):
        """Create data selection group with axis mode options"""
        data_group = QGroupBox("Data Selection")
        data_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        data_layout = QGridLayout(data_group)
        data_layout.setContentsMargins(5, 5, 5, 5)
        data_layout.setHorizontalSpacing(5)
        data_layout.setVerticalSpacing(5)
        # Axis mode selection
        axis_mode_label = QLabel("Axis Mode:")
        self.axis_mode_group = QButtonGroup(self)
        self.two_axis_radio = QRadioButton("Two Axis")
        self.four_axis_radio = QRadioButton("Four Axis")
        self.two_axis_radio.setChecked(True)
        self.axis_mode_group.addButton(self.two_axis_radio)
        self.axis_mode_group.addButton(self.four_axis_radio)
        # Primary axis selection
        x_label = QLabel("X-Axis:")
        self.x_combo = QComboBox()
        if not self.data.empty: self.x_combo.addItems(list(self.data.columns))
        y_label = QLabel("Y-Axis:")
        self.y_combo = QComboBox()
        if not self.data.empty: self.y_combo.addItems(list(self.data.columns))
        # Secondary axis selection (initially hidden)
        self.x1_label = QLabel("X1-Axis:")
        self.x1_combo = QComboBox()
        if not self.data.empty: self.x1_combo.addItems(list(self.data.columns))
        self.y1_label = QLabel("Y1-Axis:")
        self.y1_combo = QComboBox()
        if not self.data.empty: self.y1_combo.addItems(list(self.data.columns))
        # Layout arrangement
        data_layout.addWidget(axis_mode_label, 0, 0)
        data_layout.addWidget(self.two_axis_radio, 0, 1)
        data_layout.addWidget(self.four_axis_radio, 0, 2)
        
        data_layout.addWidget(x_label, 1, 0)
        data_layout.addWidget(self.x_combo, 1, 1, 1, 2)
        data_layout.addWidget(y_label, 2, 0)
        data_layout.addWidget(self.y_combo, 2, 1, 1, 2)
        
        data_layout.addWidget(self.x1_label, 3, 0)
        data_layout.addWidget(self.x1_combo, 3, 1, 1, 2)
        data_layout.addWidget(self.y1_label, 4, 0)
        data_layout.addWidget(self.y1_combo, 4, 1, 1, 2)

        self.x1_label.setVisible(False)
        self.x1_combo.setVisible(False)
        self.y1_label.setVisible(False)
        self.y1_combo.setVisible(False)

        self.two_axis_radio.toggled.connect(self.on_axis_mode_changed)
        self.four_axis_radio.toggled.connect(self.on_axis_mode_changed)
        return data_group
    
    def create_date_filter_group(self):
        """Create date filter group"""
        filter_group = QGroupBox("Date Filter")
        filter_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        filter_layout = QGridLayout(filter_group)
        filter_layout.setContentsMargins(5, 5, 5, 5)
        filter_layout.setHorizontalSpacing(5)
        filter_layout.setVerticalSpacing(5)
        
        self.enable_date_filter = QCheckBox("Enable Date Filter")
        filter_layout.addWidget(self.enable_date_filter, 0, 0, 1, 2)
        
        start_date_label = QLabel("Start Date:")
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addYears(-1))
        self.start_date_edit.setEnabled(False)
        
        end_date_label = QLabel("End Date:")
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setEnabled(False)
        
        filter_layout.addWidget(start_date_label, 1, 0)
        filter_layout.addWidget(self.start_date_edit, 1, 1)
        filter_layout.addWidget(end_date_label, 2, 0)
        filter_layout.addWidget(self.end_date_edit, 2, 1)
        
        # Connect enable/disable
        self.enable_date_filter.stateChanged.connect(
            lambda state: [
                self.start_date_edit.setEnabled(state == Qt.Checked),
                self.end_date_edit.setEnabled(state == Qt.Checked)
            ]
        )
        
        return filter_group
    
    def create_legend_options_group(self):
        """Create legend options group"""
        legend_group = QGroupBox("Legend Options")
        legend_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        legend_layout = QGridLayout(legend_group)
        legend_layout.setContentsMargins(5, 5, 5, 5)
        legend_layout.setHorizontalSpacing(5)
        legend_layout.setVerticalSpacing(5)
        
        self.show_legend = QCheckBox("Show Legend")
        self.show_legend.setChecked(True)
        
        legend_pos_label = QLabel("Position:")
        self.legend_position = QComboBox()
        self.legend_position.addItems(["Top Left", "Top Right", "Bottom Left", "Bottom Right"])
        self.legend_position.setCurrentText("Top Left")
        
        legend_layout.addWidget(self.show_legend, 0, 0)
        legend_layout.addWidget(legend_pos_label, 1, 0)
        legend_layout.addWidget(self.legend_position, 1, 1)
        
        return legend_group
    
    # 13. CREATE REMAINING GROUPS - Methods for trend analysis and actions
    def create_trend_analysis_group(self):
        """Create enhanced trend analysis group"""
        trend_group = QGroupBox("Trend Analysis")
        trend_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        trend_layout = QVBoxLayout(trend_group)
        trend_layout.setContentsMargins(5, 5, 5, 5)
        trend_layout.setSpacing(3)
        
        self.trend_check = QCheckBox("Add Trend Line")
        trend_layout.addWidget(self.trend_check)
        
        # Trend options in horizontal layout
        trend_options_layout = QHBoxLayout()
        trend_type_label = QLabel("Type:")
        self.trend_type_combo = QComboBox()
        self.trend_type_combo.addItems(["Linear", "Polynomial", "Moving Average", "Exponential", "Logarithmic"])
        
        trend_order_label = QLabel("Order/Window:")
        self.trend_order_spin = QSpinBox()
        self.trend_order_spin.setRange(1, 10)
        self.trend_order_spin.setValue(2)
        self.trend_order_spin.setEnabled(False)
        self.trend_type_combo.setEnabled(False)
        
        trend_options_layout.addWidget(trend_type_label)
        trend_options_layout.addWidget(self.trend_type_combo)
        trend_options_layout.addWidget(trend_order_label)
        trend_options_layout.addWidget(self.trend_order_spin)
        trend_layout.addLayout(trend_options_layout)
        # Trend equation display
        self.trend_equation_label = QLabel("")
        self.trend_equation_label.setWordWrap(True)
        self.trend_equation_label.setStyleSheet("QLabel { color: #666; font-size: 9pt; }")
        trend_layout.addWidget(self.trend_equation_label)
        # Connect trend checkbox
        self.trend_check.stateChanged.connect(
            lambda state: [
                self.trend_order_spin.setEnabled(state == Qt.Checked),
                self.trend_type_combo.setEnabled(state == Qt.Checked)
            ]
        )
        
        return trend_group
    
    def create_actions_group(self):
        """Create actions group with enhanced buttons"""
        action_group = QGroupBox("Actions")
        action_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        action_layout = QVBoxLayout(action_group)
        action_layout.setContentsMargins(5, 5, 5, 5)
        action_layout.setSpacing(5)
        
        self.plot_button = QPushButton("🔄 Plot/Refresh")
        self.plot_button.setStyleSheet("QPushButton { font-weight: bold; padding: 8px; }")
        
        self.export_button = QPushButton("📊 Export Plot")
        self.data_export_button = QPushButton("📋 Export Data")
        self.reset_button = QPushButton("🔄 Reset View")
        self.close_button = QPushButton("❌ Close")
        
        action_layout.addWidget(self.plot_button)
        action_layout.addWidget(self.export_button)
        action_layout.addWidget(self.data_export_button)
        action_layout.addWidget(self.reset_button)
        action_layout.addWidget(self.close_button)
        
        # Connect buttons
        self.plot_button.clicked.connect(self.plot_custom)
        self.export_button.clicked.connect(self.export_custom_graph)
        self.data_export_button.clicked.connect(self.export_custom_data)
        self.reset_button.clicked.connect(self.reset_view)
        self.close_button.clicked.connect(self.close)
        return action_group
    # 6. AXIS MODE CHANGE HANDLER - Add this new method
    def on_axis_mode_changed(self):
        """Handle axis mode changes"""
        if self.two_axis_radio.isChecked():
            self.axis_mode = "two_axis"
            self.x1_label.setVisible(False)
            self.x1_combo.setVisible(False)
            self.y1_label.setVisible(False)
            self.y1_combo.setVisible(False)
            self.secondary_color_label.setVisible(False)
            self.secondary_color_combo.setVisible(False)
        else:
            self.axis_mode = "four_axis"
            self.x1_label.setVisible(True)
            self.x1_combo.setVisible(True)
            self.y1_label.setVisible(True)
            self.y1_combo.setVisible(True)
            self.secondary_color_label.setVisible(True)
            self.secondary_color_combo.setVisible(True)

    def apply_date_filter(self, df):
        """Apply date filter to data"""
        if not self.enable_date_filter.isChecked():
            return df
        
        # Try to find date/timestamp columns
        date_columns = []
        for col in df.columns:
            if df[col].dtype == 'datetime64[ns]' or 'date' in col.lower() or 'time' in col.lower():
                date_columns.append(col)
        
        if not date_columns:
            QMessageBox.warning(self, "Warning", "No date columns found for filtering.")
            return df
        
        # Use the first date column found
        date_col = date_columns[0]
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()
        
        # Convert to pandas datetime if needed
        if df[date_col].dtype != 'datetime64[ns]':
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Filter data
        mask = (df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)
        return df[mask]
    
    def format_timestamp_axis(self, plot_item, x_data, x_col):
        """Format timestamp axis to be human readable"""
        # Check if x_data appears to be timestamps
        if self.is_timestamp_data(x_data):
            try:
                # Convert timestamps to datetime objects
                dates = self.convert_timestamps_to_dates(x_data)
                
                if dates:
                    # Create readable ticks based on data range
                    ticks = self.create_timestamp_ticks(x_data, dates)
                    
                    if ticks:
                        plot_item.getAxis('bottom').setTicks([ticks])
                        plot_item.setLabel('bottom', f"{x_col} (Date/Time)", **{'color': '#404040', 'font-size': '10pt'})
                        
                        # Enable date-time axis formatting
                        axis = plot_item.getAxis('bottom')
                        axis.enableAutoSIPrefix(False)
                    
            except Exception as e:
                print(f"Warning: Could not format timestamp axis: {e}")
                # Fallback to default formatting
                pass
    
    def is_timestamp_data(self, data):
        """Check if data appears to be timestamps"""
        if len(data) == 0:
            return False
        
        # Check if values are in typical timestamp ranges
        min_val = np.min(data)
        max_val = np.max(data)
        
        # Unix timestamp ranges (seconds, milliseconds, microseconds)
        unix_sec_min = 946684800    # Year 2000 in seconds
        unix_sec_max = 2147483647   # Year 2038 in seconds
        unix_ms_min = unix_sec_min * 1000
        unix_ms_max = unix_sec_max * 1000
        unix_us_min = unix_sec_min * 1000000
        unix_us_max = unix_sec_max * 1000000
        
        # Check different timestamp formats
        is_unix_seconds = unix_sec_min <= min_val <= unix_sec_max and unix_sec_min <= max_val <= unix_sec_max
        is_unix_milliseconds = unix_ms_min <= min_val <= unix_ms_max and unix_ms_min <= max_val <= unix_ms_max
        is_unix_microseconds = unix_us_min <= min_val <= unix_us_max and unix_us_min <= max_val <= unix_us_max
        
        return is_unix_seconds or is_unix_milliseconds or is_unix_microseconds
    
    def convert_timestamps_to_dates(self, x_data):
        """Convert timestamp data to datetime objects"""
        dates = []
        
        try:
            for timestamp in x_data:
                if timestamp < 1e10:  # Unix seconds
                    date = datetime.datetime.fromtimestamp(timestamp)
                elif timestamp < 1e13:  # Unix milliseconds
                    date = datetime.datetime.fromtimestamp(timestamp / 1000)
                elif timestamp < 1e16:  # Unix microseconds
                    date = datetime.datetime.fromtimestamp(timestamp / 1000000)
                else:
                    # Try nanoseconds or other formats
                    date = datetime.datetime.fromtimestamp(timestamp / 1e9)
                
                dates.append(date)
        except (ValueError, OSError, OverflowError) as e:
            print(f"Error converting timestamps: {e}")
            return []
        
        return dates

    def create_timestamp_ticks(self, x_data, dates):
        """Create appropriate tick marks for timestamp data"""
        if not dates or len(dates) == 0:
            return []
        
        try:
            # Sort dates with their corresponding x values
            date_x_pairs = list(zip(dates, x_data))
            date_x_pairs.sort(key=lambda x: x[0])
            
            # Determine the time range and appropriate formatting
            time_range = max(dates) - min(dates)
            
            # Select appropriate number of ticks (max 10)
            num_ticks = min(10, len(dates))
            step = max(1, len(date_x_pairs) // num_ticks)
            selected_pairs = date_x_pairs[::step]
            
            # Choose format based on time range
            if time_range.days > 365:
                date_format = "%Y-%m"  # Year-Month
            elif time_range.days > 30:
                date_format = "%m/%d/%Y"  # Month/Day/Year
            elif time_range.days > 1:
                date_format = "%m/%d %H:%M"  # Month/Day Hour:Minute
            elif time_range.seconds > 3600:
                date_format = "%H:%M:%S"  # Hour:Minute:Second
            else:
                date_format = "%H:%M:%S.%f"  # Include microseconds
                date_format = date_format[:-3]  # Remove last 3 digits of microseconds
            
            # Create tick list
            ticks = []
            for date, x_val in selected_pairs:
                formatted_date = date.strftime(date_format)
                ticks.append((x_val, formatted_date))
            
            return ticks
            
        except Exception as e:
            print(f"Error creating timestamp ticks: {e}")
            return []

    
    # 10. UPDATE COMMAND CENTER WIDTH - Replace the command dock setup
    def setup_command_dock(self):
        """Setup command dock with increased width"""
        self.command_dock = QDockWidget("Command Center", self)
        self.command_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        command_widget = QWidget()
        command_layout_v = QVBoxLayout(command_widget)
        command_layout_v.setContentsMargins(5, 5, 5, 5)
        command_layout_v.setSpacing(5)

        # Add all groups
        command_layout_v.addWidget(self.create_data_selection_group())
        command_layout_v.addWidget(self.create_date_filter_group())
        command_layout_v.addWidget(self.create_enhanced_plot_options_group())
        command_layout_v.addWidget(self.create_legend_options_group())
        command_layout_v.addWidget(self.create_trend_analysis_group())
        command_layout_v.addWidget(self.create_actions_group())
        command_layout_v.addStretch(1)

        self.command_dock.setWidget(command_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.command_dock)
        # Increased width for better usability
        self.command_dock.setMinimumWidth(300)
        self.command_dock.setMaximumWidth(400)
    

    # 11. ENHANCED PLOT_CUSTOM METHOD - Major updates to existing method
    def plot_custom(self):
        """Enhanced plotting method with all new features"""
        # Get selected columns
        x_col = self.x_combo.currentText()
        y_col = self.y_combo.currentText()
        
        if self.data.empty or not x_col or not y_col:
            QMessageBox.warning(self, "Error", "No data available for plotting or columns not selected.")
            return
        
        # Apply date filter if enabled
        filtered_data = self.apply_date_filter(self.data)
        if filtered_data.empty:
            QMessageBox.warning(self, "Error", "No data available after applying date filter.")
            return
        
        # Validate columns exist
        if x_col not in filtered_data.columns or y_col not in filtered_data.columns:
            QMessageBox.warning(self, "Error", f"Selected columns '{x_col}' or '{y_col}' not found in data.")
            return

        # Clear previous plot
        self.pg_widget.clear()
        self.trend_equation_label.setText("")

        try:
            # Convert data to numeric, handling non-numeric values
            x_data_raw = pd.to_numeric(filtered_data[x_col], errors='coerce')
            y_data_raw = pd.to_numeric(filtered_data[y_col], errors='coerce')
            
            # Remove NaN values
            valid_mask = ~(x_data_raw.isna() | y_data_raw.isna())
            x_data = x_data_raw[valid_mask].values
            y_data = y_data_raw[valid_mask].values
            
            if len(x_data) == 0 or len(y_data) == 0:
                QMessageBox.warning(self, "Error", "No valid numeric data points found.")
                return
            
            # Handle four-axis mode
            x1_data, y1_data = None, None
            if self.axis_mode == "four_axis":
                x1_col = self.x1_combo.currentText()
                y1_col = self.y1_combo.currentText()
                
                if x1_col not in filtered_data.columns or y1_col not in filtered_data.columns:
                    QMessageBox.warning(self, "Error", f"Secondary axis columns '{x1_col}' or '{y1_col}' not found.")
                    return
                
                x1_data_raw = pd.to_numeric(filtered_data[x1_col], errors='coerce')
                y1_data_raw = pd.to_numeric(filtered_data[y1_col], errors='coerce')
                
                valid_mask1 = ~(x1_data_raw.isna() | y1_data_raw.isna())
                x1_data = x1_data_raw[valid_mask1].values
                y1_data = y1_data_raw[valid_mask1].values
                
                if len(x1_data) == 0 or len(y1_data) == 0:
                    QMessageBox.warning(self, "Error", "No valid data points for secondary axis.")
                    return
                    
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Data conversion error: {str(e)}")
            return

        # Enhanced color mapping
        color_map = {
            "Blue": (0, 102, 204), "Red": (220, 20, 60), "Green": (46, 139, 87),
            "Purple": (148, 0, 211), "Orange": (255, 140, 0), "Teal": (0, 128, 128),
            "Pink": (255, 20, 147), "Brown": (139, 69, 19)
        }

        # Get colors and settings
        primary_color = color_map.get(self.color_combo.currentText(), (0, 102, 204))
        secondary_color = color_map.get(self.secondary_color_combo.currentText(), (220, 20, 60))
        
        # Setup plot
        plot_item = self.pg_widget.getPlotItem()
        plot_item.clear()
        
        # Grid settings
        if self.show_grid.isChecked():
            plot_item.showGrid(x=True, y=True, alpha=0.3)
        
        # Format timestamp axis if needed
        if hasattr(self, 'is_timestamp_data') and self.is_timestamp_data(x_data):
            self.format_timestamp_axis(plot_item, x_data, x_col)
        
        # Setup secondary axis for four-axis mode
        view_box_right = None
        if self.axis_mode == "four_axis":
            plot_item.showAxis('right')
            view_box_right = pg.ViewBox()
            plot_item.scene().addItem(view_box_right)
            plot_item.getAxis('right').linkToView(view_box_right)
            view_box_right.setXLink(plot_item)
            
            def update_views():
                view_box_right.setGeometry(plot_item.vb.sceneBoundingRect())
                view_box_right.linkedViewChanged(plot_item.vb, view_box_right.XAxis)
            
            update_views()
            plot_item.vb.sigResized.connect(update_views)
            
            # Labels for four-axis mode
            plot_item.setLabel('bottom', x_col, **{'color': '#404040', 'font-size': '11pt'})
            plot_item.setLabel('left', y_col, **{'color': '#404040', 'font-size': '11pt'})
            plot_item.getAxis('right').setLabel(y1_col, **{'color': '#404040', 'font-size': '11pt'})
        else:
            # Labels for two-axis mode
            plot_item.setLabel('bottom', x_col, **{'color': '#404040', 'font-size': '11pt'})
            plot_item.setLabel('left', y_col, **{'color': '#404040', 'font-size': '11pt'})

        # Plot primary data
        self.plot_data_series(plot_item, x_data, y_data, primary_color, "Primary Data")
        
        # Plot secondary data (four-axis mode)
        if self.axis_mode == "four_axis" and view_box_right is not None and x1_data is not None:
            self.plot_data_series_fixed(view_box_right, x1_data, y1_data, secondary_color, "Secondary Data", is_secondary=True)

        # Add trend line if requested
        if self.trend_check.isChecked():
            self.add_trend_line_fixed(plot_item, x_data, y_data, primary_color)

        # Setup legend
        if self.show_legend.isChecked():
            legend_positions = {
                "Top Left": (10, 10), "Top Right": (-10, 10),
                "Bottom Left": (10, -10), "Bottom Right": (-10, -10)
            }
            offset = legend_positions.get(self.legend_position.currentText(), (10, 10))
            if not hasattr(plot_item, 'legend') or plot_item.legend is None:
                plot_item.addLegend(offset=offset)

        # Update statistics
        if self.axis_mode == "four_axis" and x1_data is not None:
            self.update_statistics_table(x_data, y_data, x1_data, y1_data)
        else:
            self.update_statistics_table(x_data, y_data)
        
        # Enable auto-range after plotting
        plot_item.enableAutoRange(axis='xy', enable=True)

    def add_trend_line(self, plot_item, x_data, y_data, line_color):
        """Fixed trend line method"""
        try:
            trend_type = self.trend_type_combo.currentText()
            trend_order = self.trend_order_spin.value()
            
            # Sort data for proper trend line plotting
            sort_indices = np.argsort(x_data)
            x_sorted = x_data[sort_indices]
            y_sorted = y_data[sort_indices]
            
            # Create trend line data
            x_trend = np.linspace(np.min(x_data), np.max(x_data), 100)
            trend_name = ""
            
            if trend_type == "Linear":
                coeffs = np.polyfit(x_data, y_data, 1)
                y_trend = np.polyval(coeffs, x_trend)
                trend_name = f"Linear: y = {coeffs[0]:.4f}x + {coeffs[1]:.4f}"
                
            elif trend_type == "Polynomial":
                order = min(trend_order, len(x_data) - 1, 6)  # Limit polynomial order
                coeffs = np.polyfit(x_data, y_data, order)
                y_trend = np.polyval(coeffs, x_trend)
                trend_name = f"Polynomial (order {order})"
                
            elif trend_type == "Moving Average":
                window = min(trend_order, len(x_sorted) // 2, len(x_sorted))
                if window < 2:
                    window = 2
                y_ma = np.convolve(y_sorted, np.ones(window)/window, mode='valid')
                x_ma = x_sorted[window-1:]
                
                if len(x_ma) > 1:
                    from scipy.interpolate import interp1d
                    interp_func = interp1d(x_ma, y_ma, bounds_error=False, fill_value="extrapolate", kind='linear')
                    y_trend = interp_func(x_trend)
                    trend_name = f"Moving Average (window={window})"
                else:
                    return
            else:
                # Default to linear for other types
                coeffs = np.polyfit(x_data, y_data, 1)
                y_trend = np.polyval(coeffs, x_trend)
                trend_name = f"Linear: y = {coeffs[0]:.4f}x + {coeffs[1]:.4f}"

            # Plot trend line
            trend_pen = pg.mkPen(color=(255, 0, 0), width=3, style=Qt.DashLine)
            plot_item.plot(x_trend, y_trend, pen=trend_pen, name=f"Trend: {trend_type}")
            
            # Update trend equation label
            self.trend_equation_label.setText(f"Equation: {trend_name}")
                
        except Exception as e:
            print(f"Error adding trend line: {str(e)}")
            QMessageBox.warning(self, "Warning", f"Could not add trend line: {str(e)}")    

    def plot_data_series(self, plot_target, x_data, y_data, color, name, is_secondary=False):
        """Fixed plot data series method"""
        plot_type = self.plot_type_combo.currentText()
        marker = self.marker_combo.currentText()
        size = self.size_spin.value()
        alpha = int(self.alpha_spin.value() * 255)
        
        # Enhanced marker mapping
        marker_map = {
            "Circle": 'o', "Square": 's', "Triangle": 't', "Diamond": 'd',
            "Cross": 'x', "Plus": '+', "Star": 'star', "None": None
        }
        marker_symbol = marker_map.get(marker, 'o')
        
        # Create brush and pen with alpha
        brush = pg.mkBrush(color + (alpha,))
        pen = pg.mkPen(color=color + (alpha,), width=2)
        
        try:
            if plot_type == "Scatter":
                if isinstance(plot_target, pg.ViewBox):
                    # For secondary axis (ViewBox)
                    scatter = pg.ScatterPlotItem(
                        x=x_data, y=y_data,
                        symbol=marker_symbol,
                        size=size,
                        brush=brush,
                        name=name
                    )
                    plot_target.addItem(scatter)
                else:
                    # For primary axis (PlotItem)
                    plot_target.plot(
                        x_data, y_data,
                        pen=None,
                        symbol=marker_symbol,
                        symbolSize=size,
                        symbolBrush=brush,
                        name=name
                    )
            
            elif plot_type == "Line":
                if isinstance(plot_target, pg.ViewBox):
                    line = pg.PlotCurveItem(x=x_data, y=y_data, pen=pen, name=name)
                    plot_target.addItem(line)
                else:
                    plot_target.plot(x_data, y_data, pen=pen, name=name)
            
            elif plot_type == "Scatter+Line":
                if isinstance(plot_target, pg.ViewBox):
                    line = pg.PlotCurveItem(x=x_data, y=y_data, pen=pen)
                    scatter = pg.ScatterPlotItem(
                        x=x_data, y=y_data,
                        symbol=marker_symbol,
                        size=size,
                        brush=brush
                    )
                    plot_target.addItem(line)
                    plot_target.addItem(scatter)
                else:
                    plot_target.plot(
                        x_data, y_data,
                        pen=pen,
                        symbol=marker_symbol,
                        symbolSize=size,
                        symbolBrush=brush,
                        name=name
                    )
            
            elif plot_type == "Area":
                if isinstance(plot_target, pg.ViewBox):
                    area = pg.PlotCurveItem(
                        x=x_data, y=y_data,
                        pen=pen,
                        fillLevel=0,
                        brush=brush
                    )
                    plot_target.addItem(area)
                else:
                    plot_target.plot(
                        x_data, y_data,
                        pen=pen,
                        fillLevel=0,
                        fillBrush=brush,
                        name=name
                    )
            
            elif plot_type == "Bar":
                # Create bar positions
                if len(x_data) > 20:  # If too many bars, use indices
                    x_positions = np.arange(len(x_data))
                else:
                    x_positions = x_data
                
                bar_item = pg.BarGraphItem(
                    x=x_positions,
                    height=y_data,
                    width=0.6,
                    brush=brush,
                    name=name
                )
                
                if isinstance(plot_target, pg.ViewBox):
                    plot_target.addItem(bar_item)
                else:
                    plot_target.addItem(bar_item)
            
            elif plot_type == "Histogram":
                y_hist, x_hist = np.histogram(y_data, bins=min(30, len(y_data)//3 + 1))
                x_center = (x_hist[:-1] + x_hist[1:]) / 2
                width = (x_center[1] - x_center[0]) * 0.8 if len(x_center) > 1 else 1
                
                hist_item = pg.BarGraphItem(
                    x=x_center,
                    height=y_hist,
                    width=width,
                    brush=brush,
                    name=name
                )
                
                if isinstance(plot_target, pg.ViewBox):
                    plot_target.addItem(hist_item)
                else:
                    plot_target.addItem(hist_item)
        
        except Exception as e:
            print(f"Error plotting {plot_type}: {str(e)}")
            # Fallback to simple scatter plot
            if isinstance(plot_target, pg.ViewBox):
                scatter = pg.ScatterPlotItem(x=x_data, y=y_data, brush=brush)
                plot_target.addItem(scatter)
            else:
                plot_target.plot(x_data, y_data, pen=None, symbol='o', symbolBrush=brush)

    # 8. ENHANCED STATISTICS TABLE - Replace the existing update_statistics_table method
    def update_statistics_table(self, x_data, y_data, x1_data=None, y1_data=None):
        """Update statistics table with properly formatted numbers, excluding timestamp columns"""
        stats = {}
        
        # Get column names for context
        x_col = self.x_combo.currentText()
        y_col = self.y_combo.currentText()
        
        # Check if X data is timestamp - if so, provide date range instead of statistics
        if self.is_timestamp_data(x_data):
            try:
                dates = self.convert_timestamps_to_dates(x_data)
                if dates:
                    min_date = min(dates).strftime("%Y-%m-%d %H:%M:%S")
                    max_date = max(dates).strftime("%Y-%m-%d %H:%M:%S")
                    stats[f"{x_col} Range Start"] = min_date
                    stats[f"{x_col} Range End"] = max_date
                    time_span = max(dates) - min(dates)
                    stats[f"{x_col} Time Span"] = f"{time_span.days} days, {time_span.seconds//3600} hours"
            except Exception:
                # Fallback to basic info
                stats[f"{x_col} Data Points"] = len(x_data)
        else:
            # Regular numeric statistics for X
            stats.update({
                f"{x_col} Min": np.min(x_data),
                f"{x_col} Max": np.max(x_data),
                f"{x_col} Mean": np.mean(x_data),
                f"{x_col} Median": np.median(x_data),
                f"{x_col} Std Dev": np.std(x_data)
            })
        
        # Y data statistics (assuming Y is always numeric for plotting)
        stats.update({
            f"{y_col} Min": np.min(y_data),
            f"{y_col} Max": np.max(y_data),
            f"{y_col} Mean": np.mean(y_data),
            f"{y_col} Median": np.median(y_data),
            f"{y_col} Std Dev": np.std(y_data),
            "Sample Size": len(x_data)
        })
        
        # Secondary axis statistics (if four-axis mode)
        if self.axis_mode == "four_axis" and x1_data is not None and y1_data is not None:
            x1_col = self.x1_combo.currentText()
            y1_col = self.y1_combo.currentText()
            
            # Check if X1 data is timestamp
            if self.is_timestamp_data(x1_data):
                try:
                    dates1 = self.convert_timestamps_to_dates(x1_data)
                    if dates1:
                        min_date1 = min(dates1).strftime("%Y-%m-%d %H:%M:%S")
                        max_date1 = max(dates1).strftime("%Y-%m-%d %H:%M:%S")
                        stats[f"{x1_col} Range Start"] = min_date1
                        stats[f"{x1_col} Range End"] = max_date1
                except Exception:
                    stats[f"{x1_col} Data Points"] = len(x1_data)
            else:
                stats.update({
                    f"{x1_col} Min": np.min(x1_data),
                    f"{x1_col} Max": np.max(x1_data),
                    f"{x1_col} Mean": np.mean(x1_data),
                    f"{x1_col} Median": np.median(x1_data),
                    f"{x1_col} Std Dev": np.std(x1_data)
                })
            
            # Y1 statistics
            stats.update({
                f"{y1_col} Min": np.min(y1_data),
                f"{y1_col} Max": np.max(y1_data),
                f"{y1_col} Mean": np.mean(y1_data),
                f"{y1_col} Median": np.median(y1_data),
                f"{y1_col} Std Dev": np.std(y1_data)
            })
        
        # Correlation statistics (only for non-timestamp data)
        if not self.is_timestamp_data(x_data) and self.trend_check.isChecked():
            corr_coef = np.corrcoef(x_data, y_data)[0, 1]
            stats["Correlation (r)"] = corr_coef
            
            slope, intercept = np.polyfit(x_data, y_data, 1)
            y_pred = slope * x_data + intercept
            ss_total = np.sum((y_data - np.mean(y_data)) ** 2)
            ss_residual = np.sum((y_data - y_pred) ** 2)
            r_squared = 1 - (ss_residual / ss_total) if ss_total != 0 else 0
            stats["R-squared"] = r_squared
            stats["Regression Slope"] = slope
            stats["Regression Intercept"] = intercept
        
        # Populate the table
        self.stats_table.setRowCount(len(stats))
        for row, (metric, value) in enumerate(stats.items()):
            self.stats_table.setItem(row, 0, QTableWidgetItem(metric))
            
            # Format numbers properly
            if isinstance(value, str):
                value_text = value
            elif isinstance(value, (int, np.integer)):
                if abs(value) >= 1000:
                    value_text = f"{value:,d}"
                else:
                    value_text = str(value)
            elif isinstance(value, (float, np.floating)):
                if abs(value) >= 1000 or abs(value) < 0.001:
                    value_text = f"{value:.2e}"
                else:
                    value_text = f"{value:.4f}"
            else:
                value_text = str(value)
                
            self.stats_table.setItem(row, 1, QTableWidgetItem(value_text))
        
        self.stats_table.resizeColumnsToContents()

    def export_custom_graph(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Plot", "", "PNG Files (*.png);;PDF Files (*.pdf)")
        if file_name:
            exporter = pg.exporters.ImageExporter(self.pg_widget.plotItem)
            exporter.params.param('width').setValue(800, blockSignal=exporter)
            exporter.export(file_name)
            QMessageBox.information(self, "Success", f"Plot exported successfully to:\n{file_name}")

    def export_custom_data(self):
        x_col = self.x_combo.currentText()
        y_col = self.y_combo.currentText()
        if self.data.empty or x_col not in self.data.columns or y_col not in self.data.columns:
            QMessageBox.warning(self, "Error", "No valid data to export.")
            return
        try:
            export_df = self.data[[x_col, y_col]].copy()
            export_df.dropna(inplace=True)
            file_name, _ = QFileDialog.getSaveFileName(self, "Export Data", "", "CSV Files (*.csv)")
            if file_name:
                export_df.to_csv(file_name, index=False)
                QMessageBox.information(self, "Success", f"Data exported successfully to {file_name}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export data: {e}")

    def handle_errors(self, message):
        QMessageBox.warning(self, "Error", message)

    def zoom_in(self):
        """Zoom in on the plot"""
        try:
            plot_item = self.pg_widget.getPlotItem()
            vb = plot_item.getViewBox()
            current_range = vb.viewRange()
            
            # Zoom in by 20% around the center
            x_range = current_range[0]
            y_range = current_range[1]
            
            x_center = (x_range[0] + x_range[1]) / 2
            y_center = (y_range[0] + y_range[1]) / 2
            
            x_width = (x_range[1] - x_range[0]) * 0.8
            y_width = (y_range[1] - y_range[0]) * 0.8
            
            new_x_range = [x_center - x_width/2, x_center + x_width/2]
            new_y_range = [y_center - y_width/2, y_center + y_width/2]
            
            vb.setRange(xRange=new_x_range, yRange=new_y_range)
        except Exception as e:
            self.handle_errors(f"Error zooming in: {str(e)}")

    def zoom_out(self):
        """Zoom out on the plot"""
        try:
            plot_item = self.pg_widget.getPlotItem()
            vb = plot_item.getViewBox()
            current_range = vb.viewRange()
            
            # Zoom out by 25% around the center
            x_range = current_range[0]
            y_range = current_range[1]
            
            x_center = (x_range[0] + x_range[1]) / 2
            y_center = (y_range[0] + y_range[1]) / 2
            
            x_width = (x_range[1] - x_range[0]) * 1.25
            y_width = (y_range[1] - y_range[0]) * 1.25
            
            new_x_range = [x_center - x_width/2, x_center + x_width/2]
            new_y_range = [y_center - y_width/2, y_center + y_width/2]
            
            vb.setRange(xRange=new_x_range, yRange=new_y_range)
        except Exception as e:
            self.handle_errors(f"Error zooming out: {str(e)}")

    def reset_view(self):
        """Reset the plot view to auto-range"""
        try:
            plot_item = self.pg_widget.getPlotItem()
            plot_item.enableAutoRange(axis='xy', enable=True)
            plot_item.autoRange()
        except Exception as e:
            self.handle_errors(f"Error resetting view: {str(e)}")

    def validate_data_columns(self):
        """Validate that selected columns exist and contain numeric data"""
        if self.data.empty:
            return False, "No data available"
        
        x_col = self.x_combo.currentText()
        y_col = self.y_combo.currentText()
        
        # Check if columns exist
        if x_col not in self.data.columns or y_col not in self.data.columns:
            return False, f"Columns '{x_col}' or '{y_col}' not found in data"
        
        # Check for numeric data
        try:
            pd.to_numeric(self.data[x_col], errors='coerce')
            pd.to_numeric(self.data[y_col], errors='coerce')
        except Exception:
            return False, f"Columns '{x_col}' or '{y_col}' do not contain numeric data"
        
        # Additional validation for four-axis mode
        if self.axis_mode == "four_axis":
            x1_col = self.x1_combo.currentText()
            y1_col = self.y1_combo.currentText()
            
            if x1_col not in self.data.columns or y1_col not in self.data.columns:
                return False, f"Secondary axis columns '{x1_col}' or '{y1_col}' not found"
            
            try:
                pd.to_numeric(self.data[x1_col], errors='coerce')
                pd.to_numeric(self.data[y1_col], errors='coerce')
            except Exception:
                return False, f"Secondary axis columns do not contain numeric data"
        
        return True, "Validation successful"

    def get_plot_title(self):
        """Generate appropriate plot title based on selected data"""
        x_col = self.x_combo.currentText()
        y_col = self.y_combo.currentText()
        
        if self.axis_mode == "four_axis":
            x1_col = self.x1_combo.currentText()
            y1_col = self.y1_combo.currentText()
            return f"{y_col} vs {x_col} & {y1_col} vs {x1_col}"
        else:
            return f"{y_col} vs {x_col}"

    def update_combo_boxes(self):
        """Update combo box items when data changes"""
        if not self.data.empty:
            columns = list(self.data.columns)
            for combo in [self.x_combo, self.y_combo, self.x1_combo, self.y1_combo]:
                current_text = combo.currentText()
                combo.clear()
                combo.addItems(columns)
                # Restore previous selection if it exists
                if current_text in columns:
                    combo.setCurrentText(current_text)

    def get_available_date_columns(self):
        """Get list of columns that could be date/time columns"""
        if self.data.empty:
            return []
        
        date_columns = []
        for col in self.data.columns:
            # Check if column is already datetime
            if self.data[col].dtype == 'datetime64[ns]':
                date_columns.append(col)
            # Check if column name suggests it's a date
            elif any(keyword in col.lower() for keyword in ['date', 'time', 'timestamp', 'datetime']):
                date_columns.append(col)
            # Check if column contains date-like strings
            elif self.data[col].dtype == 'object':
                sample_values = self.data[col].dropna().head(5)
                if len(sample_values) > 0:
                    try:
                        pd.to_datetime(sample_values.iloc[0])
                        date_columns.append(col)
                    except (ValueError, TypeError):
                        pass
        return date_columns
    
    def set_plot_theme(self, theme='light'):
        """Set the plot theme (light/dark)"""
        if theme == 'dark':
            pg.setConfigOption('background', 'k')
            pg.setConfigOption('foreground', 'w')
            self.pg_widget.setBackground('k')
        else:
            pg.setConfigOption('background', 'w')
            pg.setConfigOption('foreground', 'k')
            self.pg_widget.setBackground('w')

    def clear_plot(self):
        """Clear the current plot"""
        self.pg_widget.clear()
        self.trend_equation_label.setText("")
        self.stats_table.setRowCount(0)

    def auto_select_columns(self):
        if self.data.empty:
            return
        columns = list(self.data.columns)
        if len(columns) >= 2:
            # Try to find numeric columns
            numeric_cols = []
            for col in columns:
                try:
                    pd.to_numeric(self.data[col], errors='coerce')
                    numeric_cols.append(col)
                except Exception:
                    pass
            if len(numeric_cols) >= 2:
                self.x_combo.setCurrentText(numeric_cols[0])
                self.y_combo.setCurrentText(numeric_cols[1])
    
            if len(numeric_cols) >= 4:
                self.x1_combo.setCurrentText(numeric_cols[2])
                self.y1_combo.setCurrentText(numeric_cols[3])