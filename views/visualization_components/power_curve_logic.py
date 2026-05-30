"""
Power Curve Logic Module
Contains reusable functions for power curve overlays and calculations
"""
import pandas as pd
import numpy as np
import models.scada_utils as su
import math
from utils.numeric_utils import to_numeric_safe
from utils.binning_utils import get_bins, bin_data

def calculate_air_density(z, T):
    """
    Calculate air density using atmospheric model
    
    Args:
        z: Height above sea level (m)
        T: Temperature (K)
    
    Returns:
        Air density (kg/m³)
    """
    ad = (352.9886 / T) * math.exp(-0.034163 * z / T)
    return ad


# def calculate_binned_curve(filtered_df, enable_iec_binning=False):
#     """
#     Calculate binned power curve statistics
    
#     Args:
#         filtered_df: DataFrame with wind_speed and power columns
#         enable_iec_binning: If True, use 0.5 m/s bins, else 1.0 m/s
    
#     Returns:
#         DataFrame with binned statistics (wind_speed, power, std_dev, min, max, count)
#     """
#     ws_cols = su.find_matching_columns(filtered_df, 'wind_speed')
#     power_cols = su.find_matching_columns(filtered_df, 'power')
    
#     if not ws_cols or not power_cols:
#         return pd.DataFrame()
    
#     df = pd.DataFrame({
#         'wind_speed': to_numeric_safe(filtered_df, ws_cols[0]),
#         'power': to_numeric_safe(filtered_df, power_cols[0])
#     }).dropna()
    
#     if df.empty:
#         return pd.DataFrame()
    
#     bins = get_bins(df['wind_speed'].max(), enable_iec_binning)
#     df['bin'] = bin_data(df, 'wind_speed', bins)
    
#     bin_stats = df.groupby('bin', observed=True).agg({
#         'power': ['mean', 'std', 'min', 'max', 'count'],
#         'wind_speed': 'mean'
#     }).reset_index()
    
#     bin_stats.columns = ['bin', 'power_mean', 'power_std', 'power_min', 'power_max', 'count', 'wind_speed']
    
#     return bin_stats.dropna()

def calculate_binned_curve(filtered_df, enable_iec_binning=False, wind_speed_col=None, power_col=None):
    """
    Calculate binned power curve statistics - matches plot_binned_power_curve logic
    
    Args:
        filtered_df: DataFrame with wind_speed and power columns
        enable_iec_binning: If True, use 0.5 m/s bins, else 1.0 m/s
        wind_speed_col: Optional explicit wind speed column name
        power_col: Optional explicit power column name
    
    Returns:
        DataFrame with binned statistics (wind_speed, power_mean, power_std, power_min, power_max, count)
    """
    # Auto-detect columns if not provided
    if wind_speed_col is None:
        ws_cols = su.find_matching_columns(filtered_df, 'wind_speed')
        if not ws_cols:
            return pd.DataFrame()
        wind_speed_col = ws_cols[0]
    
    if power_col is None:
        power_cols = su.find_matching_columns(filtered_df, 'power')
        if not power_cols:
            return pd.DataFrame()
        power_col = power_cols[0]
    
    # Convert to numeric
    speed_data = to_numeric_safe(filtered_df, wind_speed_col)
    power_data = to_numeric_safe(filtered_df, power_col)
    
    df = pd.DataFrame({'wind_speed': speed_data, 'power': power_data})
    
    if df.empty:
        return pd.DataFrame()
    
    # Binning logic - matches plot_binned_power_curve exactly
    bin_width = 0.5 if enable_iec_binning else 1.0
    bins = get_bins(df['wind_speed'].max(), enable_iec_binning, bin_width)
    df['bin'] = bin_data(df, 'wind_speed', bins)
    
    # Aggregate statistics - matches plot_binned_power_curve
    stats = df.groupby('bin', observed=False).agg({
        'power': ['mean', 'std', 'count', 'min', 'max'],
        'wind_speed': ['count']
    }).dropna()
    
    stats.columns = ['mean_power', 'std_power', 'count_power', 'min_power', 'max_power', 'count_speed']
    
    # Filter valid bins (minimum 5 points) - matches plot_binned_power_curve
    valid_stats = stats[stats['count_power'] >= 5]
    
    if valid_stats.empty or len(valid_stats) < 2:
        return pd.DataFrame()
    
    # Calculate bin midpoints for plotting
    bin_midpoints = [(interval.left + interval.right) / 2 for interval in valid_stats.index]
    
    result = pd.DataFrame({
        'wind_speed': bin_midpoints,
        'power_mean': valid_stats['mean_power'].values,
        'power_std': valid_stats['std_power'].values,
        'power_min': valid_stats['min_power'].values,
        'power_max': valid_stats['max_power'].values,
        'count': valid_stats['count_power'].values
    })
    
    return result

def overlay_binned_curve(ax, filtered_df, enable_iec_binning=False, show_legend=True):
    """
    Overlay binned power curve on existing axis
    
    Args:
        ax: Matplotlib axis object
        filtered_df: DataFrame with wind_speed and power columns
        enable_iec_binning: If True, use 0.5 m/s bins
        show_legend: If True, update legend
    """
    bin_stats = calculate_binned_curve(filtered_df, enable_iec_binning)
    
    if not bin_stats.empty:
        ax.plot(bin_stats['wind_speed'], bin_stats['power_mean'], 
               color='black', linewidth=2.5, marker='o', markersize=6,
               label='Binned Curve', zorder=10)
        
        if show_legend:
            ax.legend()


def overlay_average_line(ax, filtered_df, enable_iec_binning=False, show_legend=True):
    """
    Overlay average power line on existing axis
    
    Args:
        ax: Matplotlib axis object
        filtered_df: DataFrame with wind_speed and power columns
        enable_iec_binning: If True, use 0.5 m/s bins
        show_legend: If True, update legend
    """
    bin_stats = calculate_binned_curve(filtered_df, enable_iec_binning)
    
    if not bin_stats.empty:
        ax.plot(bin_stats['wind_speed'], bin_stats['power_mean'], 
               color='purple', linewidth=2, linestyle='--',
               label='Average Line', zorder=10)
        
        if show_legend:
            ax.legend()