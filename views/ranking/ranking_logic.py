"""
Ranking-specific plotting and calculation logic
Reuses visualization window utilities
"""
import pandas as pd
import numpy as np
from utils.plot_helpers import apply_legend, apply_grid, format_axes

def calculate_cumulative_data(data, turbine_id_col, timestamp_col, kpi_cols):
    """
    Calculate cumulative values for KPIs over time
    
    Args:
        data: DataFrame with turbine data
        turbine_id_col: Column name for turbine IDs
        timestamp_col: Column name for timestamps
        kpi_cols: List of KPI column names
    
    Returns:
        DataFrame with cumulative values
    """
    cumulative_results = []
    
    for turbine in data[turbine_id_col].unique():
        turbine_data = data[data[turbine_id_col] == turbine].sort_values(timestamp_col)
        
        for kpi in kpi_cols:
            cumulative = turbine_data[kpi].cumsum()
            for idx, (timestamp, cum_val) in enumerate(zip(turbine_data[timestamp_col], cumulative)):
                cumulative_results.append({
                    turbine_id_col: turbine,
                    'timestamp': timestamp,
                    'kpi': kpi,
                    'cumulative_value': cum_val,
                    'original_value': turbine_data[kpi].iloc[idx]
                })
    
    return pd.DataFrame(cumulative_results)


def plot_cumulative_comparison(ax, data, turbine_id_col, kpi_cols, show_legend=True):
    """
    Plot cumulative comparison across turbines
    
    Args:
        ax: Matplotlib axis
        data: Cumulative data from calculate_cumulative_data
        turbine_id_col: Column name for turbine IDs
        kpi_cols: List of KPI names
        show_legend: Whether to show legend
    """
    for turbine in data[turbine_id_col].unique():
        turbine_data = data[data[turbine_id_col] == turbine]
        for kpi in kpi_cols:
            kpi_data = turbine_data[turbine_data['kpi'] == kpi]
            ax.plot(kpi_data['timestamp'], kpi_data['cumulative_value'], 
                   label=f"{turbine} - {kpi}", linewidth=2)
    
    format_axes(ax, "Time", "", "Cumulative Performance Comparison")
    
    if show_legend:
        apply_legend(ax, True, fontsize='small')
    
    apply_grid(ax)
