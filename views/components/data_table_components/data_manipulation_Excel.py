import pandas as pd
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from utils.logger import logger

class DataManipulationToolbar(QToolBar):
    def __init__(self, data_table_module, parent=None):
        """
        Initialize the Data Manipulation Toolbar
        
        Args:
            data_table_module (DataTableModule): Reference to the data table module
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.data_table_module = data_table_module
        self.original_data = None
        
        # Create actions for the toolbar
        self._create_actions()
    
    def _create_actions(self):
        """Create toolbar actions for data manipulation"""
        actions = [
            ("Group By", "group_by.png", self.show_group_by_dialog),
            ("Group By Date", "group_by_date.png", self.group_by_date),
            ("Pivot", "pivot.png", self.show_pivot_dialog),
            ("Aggregate", "aggregate.png", self.show_aggregate_dialog),
            ("Filter", "filter.png", self.show_filter_dialog),
            ("Sort", "sort.png", self.show_sort_dialog),
            ("Reset", "reset.png", self.reset_data)
        ]
        
        for text, icon_name, handler in actions:
            action = QAction(QIcon(f"resources/icons/{icon_name}"), text, self)
            action.triggered.connect(handler)
            self.addAction(action)
    
    #Group by date function:
    def group_by_date(self):
        """Group data by date while maintaining time intervals"""
        try:
            data = self._get_current_data()
            if data is None or data.empty:
                return

            if 'Date' not in data.columns:
                logger.error("Date column not found in the data")
                return
            
            # Create copy of data
            working_data = data.copy()
            
            # Sort by Date and Time
            working_data = working_data.sort_values(['Date', 'Time'])
            
            # Group by date only
            grouped_data = []
            current_date = None
            
            # Iterate through sorted data
           # Iterate through sorted data
            for date, group in working_data.groupby('Date'):
                # Add date header when date changes
                header = pd.DataFrame([{col: "===" if col != 'Date' else f"Date: {date}"
                                      for col in working_data.columns}])
                grouped_data.append(header)
                
                # Add the data rows with empty date column
                group_data = group.copy()
                group_data['Date'] = ''  # Clear the date column in data rows
                grouped_data.append(group_data)
            
            # Combine all data
            result_data = pd.concat(grouped_data, ignore_index=True)
            
            # Update table
            self._update_table(result_data)
            logger.info("Successfully grouped data by date")
            
        except Exception as e:
            logger.error(f"Date grouping operation failed: {str(e)}")

    def _get_current_data(self):
        """Safely get current data from the data table module"""
        if self.data_table_module is None:
            return pd.DataFrame()
        return self.data_table_module.get_current_data()
    
    def _update_table(self, data):
        """
        Update the data table with new data
        
        Args:
            data (pandas.DataFrame): Data to update the table with
        """
        # Store original data if not already stored
        if self.original_data is None:
            self.original_data = self._get_current_data().copy()
        
        # Update table
        self.data_table_module.update_data_table(data)
    
    def reset_data(self):
        """Reset to original data"""
        if self.original_data is not None:
            self.data_table_module.update_data_table(self.original_data)
            self.original_data = None
            logger.info("Data reset to original state")
    
    def show_group_by_dialog(self):
        """Show dialog for grouping data"""
        data = self._get_current_data()
        if data is None:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Group By")
        layout = QFormLayout(dialog)
        
        # Column selection
        column_combo = QComboBox()
        column_combo.addItems(data.columns)
        layout.addRow("Group By Column:", column_combo)
        
        # Aggregation method selection
        agg_combo = QComboBox()
        agg_methods = ['mean', 'sum', 'count', 'min', 'max', 'first', 'last']
        agg_combo.addItems(agg_methods)
        layout.addRow("Aggregation Method:", agg_combo)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                column = column_combo.currentText()
                agg_method = agg_combo.currentText()
                
                # Perform grouping
                grouped_data = data.groupby(column).agg({column: agg_method}).reset_index()
                
                # Update table
                self._update_table(grouped_data)
                logger.info(f"Grouped data by {column} with {agg_method} aggregation")
            except Exception as e:
                logger.error(f"Group By operation failed: {str(e)}")
    def show_pivot_dialog(self):
        """Show dialog for creating a pivot table"""
        data = self._get_current_data()
        if data is None:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Pivot Table")
        layout = QFormLayout(dialog)
        
        # Column selections
        columns = data.columns
        
        # Index column selection
        index_combo = QComboBox()
        index_combo.addItems(columns)
        layout.addRow("Index Column:", index_combo)
        
        # Columns column selection
        columns_combo = QComboBox()
        columns_combo.addItems(columns)
        layout.addRow("Columns Column:", columns_combo)
        
        # Values column selection
        values_combo = QComboBox()
        values_combo.addItems(columns)
        layout.addRow("Values Column:", values_combo)
        
        # Aggregation method selection
        agg_combo = QComboBox()
        agg_methods = ['mean', 'sum', 'count', 'min', 'max']
        agg_combo.addItems(agg_methods)
        layout.addRow("Aggregation Method:", agg_combo)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                # Get selected columns and aggregation method
                index = index_combo.currentText()
                columns_col = columns_combo.currentText()
                values_col = values_combo.currentText()
                agg_method = agg_combo.currentText()
                
                # Perform pivot table creation
                pivoted_data = pd.pivot_table(
                    data, 
                    values=values_col, 
                    index=index, 
                    columns=columns_col, 
                    aggfunc=agg_method
                ).reset_index()
                
                # Update table
                self._update_table(pivoted_data)
                logger.info(f"Created pivot table with {index}, {columns_col}, {values_col}")
            except Exception as e:
                logger.error(f"Pivot operation failed: {str(e)}")
    
    def show_aggregate_dialog(self):
        """Show dialog for aggregating data"""
        data = self._get_current_data()
        if data is None:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Aggregate")
        layout = QFormLayout(dialog)
        
        # Select only numeric columns
        columns = data.select_dtypes(include=[np.number]).columns
        
        # Column selection
        column_combo = QComboBox()
        column_combo.addItems(columns)
        layout.addRow("Column:", column_combo)
        
        # Aggregation methods
        agg_methods_dict = {
            'Mean': 'mean', 
            'Sum': 'sum', 
            'Count': 'count', 
            'Min': 'min', 
            'Max': 'max', 
            'Median': 'median', 
            'Standard Deviation': 'std'
        }
        
        # Aggregation method selection
        agg_combo = QComboBox()
        agg_combo.addItems(list(agg_methods_dict.keys()))
        layout.addRow("Aggregation Method:", agg_combo)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                column = column_combo.currentText()
                agg_method = agg_methods_dict[agg_combo.currentText()]
                
                # Perform aggregation
                result = getattr(data[column], agg_method)()
                
                # Create a single-row DataFrame to display the result
                result_df = pd.DataFrame({
                    'Metric': [f'{agg_combo.currentText()} of {column}'],
                    'Value': [result]
                })
                
                # Update table
                self._update_table(result_df)
                logger.info(f"Aggregated {column} with {agg_method}")
            except Exception as e:
                logger.error(f"Aggregation operation failed: {str(e)}")
    
    def show_filter_dialog(self):
        """Show dialog for filtering data"""
        data = self._get_current_data()
        if data is None:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Filter Data")
        layout = QFormLayout(dialog)
        
        # Column selection
        column_combo = QComboBox()
        column_combo.addItems(data.columns)
        layout.addRow("Column:", column_combo)
        
        # Condition selection
        condition_combo = QComboBox()
        conditions = ['==', '!=', '>', '<', '>=', '<=', 'contains']
        condition_combo.addItems(conditions)
        layout.addRow("Condition:", condition_combo)
        
        # Value input
        value_input = QLineEdit()
        layout.addRow("Value:", value_input)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                column = column_combo.currentText()
                condition = condition_combo.currentText()
                value = value_input.text()
                
                # Convert value to appropriate type
                try:
                    value = float(value)
                except ValueError:
                    pass  # Keep as string if not convertible to float
                
                # Perform filtering
                if condition == 'contains':
                    filtered_data = data[data[column].astype(str).str.contains(str(value), case=False)]
                else:
                    filtered_data = data.query(f"{column} {condition} {repr(value)}")
                
                # Update table
                self._update_table(filtered_data)
                logger.info(f"Filtered data: {column} {condition} {value}")
            except Exception as e:
                logger.error(f"Filter operation failed: {str(e)}")
    
    def show_sort_dialog(self):
        """Show dialog for sorting data"""
        data = self._get_current_data()
        if data is None:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Sort Data")
        layout = QFormLayout(dialog)
        
        # Column selection
        column_combo = QComboBox()
        column_combo.addItems(data.columns)
        layout.addRow("Column:", column_combo)
        
        # Sort order selection
        order_combo = QComboBox()
        order_combo.addItems(['Ascending', 'Descending'])
        layout.addRow("Order:", order_combo)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                column = column_combo.currentText()
                ascending = order_combo.currentText() == 'Ascending'
                
                # Perform sorting
                sorted_data = data.sort_values(
                    by=column, 
                    ascending=ascending
                )
                
                # Update table
                self._update_table(sorted_data)
                logger.info(f"Sorted data by {column}, {'ascending' if ascending else 'descending'}")
            except Exception as e:
                logger.error(f"Sort operation failed: {str(e)}")