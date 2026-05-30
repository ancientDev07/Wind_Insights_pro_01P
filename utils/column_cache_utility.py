import pandas as pd
from typing import Dict, List, Optional, Any
from models.scada_utils import find_matching_columns

class ColumnCacheManager:
    """Centralized column cache management for SCADA data across multiple applications"""
    
    def __init__(self):
        self.cache = {}
        self.data_hash = None
        self.fuzzy_enabled = False
        self.fuzzy_threshold = 80
    
    def populate_cache(self, data: pd.DataFrame, force_refresh: bool = False) -> Dict[str, Optional[str]]:
        """Populate column cache for given dataframe"""
        if data.empty:
            return {}
        
        # Check if data changed
        current_hash = hash(tuple(data.columns))
        if not force_refresh and current_hash == self.data_hash and self.cache:
            return self.cache
        
        self.data_hash = current_hash
        self.cache.clear()
        
        # Standard parameters to cache
        parameters = [
            'timestamp', 'wind_speed', 'nacelle_direction', 'power', 'rotor_speed',
            'generator_speed', 'ambient_temp', 'nacelle_temp', 'gearbox_temp',
            'generator_temp', 'bearing_temp', 'cabinet_temp', 'motor_temp',
            'voltage', 'current', 'frequency', 'blade_angles', 'yaw_speed',
            'tower_acceleration', 'turbine_id', 'battery_voltage'
        ]
        
        for param in parameters:
            matched = find_matching_columns(data, param, self.fuzzy_enabled, self.fuzzy_threshold)
            self.cache[param] = matched[0] if matched else None
        
        return self.cache
    
    def get_column(self, param: str, data: pd.DataFrame = None) -> Optional[str]:
        """Get cached column for parameter"""
        if param not in self.cache and data is not None:
            self.populate_cache(data)
        return self.cache.get(param)
    
    def get_columns(self, params: List[str], data: pd.DataFrame = None) -> Dict[str, Optional[str]]:
        """Get multiple cached columns"""
        if not self.cache and data is not None:
            self.populate_cache(data)
        return {param: self.cache.get(param) for param in params}
    
    def validate_columns(self, data: pd.DataFrame, required_params: List[str]) -> Dict[str, Optional[str]]:
        """Validate required columns exist and return matched columns"""
        if not self.cache:
            self.populate_cache(data)
        
        matched = {}
        for param in required_params:
            col = self.cache.get(param)
            if col and col in data.columns:
                matched[param] = col
        return matched
    
    def get_numeric_data(self, data: pd.DataFrame, param: str) -> Optional[pd.Series]:
        """Get numeric data for parameter"""
        col = self.get_column(param, data)
        if not col or col not in data.columns:
            return None
        return pd.to_numeric(data[col], errors='coerce').dropna()
    
    def get_temperature_data(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Get all temperature data"""
        temp_params = ['generator_temp', 'bearing_temp', 'gearbox_temp', 
                      'ambient_temp', 'cabinet_temp', 'motor_temp', 'nacelle_temp']
        temp_data = {}
        for param in temp_params:
            numeric_data = self.get_numeric_data(data, param)
            if numeric_data is not None and not numeric_data.empty:
                temp_data[param] = numeric_data
        return temp_data
    
    def enable_fuzzy_matching(self, threshold: int = 80):
        """Enable fuzzy matching with threshold"""
        self.fuzzy_enabled = True
        self.fuzzy_threshold = threshold
        self.cache.clear()  # Force refresh on next populate
    
    def disable_fuzzy_matching(self):
        """Disable fuzzy matching"""
        self.fuzzy_enabled = False
        self.cache.clear()  # Force refresh on next populate
    
    def add_custom_mapping(self, param: str, column: str):
        """Add custom parameter mapping"""
        self.cache[param] = column
    
    def clear_cache(self):
        """Clear the cache"""
        self.cache.clear()
        self.data_hash = None
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        return {
            'cached_params': len(self.cache),
            'fuzzy_enabled': self.fuzzy_enabled,
            'fuzzy_threshold': self.fuzzy_threshold,
            'parameters': list(self.cache.keys())
        }

# Global instance for shared use
column_cache = ColumnCacheManager()

# Convenience functions
def get_cached_column(param: str, data: pd.DataFrame = None) -> Optional[str]:
    """Get cached column for parameter"""
    return column_cache.get_column(param, data)

def get_cached_columns(params: List[str], data: pd.DataFrame = None) -> Dict[str, Optional[str]]:
    """Get multiple cached columns"""
    return column_cache.get_columns(params, data)

def populate_column_cache(data: pd.DataFrame, force_refresh: bool = False) -> Dict[str, Optional[str]]:
    """Populate column cache"""
    return column_cache.populate_cache(data, force_refresh)

def validate_required_columns(data: pd.DataFrame, required_params: List[str]) -> Dict[str, Optional[str]]:
    """Validate required columns"""
    return column_cache.validate_columns(data, required_params)

def get_numeric_column_data(data: pd.DataFrame, param: str) -> Optional[pd.Series]:
    """Get numeric data for parameter"""
    return column_cache.get_numeric_data(data, param)
