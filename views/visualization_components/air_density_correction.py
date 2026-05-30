import pandas as pd
import numpy as np
import math
import models.scada_utils as su

# def get_t_hub_average(filtered_data, timestamp_col, selected_month=None):
#     t_hub_cols = su.find_matching_columns(filtered_data, 'cab_hub_temp')
#     if not t_hub_cols:
#         raise ValueError("T_hub temperature column not found in data")
#     T_hub_avg = pd.to_numeric(filtered_data[t_hub_cols[0]], error='coerce').mean()
#     return T_hub_avg
def get_t_hub_average(filtered_data, timestamp_col, selected_month=None):
    t_hub_cols = su.find_matching_columns(filtered_data, 'cab_hub_temp')
    if not t_hub_cols:
        raise ValueError("T_hub temperature column not found in data")
    T_hub_avg = pd.to_numeric(filtered_data[t_hub_cols[0]], errors='coerce').mean()
    return T_hub_avg

def calculate_air_density(elevation, hub_height, T_hub):
    z = elevation +hub_height
    T_kelvin = T_hub +273.15
    rho = (352.9886 / T_kelvin) * math.exp(-0.034163 * z / T_kelvin)

    return rho

# def normalize_wind_speed_power(standard_power_curve, rho_site):
#     rho_std = 1.225

#     V = standard_power_curve['wind_speed'].values
#     P = standard_power_curve['power'].values

#     # step 3.1 : Normalized wind speed
#     V_norm = V * (rho_site / rho_std)**(1/3)

#     # step 3.2 : Linear interpolation of normalized power curve
#     P_norm = np.interp(V_norm, V, P)

#     # store the values in array dataframe
#     corrected_curve = pd.DataFrame({'wind_speed_normalized': V_norm, 'power_corrected': P_norm})

#     return corrected_curve

def normalize_wind_speed_power(standard_power_curve, rho_site):
    rho_std = 1.225
    V = standard_power_curve['wind_speed'].values
    P = standard_power_curve['power'].values
    V_norm = V * (rho_site / rho_std)**(1/3)
    P_norm = np.interp(V_norm, V, P)
    
    # FIX: Change 'wind_speed_normalised' to 'wind_speed_normalized'
    corrected_curve = pd.DataFrame({'wind_speed_normalized': V_norm, 'power_corrected': P_norm})
    return corrected_curve