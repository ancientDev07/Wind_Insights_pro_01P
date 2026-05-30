from PyQt5.QtCore import *
import pandas as pd
import numpy as np
import pyqtgraph as pg
from utils import column_cache_utility as ccu
from models import scada_utils as su
from utils.numeric_utils import to_numeric_safe
from utils.plot_helpers import insert_nans_at_day_boundaries, insert_nans_at_time_gaps
from utils import datetime_utils as dtu

class TSAnalysisEngine(QObject):
    analysis_finished = pyqtSignal(pd.DataFrame, dict)
    progress_updated = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.data_cache = {}
        
    def start_analysis(self, data):
        """Start time series analysis with real data"""
        try:
            if data.empty:
                raise ValueError("Data is empty")
            
            # Use column cache to find power and timestamp columns
            power_col = ccu.column_cache.get_column('power', data)
            timestamp_col = ccu.column_cache.get_column('timestamp', data)
            
            if not power_col or power_col not in data.columns:
                raise ValueError("No power column found in data")
            if not timestamp_col or timestamp_col not in data.columns:
                raise ValueError("No timestamp column found in data")
            
            # Ensure timestamp is in datetime format
            data[timestamp_col] = dtu.parse_and_normalize_timestamps(data[timestamp_col])
            if data[timestamp_col].isna().all():
                raise ValueError("Invalid timestamp data")
            
            # Store columns for reference
            self.data_cache = {
                'power_col': power_col,
                'timestamp_col': timestamp_col,
                'data': data
            }
            
            # Compute statistics
            statistics = self.compute_statistics(data)
            
            self.analysis_finished.emit(data, statistics)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    # Fix in compute_statistics method in time_series_logic.py
    def compute_statistics(self, data):
        stats = {}
        param_keys = ['power', 'wind_speed', 'rotor_speed', 'yaw_speed', 'nacelle_direction', 'voltage_phase_a', 'voltage_phase_b', 'voltage_phase_c', 'frequency']
        
        for param_key in param_keys:
            matched_columns = su.find_matching_columns(data, param_key)
            for col in matched_columns:
                if col in data.columns:
                    # series = pd.to_numeric(data[col], errors='coerce').dropna()
                    series = to_numeric_safe(data, col)
                    if not series.empty:
                        # Use consistent naming
                        clean_name = col.replace(' ', '_').lower()
                        stats[f'{clean_name}_mean'] = series.mean()
                        stats[f'{clean_name}_std'] = series.std()
                        stats[f'{clean_name}_min'] = series.min()
                        stats[f'{clean_name}_max'] = series.max()
        
        return stats

    def get_plot_data(self, data, col, param_key, power_type=None):
        """Extract plot data without rendering"""
        values = to_numeric_safe(data, col)
        if values.empty:
            return None
        
        timestamp_col = ccu.column_cache.get_column('timestamp', data)
        timestamps = data[timestamp_col][values.index]
        if timestamps.isna().all():
            return None
        
        df = pd.DataFrame({col: values, timestamp_col: timestamps})
        df = insert_nans_at_time_gaps(df, timestamp_col, max_gap_hours=1)
        df = insert_nans_at_day_boundaries(df, timestamp_col)
        
        values = df[col]
        timestamps = df[timestamp_col]
        
        # Return structured data
        return {
            'timestamps': timestamps.tolist(),
            'values': values.tolist(),
            'param_key': param_key,
            'power_type': power_type
        }

    # def get_power_data(self, data, col, power_type):
    #     """Extract power data with type filtering"""
    #     values = pd.to_numeric(data[col], errors='coerce').dropna()
    #     if values.empty:
    #         return None
        
    #     timestamp_col = ccu.column_cache.get_column('timestamp', data)
    #     timestamps = data[timestamp_col][values.index]
    #     if timestamps.isna().all():
    #         return None
        
    #     df = pd.DataFrame({col: values, timestamp_col: timestamps})
    #     df = insert_nans_at_time_gaps(df, timestamp_col, max_gap_hours=1)
    #     df = insert_nans_at_day_boundaries(df, timestamp_col)
        
    #     values = df[col]
    #     timestamps = df[timestamp_col]
        
    #     x_data = np.array([t.timestamp() if pd.notna(t) else np.nan for t in timestamps])
    #     y_data = values.values
        
    #     if power_type == 'active':
    #         mask = y_data >= 0
    #     elif power_type == 'reactive':
    #         mask = y_data < 0
    #     else:
    #         mask = np.ones(len(y_data), dtype=bool)
        
    #     return {
    #         'timestamps': timestamps[mask].tolist(),
    #         'values': y_data[mask].tolist(),
    #         'param_key': 'power',
    #         'power_type': power_type
    #     }

    # REPLACE get_power_data in time_series_logic.py

    def get_power_data(self, data, col, power_type):
        """Extract power data with gap NaNs preserved, then mask by power type."""
        # Use the same safe utility as get_plot_data
        values = to_numeric_safe(data, col)
        if values.empty:
            return None

        timestamp_col = ccu.column_cache.get_column('timestamp', data)
        timestamps = data[timestamp_col][values.index]
        if timestamps.isna().all():
            return None

        df = pd.DataFrame({col: values, timestamp_col: timestamps})
        df = insert_nans_at_time_gaps(df, timestamp_col, max_gap_hours=1)
        df = insert_nans_at_day_boundaries(df, timestamp_col)

        y = df[col].values.astype(float)

        # Apply active / reactive mask without dropping NaN rows (keeps gap structure)
        if power_type == 'active':
            y = np.where(y >= 0, y, np.nan)
        elif power_type == 'reactive':
            y = np.where(y < 0, y, np.nan)
        # 'full' → keep as-is

        return {
            'timestamps': df[timestamp_col].tolist(),
            'values':     y.tolist(),
            'param_key':  'power',
            'power_type': power_type,
        }