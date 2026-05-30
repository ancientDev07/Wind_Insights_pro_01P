"""Centralized binning utilities for wind data analysis"""
import numpy as np
import pandas as pd


def create_iec_bins(max_value, start=0.25, bin_width=0.5):
    """
    Create IEC standard bins (0.5 m/s bins starting from 0.25 m/s)
    
    Args:
        max_value: Maximum value for binning
        start: Starting value (default 0.25)
        bin_width: Bin width (default 0.5)
    
    Returns:
        numpy array of bin edges
    """
    return np.arange(start, max_value + bin_width, bin_width)


def create_standard_bins(max_value, bin_width=1.0, start=0):
    """
    Create standard bins with custom width
    
    Args:
        max_value: Maximum value for binning
        bin_width: Bin width (default 1.0)
        start: Starting value (default 0)
    
    Returns:
        numpy array of bin edges
    """
    return np.arange(start, max_value + bin_width, bin_width)


def get_bins(max_value, enable_iec=False, bin_width=1.0):
    """
    Get appropriate bins based on configuration
    
    Args:
        max_value: Maximum value for binning
        enable_iec: If True, use IEC standard bins
        bin_width: Custom bin width (used if enable_iec=False)
    
    Returns:
        numpy array of bin edges
    """
    if enable_iec:
        return create_iec_bins(max_value)
    return create_standard_bins(max_value, bin_width)


def bin_data(df, column, bins, labels=None):
    """
    Bin data in DataFrame column
    
    Args:
        df: pandas DataFrame
        column: Column name to bin
        bins: Bin edges
        labels: Optional bin labels
    
    Returns:
        Series with binned data
    """
    return pd.cut(df[column], bins=bins, labels=labels, include_lowest=True)
