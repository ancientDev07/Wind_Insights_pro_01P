from PyQt5.QtCore import *
import pandas as pd

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data.reset_index(drop=True)  # Reset index to avoid issues
        self._string_cache = {}

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._data.columns)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        # Bounds check
        if index.row() >= len(self._data) or index.column() >= len(self._data.columns):
            return None
            
        if role == Qt.DisplayRole:
            cache_key = (index.row(), index.column())
            if cache_key not in self._string_cache:
                value = self._data.iloc[index.row(), index.column()]
                self._string_cache[cache_key] = str(value)
            return self._string_cache[cache_key]
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
            
        if orientation == Qt.Horizontal:
            if section < len(self._data.columns):
                return str(self._data.columns[section])
        elif orientation == Qt.Vertical:
            if section < len(self._data):
                return str(section)  # Use section number instead of index
        
        return None
    
    def filter_data(self, query):
        if query:
            string_data = self._data.astype(str)
            mask = string_data.apply(lambda col: col.str.contains(query, na=False)).any(axis=1)
            self._filtered_data = self._data[mask]
        else:
            self._filtered_data = self._data
        self._string_cache.clear()  # Clear cache on filter
        self.layoutChanged.emit()

    def filter_data_by_column(self, column, value):
        if column in self._data.columns:
            string_data = self._data[column].astype(str)
            mask = string_data.str.contains(value, na=False, case=False)
            self._filtered_data = self._data[mask]
        self._string_cache.clear()  # Clear cache on filter
        self.layoutChanged.emit()
