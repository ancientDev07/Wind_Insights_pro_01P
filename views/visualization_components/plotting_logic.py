from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableWidgetItem, QDockWidget, QTableWidget
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from windrose import WindroseAxes
from functools import wraps
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

# new
from utils.numeric_utils import ensure_matching_lengths, to_numeric_safe
from utils.error_handler import handle_error_simple
from utils.plot_helpers import apply_legend, apply_grid, format_axes, handle_layout, add_kpi_label_inside, insert_nans_at_time_gaps
from utils.binning_utils import get_bins, bin_data
from utils.air_density_utils import (get_selected_air_densities, calculate_air_density_curves,
                                      update_air_density_table, plot_air_density_curves)


def plotting_decorator(required_params=None):
    def decorator(func):
        @wraps(func)
        def wrapper(vw, column_cache, *args, **kwargs):
            filtered_data = vw.get_filtered_data()
            if filtered_data.empty:
                vw.handle_errors("No data available for the selected time range.")
                return False
            if required_params and not validate_required_columns(filtered_data, required_params, vw, column_cache):
                return False
            vw.figure.clear() 
            result = func(vw, filtered_data, column_cache, *args, **kwargs)
            if hasattr(vw, "show_grid") and vw.show_grid.isChecked():
                for ax in vw.figure.get_axes():
                    ax.grid(True)
            vw.canvas.draw()
            return result
        return wrapper
    return decorator

def validate_required_columns(data, required_params, vw, column_cache):
    missing = []
    matched_columns = {}
    for param in required_params:
        col = column_cache.get(param)
        if not col or col not in data.columns:
            missing.append(param)
        else:
            matched_columns[param] = col
    if missing:
        vw.handle_errors(f"Missing required parameters: {', '.join(missing)}")
        return False
    return matched_columns


def get_numeric_data(data, column, fallback=None):
    result = to_numeric_safe(data, column)
    return result if result is not None else fallback


# windrose section
def _get_windrose_bin_edges(vw, max_speed, speed_bins):
    """Extract bin edge calculation logic"""
    if hasattr(vw, "enable_iec_binning") and vw.enable_iec_binning.isChecked():
        return np.arange(0, max_speed + 0.5, 0.5)
    return np.linspace(0, max_speed, speed_bins + 1)

def _get_windrose_sectors(vw):
    """Extract sector configuration logic"""
    if hasattr(vw, "windrose_sectors_12") and vw.windrose_sectors_12.isChecked():
        return 12
    elif hasattr(vw, "windrose_sectors_16") and vw.windrose_sectors_16.isChecked():
        return 16
    elif hasattr(vw, "windrose_sectors_24") and vw.windrose_sectors_24.isChecked():
        return 24
    elif hasattr(vw, "windrose_sectors_36") and vw.windrose_sectors_36.isChecked():
        return 36
    return 8

def get_compass_labels(num_sectors):
    """Return compass direction labels for wind rose sectors."""
    if num_sectors == 8:
        return ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    elif num_sectors == 12:
        return ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW']
    elif num_sectors == 16:
        return ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    else:
        # Fallback to degrees for unsupported sector counts
        return [f"{int(deg)}°" for deg in np.linspace(0, 360, num_sectors, endpoint=False)]

def _add_compass_overlay(vw):
    """Extract compass image overlay logic"""
    try:
        import os
        compass_path = os.path.join('resources', 'direction', 'compass-1.png')
        if os.path.exists(compass_path):
            compass_img = plt.imread(compass_path)
            imagebox = OffsetImage(compass_img, zoom=0.1)
            ab = AnnotationBbox(imagebox, (0.9, 0.9), 
                            xycoords='figure fraction', 
                            frameon=False)
            vw.figure.add_artist(ab)
    except Exception as e:
        print(f"Could not add compass image: {e}")


def _validate_windrose_data(speed_data, dir_data):
    """Validate wind rose data and return cleaned arrays"""
    if speed_data is None or dir_data is None:
        return None, None, "No valid wind speed or direction data available."
    
    valid_mask = ~(speed_data.isna() | dir_data.isna())
    speed_clean = speed_data[valid_mask].values
    dir_clean = dir_data[valid_mask].values
    
    if len(speed_clean) == 0:
        return None, None, "No valid wind speed or direction data available."
    
    max_speed = np.max(speed_clean)
    if max_speed == 0:
        return None, None, "No valid wind speed data for binning."
    
    return speed_clean, dir_clean, None

def _make_windrose_interactive(ax_windrose, vw):
    """Enable pick events on windrose bars for sector clicking"""
    try:
        # Get all bar collections from windrose
        for container in ax_windrose.containers:
            for bar in container:
                bar.set_picker(True)
                bar.set_pickradius(5)
    except Exception as e:
        print(f"Could not enable windrose interactivity: {e}")



@plotting_decorator(required_params=["wind_speed", "nacelle_direction"])
def plot_wind_rose(vw, filtered_data, column_cache):
    import logging
    columns = validate_required_columns(filtered_data, ["wind_speed", "nacelle_direction"], vw, column_cache)
    if not columns:
        return False
    
    wind_speed_col = columns["wind_speed"]
    wind_dir_col = columns["nacelle_direction"]
    
    # Vectorized data processing
    speed_data = pd.to_numeric(filtered_data[wind_speed_col], errors='coerce')
    dir_data = pd.to_numeric(filtered_data[wind_dir_col], errors='coerce')
    
    # Validate and clean data
    speed_clean, dir_clean, error_msg = _validate_windrose_data(speed_data, dir_data)
    if error_msg:
        vw.handle_errors(error_msg)
        return False
    
    max_speed = np.max(speed_clean)
    
    # Get configuration
    speed_bins = getattr(vw, 'speed_bins', None)
    speed_bins = speed_bins.value() if speed_bins else 6
    bin_edges = _get_windrose_bin_edges(vw, max_speed, speed_bins)
    direction_bins = _get_windrose_sectors(vw)
    
    # Get color scheme
    color_scheme_name = getattr(vw, 'color_scheme', None)
    color_scheme_name = color_scheme_name.currentText() if color_scheme_name else "viridis"
    cmap = plt.get_cmap(color_scheme_name)
    
    # Create windrose
    ax = WindroseAxes.from_ax(fig=vw.figure)
    ax.bar(dir_clean, speed_clean, bins=bin_edges, nsector=direction_bins, cmap=cmap, normed=True)
    
    # Set orientation
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    
    # Set tick labels
    tick_angles = np.linspace(0, 2 * np.pi, direction_bins + 1)[:-1]
    tick_degrees = np.linspace(0, 360, direction_bins, endpoint=False)
    ax.set_xticks(tick_angles)
    # ax.set_xticklabels([f"{int(deg)}°" for deg in tick_degrees])
    ax.set_xticklabels(get_compass_labels(direction_bins))
    
    # Add compass overlay
    _add_compass_overlay(vw)
    
    # Add legend if requested
    if hasattr(vw, "show_legend") and vw.show_legend.isChecked():
        ax.set_title("WindRose")
        ax.set_legend(loc='upper left', bbox_to_anchor=(1.1, 1))
    
    # NEW: Enable sector clicking if this is a comparison window
    if hasattr(vw, 'selected_sector'):
        _make_windrose_interactive(ax, vw)
    
    return True

# wind speed distribution
@plotting_decorator(required_params=["wind_speed"])
def plot_wind_speed_distribution(vw, filtered_data, column_cache):
    columns = validate_required_columns(filtered_data, ["wind_speed"], vw, column_cache)
    if not columns:
        return False
    wind_speed_col = columns["wind_speed"]
    speed_data = get_numeric_data(filtered_data, wind_speed_col)
    if speed_data is None or len(speed_data) == 0:
        # vw.handle_errors("No valid wind speed data available.")
        # NEW:
        handle_error_simple(ValueError("No valid wind speed data"), 
                           "No valid wind speed data available.")
        return False
    bin_width = vw.bin_width.value() if hasattr(vw, "bin_width") else 1
    enable_iec = hasattr(vw, "enable_iec_binning") and vw.enable_iec_binning.isChecked()
    bins = get_bins(speed_data.max(), enable_iec, bin_width)
    num_bins = len(bins) - 1
    ax = vw.figure.add_subplot(111)
    sns.histplot(data=speed_data, bins=num_bins, stat='density', ax=ax)
    shape, loc, scale = stats.weibull_min.fit(speed_data, loc=0)
    x = np.linspace(0, speed_data.max(), 100)
    weibull_pdf = stats.weibull_min.pdf(x, shape, loc, scale)
    ax.plot(x, weibull_pdf, 'r-', label=f'Weibull fit (k={shape:.2f}, A={scale:.2f})')
    format_axes(ax, "Wind Speed (m/s)", "Density", "Wind Speed Distribution")
    # Add KPI label inside graph
    add_kpi_label_inside(ax, "Density", position='top-right')
    show_legend = hasattr(vw, "show_legend") and vw.show_legend.isChecked()
    apply_legend(ax, show_legend)
    return True

# @plotting_decorator(required_params=["wind_speed"])
# def plot_turbulence_intensity(vw, filtered_data, column_cache):
#     columns = validate_required_columns(filtered_data, ["wind_speed"], vw, column_cache)
#     if not columns:
#         return False
    
#     wind_speed_col = columns["wind_speed"]
    
#     # Check if we have wind speed standard deviation data for proper TI calculation
#     wind_speed_std_col = column_cache.get("wind_speed_std")
#     if wind_speed_std_col and wind_speed_std_col in filtered_data.columns:
#         # VECTORIZE: Process all data points simultaneously
#         speed_data = pd.to_numeric(filtered_data[wind_speed_col], errors='coerce')
#         speed_std_data = pd.to_numeric(filtered_data[wind_speed_std_col], errors='coerce')
        
#         # VECTORIZE: Remove invalid data in one operation
#         valid_mask = (speed_data > 0) & (speed_std_data >= 0) & ~speed_data.isna() & ~speed_std_data.isna()
#         speed_mean = speed_data[valid_mask]
#         speed_std = speed_std_data[valid_mask]
        
#         if len(speed_mean) == 0:
#             # vw.handle_errors("No valid data points for TI calculation.")
#             handle_error_simple(ValueError("No valid TI data"), 
#                    "No valid data points for TI calculation.")
#             return False
        
#         # VECTORIZE: Calculate TI for all points at once
#         ti_values = speed_std / speed_mean
#         wind_speeds = speed_mean
        
#     else:
#         # VECTORIZE: Process wind speed data
#         speed_data = pd.to_numeric(filtered_data[wind_speed_col], errors='coerce')
#         speed_data = speed_data.dropna()
        
#         if speed_data.empty:
#             vw.handle_errors("No valid wind speed data available.")
#             return False
        
#         df = pd.DataFrame({'wind_speed': speed_data})

#         enable_iec = hasattr(vw, "enable_iec_binning") and vw.enable_iec_binning.isChecked()
#         bins = get_bins(df['wind_speed'].max(), enable_iec, bin_width=0.5)
#         df['bin'] = bin_data(df, 'wind_speed', bins)
#         bin_stats = df.groupby('bin', observed=True).agg({
#             'wind_speed': ['mean', 'std', 'count']
#         }).dropna()

#         bin_stats.columns = ['mean_speed', 'std_speed', 'count']
        
#         # Filter bins with sufficient data points (minimum 10 points per IEC)
#         valid_bins = bin_stats[bin_stats['count'] >= 10]
        
#         if len(valid_bins) == 0:
#             # vw.handle_errors("Insufficient data points in bins for TI calculation.")
#             handle_error_simple(ValueError("Insufficient TI data"), 
#                    "Insufficient data points in bins for TI calculation.")
#             return False
        
#         # VECTORIZE: Calculate TI for all bins at once
#         ti_values = valid_bins['std_speed'] / valid_bins['mean_speed']
#         wind_speeds = valid_bins['mean_speed']
    
#     # IEC 61400-1 turbulence categories with correct I_ref values from Table 1
#     iec_categories = {
#         "A+": {"I_ref": 0.18, "label": "IEC 61400-1 Category A+ (Very High)", "color": "darkred"},
#         "A": {"I_ref": 0.16, "label": "IEC 61400-1 Category A (High)", "color": "red"},
#         "B": {"I_ref": 0.14, "label": "IEC 61400-1 Category B (Medium)", "color": "orange"}, 
#         "C": {"I_ref": 0.12, "label": "IEC 61400-1 Category C (Low)", "color": "green"}
#     }
    
#     # VECTORIZE: Calculate statistics for all data at once
#     ti_90th = np.percentile(ti_values, 90)
#     ti_mean = np.mean(ti_values)
#     ti_max = np.max(ti_values)
    
#     # Create the plot
#     ax = vw.figure.add_subplot(111)
    
#     # VECTORIZE: Sort data by wind speed for continuous line plotting
#     sorted_indices = np.argsort(wind_speeds)
#     sorted_wind_speeds = wind_speeds.iloc[sorted_indices] if hasattr(wind_speeds, 'iloc') else wind_speeds[sorted_indices]
#     sorted_ti_values = ti_values.iloc[sorted_indices] if hasattr(ti_values, 'iloc') else ti_values[sorted_indices]
    
#     # Plot TI data points connected with continuous line
#     ax.plot(sorted_wind_speeds, sorted_ti_values, 'b-', linewidth=2, 
#             marker='o', markersize=4, alpha=0.7, label='Turbulence Intensity')
    
#     # ADD THIS RIGHT AFTER IT:
#     if hasattr(vw, 'show_original_values') and vw.show_original_values.isChecked():
#         ax.scatter(wind_speeds, ti_values, c='brown', alpha=0.3, s=15, label='Raw TI Data', zorder=1)
    
#     # Calculate and display IEC NTM formula curves using correct formula
#     if len(wind_speeds) > 0:
#         ws_range = np.linspace(max(1, wind_speeds.min()), min(25, wind_speeds.max()), 100)
        
#         # IEC 61400-1 NTM formula: σ₁ = I_ref(0.75*V_hub + b) where b = 5.6 m/s
#         # Turbulence Intensity = σ₁ / V_hub = I_ref(0.75*V_hub + 5.6) / V_hub
#         # Simplified: TI = I_ref * (0.75 + 5.6/V_hub)
#         b = 5.6  # m/s as per IEC standard
        
#         for category, props in iec_categories.items():
#             I_ref = props["I_ref"]
            
#             # Apply NTM formula: TI = I_ref * (0.75 + 5.6/V_hub)
#             # For very low wind speeds, limit the calculation to avoid unrealistic values
#             ws_calc = np.maximum(ws_range, 1.0)  # Minimum 1 m/s to avoid division issues
#             iec_curve = I_ref * (0.75 + b / ws_calc)
            
#             # Plot only the NTM curve (no horizontal reference lines)
#             ax.plot(ws_range, iec_curve, '--', color=props["color"], 
#                     alpha=0.8, linewidth=2, 
#                     label=f'IEC {category} NTM curve')
    
#     # Formatting
#     format_axes(ax, "Wind Speed (m/s)", "Turbulence Intensity (-)", 
#                 "Turbulence Intensity vs Wind Speed\\n(IEC 61400-1 NTM Standard)")
#     ax.set_ylim(0, min(1.0, max(ti_max * 1.1, 0.5)))  # Cap at reasonable TI values
#     apply_grid(ax)
    
#     # Show legend and statistics only if legend is enabled
#     if hasattr(vw, "show_legend") and vw.show_legend.isChecked():
#         # Show legend
#         ax.legend(loc='upper left', fontsize='small',framealpha=0.9)
        
#         # Add text box with statistics and IEC compliance assessment
#         stats_text = f'Data Statistics:\\n'
#         stats_text += f'Points: {len(ti_values)}\\n'
#         stats_text += f'Mean TI: {ti_mean:.3f}\\n'
#         stats_text += f'90th %ile: {ti_90th:.3f}\\n'
#         stats_text += f'Max TI: {ti_max:.3f}\\n'
        
#         # Determine IEC category compliance based on 90th percentile
#         compliance_category = None
#         for category in ["C", "B", "A", "A+"]:
#             if ti_90th <= iec_categories[category]["I_ref"]:
#                 compliance_category = category
#                 break
        
#         if compliance_category:
#             stats_text += f'\\nSuggested IEC Category: {compliance_category}'
#         else:
#             stats_text += f'\\nExceeds IEC Category A+'
        
#         ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
#                 verticalalignment='top', bbox=dict(boxstyle='round', 
#                 facecolor='wheat', alpha=0.8), fontsize='small')
        
#     vw.figure.tight_layout(rect=[0, 0, 0.85, 1])
#     return True

@plotting_decorator(required_params=["wind_speed"])
def plot_turbulence_intensity(vw, filtered_data, column_cache):
    columns = validate_required_columns(filtered_data, ["wind_speed"], vw, column_cache)
    if not columns:
        return False
    
    wind_speed_col = columns["wind_speed"]
    raw_wind_speeds = None
    raw_ti_values = None
    
    # Check if we have wind speed standard deviation data
    wind_speed_std_col = column_cache.get("wind_speed_std")
    if wind_speed_std_col and wind_speed_std_col in filtered_data.columns:
        speed_data = pd.to_numeric(filtered_data[wind_speed_col], errors='coerce')
        speed_std_data = pd.to_numeric(filtered_data[wind_speed_std_col], errors='coerce')
        
        valid_mask = (speed_data > 0) & (speed_std_data >= 0) & ~speed_data.isna() & ~speed_std_data.isna()
        speed_mean = speed_data[valid_mask]
        speed_std = speed_std_data[valid_mask]
        
        if len(speed_mean) == 0:
            handle_error_simple(ValueError("No valid TI data"), "No valid data points for TI calculation.")
            return False
        
        raw_wind_speeds = speed_mean
        raw_ti_values = speed_std / speed_mean
        ti_values = raw_ti_values
        wind_speeds = raw_wind_speeds
    else:
        speed_data = pd.to_numeric(filtered_data[wind_speed_col], errors='coerce').dropna()
        if speed_data.empty:
            vw.handle_errors("No valid wind speed data available.")
            return False
        
        df = pd.DataFrame({'wind_speed': speed_data})
        enable_iec = hasattr(vw, "enable_iec_binning") and vw.enable_iec_binning.isChecked()
        bins = get_bins(df['wind_speed'].max(), enable_iec, bin_width=0.5)
        df['bin'] = bin_data(df, 'wind_speed', bins)
        
        # Calculate raw TI for scatter
        raw_ws_list, raw_ti_list = [], []
        for bin_val in df['bin'].unique():
            if pd.isna(bin_val):
                continue
            bin_points = df[df['bin'] == bin_val]['wind_speed']
            if len(bin_points) > 1:
                ws_mean, ws_std = bin_points.mean(), bin_points.std()
                for ws in bin_points:
                    raw_ws_list.append(ws)
                    raw_ti_list.append(ws_std / ws_mean if ws_mean > 0 else 0)
        
        if raw_ws_list:
            raw_wind_speeds = pd.Series(raw_ws_list)
            raw_ti_values = pd.Series(raw_ti_list)
        
        bin_stats = df.groupby('bin', observed=True).agg({'wind_speed': ['mean', 'std', 'count']}).dropna()
        bin_stats.columns = ['mean_speed', 'std_speed', 'count']
        valid_bins = bin_stats[bin_stats['count'] >= 10]
        
        if len(valid_bins) == 0:
            handle_error_simple(ValueError("Insufficient TI data"), "Insufficient data points in bins for TI calculation.")
            return False
        
        ti_values = valid_bins['std_speed'] / valid_bins['mean_speed']
        wind_speeds = valid_bins['mean_speed']
    
    iec_categories = {
        "A+": {"I_ref": 0.18, "color": "darkred"},
        "A": {"I_ref": 0.16, "color": "red"},
        "B": {"I_ref": 0.14, "color": "orange"}, 
        "C": {"I_ref": 0.12, "color": "green"}
    }
    
    ti_90th = np.percentile(ti_values, 90)
    ti_mean = np.mean(ti_values)
    ti_max = np.max(ti_values)
    
    ax = vw.figure.add_subplot(111)
    
    # Plot raw data first (behind)
    if hasattr(vw, 'show_original_values') and vw.show_original_values.isChecked() and raw_wind_speeds is not None:
        ax.scatter(raw_wind_speeds, raw_ti_values, c='lightcoral', alpha=0.4, s=8, label='Raw TI Data', zorder=1)
    
    # Plot binned TI line
    sorted_indices = np.argsort(wind_speeds)
    sorted_ws = wind_speeds.iloc[sorted_indices] if hasattr(wind_speeds, 'iloc') else wind_speeds[sorted_indices]
    sorted_ti = ti_values.iloc[sorted_indices] if hasattr(ti_values, 'iloc') else ti_values[sorted_indices]
    ax.plot(sorted_ws, sorted_ti, 'b-', linewidth=2, marker='o', markersize=4, alpha=0.7, label='Turbulence Intensity', zorder=5)
    
    # IEC curves
    if len(wind_speeds) > 0:
        ws_range = np.linspace(max(1, wind_speeds.min()), min(25, wind_speeds.max()), 100)
        b = 5.6
        for category, props in iec_categories.items():
            I_ref = props["I_ref"]
            ws_calc = np.maximum(ws_range, 1.0)
            iec_curve = I_ref * (0.75 + b / ws_calc)
            ax.plot(ws_range, iec_curve, '--', color=props["color"], alpha=0.8, linewidth=2, label=f'IEC {category} NTM curve')
    
    # format_axes(ax, "Wind Speed (m/s)", "Turbulence Intensity (-)", "Turbulence Intensity vs Wind Speed\n(IEC 61400-1 NTM Standard)")
    # ax.set_ylim(0, min(1.0, max(ti_max * 1.1, 0.5)))
    # apply_grid(ax)
    format_axes(ax, "Wind Speed (m/s)", "", 
                    "Turbulence Intensity vs Wind Speed\n(IEC 61400-1 NTM Standard)")
        
        # Add KPI label inside graph
    add_kpi_label_inside(ax, "Turbulence Intensity (-)", position='top-right')
        
    ax.set_ylim(0, min(1.0, max(ti_max * 1.1, 0.5)))
    apply_grid(ax)

    
    if hasattr(vw, "show_legend") and vw.show_legend.isChecked():
        ax.legend(loc='upper right', fontsize='small', framealpha=0.9)
        
        stats_text = f'Data Statistics:\nPoints: {len(ti_values)}\nMean TI: {ti_mean:.3f}\n90th %ile: {ti_90th:.3f}\nMax TI: {ti_max:.3f}\n'
        compliance_category = None
        for category in ["C", "B", "A", "A+"]:
            if ti_90th <= iec_categories[category]["I_ref"]:
                compliance_category = category
                break
        
        stats_text += f'\nSuggested IEC Category: {compliance_category}' if compliance_category else '\nExceeds IEC Category A+'
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, verticalalignment='top', 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8), fontsize='small')
    
    vw.figure.tight_layout()
    return True





@plotting_decorator(required_params=["wind_speed"])
def plot_power_curve(vw, filtered_data, column_cache):
    columns = validate_required_columns(filtered_data, ["wind_speed"], vw, column_cache)
    if not columns:
        return False
    
    ws_col = columns["wind_speed"]
    if not hasattr(vw, "client_power_data") or vw.client_power_data is None:
        vw.upload_client_power_curve()
    if not hasattr(vw, "client_power_interp"):
        return False

    # Use client data range for plotting
    min_ws = vw.client_power_data['wind_speed'].min()
    max_ws = vw.client_power_data['wind_speed'].max()
    x_plot = np.linspace(min_ws, max_ws, 200)
    y_std_plot = vw.client_power_interp(x_plot)

    ax = vw.figure.add_subplot(111)
    ax.plot(x_plot, y_std_plot, 'r-', label='Client-Provided Power Curve (Interpolated)')
    ax.scatter(vw.client_power_data['wind_speed'], vw.client_power_data['power'], color='blue', label='Original Data Points')

    # Add blue dots at every 0.5 m/s interval on the interpolated curve
    interval = 0.5
    x_dots = np.arange(np.ceil(min_ws / interval) * interval, max_ws + interval, interval)
    y_dots = vw.client_power_interp(x_dots)
    ax.plot(x_dots, y_dots, 'bo', markersize=5, label='Interpolated Points (0.5 m/s interval)')

    format_axes(ax, "Wind Speed (m/s)", "Power (kW)", "Client-Provided Power Curve")
    apply_legend(ax, vw.show_legend.isChecked())
    return True

@plotting_decorator(required_params=["wind_speed", "power"])
def plot_actual_power_curve(vw, filtered_data, column_cache):
    cols = validate_required_columns(filtered_data, ["wind_speed", "power"], vw, column_cache)
    if not cols:
        return False
    ws_col, p_col = cols["wind_speed"], cols["power"]
    spd = get_numeric_data(filtered_data, ws_col)
    pwr = get_numeric_data(filtered_data, p_col)
    
    # Create a DataFrame to ensure proper indexing
    df = pd.DataFrame({'wind_speed': spd, 'power': pwr})
    
    # Apply wind speed threshold filter if set
    if hasattr(vw, 'current_wind_speed_threshold') and vw.current_wind_speed_threshold is not None:
        print(f"Applying wind speed threshold filter in actual power curve: {vw.current_wind_speed_threshold} m/s")
        print(f"Number of points before filter: {len(df)}")
        df = df[df['wind_speed'] >= vw.current_wind_speed_threshold]
        print(f"Number of points after filter: {len(df)}")
    
    if df.empty:
        # vw.handle_errors("No valid wind speed/power data after filtering.")
        handle_error_simple(ValueError("No valid power curve data"), 
                   "No valid wind speed/power data after filtering.")
        return False
    
    ax = vw.figure.add_subplot(111)
    
    # Multicolor scatter plot based on power values
    scatter = ax.scatter(df['wind_speed'], df['power'], 
                        c=df['power'], cmap='viridis', 
                        s=20, alpha=0.6, label="Actual Power Data")
    
    # Add colorbar
    cbar = vw.figure.colorbar(scatter, ax=ax)
    cbar.set_label('Power (kW)', rotation=270, labelpad=15)
    
    # Standard power curve overlay (red color for client curve)
    if vw.show_standard_power_curve.isChecked() and hasattr(vw, "client_power_interp") and vw.client_power_data is not None:
        min_ws_client = vw.client_power_data['wind_speed'].min()
        max_ws_client = vw.client_power_data['wind_speed'].max()
        speeds_client = np.linspace(min_ws_client, max_ws_client, 200)
        std_curve = vw.client_power_interp(speeds_client)
        ax.plot(speeds_client, std_curve, linestyle='--', linewidth=2, color='red', label="Client-Provided Curve")
    
    format_axes(ax, "Wind Speed (m/s)", "Power (kW)", "Actual Power Curve")
    
    # Adjust x-axis to start from the wind speed threshold if set
    if hasattr(vw, 'current_wind_speed_threshold') and vw.current_wind_speed_threshold is not None:
        ax.set_xlim(left=vw.current_wind_speed_threshold)
    
    # Show legend if enabled
    show_legend = hasattr(vw, "show_legend") and vw.show_legend.isChecked()
    apply_legend(ax, show_legend)
    handle_layout(vw.figure, show_legend)
    vw.canvas.draw()
    return True


@plotting_decorator(required_params=["wind_speed", "power"])
def plot_binned_power_curve(vw, filtered_data, column_cache):
    columns = validate_required_columns(filtered_data, ["wind_speed", "power"], vw, column_cache)
    if not columns:
        return False
    wind_speed_col = columns["wind_speed"]
    power_col = columns["power"]
    speed_data = get_numeric_data(filtered_data, wind_speed_col)
    power_data = get_numeric_data(filtered_data, power_col)
    
    df = pd.DataFrame({'wind_speed': speed_data, 'power': power_data})
    
    if df.empty:
        # vw.handle_errors("No valid data after filtering for binned power curve.")
        handle_error_simple(ValueError("No valid binned data"), 
                   "No valid data after filtering for binned power curve.")
        return False

    # Set up binning for the main power curve (unaffected by threshold)
    bin_width = vw.bin_width.value() if hasattr(vw, "bin_width") else 1
    enable_iec = hasattr(vw, "enable_iec_binning") and vw.enable_iec_binning.isChecked()
    bins = get_bins(df['wind_speed'].max(), enable_iec, bin_width)
    df['bin'] = bin_data(df, 'wind_speed', bins)
    stats = df.groupby('bin', observed=False).agg({
        'power': ['mean', 'std', 'count', 'min', 'max'],
        'wind_speed': ['count']
    }).dropna()
    stats.columns = ['mean_power', 'std_power', 'count_power', 'min_power', 'max_power', 'count_speed']
    valid_stats = stats[stats['count_power'] >= 5]
    if valid_stats.empty or len(valid_stats) < 2:
        # vw.handle_errors("Insufficient valid bins for binned power curve.")
        # NEW:
        handle_error_simple(ValueError("Insufficient bins"), 
                        "Insufficient valid bins for binned power curve.")
        return False
    bin_ranges = [f"({interval.left:.2f}, {interval.right:.2f}]" for interval in valid_stats.index]
    bin_midpoints = [(interval.left + interval.right) / 2 for interval in valid_stats.index]
    mean_power = valid_stats['mean_power'].values
    std_power = valid_stats['std_power'].values
    count = valid_stats['count_power'].values
    min_power = valid_stats['min_power'].values
    max_power = valid_stats['max_power'].values

    # Only check for client power curve data if it's actually needed
    client_curve_needed = (hasattr(vw, "show_standard_power_curve") and vw.show_standard_power_curve.isChecked()) or \
                         (hasattr(vw, 'enable_percentage_bands') and vw.enable_percentage_bands.isChecked())

    if client_curve_needed and (not hasattr(vw, "client_power_interp") or vw.client_power_interp is None or 
                               not hasattr(vw, "client_power_data") or vw.client_power_data is None):
        # vw.handle_errors("Client power curve data not available. Please upload client power curve first.")
        handle_error_simple(ValueError("Missing client power curve"), 
                   "Client power curve data not available. Please upload client power curve first.")
        return False

    # Get client power curve data for percentage bands
    enable_percentage = hasattr(vw, 'enable_percentage_bands') and vw.enable_percentage_bands.isChecked()
    try:
        percentage = float(vw.percentage_input.text()) if enable_percentage else 0.0
    except ValueError:
        # vw.handle_errors("Invalid percentage value entered.")
        handle_error_simple(ValueError("Invalid percentage"), 
                   "Invalid percentage value entered.")
        percentage = 0.0

    # Use client power curve data for percentage bands
    if enable_percentage and client_curve_needed:
        # Get client power curve data
        client_ws = vw.client_power_data['wind_speed'].values
        client_power = vw.client_power_data['power'].values
        
        # Apply threshold filter if needed
        threshold = 4.0
        mask = client_ws >= threshold
        filtered_ws = client_ws[mask]
        filtered_power = client_power[mask]
        
        # Calculate percentage bands
        plus_percentage_power = filtered_power * (1 + percentage / 100)
        minus_percentage_power = filtered_power * (1 - percentage / 100)
        
        # Cap the power at the maximum client power
        power_cap = vw.client_power_data['power'].max()
        capped_plus = np.minimum(plus_percentage_power, power_cap)

    ax = vw.figure.add_subplot(111)
    # Plot the original binned data
    ax.plot(bin_midpoints, mean_power, color='#1E90FF', label='Binned Power', linewidth=2)

    # Plot percentage bands using client power curve data
    if enable_percentage and client_curve_needed:
        if vw.show_plus_percentage.isChecked():
            ax.plot(filtered_ws, capped_plus, color='darkgreen', linestyle='--', label=f'+{percentage}% Power', linewidth=2.5)
        if vw.show_minus_percentage.isChecked():
            ax.plot(filtered_ws, minus_percentage_power, color='darkred', linestyle='--', label=f'-{percentage}% Power', linewidth=2.5)

    # Plot client power curve
    if hasattr(vw, "show_standard_power_curve") and vw.show_standard_power_curve.isChecked() and client_curve_needed:
        ax.plot(vw.client_power_data['wind_speed'], vw.client_power_data['power'], 
                'black', linestyle='--', label='Client-Provided Power Curve', linewidth=2)

    # Plot standard deviation error bars if requested
    if hasattr(vw, "show_std_dev") and vw.show_std_dev.isChecked():
        for i in range(len(bin_midpoints)):
            ax.plot([bin_midpoints[i], bin_midpoints[i]], [mean_power[i] - std_power[i], mean_power[i] + std_power[i]], color='black', linewidth=1.8)
            cap_width = 0.05
            ax.plot([bin_midpoints[i] - cap_width, bin_midpoints[i] + cap_width], [mean_power[i] - std_power[i], mean_power[i] - std_power[i]], color='black', linewidth=1.8)
            ax.plot([bin_midpoints[i] - cap_width, bin_midpoints[i] + cap_width], [mean_power[i], mean_power[i]], color='black', linewidth=1.8)
            ax.plot([bin_midpoints[i] - cap_width, bin_midpoints[i] + cap_width], [mean_power[i] + std_power[i], mean_power[i] + std_power[i]], color='black', linewidth=1.8)

    # Plot original data points if requested
    if hasattr(vw, "show_original_values") and vw.show_original_values.isChecked():
        scatter = ax.scatter(df['wind_speed'], df['power'], c=df['wind_speed'], cmap='viridis', alpha=0.6, s=20,
                             label='Original Values', edgecolor='white')

    # Set labels and title
    title = f"Binned Power Curve{' - ' + vw.turbine_id if hasattr(vw, 'turbine_id') and vw.turbine_id else ''}"
    format_axes(ax, "Wind Speed (m/s)", "Power (kW)", title)
    apply_grid(ax)
    
    # Show legend if requested
    show_legend = hasattr(vw, "show_legend") and vw.show_legend.isChecked()
    if show_legend:
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10, frameon=True, edgecolor='black')
    
    # Proper layout handling with legend consideration
    handle_layout(vw.figure, show_legend)

    # Update bin table if available
    if hasattr(vw, 'bin_table') and hasattr(vw, 'bin_table_dock'):
        vw.bin_table.setColumnCount(6)
        vw.bin_table.setHorizontalHeaderLabels(["Bin Range", "Mean Power", "Std Dev", "Min Value", "Max Value", "Count"])
        vw.bin_table.setRowCount(len(bin_ranges))
        for row, (rng, mid, mean, std, min_val, max_val, cnt) in enumerate(zip(bin_ranges, bin_midpoints, mean_power, std_power, min_power, max_power, count)):
            rounded_mean = round(mean)
            vw.bin_table.setItem(row, 0, QTableWidgetItem(rng))
            vw.bin_table.setItem(row, 1, QTableWidgetItem(f"{rounded_mean}"))
            vw.bin_table.setItem(row, 2, QTableWidgetItem(f"{std:.2f}"))
            vw.bin_table.setItem(row, 3, QTableWidgetItem(f"{min_val:.2f}"))
            vw.bin_table.setItem(row, 4, QTableWidgetItem(f"{max_val:.2f}"))
            vw.bin_table.setItem(row, 5, QTableWidgetItem(str(cnt)))
        vw.bin_table.resizeColumnsToContents()

    # Update percentage bands table if enabled
    if enable_percentage and client_curve_needed and hasattr(vw, 'percentage_bands_table'):
        if not hasattr(vw, 'percentage_bands_dock'):
            from PyQt5.QtWidgets import QDockWidget
            from PyQt5.QtCore import Qt
            vw.percentage_bands_dock = QDockWidget("Percentage Bands", vw)
            vw.percentage_bands_dock.setWidget(vw.percentage_bands_table)
            if hasattr(vw, 'bin_table_dock'):
                vw.addDockWidget(vw.bin_table_dock.widget().parent().dockWidgetArea(), vw.percentage_bands_dock)
                vw.tabifyDockWidget(vw.bin_table_dock, vw.percentage_bands_dock)
            else:
                vw.addDockWidget(Qt.RightDockWidgetArea, vw.percentage_bands_dock)

        # Create table entries using client power curve data
        vw.percentage_bands_table.setColumnCount(3)
        vw.percentage_bands_table.setHorizontalHeaderLabels(["Wind Speed", f"+{percentage:.1f}% Power", f"-{percentage:.1f}% Power"])
        vw.percentage_bands_table.setRowCount(len(filtered_ws))
        
        for row, (ws, plus, minus) in enumerate(zip(filtered_ws, capped_plus, minus_percentage_power)):
            vw.percentage_bands_table.setItem(row, 0, QTableWidgetItem(f"{ws:.1f}"))
            vw.percentage_bands_table.setItem(row, 1, QTableWidgetItem(f"{plus:.2f}"))
            vw.percentage_bands_table.setItem(row, 2, QTableWidgetItem(f"{minus:.2f}"))
        
        vw.percentage_bands_table.resizeColumnsToContents()
        vw.percentage_bands_dock.setVisible(True)

    return True

@plotting_decorator(required_params=["wind_speed", "nacelle_direction"])
def plot_joint_distribution(vw, filtered_data, column_cache):
    columns = validate_required_columns(filtered_data, ["wind_speed", "nacelle_direction"], vw, column_cache)
    if not columns:
        return False
    wind_speed_col = columns["wind_speed"]
    wind_dir_col = columns["nacelle_direction"]
    speed_data = get_numeric_data(filtered_data, wind_speed_col)
    dir_data = get_numeric_data(filtered_data, wind_dir_col)
    if speed_data is None or dir_data is None:
        # vw.handle_errors("No valid wind speed or direction data available.")
        handle_error_simple(ValueError("No valid joint distribution data"), 
                   "No valid wind speed or direction data available.")
        return False
    max_samples = 10000
    if len(speed_data) > max_samples:
        # pick every Nth point so result is always the same
        step = max(1, len(speed_data) // max_samples)
        speed_data = speed_data.iloc[::step].reset_index(drop=True)[:max_samples]
        dir_data   = dir_data.iloc[::step].reset_index(drop=True)[:max_samples]
    selected_color = vw.color_scheme.currentText() if hasattr(vw, "color_scheme") else "viridis"
    ax = vw.figure.add_subplot(111)
    sns.kdeplot(
        data=pd.DataFrame({'Speed': speed_data, 'Direction': dir_data}),
        x='Speed', y='Direction', cmap=selected_color,
        fill=True, levels=20, bw_adjust=0.5, ax=ax
    )
    format_axes(ax, "Wind Speed (m/s)", "Wind Direction (°)", "Joint Distribution")
    show_legend = hasattr(vw, "show_legend") and vw.show_legend.isChecked()
    if show_legend:
        ax.legend(["Joint Distribution"])
    return True

@plotting_decorator(required_params=["wind_speed"])
def plot_extreme_wind(vw, filtered_data, column_cache):
    columns = validate_required_columns(filtered_data, ["wind_speed"], vw, column_cache)
    if not columns:
        return False
    wind_speed_col = columns["wind_speed"]
    speed_data = get_numeric_data(filtered_data, wind_speed_col)
    if speed_data is None or len(speed_data) == 0:
        # vw.handle_errors("No valid wind speed data available.")
        # NEW:
        handle_error_simple(ValueError("No valid extreme wind data"), 
                        "No valid wind speed data available.")
        return False
    ax = vw.figure.add_subplot(111)
    sorted_speeds = np.sort(speed_data)[::-1]
    n = len(sorted_speeds)
    return_periods = n / (np.arange(n) + 1)
    if len(sorted_speeds) > 5000:
        indices = np.linspace(0, len(sorted_speeds) - 1, 5000, dtype=int)
        sorted_speeds = sorted_speeds[indices]
        return_periods = return_periods[indices]
    ax.semilogx(return_periods, sorted_speeds, 'o', markersize=3)
    format_axes(ax, "Return Period (days)", "Wind Speed (m/s)", "Extreme Wind Analysis")
    return True

@plotting_decorator(required_params=["rotor_speed", "gearbox_temp"])
def plot_rotor_speed_vs_gearbox_temperature(vw, filtered_data, column_cache):
    columns = validate_required_columns(filtered_data, ["rotor_speed", "gearbox_temp"], vw, column_cache)
    if not columns:
        return False
    rotor_speed_col = columns["rotor_speed"]
    gearbox_temp_col = columns["gearbox_temp"]
    rotor_speed = get_numeric_data(filtered_data, rotor_speed_col)
    gearbox_temp = get_numeric_data(filtered_data, gearbox_temp_col)
    if rotor_speed is None or gearbox_temp is None:
        # vw.handle_errors("No valid rotor speed or gearbox temperature data available.")
        handle_error_simple(ValueError("No valid rotor/gearbox data"), 
                   "No valid rotor speed or gearbox temperature data available.")
        return False
    # if len(rotor_speed) > 5000:
    #     indices = np.random.choice(len(rotor_speed), 5000, replace=False)
    #     rotor_speed = rotor_speed.iloc[indices]
    #     gearbox_temp = gearbox_temp.iloc[indices]
    ax = vw.figure.add_subplot(111)
    ax.scatter(gearbox_temp, rotor_speed, color='green', alpha=0.6, s=10)
    format_axes(ax, "Gearbox Temperature (°C)", "Rotor Speed (RPM)", 
                "Rotor Speed vs. Gearbox Temperature")
    return True

@plotting_decorator(required_params=["rotor_speed", "generator_speed"])
def plot_rotor_speed_vs_generator_speed(vw, filtered_data, column_cache):
    columns = validate_required_columns(filtered_data, ["rotor_speed", "generator_speed"], vw, column_cache)
    if not columns:
        return False
    rotor_speed_col = columns["rotor_speed"]
    generator_speed_col = columns["generator_speed"]
    rotor_speed = get_numeric_data(filtered_data, rotor_speed_col)
    generator_speed = get_numeric_data(filtered_data, generator_speed_col)
    if rotor_speed is None or generator_speed is None:
        # vw.handle_errors("No valid rotor speed or generator speed data available.")
        handle_error_simple(ValueError("No valid rotor/generator data"), 
                   "No valid rotor speed or generator speed data available.")
        return False    
    ax = vw.figure.add_subplot(111)
    ax.scatter(generator_speed, rotor_speed, color='red', alpha=0.6, s=10)
    if len(rotor_speed) > 1:
        coef = np.polyfit(generator_speed, rotor_speed, 1)
        poly1d_fn = np.poly1d(coef)
        x_range = np.linspace(generator_speed.min(), generator_speed.max(), 100)
        ax.plot(x_range, poly1d_fn(x_range), '--k', alpha=0.7, 
                label=f'Fit: y = {coef[0]:.4f}x + {coef[1]:.4f}')
    format_axes(ax, "Generator Speed (RPM)", "Rotor Speed (RPM)", 
                "Rotor Speed vs. Generator Speed")
    show_legend = hasattr(vw, "show_legend") and vw.show_legend.isChecked()
    apply_legend(ax, show_legend)
    return True


@plotting_decorator(required_params=["ambient_temp", "nacelle_temp"])
def plot_ambient_vs_nacelle_temperature(vw, filtered_data, column_cache):
    # Validate and retrieve required columns from column_cache
    columns = validate_required_columns(filtered_data, ["ambient_temp", "nacelle_temp"], vw, column_cache)
    if not columns:
        return False
    ambient_temp_col = columns["ambient_temp"]
    nacelle_temp_col = columns["nacelle_temp"]

    ambient_temp = get_numeric_data(filtered_data, ambient_temp_col)
    nacelle_temp = get_numeric_data(filtered_data, nacelle_temp_col)
    if ambient_temp is None or nacelle_temp is None:
        # vw.handle_errors("No valid temperature data available.")
        # NEW:
        handle_error_simple(ValueError("No valid temperature data"), 
                        "No valid temperature data available.")
        return False

    # # Limit sample size if necessary
    # if len(ambient_temp) > 5000:
    #     indices = np.random.choice(len(ambient_temp), 5000, replace=False)
    #     ambient_temp = ambient_temp.iloc[indices]
    #     nacelle_temp = nacelle_temp.iloc[indices]

    ax = vw.figure.add_subplot(111)
    ax.scatter(ambient_temp, nacelle_temp, color='blue', alpha=0.6, s=10)
    if len(ambient_temp) > 1:
        coef = np.polyfit(ambient_temp, nacelle_temp, 1)
        poly1d_fn = np.poly1d(coef)
        x_range = np.linspace(ambient_temp.min(), ambient_temp.max(), 100)
        ax.plot(x_range, poly1d_fn(x_range), '--k', alpha=0.7,
                label=f'Fit: y = {coef[0]:.2f}x + {coef[1]:.2f}')
    format_axes(ax, "Ambient Temperature (°C)", "Nacelle Temperature (°C)", 
                "Ambient vs. Nacelle Temperature")
    show_legend = hasattr(vw, "show_legend") and vw.show_legend.isChecked()
    apply_legend(ax, show_legend)
    return True

from models import scada_utils as su
@plotting_decorator(required_params=["rotor_speed"])
def plot_rotor_speed_graph(vw, filtered_data, column_cache):
    columns = validate_required_columns(filtered_data, ["rotor_speed"], vw, column_cache)
    if not columns:
        return False
    rotor_speed_col = columns["rotor_speed"]
    
    # Find timestamp column dynamically
    ts_cols = su.find_matching_columns(filtered_data, 'timestamp')
    if not ts_cols:
        # vw.handle_errors("Timestamp column not found in data")
        # NEW:
        handle_error_simple(ValueError("Missing timestamp column"), 
                        "Timestamp column not found in data")
        return False
    
    ts_col = ts_cols[0]
    
    # FIX: Create copy to avoid SettingWithCopyWarning
    filtered_data = filtered_data.copy()
    filtered_data[ts_col] = pd.to_datetime(filtered_data[ts_col], errors='coerce')
    
    rotor_speed = get_numeric_data(filtered_data, rotor_speed_col)
    if rotor_speed is None:
        # vw.handle_errors("No valid rotor speed data available.")
        # NEW:
        handle_error_simple(ValueError("No valid rotor speed data"),
                        "No valid rotor speed data available.")
        return False
    
    filtered_data.loc[filtered_data[rotor_speed_col] == 0, rotor_speed_col] = np.nan
    
    # if len(filtered_data) > 5000:
    #     filtered_data = filtered_data.iloc[::len(filtered_data)//5000]
    
    # # Extract time only (HH:MM:SS)
    # time_only = filtered_data[ts_col].dt.time
    
    # ax = vw.figure.add_subplot(111)
    # ax.plot(range(len(time_only)), filtered_data[rotor_speed_col], label="Rotor Speed")
    if len(filtered_data) > 5000:
        filtered_data = filtered_data.iloc[::len(filtered_data)//5000]
    
    # Insert NaNs at time gaps to break line connections
    filtered_data = insert_nans_at_time_gaps(filtered_data, ts_col, max_gap_hours=1)
    
    # Extract time only (HH:MM:SS)
    time_only = filtered_data[ts_col].dt.time
    
    ax = vw.figure.add_subplot(111)
    ax.plot(range(len(time_only)), filtered_data[rotor_speed_col], label="Rotor Speed")
    
    # Set x-axis labels to show time
    step = max(1, len(time_only) // 10)
    ax.set_xticks(range(0, len(time_only), step))
    ax.set_xticklabels([str(t) for t in time_only[::step]], rotation=45, ha='right')
    
    format_axes(ax, "Time", "Rotor Speed (RPM)", "Rotor Speed Over Time")
    show_legend = hasattr(vw, "show_legend") and vw.show_legend.isChecked()
    apply_legend(ax, show_legend)
    
    return True


@plotting_decorator(required_params=["wind_speed", "nacelle_direction"])
def plot_wind_frequency_histogram(vw, filtered_data, column_cache):
    """Plot wind speed frequency histogram by direction bins"""
    columns = validate_required_columns(filtered_data, ["wind_speed", "nacelle_direction"], vw, column_cache)
    if not columns:
        return False
        
    wind_speed_col = columns["wind_speed"]
    wind_dir_col = columns["nacelle_direction"]
    
    # Get numeric data
    speed_data = get_numeric_data(filtered_data, wind_speed_col)
    dir_data = get_numeric_data(filtered_data, wind_dir_col)
    
    if speed_data is None or dir_data is None or len(speed_data) == 0 or len(dir_data) == 0:
        # vw.handle_errors("No valid wind speed or direction data available.")
        # NEW:
        handle_error_simple(ValueError("No valid frequency histogram data"), 
                        "No valid wind speed or direction data available.")
        return False
    
    # Create DataFrame for processing
    df = pd.DataFrame({
        'wind_speed': speed_data,
        'wind_direction': dir_data
    })
    
    # Create direction bins (12 sectors of 30 degrees each)
    dir_bins = np.arange(0, 361, 30)
    dir_labels = [f"{i}-{i+30}°" for i in range(0, 360, 30)]
    
    # Create wind speed bins
    enable_iec = hasattr(vw, 'enable_iec_binning') and vw.enable_iec_binning.isChecked()
    ws_max = df['wind_speed'].max()
    ws_bins = get_bins(ws_max, enable_iec, bin_width=2.0)
    ws_labels = [f"({ws_bins[i]:.1f}, {ws_bins[i+1]:.1f}]" if enable_iec 
                 else f"({ws_bins[i]:.0f}, {ws_bins[i+1]:.0f}]" 
                 for i in range(len(ws_bins)-1)]
    
    # Bin the data
    df['dir_bin'] = bin_data(df, 'wind_direction', dir_bins, labels=dir_labels)
    df['ws_bin'] = bin_data(df, 'wind_speed', ws_bins, labels=ws_labels)
    
    # Create frequency table
    freq_table = df.groupby(['dir_bin', 'ws_bin'], observed=True).size().unstack(fill_value=0)
    
    # Convert to percentage if enabled
    if hasattr(vw, 'show_frequency_percentage') and vw.show_frequency_percentage.isChecked():
        total_count = len(df)
        plot_data = freq_table.div(total_count) * 100
        ylabel = 'Frequency (%)'
    else:
        plot_data = freq_table
        ylabel = 'Frequency Count'
    
    # Store frequency data for table updates
    vw.frequency_data = plot_data
    
    # Create the plot
    ax = vw.figure.add_subplot(111)
    
    # Use a professional color scheme
    color_scheme_name = getattr(vw, 'color_scheme', None)
    color_scheme_name = color_scheme_name.currentText() if color_scheme_name else "viridis"
    
    plot_data.plot(kind='bar', stacked=True, ax=ax, colormap=color_scheme_name, 
                   edgecolor='white', linewidth=0.5)
    
    # Formatting
    format_axes(ax, 'Wind Direction (degrees)', ylabel, 'Wind Speed Frequency by Direction')
    
    # Rotate x-axis labels for better readability
    ax.tick_params(axis='x', rotation=45)
    apply_grid(ax)
    
    # Legend handling
    show_legend = hasattr(vw, "show_legend") and vw.show_legend.isChecked()
    if show_legend:
        legend = ax.legend(title='Wind Speed (m/s)', bbox_to_anchor=(1.05, 1), 
                          loc='upper left', fontsize='small', frameon=True, 
                          edgecolor='black')
        legend.get_title().set_fontweight('bold')
    else:
        # Remove legend if not requested
        if ax.get_legend():
            ax.get_legend().remove()
    
    # Professional layout handling
    handle_layout(vw.figure, show_legend)
    
    # Update frequency table if it exists
    if hasattr(vw, 'frequency_table') and hasattr(vw, '_update_frequency_table'):
        try:
            vw._update_frequency_table()
        except Exception as e:
            print(f"Could not update frequency table: {e}")
    
    return True

@plotting_decorator(required_params=["wind_speed", "power"])
def plot_air_density_power_curve(vw, filtered_data, column_cache):
    columns = validate_required_columns(filtered_data, ["wind_speed", "power"], vw, column_cache)
    if not columns:
        return False
    
    # Get selected densities
    selected_densities = get_selected_air_densities(vw)
    if not selected_densities:
        handle_error_simple(ValueError("No air density selected"), 
                           "Please select at least one air density value.")
        return False
    
    # Get and validate data
    wind_speed_col = columns["wind_speed"]
    power_col = columns["power"]
    speed_data = get_numeric_data(filtered_data, wind_speed_col)
    power_data = get_numeric_data(filtered_data, power_col)
    
    if speed_data is None or power_data is None:
        handle_error_simple(ValueError("No valid air density data"), 
                           "No valid wind speed or power data available.")
        return False
    
    # Bin data
    df = pd.DataFrame({'wind_speed': speed_data, 'power': power_data})
    enable_iec = hasattr(vw, "enable_iec_binning") and vw.enable_iec_binning.isChecked()
    bins = get_bins(df['wind_speed'].max(), enable_iec)
    df['bin'] = bin_data(df, 'wind_speed', bins)
    stats = df.groupby('bin', observed=True).agg({'power': 'mean', 'wind_speed': 'mean'}).dropna()
    
    if stats.empty:
        handle_error_simple(ValueError("No valid air density bins"), 
                           "No valid bins for air density power curve.")
        return False
    
    bin_wind_speeds = stats['wind_speed'].values
    bin_powers = stats['power'].values
    
    # Calculate curves
    table_data, colors = calculate_air_density_curves(bin_wind_speeds, bin_powers, selected_densities)
    
    # Plot
    ax = vw.figure.add_subplot(111)
    plot_air_density_curves(ax, bin_wind_speeds, bin_powers, selected_densities, colors)
    
    format_axes(ax, "Wind Speed (m/s)", "Power (kW)", "Air Density-Corrected Power Curves")
    apply_grid(ax)
    
    show_legend = hasattr(vw, "show_legend") and vw.show_legend.isChecked()
    apply_legend(ax, show_legend, fontsize='small')
    
    # Update table
    update_air_density_table(vw, table_data)
    
    return True


def plot_selected_graph(vw, graph_type, column_cache, canvas=None, data=None, *args, **kwargs):
    plot_functions = {
        "wind_rose": plot_wind_rose,
        "wind_speed_distribution": plot_wind_speed_distribution,
        "turbulence_intensity": plot_turbulence_intensity,
        "power_curve": plot_power_curve,
        "actual_power_curve": plot_actual_power_curve,
        "binned_power_curve": plot_binned_power_curve,
        "joint_distribution": plot_joint_distribution,
        "wind_frequency_histogram": plot_wind_frequency_histogram,
        "rotor_speed_vs_gearbox_temperature": plot_rotor_speed_vs_gearbox_temperature,
        "rotor_speed_vs_generator_speed": plot_rotor_speed_vs_generator_speed,
        "ambient_vs_nacelle_temperature": plot_ambient_vs_nacelle_temperature,
        "rotor_speed_graph": plot_rotor_speed_graph,
        "air_density_power_curve": plot_air_density_power_curve,
    }

    if graph_type not in plot_functions:
        # vw.handle_errors(f"Unknown graph type: {graph_type}")
        handle_error_simple(ValueError(f"Unknown graph type: {graph_type}"),
                   f"Unknown graph type: {graph_type}")
        return False
    try:
        # Override vw.figure and vw.canvas with the provided canvas and data
        original_figure = getattr(vw, 'figure', None)
        original_canvas = getattr(vw, 'canvas', None)
        if canvas:
            vw.figure = canvas.figure
            vw.canvas = canvas
        if data is not None:
            filtered_data = data
        else:
            filtered_data = vw.get_filtered_data()
        result = plot_functions[graph_type](vw, column_cache, *args, **kwargs)
        # Restore original attributes if overridden
        if original_figure:
            vw.figure = original_figure
        if original_canvas:
            vw.canvas = original_canvas
        return result
    except Exception as e:
        # vw.handle_errors(f"Error plotting {graph_type}: {str(e)}")
        # NEW:
        handle_error_simple(e, f"Error plotting {graph_type}: {str(e)}")
        return False