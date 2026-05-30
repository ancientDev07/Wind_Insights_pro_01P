"""Centralized numeric data conversion utilities"""
import pandas as pd
import numpy as np

def to_numeric_safe(data, column=None, errors='coerce'):
    """
    Safely convert data to numeric, handling Series, DataFrame columns, or arrays
    
    Args:
        data: pd.Series, pd.DataFrame, or array-like
        column: Column name if data is DataFrame
        errors: How to handle errors ('coerce', 'raise', 'ignore')
    
    Returns:
        Numeric data with NaN for invalid values, or None if empty
    """
    if data is None:
        return None
    
    # Handle DataFrame column
    if isinstance(data, pd.DataFrame) and column:
        if column not in data.columns:
            return None
        data = data[column]
    
    # Convert to numeric
    numeric_data = pd.to_numeric(data, errors=errors).dropna()
    
    return numeric_data if not numeric_data.empty else None


def ensure_matching_lengths(*arrays):
    """
    Ensure all arrays have matching lengths by truncating to minimum
    
    Args:
        *arrays: Variable number of array-like objects
    
    Returns:
        List of arrays with matching lengths
    """
    if not arrays:
        return []
    min_length = min(len(arr) for arr in arrays)
    return [arr[:min_length] for arr in arrays]
