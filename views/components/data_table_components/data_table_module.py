import pandas as pd
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from utils.logger import logger
from views.components.data_table_components.data_CustomModel import PandasModel
from views.components.data_table_components.data_manipulation_Excel import DataManipulationToolbar

class DataTableModule(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.table = QTableView()
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._delayed_resize)
        # self.model = None #add model instance variable

        # Initialize model with empty DataFrame
        self.model = PandasModel(pd.DataFrame())  # Initialize with empty DataFrame
        self.table.setModel(self.model)

        # Enable column reordering
        self.table.horizontalHeader().setSectionsMovable(True)
        self.table.horizontalHeader().sectionMoved.connect(self._on_column_moved)

        # Add context menu for column management
        self.table.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.horizontalHeader().customContextMenuRequested.connect(self._show_column_menu)   

        self.data_toolbar_layout = QHBoxLayout()
        self.data_toolbar_widget = QWidget()
        self.data_toolbar_widget.setLayout(self.data_toolbar_layout)
        self.layout.addWidget(self.data_toolbar_widget)

        # Toolbar: Integrate the DataManipulationToolbar
        self.data_toolbar = DataManipulationToolbar(data_table_module=self, parent=self)
        self.data_toolbar_layout.addWidget(self.data_toolbar)
        self.data_toolbar.setMinimumHeight(40)
        self.data_toolbar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.data_toolbar.setStyleSheet("background-color: #34495E; color: #ECF0F1; font-size: 12px;")

        # Set table properties for better display
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)

        # self.layout.addWidget(self.search_bar)
        self.layout.addWidget(self.table)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def _on_column_moved(self, logical_index, old_visual_index, new_visual_index):
        """Handle column move event"""
        try:
            # Get current column order
            header = self.table.horizontalHeader()
            column_order = [header.logicalIndex(i) for i in range(header.count())]
            
            # Reorder columns in the DataFrame
            current_data = self.get_current_data()
            columns = current_data.columns.tolist()
            reordered_columns = [columns[i] for i in column_order]
            
            # Update the model with reordered columns
            new_data = current_data[reordered_columns]
            self.update_data(new_data)
            
            logger.info(f"Column moved from position {old_visual_index} to {new_visual_index}")
        except Exception as e:
            logger.error(f"Error reordering columns: {str(e)}")
    
    def _show_column_menu(self, pos):
        """Show context menu for column management"""
        menu = QMenu(self)
        
        # Reset column order action
        reset_action = QAction("Reset Column Order", self)
        reset_action.triggered.connect(self._reset_column_order)
        menu.addAction(reset_action)
        
        # Show/hide columns submenu
        column_menu = QMenu("Show/Hide Columns", self)
        header = self.table.horizontalHeader()
        
        for i in range(header.count()):
            column_name = self.model._data.columns[i]
            action = QAction(column_name, self)
            action.setCheckable(True)
            action.setChecked(not header.isSectionHidden(i))
            action.triggered.connect(lambda checked, col=i: self._toggle_column(col))
            column_menu.addAction(action)
        
        menu.addMenu(column_menu)
        menu.exec_(self.table.horizontalHeader().mapToGlobal(pos))

    def _toggle_column(self, column_index):
        """Toggle column visibility"""
        header = self.table.horizontalHeader()
        is_hidden = header.isSectionHidden(column_index)
        header.setSectionHidden(column_index, not is_hidden)
        
        column_name = self.model._data.columns[column_index]
        logger.info(f"Column '{column_name}' {'shown' if is_hidden else 'hidden'}")

    def _reset_column_order(self):
        """Reset columns to original order"""
        try:
            current_data = self.get_current_data()
            original_columns = self.model._data.columns.tolist()
            
            # Reset to original column order
            reordered_data = current_data[original_columns]
            self.update_data(reordered_data)
            
            # Reset column visibility
            header = self.table.horizontalHeader()
            for i in range(header.count()):
                header.setSectionHidden(i, False)
            
            logger.info("Column order and visibility reset to default")
        except Exception as e:
            logger.error(f"Error resetting column order: {str(e)}")

    def export_table(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Data", "", "CSV Files (*.csv);;Excel Files (*.xlsx)")
        if file_path:
            if file_path.endswith(".csv"):
                self.model._filtered_data.to_csv(file_path, index=False)
            elif file_path.endswith(".xlsx"):
                self.model._filtered_data.to_excel(file_path, index=False)
            logger.info(f"Data exported to {file_path}")
    
    # def update_data(self, data):
    #     """Update the table with new data """
    #     if isinstance(data, pd.DataFrame):
    #         self.model = PandasModel(data)
    #         self.table.setModel(self.model)
    #         self.table.resizeColumnsToContents()
    #         return True
    #     return False
    def update_data(self, data):
        if isinstance(data, pd.DataFrame):
            self.model = PandasModel(data)
            self.table.setModel(self.model)
            # Debounce resize - only resize after 200ms of no updates
            self._resize_timer.start(200)
            return True
        return False

    def _delayed_resize(self):
        """Resize columns after debounce delay"""
        self.table.resizeColumnsToContents()

    def update_data_table(self, data):
        """Alias for update_data for backward compatibility"""
        return self.update_data(data)
    
    def get_current_data(self):
        """Safely get the current data from the model"""
        if self.model is None:
            return pd.DataFrame()  # Return empty DataFrame if no model
        return getattr(self.model, '_data', pd.DataFrame())  # Return data or empty DataFrame