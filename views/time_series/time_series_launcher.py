import sys
import os
import webbrowser

from views.time_series import dash_app

# Ensure project root is always on path
_ROOT = os.path.abspath(os.path.dirname(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pandas as pd

try:
    from utils import column_cache_utility as ccu
    from models import scada_utils as su
    _HAS_UTILS = True
except ImportError:
    _HAS_UTILS = False


# ─────────────────────────────────────────────────────────────────────────────
# Column detection
# ─────────────────────────────────────────────────────────────────────────────
# _PARAM_KEYS = [
#     "power",
#     "wind_speed",
#     "rotor_speed",
#     "yaw_speed",
#     "nacelle_direction",
#     "voltage_phase_a",
#     "voltage_phase_b",
#     "voltage_phase_c",
#     "frequency",
# ]

_PARAM_KEYS = [
    "power",
    "wind_speed",
    # Rotational — separate keys, separate columns
    "rotor_speed",
    "generator_speed",
    # Pitch — each blade addressed individually
    "pitch_blade_1",
    "pitch_blade_2",
    "pitch_blade_3",
    # Yaw — position and rate are different signals
    "yaw_position",
    "yaw_speed",
    "nacelle_direction",
    # Electrical
    "voltage_phase_a",
    "voltage_phase_b",
    "voltage_phase_c",
    "frequency",
]

def _detect_timestamp_col(data: pd.DataFrame) -> str:
    """Detect timestamp column using column cache or fallback heuristics."""
    if _HAS_UTILS:
        col = ccu.column_cache.get_column("timestamp", data)
        if col and col in data.columns:
            return col

    # Fallback: find first datetime-like column
    for col in data.columns:
        if any(kw in col.lower() for kw in ["time", "date", "timestamp", "ts"]):
            try:
                pd.to_datetime(data[col].dropna().iloc[:5], errors="raise")
                return col
            except Exception:
                continue

    # Last resort: try parsing every column
    for col in data.columns:
        try:
            pd.to_datetime(data[col].dropna().iloc[:5], errors="raise")
            return col
        except Exception:
            continue

    return ""


# def _detect_column_map(data: pd.DataFrame) -> dict:
#     """Build param_key → column_name mapping using scada_utils or fallback."""
#     column_map = {}

#     if _HAS_UTILS:
#         for key in _PARAM_KEYS:
#             matched = su.find_matching_columns(data, key)
#             if matched:
#                 column_map[key] = matched[0]
#         return column_map

#     # Fallback: simple keyword matching
#     keyword_map = {
#         "power":             ["power", "kw", "watt"],
#         "wind_speed":        ["wind_speed", "windspeed", "wind speed", "ws"],
#         "rotor_speed":       ["rotor", "rpm"],
#         "yaw_speed":         ["yaw"],
#         "nacelle_direction": ["nacelle", "direction", "wind_dir"],
#         "voltage_phase_a":   ["voltage_a", "phase_a", "va"],
#         "voltage_phase_b":   ["voltage_b", "phase_b", "vb"],
#         "voltage_phase_c":   ["voltage_c", "phase_c", "vc"],
#         "frequency":         ["frequency", "freq", "hz"],
#     }
#     cols_lower = {c.lower(): c for c in data.columns}
#     for key, keywords in keyword_map.items():
#         for kw in keywords:
#             for col_lower, col_orig in cols_lower.items():
#                 if kw in col_lower:
#                     column_map[key] = col_orig
#                     break
#             if key in column_map:
#                 break

#     return column_map

def _detect_column_map(data: pd.DataFrame) -> dict:

    if _HAS_UTILS:
        from models.scada_utils import resolve_columns
        return resolve_columns(data, _PARAM_KEYS)

    # ── Fallback: keyword matching (no scada_utils available) ────────────────
    # Each keyword list is exclusive to its physical signal.
    keyword_map = {
        "power":            ["p_act", "activepower", "power_output", "power"],
        "wind_speed":       ["v_win", "windspeed", "wind_speed", "wind speed"],
        "rotor_speed":      ["n_rot", "rotorspeed", "rotor_speed"],
        "generator_speed":  ["n_gen", "generatorspeed", "generator_speed"],
        "pitch_blade_1":    ["bl1_act", "blade1pitch", "pitch1", "pitchangle1"],
        "pitch_blade_2":    ["bl2_act", "blade2pitch", "pitch2", "pitchangle2"],
        "pitch_blade_3":    ["bl3_act", "blade3pitch", "pitch3", "pitchangle3"],
        "yaw_position":     ["yawposition", "yaw_position", "nacelleangle", "yawangle"],
        "yaw_speed":        ["yawspeed", "yaw_speed", "yawrate"],
        "nacelle_direction":["pos_nac", "nacelle_dir", "wind_dir", "direction"],
        "voltage_phase_a":  ["u_a_n", "voltage_a", "phase_a", "va"],
        "voltage_phase_b":  ["u_b_n", "voltage_b", "phase_b", "vb"],
        "voltage_phase_c":  ["u_c_n", "voltage_c", "phase_c", "vc"],
        "frequency":        ["freq_avg", "frequency", "freq"],
    }
    cols_lower = {c.lower(): c for c in data.columns}
    column_map = {}
    for key, keywords in keyword_map.items():
        for kw in keywords:
            for col_lower, col_orig in cols_lower.items():
                if kw in col_lower:
                    column_map[key] = col_orig
                    break
            if key in column_map:
                break
    return column_map

# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
_DASH_PORT = 8050


def open_timeseries(data: pd.DataFrame, turbine_name: str = "Unknown", port: int = _DASH_PORT):
    """
    Push data to Dash store, start server if needed, open browser tab.
    Safe to call for N turbines — each gets its own URL key.
    Server starts only once regardless of how many times called.

    Parameters
    ----------
    data         : pd.DataFrame  — turbine SCADA data
    turbine_name : str           — turbine/page label shown in UI
    port         : int           — Dash server port (default 8050)
    """
    if data is None or data.empty:
        print(f"[TimeSeries] No data for {turbine_name}, skipping.")
        return

    # Unique key per turbine+session — uses id(data) for uniqueness
    turbine_key   = f"{turbine_name}_{id(data)}"
    timestamp_col = _detect_timestamp_col(data)
    column_map    = _detect_column_map(data)

    if not timestamp_col:
        print(f"[TimeSeries] WARNING: No timestamp column detected for {turbine_name}.")

    # Push to shared store (same Python process as Dash server)
    dash_app.stores[turbine_key] = {
        "raw_data":      data,
        "timestamp_col": timestamp_col,
        "turbine_name":  turbine_name,
        "column_map":    column_map,
    }

    print(f"[TimeSeries] Stored data for '{turbine_name}' → key: {turbine_key}")
    print(f"[TimeSeries] Rows: {len(data)} | Timestamp col: '{timestamp_col}'")
    print(f"[TimeSeries] Columns mapped: {list(column_map.keys())}")

    # Start Dash server (no-op if already running)
    dash_app.start_server(port=port)

    # Open browser tab — each turbine gets its own URL
    url = f"http://127.0.0.1:{port}/?turbine={turbine_key}"
    print(f"[TimeSeries] Opening browser → {url}")
    webbrowser.open(url)


def cleanup(turbine_name: str, data: pd.DataFrame):
    """
    Remove turbine data from store when done.
    Call this if you want to free RAM after closing the browser tab.
    """
    key = f"{turbine_name}_{id(data)}"
    removed = dash_app.stores.pop(key, None)
    if removed is not None:
        print(f"[TimeSeries] Cleaned up store for key: {key}")