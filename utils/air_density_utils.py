"""Centralized air density utilities for power curve corrections"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QDockWidget
from PyQt5.QtCore import Qt


def get_selected_air_densities(vw):
    """
    Extract selected air density values from checkboxes
    
    Args:
        vw: Visualization window object with air density checkboxes
    
    Returns:
        List of selected air density values
    """
    densities = [1.02, 1.04, 1.06, 1.08, 1.1, 1.12, 1.14, 1.16, 1.18, 1.225]
    selected = []
    for density in densities:
        checkbox_name = f"air_density_{str(density).replace('.', '_')}"
        if hasattr(vw, checkbox_name) and getattr(vw, checkbox_name).isChecked():
            selected.append(density)
    return selected


def calculate_air_density_correction(bin_powers, air_density, standard_density=1.225):
    """
    Calculate power correction for given air density
    
    Args:
        bin_powers: Array of power values
        air_density: Target air density (kg/m³)
        standard_density: Standard air density (default 1.225 kg/m³)
    
    Returns:
        Corrected power values
    """
    correction_factor = (air_density / standard_density) ** 1.5
    return bin_powers * correction_factor


def calculate_air_density_curves(bin_wind_speeds, bin_powers, selected_densities, standard_density=1.225):
    """
    Calculate corrected power curves for multiple air densities
    
    Args:
        bin_wind_speeds: Array of wind speed bin centers
        bin_powers: Array of power values
        selected_densities: List of air densities to calculate
        standard_density: Standard air density (default 1.225)
    
    Returns:
        Tuple of (table_data, colors) for plotting
    """
    table_data = []
    colors = plt.cm.viridis(np.linspace(0, 1, len(selected_densities)))
    
    for rho in selected_densities:
        corrected_power = calculate_air_density_correction(bin_powers, rho, standard_density)
        for ws, power in zip(bin_wind_speeds, corrected_power):
            table_data.append([rho, ws, power])
    
    return table_data, colors


def update_air_density_table(vw, table_data):
    """
    Update or create air density table widget
    
    Args:
        vw: Visualization window object
        table_data: List of [density, wind_speed, power] rows
    """
    if not hasattr(vw, 'air_density_table_dock'):
        vw.air_density_table_dock = QDockWidget("Air Density Data", vw)
        vw.air_density_table = QTableWidget()
        vw.air_density_table_dock.setWidget(vw.air_density_table)
        vw.addDockWidget(Qt.RightDockWidgetArea, vw.air_density_table_dock)
    
    vw.air_density_table.setColumnCount(3)
    vw.air_density_table.setHorizontalHeaderLabels(["Air Density (kg/m³)", "Wind Speed (m/s)", "Power (kW)"])
    vw.air_density_table.setRowCount(len(table_data))
    
    for row, (rho, ws, power) in enumerate(table_data):
        vw.air_density_table.setItem(row, 0, QTableWidgetItem(f"{rho:.2f}"))
        vw.air_density_table.setItem(row, 1, QTableWidgetItem(f"{ws:.1f}"))
        vw.air_density_table.setItem(row, 2, QTableWidgetItem(f"{power:.2f}"))
    
    vw.air_density_table.resizeColumnsToContents()
    vw.air_density_table_dock.setVisible(True)


def plot_air_density_curves(ax, bin_wind_speeds, bin_powers, selected_densities, colors):
    """
    Plot air density corrected power curves
    
    Args:
        ax: Matplotlib axis object
        bin_wind_speeds: Array of wind speed bin centers
        bin_powers: Array of power values
        selected_densities: List of air densities
        colors: Color array for each density
    """
    for i, rho in enumerate(selected_densities):
        corrected_power = calculate_air_density_correction(bin_powers, rho)
        label = f"ρ = {rho:.2f} kg/m³" + (" (Standard)" if rho == 1.225 else "")
        ax.plot(bin_wind_speeds, corrected_power, color=colors[i], linewidth=2, 
                marker='o', markersize=4, label=label)
