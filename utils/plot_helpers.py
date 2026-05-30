"""Centralized plotting helper utilities"""
import matplotlib.pyplot as plt
import pandas as pd


def apply_legend(ax, show_legend, **kwargs):
    """
    Apply legend to axis if enabled
    
    Args:
        ax: Matplotlib axis object
        show_legend: Boolean to show/hide legend
        **kwargs: Additional legend parameters
    """
    if show_legend:
        default_params = {'bbox_to_anchor': (1.05, 1), 'loc': 'upper left', 'fontsize': 'small'}
        default_params.update(kwargs)
        ax.legend(**default_params)


def apply_grid(ax, show_grid=True, **kwargs):
    """
    Apply grid to axis
    
    Args:
        ax: Matplotlib axis object
        show_grid: Boolean to show/hide grid
        **kwargs: Additional grid parameters
    """
    if show_grid:
        default_params = {'alpha': 0.3, 'linestyle': '--'}
        default_params.update(kwargs)
        ax.grid(True, **default_params)


def format_axes(ax, xlabel=None, ylabel=None, title=None, fontweight='bold'):
    """
    Format axis labels and title
    
    Args:
        ax: Matplotlib axis object
        xlabel: X-axis label
        ylabel: Y-axis label
        title: Plot title
        fontweight: Font weight for labels
    """
    if xlabel:
        ax.set_xlabel(xlabel, fontweight=fontweight)
    if ylabel:
        ax.set_ylabel(ylabel, fontweight=fontweight)
    if title:
        ax.set_title(title, fontweight=fontweight)


def handle_layout(fig, has_legend=False):
    """
    Handle figure layout with proper spacing
    
    Args:
        fig: Matplotlib figure object
        has_legend: Boolean indicating if legend is present
    """
    try:
        if has_legend:
            fig.tight_layout(rect=[0, 0, 0.82, 1], pad=1.0)
        else:
            fig.tight_layout(pad=1.0)
    except Exception:
        if has_legend:
            fig.subplots_adjust(bottom=0.15, right=0.75, top=0.9, left=0.1)
        else:
            fig.subplots_adjust(bottom=0.15, right=0.95, top=0.9, left=0.1)



# ADD THIS FUNCTION:

def filter_data_by_wind_sector(data, direction_col, sector_id, num_sectors=16):
    """
    Filter data for a specific directional sector.
    
    Args:
        data: DataFrame with wind direction column
        direction_col: Column name containing wind direction (0-360°)
        sector_id: Sector index (0 to num_sectors-1)
        num_sectors: Total number of sectors (8, 12, 16, 24, or 36)
    
    Returns:
        Filtered DataFrame for the sector
    """
    if direction_col not in data.columns:
        return data.copy()
    
    sector_width = 360 / num_sectors
    min_dir = (sector_id * sector_width - sector_width / 2) % 360
    max_dir = min_dir + sector_width
    
    dir_data = pd.to_numeric(data[direction_col], errors='coerce')
    
    # Handle wraparound (e.g., N = 350-10°)
    if max_dir > 360:
        mask = (dir_data >= min_dir) | (dir_data < (max_dir - 360))
    else:
        mask = (dir_data >= min_dir) & (dir_data < max_dir)
    
    return data[mask].copy()

def add_kpi_label_inside(ax, kpi_name, position='top-left'):
    """
    Add KPI label inside graph area instead of Y-axis
    
    Args:
        ax: Matplotlib axis object
        kpi_name: Name of the KPI to display
        position: Position in graph ('top-left', 'top-right', 'top-center')
    """
    # Remove Y-axis label
    ax.set_ylabel("")
    
    # Position mapping
    positions = {
        'top-left': (0.02, 0.98),
        'top-right': (0.98, 0.98),
        'top-center': (0.5, 0.98)
    }
    
    x, y = positions.get(position, (0.02, 0.98))
    ha = 'left' if 'left' in position else ('right' if 'right' in position else 'center')
    
    ax.text(x, y, kpi_name, transform=ax.transAxes,
            fontsize=11, fontweight='bold', verticalalignment='top',
            horizontalalignment=ha,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                     alpha=0.85, edgecolor='#3498DB', linewidth=1.5))


def create_cumulative_series(data, value_col, sort_col=None):
    """
    Create cumulative series from data
    
    Args:
        data: DataFrame or Series
        value_col: Column to calculate cumulative sum
        sort_col: Optional column to sort by before cumsum
    
    Returns:
        Series with cumulative values
    """
    if sort_col and sort_col in data.columns:
        data = data.sort_values(sort_col)
    
    return data[value_col].cumsum()


"""
Add this function to utils/plot_helpers.py
"""

import numpy as np
import pandas as pd


def insert_nans_at_time_gaps(df, time_col, group_col=None, max_gap_hours=24, value_cols=None):
    """
    Insert NaN values at time gaps to prevent matplotlib from connecting discontinuous segments.
    
    This is useful when plotting time series data with gaps (e.g., turbine downtime, missing data)
    where you don't want lines connecting the last point before a gap to the first point after.
    
    Args:
        df: DataFrame with time series data
        time_col: Column name containing datetime values
        group_col: Optional column to group by (e.g., turbine_id) before detecting gaps
        max_gap_hours: Maximum time gap in hours before inserting NaN (default: 24)
        value_cols: List of columns to set to NaN at gaps. If None, all numeric columns except time_col
    
    Returns:
        DataFrame with NaN rows inserted at gaps
    
    Example:
        # For single turbine
        df_clean = insert_nans_at_time_gaps(df, 'timestamp', max_gap_hours=12)
        
        # For multiple turbines
        df_clean = insert_nans_at_time_gaps(df, 'timestamp', group_col='turbine_id', max_gap_hours=24)
        ax.plot(df_clean['timestamp'], df_clean['power'])  # Lines won't connect across gaps
    """
    if time_col not in df.columns:
        return df.copy()
    
    # Ensure time column is datetime
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col])
    
    # Determine which columns to set to NaN
    if value_cols is None:
        value_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if time_col in value_cols:
            value_cols.remove(time_col)
    
    gap_threshold = pd.Timedelta(hours=max_gap_hours)
    
    if group_col and group_col in df.columns:
        # Process each group separately
        result_dfs = []
        for group_val in df[group_col].unique():
            group_df = df[df[group_col] == group_val].sort_values(time_col).copy()
            group_df = _insert_nans_single_series(group_df, time_col, value_cols, gap_threshold, group_col)
            result_dfs.append(group_df)
        return pd.concat(result_dfs, ignore_index=True).sort_values([group_col, time_col])
    else:
        # Process entire dataframe as single series
        df = df.sort_values(time_col).copy()
        return _insert_nans_single_series(df, time_col, value_cols, gap_threshold)


def _insert_nans_single_series(df, time_col, value_cols, gap_threshold, group_col=None):
    """Helper function to insert NaNs in a single time series"""
    if len(df) < 2:
        return df
    
    # Calculate time differences
    time_diff = df[time_col].diff()
    
    # Find indices where gaps exceed threshold
    gap_mask = time_diff > gap_threshold
    gap_indices = df[gap_mask].index.tolist()
    
    if not gap_indices:
        return df
    
    # Create NaN rows at gap positions
    nan_rows = []
    for idx in gap_indices:
        nan_row = df.loc[idx].copy()
        # Set value columns to NaN
        for col in value_cols:
            if col in nan_row.index:
                nan_row[col] = np.nan
        # Keep time and group columns intact
        nan_rows.append(nan_row)
    
    # Concatenate and sort
    if nan_rows:
        df = pd.concat([df, pd.DataFrame(nan_rows)], ignore_index=True)
        df = df.sort_values(time_col).reset_index(drop=True)
    
    return df


def detect_time_gaps(df, time_col, group_col=None, max_gap_hours=24):
    """
    Detect time gaps in data without modifying the dataframe.
    
    Args:
        df: DataFrame with time series data
        time_col: Column name containing datetime values
        group_col: Optional column to group by
        max_gap_hours: Maximum time gap in hours to consider as a gap
    
    Returns:
        DataFrame with gap information (start_time, end_time, gap_duration_hours, group)
    """
    if time_col not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col])
    gap_threshold = pd.Timedelta(hours=max_gap_hours)
    
    gaps = []
    
    if group_col and group_col in df.columns:
        for group_val in df[group_col].unique():
            group_df = df[df[group_col] == group_val].sort_values(time_col)
            group_gaps = _detect_gaps_single_series(group_df, time_col, gap_threshold)
            for gap in group_gaps:
                gap[group_col] = group_val
                gaps.append(gap)
    else:
        df = df.sort_values(time_col)
        gaps = _detect_gaps_single_series(df, time_col, gap_threshold)
    
    return pd.DataFrame(gaps)


def _detect_gaps_single_series(df, time_col, gap_threshold):
    """Helper to detect gaps in single series"""
    if len(df) < 2:
        return []
    
    gaps = []
    time_diff = df[time_col].diff()
    gap_mask = time_diff > gap_threshold
    
    for idx in df[gap_mask].index:
        prev_idx = df.index[df.index.get_loc(idx) - 1]
        gaps.append({
            'start_time': df.loc[prev_idx, time_col],
            'end_time': df.loc[idx, time_col],
            'gap_duration_hours': (df.loc[idx, time_col] - df.loc[prev_idx, time_col]).total_seconds() / 3600
        })
    
    return gaps

def insert_nans_at_day_boundaries(df, time_col, value_cols=None):
    """
    Insert NaN values at day boundaries to prevent connecting lines across daily cycles.
    
    This ensures that time-series plots don't show continuous lines from the end of one day
    to the start of the next day, which can be misleading for cyclical data.
    
    Args:
        df: DataFrame with time series data
        time_col: Column name containing datetime values
        value_cols: List of columns to set to NaN at day boundaries. If None, all numeric columns except time_col
    
    Returns:
        DataFrame with NaN rows inserted at day boundaries
    """
    if time_col not in df.columns or df.empty:
        return df.copy()
    
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col])
    
    # Determine which columns to set to NaN
    if value_cols is None:
        value_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if time_col in value_cols:
            value_cols.remove(time_col)
    
    # Sort by time
    df = df.sort_values(time_col).reset_index(drop=True)
    
    # Find day boundaries (where date changes)
    df['date'] = df[time_col].dt.date
    date_changes = df['date'] != df['date'].shift(1)
    boundary_indices = df[date_changes].index.tolist()[1:]  # Skip first (no previous day)
    
    if not boundary_indices:
        df = df.drop(columns=['date'])
        return df
    
    # Create NaN rows at day boundaries
    nan_rows = []
    for idx in boundary_indices:
        # Insert NaN at the boundary (before the new day starts)
        nan_row = df.loc[idx].copy()
        nan_row[time_col] = df.loc[idx, time_col].replace(hour=0, minute=0, second=0, microsecond=0)
        for col in value_cols:
            if col in nan_row.index:
                nan_row[col] = np.nan
        nan_rows.append(nan_row)
    
    # Add NaN rows and sort
    if nan_rows:
        df = pd.concat([df, pd.DataFrame(nan_rows)], ignore_index=True)
        df = df.sort_values(time_col).reset_index(drop=True)
    
    df = df.drop(columns=['date'])
    return df
