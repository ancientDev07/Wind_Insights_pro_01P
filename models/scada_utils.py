import math
import numpy as np
import json
import pandas as pd
from rapidfuzz import fuzz, process
import logging


# =========================================
# Updated SCADA Dictionary with Improvements
# =========================================

Scada_Dictionary = {
    # Time-related parameters
    'timestamp': {'patterns': ['Timestamp', 'DateTime', 'Time'], 'aliases': ['TS', 'DT']},
    'time': {'patterns': ['Time'], 'aliases': ['T']},
    'date': {'patterns': ['Date'], 'aliases': ['D']},
    'turbine_id': {'patterns': ['Wtg', 'TurbineID', 'UnitID'], 'aliases': ['TID', 'Unit']},
    
    # Main operational parameters
    'power': {
        'patterns': ['P_ACT_Avg', 'Power', 'ActivePower', 'P_Act_Avg', 'power_output', 'power'],
        'aliases': ['Pwr', 'ActPwr'],
        'unit': 'kW',
        'validation': {'rate_of_change': 1000, 'correlation': ['wind_speed', 'generator_speed']}
    },
    'wind_speed': {
        'patterns': ['V_WIN_Avg', 'WindSpeed', 'wind_speed', 'V_Wind_Avg', 'WindSpeed_Avg'],
        'aliases': ['WS', 'WindSpd'],
        'unit': 'm/s',
        'validation': {'rate_of_change': 5, 'correlation': ['power']}
    },
    
    # Count or cycles
    'count': {
        'patterns': ['Count', 'Cycles'],
        'aliases': ['Cnt'],
        'unit': 'cycles'
    },
    
    # Speeds and rotational parameters
    # 'generator_speed': {
    #     'patterns': ['N_GEN_CCU_Avg', 'In_RotorSpd_Raw_Avg'],
    #     'aliases': ['GenSpd'],
    #     'unit': 'rpm',
    #     'validation': {'rate_of_change': 200, 'correlation': ['rotor_speed', 'power']}
    # },
    # 'rotor_speed': {
    #     'patterns': ['N_ROT_PLC_Avg'],
    #     'aliases': ['RotSpd'],
    #     'unit': 'rpm',
    #     'validation': {'rate_of_change': 5, 'correlation': ['wind_speed', 'generator_speed']}
    # },

    # ── Rotational speeds (physically distinct — never share patterns) ────────
    'generator_speed': {
        # High-speed shaft after gearbox. Pattern is generator-specific only.
        'patterns': ['N_GEN_CCU_Avg', 'GenSpeed_Avg', 'GeneratorSpeed'],
        'aliases': ['GenSpd', 'N_GEN'],
        'unit': 'rpm',
        'validation': {'rate_of_change': 200, 'correlation': ['rotor_speed', 'power']}
    },
    'rotor_speed': {
        # Low-speed shaft before gearbox. No overlap with generator_speed patterns.
        'patterns': ['N_ROT_PLC_Avg', 'RotorSpeed_Avg', 'RotorSpeed'],
        'aliases': ['RotSpd', 'N_ROT'],
        'unit': 'rpm',
        'validation': {'rate_of_change': 5, 'correlation': ['wind_speed', 'generator_speed']}
    },

    
    # # Blade parameters
    # 'blade_angles': {
    #     'patterns': ['BL1_ACT_Avg', 'BL2_ACT_Avg', 'BL3_ACT_Avg'],
    #     'aliases': ['BladeAng'],
    #     'unit': 'deg',
    #     'validation': {'rate_of_change': 10, 'correlation': ['wind_speed', 'power']}
    # },
    # 'blade_setpoints': {
    #     'patterns': ['BL1_SET_V_Avg', 'BL2_SET_V_Avg', 'BL3_SET_V_Avg'],
    #     'aliases': ['BladeSet'],
    #     'unit': 'deg',
    #     'validation': {'rate_of_change': 10}
    # },

     # ── Pitch angles — one key per blade, never grouped ───────────────────────
    # Grouping BL1/BL2/BL3 under 'blade_angles' caused find_matching_columns
    # to return all three columns; the caller always got blade 1 by accident.
    'pitch_blade_1': {
        'patterns': ['BL1_ACT_Avg', 'Blade1Pitch_Avg', 'PitchAngle1_Avg', 'Pitch1_Avg'],
        'aliases': ['BL1', 'Pitch1'],
        'unit': 'deg',
        'validation': {'rate_of_change': 10, 'correlation': ['wind_speed', 'power']}
    },
    'pitch_blade_2': {
        'patterns': ['BL2_ACT_Avg', 'Blade2Pitch_Avg', 'PitchAngle2_Avg', 'Pitch2_Avg'],
        'aliases': ['BL2', 'Pitch2'],
        'unit': 'deg',
        'validation': {'rate_of_change': 10, 'correlation': ['wind_speed', 'power']}
    },
    'pitch_blade_3': {
        'patterns': ['BL3_ACT_Avg', 'Blade3Pitch_Avg', 'PitchAngle3_Avg', 'Pitch3_Avg'],
        'aliases': ['BL3', 'Pitch3'],
        'unit': 'deg',
        'validation': {'rate_of_change': 10, 'correlation': ['wind_speed', 'power']}
    },

     # ── Pitch setpoints — one key per blade ───────────────────────────────────
    'pitch_setpoint_blade_1': {
        'patterns': ['BL1_SET_V_Avg', 'Blade1PitchSet_Avg', 'PitchSet1_Avg'],
        'aliases': ['BL1Set', 'PitchSet1'],
        'unit': 'deg',
        'validation': {'rate_of_change': 10}
    },
    'pitch_setpoint_blade_2': {
        'patterns': ['BL2_SET_V_Avg', 'Blade2PitchSet_Avg', 'PitchSet2_Avg'],
        'aliases': ['BL2Set', 'PitchSet2'],
        'unit': 'deg',
        'validation': {'rate_of_change': 10}
    },
    'pitch_setpoint_blade_3': {
        'patterns': ['BL3_SET_V_Avg', 'Blade3PitchSet_Avg', 'PitchSet3_Avg'],
        'aliases': ['BL3Set', 'PitchSet3'],
        'unit': 'deg',
        'validation': {'rate_of_change': 10}
    },
    
    # Electrical parameters
    'voltage_phase_a': {
        'patterns': ['U_A_N_Avg', 'Voltage_A_Avg'],
        'aliases': ['Volt_A'],
        'unit': 'V',
        'validation': {'rate_of_change': 100, 'correlation': ['current', 'power']}
    },
    'voltage_phase_b': {
        'patterns': ['U_B_N_Avg', 'Voltage_B_Avg'],
        'aliases': ['Volt_B'],
        'unit': 'V',
        'validation': {'rate_of_change': 100, 'correlation': ['current', 'power']}
    },
    'voltage_phase_c': {
        'patterns': ['U_C_N_Avg', 'Voltage_C_Avg'],
        'aliases': ['Volt_C'],
        'unit': 'V',
        'validation': {'rate_of_change': 100, 'correlation': ['current', 'power']}
    },
    'current': {
        'patterns': ['I_A_Avg', 'I_B_Avg', 'I_C_Avg', 'AI_CuRotorCurrent_Avg'],
        'aliases': ['Curr'],
        'unit': 'A'
    },
    'frequency': {
        'patterns': ['FREQ_Avg'],
        'aliases': ['Freq'],
        'unit': 'Hz'
    },
    
    # Temperature measurements
    'generator_temp': {
        'patterns': ['T_GEN_1_Avg', 'T_GEN_2_Avg', 'AI_In_TbGenWinding3Temp_Avg'],
        'aliases': ['GenTemp'],
        'unit': '°C'
    },
    'bearing_temp': {
        'patterns': ['T_BEAR_A_Avg', 'T_BEAR_B_Avg', 'T_BEAR_SHAFT_Avg', 'AI_In_TbBearing2RotorTemp_Avg'],
        'aliases': ['BearTemp'],
        'unit': '°C'
    },
    'gearbox_temp': {
        'patterns': ['T_GEAR_Avg', 'T_GEAR_BEAR_Avg', 'AI_In_TbGbxOilTempSump2_Avg', 'AI_In_TbGbxOilDistributorTemp_Avg'],
        'aliases': ['GearTemp'],
        'unit': '°C'
    },
    'ambient_temp': {
        'patterns': ['T_AMB_Avg', 'AI_In_TbOutsideTemp1_Avg', 'AI_In_TbOutsideTemp2_Avg'],
        'aliases': ['AmbTemp'],
        'unit': '°C'
    },
    'cabinet_temp': {
        'patterns': ['T_MAIN_BOX_Avg', 'T_TOP_BOX_Avg', 'T_HUB_Avg', 'AI_In_DtaDownTowerCabinetTemp_Avg'],
        'aliases': ['CabTemp'],
        'unit': '°C'
    },
    'cab_hub_temp': {
        'patterns': ['T_HUB_Avg'],
        'aliases': ['HubTemp'],
        'unit': '°C'
    },
    'motor_temp': {
        'patterns': ['AI_In_MotorTempA1_Avg', 'AI_In_MotorTempA2_Avg', 'AI_In_MotorTempA3_Avg'],
        'aliases': ['MotTemp'],
        'unit': '°C'
    },
    'nacelle_temp': {
        'patterns': ['T_NAC_Avg', 'AI_In_TbNacelleTemp_Avg', 'NacelleTemp', 'T_NACELLE_Avg', 'AI_In_NacelleTempSensor_Avg', 'NAC_TEMP_Avg', 'T_NAC_INT_Avg', 'T_NACELLE_INTERNAL_Avg'],
        'aliases': ['NacTemp'],
        'unit': 'degC'
    },
    
    # Battery parameters
    'battery_voltage': {
        'patterns': ['AI_In_Axis', 'dBatVoltC', 'd_Avg'],
        'aliases': ['BatVolt'],
        'unit': 'V'
    },
    
    # Motor parameters
    'motor_temp': {
        'patterns': ['AI_In_MotorTempA1_Avg', 'AI_In_MotorTempA2_Avg', 'AI_In_MotorTempA3_Avg'],
        'aliases': ['MotTemp'],
        'unit': '°C'
    },
    'motor_current': {
        'patterns': ['AI_In_MotorCurrentA1_Avg', 'AI_In_MotorCurrentA2_Avg', 'AI_In_MotorCurrentA3_Avg'],
        'aliases': ['MotCurr'],
        'unit': 'A'
    },
    
    # Position and movement parameters
    'nacelle_direction': {
        'patterns': ['POS_NAC_Avg'],
        'aliases': ['NacDir'],
        'unit': 'deg'
    },
    # 'nacelle_position': {
    #     'patterns': ['AI_In_TbAbsEncYawPosition_Avg'],
    #     'aliases': ['NacPos'],
    #     'unit': 'deg'
    # },
    'nacelle_temp': {
        'patterns': ['T_NAC_Avg', 'AI_In_TbNacelleTemp_Avg', 'NacelleTemp', 'T_NACELLE_Avg', 'AI_In_NacelleTempSensor_Avg', 'NAC_TEMP_Avg', 'T_NAC_INT_Avg', 'T_NACELLE_INTERNAL_Avg'],
        'aliases': ['NacTemp'],
        'unit': 'degC'
    },
    # 'yaw_speed': {
    #     'patterns': ['AI_In_TbAbsEncYawSpeed_Avg'],
    #     'aliases': ['YawSpd'],
    #     'unit': 'deg/s'
    # },

    'yaw_position': {
        # Absolute nacelle heading in degrees (0–360). Distinct from yaw rate.
        'patterns': ['AI_In_TbAbsEncYawPosition_Avg', 'YawPosition_Avg',
                     'NacelleAngle_Avg', 'YawAngle_Avg'],
        'aliases': ['YawPos', 'NacAngle'],
        'unit': 'deg'
    },
    'yaw_speed': {
        # Rate of nacelle rotation in deg/s. Distinct from yaw_position.
        'patterns': ['AI_In_TbAbsEncYawSpeed_Avg', 'YawRate_Avg', 'YawSpeed_Avg'],
        'aliases': ['YawSpd', 'YawRate'],
        'unit': 'deg/s'
    },

    'tower_acceleration': {
        'patterns': ['AI_In_TowerAccelSideSideRaw_Avg', 'AI_In_TowerAccelForeAftRaw_Avg'],
        'aliases': ['TowAcc'],
        'unit': 'm/s²'
    },

    'hub_height': {
        'patterns': ['Hub Height (m)', 'HubHeight', 'Hub_Height', 'hub_height'],
        'aliases': ['HubHt'],
        'unit': 'm'
    },
    'elevation': {
        'patterns': ['Elevation (m)', 'Elevation', 'elevation', 'site_elevation'],
        'aliases': ['Elev'],
        'unit': 'm'
    },
    'longitude': {
        'patterns': ['Longitude', 'longtitude', 'long'],
        'aliases': ['Lon'],
        'unit': 'degrees'
    },
    'latitude': {
        'patterns': ['Latitude', 'latitide', 'lat'],
        'aliases': ['Lat'],
        'unit': 'degrees'
    },
    
    # Derived parameters
    'derived_parameters': {
        'power_coefficient': {
            'formula': 'power / (0.5 * 1.225 * math.pi * (rotor_diameter/2)**2 * wind_speed**3)',
            'required_params': ['power', 'wind_speed'],
            'constants': {'rotor_diameter': 90}
        },
        'turbulence_intensity': {
            'formula': 'np.std(wind_speed) / np.mean(wind_speed)',
            'window': '1H',
            'required_params': ['wind_speed']
        },
        'blade_asymmetry': {
            'formula': 'max(abs(np.diff(blade_angles)))',
            'required_params': ['blade_angles']
        },
        'temperature_gradient': {
            'formula': 'max(bearing_temp) - ambient_temp',
            'required_params': ['bearing_temp', 'ambient_temp']
        }
    },
    
    # Quality thresholds
    'quality_thresholds': {
        'missing_data': 0.1,
        'outlier_zscore': 3,
        'outlier_iqr_factor': 1.5,
        'min_data_points': 144
    },
    
    # Time features
    'time_features': {
        'hour': {'type': 'cyclical', 'period': 24},
        'day': {'type': 'categorical'},
        'month': {'type': 'cyclical', 'period': 12},
        'season': {
            'type': 'categorical',
            'mapping': {
                12: 1, 1: 1, 2: 1,   # Winter
                3: 2, 4: 2, 5: 2,    # Spring
                6: 3, 7: 3, 8: 3,    # Summer
                9: 4, 10: 4, 11: 4   # Fall
            }
        }
    }
}

# =========================================
# Helper Functions for Parameter Lookup
# =========================================

def get_parameter_info(parameter_name):
    """
    Get the patterns and aliases for a specific parameter from the SCADA dictionary.
    """
    param_info = Scada_Dictionary.get(parameter_name, {})
    patterns = param_info.get('patterns', [])
    aliases = param_info.get('aliases', [])
    return patterns + aliases

def get_parameter_unit(parameter_name):
    """
    Get the unit for a specific parameter from the SCADA dictionary.
    """
    param_info = Scada_Dictionary.get(parameter_name, {})
    return param_info.get('unit')

def find_matching_columns(dataframe, parameter_name, use_fuzzy=False, threshold=80):
    """
    Find columns in the dataframe that match the parameter patterns or aliases.
    If use_fuzzy is True, applies fuzzy matching with a similarity threshold.
    """
    patterns = get_parameter_info(parameter_name)
    matching_columns = []
    if use_fuzzy:
        for col in dataframe.columns:
            best_match, score, _ = process.extractOne(col.lower(), patterns, scorer=fuzz.ratio)
            if score >= threshold:
                matching_columns.append(col)

    else:
        for pattern in patterns:
            matching_columns.extend([col for col in dataframe.columns if pattern.lower() in col.lower()])
    return matching_columns

def get_parameter_full(parameter_name):
    """
    Return the entire dictionary or value for a parameter from the SCADA dictionary.
    """
    return Scada_Dictionary.get(parameter_name)

# =========================================
# Helper Functions for Parameter Mapping
# =========================================

def load_custom_mappings():
    """
    Load custom SCADA mappings from a JSON file.
    Returns a dictionary of mappings.
    """
    try:
        with open('custom_mappings.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def update_custom_mappings(new_mappings):
    """
    Update the custom mappings in the JSON file.
    new_mappings should be a dict: {parameter_name: [new_pattern, ...]}.
    """
    current_mappings = load_custom_mappings()
    for param, patterns in new_mappings.items():
        if param in current_mappings:
            current_mappings[param].extend(patterns)
        else:
            current_mappings[param] = patterns
    with open('custom_mappings.json', 'w') as file:
        json.dump(current_mappings, file, indent=4)


# =========================================
# Additional Helper Functions
# =========================================

def suggest_similar_parameters(dataframe, parameter_name, threshold=80):
    """
    Suggest columns that are similar to known parameters based on fuzzy matching.
    Returns a dict of {column: (best_match, score)}.
    """
    patterns = get_parameter_info(parameter_name)
    suggestions = {}
    for col in dataframe.columns:
        best_match, score, _ = process.extractOne(col.lower(), patterns, scorer=fuzz.ratio)
        if score >= threshold:
            suggestions[col] = (best_match, score)
    return suggestions

def log_unmapped_columns(dataframe, mapped_columns):
    """
    Log columns in the dataframe that were not mapped to any parameter.
    """
    unmapped = set(dataframe.columns) - set(mapped_columns)
    if unmapped:
        raise ValueError(f"Unmapped columns found: {unmapped}")
    
# New Helper Function to Retrieve All Temperature Tags
def get_temperature_data(data, column_cache):
    """
    Retrieve all temperature-related data based on SCADA dictionary categories.
    Returns a dictionary with category names as keys and their corresponding data as values.
    """
    temp_categories = [
        'generator_temp', 'bearing_temp', 'gearbox_temp', 'ambient_temp', 
        'cabinet_temp', 'motor_temp', 'nacelle_temp'
    ]
    temp_data = {}
    for category in temp_categories:
        col = column_cache.get(category)
        if col and col in data.columns:
            numeric_data = pd.to_numeric(data[col], errors='coerce').dropna()
            if not numeric_data.empty:
                temp_data[category] = numeric_data
    return temp_data

# new helper methods
def detect_turbine_column(df):
    """
    Auto-detect turbine ID column in DataFrame
    
    Args:
        df: pandas DataFrame
    
    Returns:
        str or None: Name of turbine ID column
    """
    # Try exact match first
    matched = find_matching_columns(df, 'turbine_id')
    if matched:
        return matched[0]
    
    # Try pattern matching
    patterns = ['wtg', 'turbine', 'turbine_id', 'id', 't0', 'turb']
    for col in df.columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in patterns):
            # Verify it contains turbine-like values
            if df[col].astype(str).str.upper().str.contains('WTG|T0|TURB', na=False).any():
                return col
    
    return None


def detect_timestamp_column(df):
    """
    Identify timestamp column in DataFrame
    
    Args:
        df: pandas DataFrame
    
    Returns:
        str or None: Name of timestamp column
    """
    # Try exact match first
    matched = find_matching_columns(df, 'timestamp')
    if matched:
        return matched[0]
    
    # Try datetime type
    for col in df.columns:
        if df[col].dtype.name.startswith('datetime'):
            return col
    
    # Try keyword matching
    keywords = ['timestamp', 'datetime', 'date_time', 'time', 'date']
    for col in df.columns:
        if any(kw in col.lower() for kw in keywords):
            return col
    
    return None



# ─────────────────────────────────────────────────────────────────────────────
# ADD: Explicit single-parameter column resolver.
#
# Why: find_matching_columns returns a list and callers do matched[0], which
# silently picks the wrong sensor when patterns overlap. This function enforces
# that the caller names exactly which parameter they want and raises clearly
# if it cannot be resolved — no silent fallback to the wrong signal.
# ─────────────────────────────────────────────────────────────────────────────

def resolve_column(dataframe: pd.DataFrame, parameter_key: str,
                   use_fuzzy: bool = False, threshold: int = 80) -> str:
    """
    Resolve a single, unambiguous column name for the given parameter key.

    Unlike find_matching_columns (which returns a list and lets callers
    silently take index 0), this function:
      - Raises KeyError  if the parameter_key is not in Scada_Dictionary.
      - Raises ValueError if no matching column is found in the dataframe.
      - Returns exactly one column name — the best match only.

    Use this wherever a visualization or KPI function needs one specific
    physical signal (e.g. 'pitch_blade_1', not 'blade_angles').

    Args:
        dataframe:     The SCADA DataFrame to search.
        parameter_key: Exact key from Scada_Dictionary (e.g. 'pitch_blade_2').
        use_fuzzy:     Enable fuzzy matching (default False for strict mode).
        threshold:     Fuzzy match threshold (0–100).

    Returns:
        str: The matched column name in the dataframe.

    Raises:
        KeyError:   Unknown parameter_key.
        ValueError: No column found for the given parameter_key.
    """
    if parameter_key not in Scada_Dictionary:
        raise KeyError(
            f"Unknown SCADA parameter: '{parameter_key}'. "
            f"Valid keys: {sorted(Scada_Dictionary.keys())}"
        )

    matched = find_matching_columns(dataframe, parameter_key, use_fuzzy, threshold)

    if not matched:
        raise ValueError(
            f"No column found for parameter '{parameter_key}' "
            f"in DataFrame columns: {list(dataframe.columns)}"
        )

    # If multiple columns matched (e.g. fuzzy mode), pick the highest-scoring
    # one rather than silently returning index 0.
    if use_fuzzy and len(matched) > 1:
        patterns = get_parameter_info(parameter_key)
        best_col, best_score = matched[0], 0
        for col in matched:
            _, score, _ = process.extractOne(col.lower(), patterns, scorer=fuzz.ratio)
            if score > best_score:
                best_score, best_col = score, col
        return best_col

    return matched[0]


def resolve_columns(dataframe: pd.DataFrame, parameter_keys: list,
                    use_fuzzy: bool = False, threshold: int = 80) -> dict:
    """
    Resolve multiple parameter keys to column names in one call.
    Returns {parameter_key: column_name} for keys that resolved,
    and logs a warning (does NOT raise) for keys that did not resolve,
    so a missing optional sensor doesn't abort the whole visualization.

    Args:
        dataframe:      The SCADA DataFrame.
        parameter_keys: List of Scada_Dictionary keys.
        use_fuzzy:      Enable fuzzy matching.
        threshold:      Fuzzy match threshold.

    Returns:
        dict: {key: column_name} for successfully resolved keys only.
    """
    resolved = {}
    for key in parameter_keys:
        try:
            resolved[key] = resolve_column(dataframe, key, use_fuzzy, threshold)
        except (KeyError, ValueError) as e:
            logging.warning(f"[SCADA] Could not resolve '{key}': {e}")
    return resolved