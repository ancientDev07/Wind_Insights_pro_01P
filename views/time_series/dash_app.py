# dash_app.py  — project root
# Full Dash-based Time Series Analysis UI
# One server, N turbine sessions via ?turbine=key URL param

import threading
import pandas as pd
import numpy as np
import dash
from dash import dcc, html, dash_table, Input, Output, State, callback_context
import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────────────────────
# Shared in-memory store  (single source of truth — lives in THIS module)
# ─────────────────────────────────────────────────────────────────────────────
stores: dict = {}
# Structure per key:
# {
#   "raw_data":      pd.DataFrame,
#   "timestamp_col": str,
#   "turbine_name":  str,
#   "column_map":    { "power": "col_name", "wind_speed": "col_name", ... }
# }

_server_started = False

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
COLOR_MAP = {
    "power":             "#3498DB",
    "wind_speed":        "#2ECC71",
    "rotor_speed":       "#E67E22",
    "yaw_speed":         "#9B59B6",
    "nacelle_direction": "#1ABC9C",
    "voltage_phase_a":   "#00CED1",
    "voltage_phase_b":   "#FF6B6B",
    "voltage_phase_c":   "#4ECDC4",
    "frequency":         "#FFD93D",
}

LABEL_MAP = {
    "power":             "Power (kW)",
    "wind_speed":        "Wind Speed (m/s)",
    "rotor_speed":       "Rotor Speed (rpm)",
    "yaw_speed":         "Nacelle Angle (deg/s)",
    "nacelle_direction": "Wind Direction (deg)",
    "voltage_phase_a":   "Voltage Phase A (V)",
    "voltage_phase_b":   "Voltage Phase B (V)",
    "voltage_phase_c":   "Voltage Phase C (V)",
    "frequency":         "Frequency (Hz)",
}

# ─────────────────────────────────────────────────────────────────────────────
# Styles  (dark industrial theme matching existing PyQt5 app palette)
# ─────────────────────────────────────────────────────────────────────────────
BG_DARK   = "#1C2833"
BG_PANEL  = "#2C3E50"
BG_CARD   = "#34495E"
BG_CHART  = "#1a1a1a"
BORDER    = "#5D6D7E"
TEXT      = "#ECF0F1"
TEXT_DIM  = "#BDC3C7"
ACCENT    = "#3498DB"
RED       = "#E74C3C"
GREY      = "#7F8C8D"
GREEN     = "#2ECC71"

SIDEBAR_W = "270px"


SIDEBAR_STYLE = {
    "width": SIDEBAR_W, "minWidth": SIDEBAR_W, "maxWidth": SIDEBAR_W,
    "backgroundColor": BG_PANEL,
    "borderRight": f"1px solid {BORDER}",
    "display": "flex", "flexDirection": "column",
    "height": "100%",          # ← CHANGE from "100vh" to "100%" (inherits from parent)
    "overflowY": "auto",
    "overflowX": "hidden",     # ← ADD: prevent horizontal scroll bleed
    "padding": "0", "gap": "0",
}


CARD_STYLE = {
    "backgroundColor": BG_CARD,
    "border": f"1px solid {BORDER}",
    "borderRadius": "4px",
    "margin": "6px 8px",
    "overflow": "hidden",
}

CARD_HEADER = {
    "backgroundColor": ACCENT,
    "color": "white",
    "fontWeight": "bold",
    "fontSize": "11px",
    "padding": "5px 10px",
    "letterSpacing": "0.5px",
    "textTransform": "uppercase",
}

CARD_BODY = {
    "padding": "8px 10px",
    "display": "flex",
    "flexDirection": "column",
    "gap": "5px",
}

LABEL_STYLE = {
    "color": TEXT_DIM,
    "fontSize": "10px",
    "textTransform": "uppercase",
    "letterSpacing": "0.5px",
    "marginBottom": "2px",
}

INPUT_STYLE = {
    "backgroundColor": BG_DARK,
    "color": TEXT,
    "border": f"1px solid {BORDER}",
    "borderRadius": "3px",
    "padding": "5px 8px",
    "width": "100%",
    "fontSize": "11px",
    "boxSizing": "border-box",
}

DROPDOWN_STYLE = {
    "backgroundColor": BG_DARK,
    "color": TEXT,
    "fontSize": "11px",
}

CB_STYLE = {
    "color": TEXT,
    "fontSize": "11px",
    "marginBottom": "2px",
}

def _btn(label, btn_id, color=ACCENT):
    return html.Button(
        label,
        id=btn_id,
        style={
            "backgroundColor": color,
            "color": "white",
            "border": "none",
            "borderRadius": "3px",
            "padding": "7px 10px",
            "width": "100%",
            "fontSize": "11px",
            "cursor": "pointer",
            "textAlign": "left",
            "fontWeight": "500",
        }
    )

def _card(title, *children):
    return html.Div(style=CARD_STYLE, children=[
        html.Div(title, style=CARD_HEADER),
        html.Div(style=CARD_BODY, children=list(children)),
    ])

def _cb(label, cb_id):
    return dcc.Checklist(
        id=cb_id,
        options=[{"label": f"  {label}", "value": "1"}],
        value=[],
        style=CB_STYLE,
        inputStyle={"marginRight": "6px", "accentColor": ACCENT},
    )

def _row(*children):
    return html.Div(
        style={"display": "flex", "gap": "6px", "alignItems": "center"},
        children=list(children)
    )

def _lbl(text):
    return html.Span(text, style={"color": TEXT_DIM, "fontSize": "11px",
                                   "whiteSpace": "nowrap", "minWidth": "38px"})

# ─────────────────────────────────────────────────────────────────────────────
# App + Layout
# ─────────────────────────────────────────────────────────────────────────────
import os as _os

# Resolve path to the existing WWIP.ico in resources/app_icon/
_ASSETS_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "resources", "app_icon")

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="Wind Data Insight Pro — Time Series",
    assets_folder=_os.path.abspath(_ASSETS_DIR),   # ← serves WWIP.ico as favicon
    assets_url_path="/assets",
)

app.layout = html.Div(
    style={
        "display": "flex", "flexDirection": "column",
        "height": "100vh", "width": "100vw",
        "backgroundColor": BG_DARK,
        "fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
        "overflow": "hidden",
    },
    children=[
        dcc.Location(id="url", refresh=False),

        # ── Title bar ─────────────────────────────────────────────────────
        html.Div(
            id="title-bar",
            style={
                "backgroundColor": BG_DARK,
                "borderBottom": f"2px solid {ACCENT}",
                "padding": "8px 16px",
                "display": "flex",
                "alignItems": "center",
                "gap": "12px",
                "flexShrink": "0",
            },
            children=[
                html.Span("📈", style={"fontSize": "18px"}),
                html.Span(
                    "Time Series Analysis — Wind Data Insight Pro",
                    id="title-text",
                    style={
                        "color": TEXT,
                        "fontSize": "14px",
                        "fontWeight": "600",
                        "letterSpacing": "0.3px",
                    }
                ),
                # html.Div(style={"flex": "1"}),
                html.Div(
                    id="status-bar",
                    style={
                        "color": TEXT_DIM,
                        "fontSize": "11px",
                        "backgroundColor": BG_CARD,
                        "padding": "3px 10px",
                        "borderRadius": "12px",
                        "border": f"1px solid {BORDER}",
                    }
                ),
            ]
        ),

        # ── Main body ─────────────────────────────────────────────────────
        html.Div(
            style={"display": "flex", "flex": "1", "overflow": "hidden"},
            children=[

                # ── LEFT SIDEBAR ──────────────────────────────────────────
                html.Div(
                    style=SIDEBAR_STYLE,
                    children=[
                        # Filters

                        _card("🔍  Filters",
                            _cb("600s Cycle Only", "cb-600s"),
                            _cb("Date Filter", "cb-date"),
                            html.Div(id="date-inputs", style={"display": "none"}, children=[
                                html.Div([
                                    html.Span("Start:", style=LABEL_STYLE),
                                    dcc.Input(id="start-date", type="text", placeholder="DD-MM-YYYY",
                                              debounce=True, style=INPUT_STYLE),
                                ], style={"marginBottom": "4px"}),
                                html.Div([
                                    html.Span("End:", style=LABEL_STYLE),
                                    dcc.Input(id="end-date", type="text", placeholder="DD-MM-YYYY",
                                              debounce=True, style=INPUT_STYLE),
                                ]),
                            ]),
                            _cb("Time Filter", "cb-time"),
                            html.Div(id="time-inputs", style={"display": "none"}, children=[
                                html.Div([
                                    html.Span("Start:", style=LABEL_STYLE),
                                    dcc.Input(id="start-time", type="text", placeholder="HH:MM",
                                              debounce=True, style=INPUT_STYLE),
                                ], style={"marginBottom": "4px"}),
                                html.Div([
                                    html.Span("End:", style=LABEL_STYLE),
                                    dcc.Input(id="end-time", type="text", placeholder="HH:MM",
                                              debounce=True, style=INPUT_STYLE),
                                ]),
                            ]),
                        ),

                        # Parameters
                        _card("📊  Parameters",
                            html.Div(
                                style={
                                    "maxHeight": "210px",
                                    "overflowY": "auto",
                                    "overflowX": "hidden",
                                    "display": "flex",
                                    "flexDirection": "column",
                                    "gap": "5px",
                                },
                                children=[
                                    html.Div("⚡  Power",
                                             style={**LABEL_STYLE, "color": "#F39C12", "marginTop": "2px"}),
                                    _cb("Power — Full",        "cb-power-full"),
                                    _cb("Power — Active",      "cb-power-active"),
                                    _cb("Power — Reactive",    "cb-power-reactive"),
                                    html.Div("💨  Speed",
                                             style={**LABEL_STYLE, "color": GREEN, "marginTop": "6px"}),
                                    _cb("Wind Speed (m/s)",    "cb-wind"),
                                    _cb("Rotor Speed (rpm)",   "cb-rotor"),
                                    _cb("Nacelle Angle",       "cb-yaw"),
                                    _cb("Wind Direction",      "cb-nacelle"),
                                    html.Div("🔌  Electrical",
                                             style={**LABEL_STYLE, "color": "#00CED1", "marginTop": "6px"}),
                                    _cb("Voltage Phase A (V)", "cb-va"),
                                    _cb("Voltage Phase B (V)", "cb-vb"),
                                    _cb("Voltage Phase C (V)", "cb-vc"),
                                    _cb("Frequency (Hz)",      "cb-freq"),
                                ]
                            ),
                        ),
                        
                        # Plot Options
                        _card("⚙  Plot Options",
                            _cb("Show Grid",    "cb-grid"),
                            _cb("Show Legend",  "cb-legend"),
                            _cb("Show Markers", "cb-markers"),
                        ),


                        # Actions
                        _card("▶  Actions",
                            _btn("📊  Plot",       "btn-plot",   ACCENT),
                            _btn("🔄  Reset",      "btn-reset",  RED),
                            _btn("🗑️  Clear",      "btn-clear",  GREY),
                            _btn("💾  Export CSV", "btn-export", "#27AE60"),
                            dcc.Download(id="download-csv"),
                        ),

                        

                        # Spacer
                        html.Div(style={"flex": "1"}),

                        # Footer
                        html.Div(
                            "Wind Data Insight Pro",
                            style={
                                "color": BORDER,
                                "fontSize": "10px",
                                "textAlign": "center",
                                "padding": "8px",
                                "borderTop": f"1px solid {BORDER}",
                            }
                        ),
                    ]
                ),

                # ── RIGHT PANEL: Chart + Stats ────────────────────────────
                html.Div(
                    style={
                        "flex": "1", "display": "flex",
                        "flexDirection": "column", "overflow": "hidden",
                        "minHeight": "0",
                        "backgroundColor": BG_DARK,
                    },
                    children=[

                        # Chart
                        dcc.Graph(
                            id="ts-graph",
                            style={"flex": "1", "minHeight": "0"}, 
                            # REPLACE config in dcc.Graph
                            config={
                                "displayModeBar": True,
                                "displaylogo":    False,
                                "responsive":     True,
                                "scrollZoom":     True,    # ← ADD: enables scroll-wheel zoom
                                "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                                "toImageButtonOptions": {
                                    "format": "png", "scale": 2,
                                    "filename": "timeseries_export",
                                },
                            },
                        ),

                        # Statistics panel
                        html.Div(
                            style={
                                "backgroundColor": BG_PANEL,
                                "borderTop": f"2px solid {BORDER}",
                                "flexShrink": "0",
                                "height": "220px",
                                "minHeight": "220px",
                                "flexShrink": "0",
                                "display": "flex",
                                "flexDirection": "column",
                            },
                            children=[
                                html.Div(
                                    "📋  Statistics",
                                    style={
                                        **CARD_HEADER,
                                        "backgroundColor": BG_DARK,
                                        "borderBottom": f"1px solid {BORDER}",
                                        "flexShrink": "0",
                                    }
                                ),
                                html.Div(
                                    style={"overflowY": "auto", "flex": "1", "minHeight": "0"},
                                    children=[
                                        dash_table.DataTable(
                                            id="stats-table",
                                            columns=[
                                                {"name": "Parameter", "id": "param"},
                                                {"name": "Mean",      "id": "mean"},
                                                {"name": "Std Dev",   "id": "std"},
                                                {"name": "Min",       "id": "min"},
                                                {"name": "Max",       "id": "max"},
                                                {"name": "Count",     "id": "count"},
                                            ],
                                            data=[],
                                            style_as_list_view=True,
                                            style_table={"backgroundColor": BG_CARD, "minWidth": "100%"},
                                            style_header={
                                                "backgroundColor": BG_DARK,
                                                "color": TEXT_DIM,
                                                "fontWeight": "bold",
                                                "fontSize": "10px",
                                                "textTransform": "uppercase",
                                                "letterSpacing": "0.5px",
                                                "border": f"1px solid {BORDER}",
                                                "padding": "6px 10px",
                                            },
                                            style_cell={
                                                "backgroundColor": BG_CARD,
                                                "color": TEXT,
                                                "fontSize": "11px",
                                                "padding": "5px 10px",
                                                "border": f"1px solid {BORDER}",
                                                "fontFamily": "'Courier New', monospace",
                                            },
                                            style_data_conditional=[
                                                {
                                                    "if": {"row_index": "odd"},
                                                    "backgroundColor": BG_PANEL,
                                                },
                                                {
                                                    "if": {"column_id": "param"},
                                                    "fontFamily": "'Segoe UI', Arial, sans-serif",
                                                    "fontWeight": "500",
                                                    "color": "#AED6F1",
                                                },
                                            ],
                                        ),
                                    ]
                                ),
                            ]
                        ),
                    ]
                ),
            ]
        ),
    ]
)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: Apply filters
# ─────────────────────────────────────────────────────────────────────────────
def _apply_filters(df, timestamp_col, cb600, cb_date, start_date, end_date,
                   cb_time, start_time, end_time):
    df = df.copy()
    df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors="coerce")

    # 600s cycle filter
    if cb600 and "1" in cb600:
        if "Count" in df.columns:
            df = df[df["Count"] == 600]

    # Date filter
    if cb_date and "1" in cb_date:
        if start_date and start_date.strip():
            sd = pd.to_datetime(start_date.strip(), format="%d-%m-%Y", errors="coerce")
            if pd.notna(sd):
                df = df[df[timestamp_col] >= sd]
        if end_date and end_date.strip():
            ed = pd.to_datetime(end_date.strip(), format="%d-%m-%Y", errors="coerce")
            if pd.notna(ed):
                df = df[df[timestamp_col] <= ed + pd.Timedelta(days=1)]

    # Time-of-day filter
    if cb_time and "1" in cb_time:
        if start_time and start_time.strip():
            st = pd.to_datetime(start_time.strip(), format="%H:%M", errors="coerce")
            if pd.notna(st):
                df = df[df[timestamp_col].dt.time >= st.time()]
        if end_time and end_time.strip():
            et = pd.to_datetime(end_time.strip(), format="%H:%M", errors="coerce")
            if pd.notna(et):
                df = df[df[timestamp_col].dt.time <= et.time()]

    return df.reset_index(drop=True)




# ─────────────────────────────────────────────────────────────────────────────
# Helper: Apply time window + slider position
# ─────────────────────────────────────────────────────────────────────────────
def _apply_window_from_start(df, timestamp_col, preset):
    if df.empty or not preset:
        return df

    ts = df[timestamp_col]
    if ts.empty:
        return df

    start = ts.min()
    if preset == "1w":
        end = start + pd.Timedelta(weeks=1)
    elif preset == "1mo":
        end = start + pd.DateOffset(months=1)
    elif preset == "1d":
        end = start + pd.Timedelta(days=1)
    else:
        return df

    return df[(ts >= start) & (ts <= end)].reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: Insert NaN gaps at day boundaries and time gaps > 1h
# ─────────────────────────────────────────────────────────────────────────────
def _insert_gaps(df, timestamp_col, col, max_gap_hours=1):
    if df.empty:
        return df
    result_rows = []
    df = df.sort_values(timestamp_col).reset_index(drop=True)
    for i, row in df.iterrows():
        result_rows.append(row)
        if i < len(df) - 1:
            gap = (df.loc[i + 1, timestamp_col] - row[timestamp_col]).total_seconds() / 3600
            if gap > max_gap_hours:
                nan_row = row.copy()
                nan_row[col] = np.nan
                result_rows.append(nan_row)
    return pd.DataFrame(result_rows).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: Build Plotly figure
# ─────────────────────────────────────────────────────────────────────────────
def _build_figure(df, timestamp_col, selected_params, show_grid, show_legend, show_markers):
    fig  = go.Figure()
    mode = "lines+markers" if show_markers else "lines"

    for param_key, col, label, power_type in selected_params:
        if col not in df.columns:
            continue

        plot_df = _insert_gaps(df[[timestamp_col, col]].copy(), timestamp_col, col)
        y = pd.to_numeric(plot_df[col], errors="coerce")

        # Power type masking
        if power_type == "active":
            y = y.where(y >= 0)
        elif power_type == "reactive":
            y = y.where(y < 0)

        color = COLOR_MAP.get(param_key, ACCENT)

        fig.add_trace(go.Scatter(
            x=plot_df[timestamp_col],
            y=y,
            name=label,
            mode=mode,
            line=dict(color=color, width=1.8),
            marker=dict(size=4, color=color) if show_markers else {},
            connectgaps=False,
            hovertemplate=f"<b>{label}</b><br>%{{x|%Y-%m-%d %H:%M}}<br>%{{y:.3f}}<extra></extra>",
        ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BG_PANEL,
        plot_bgcolor=BG_CHART,
        font=dict(color=TEXT, size=11),
        autosize=True,
        margin=dict(l=65, r=30, t=30, b=55),
        hovermode="x unified",
        showlegend=show_legend,
        legend=dict(
            x=0.01, y=0.99,
            bgcolor="rgba(28,40,51,0.85)",
            bordercolor=BORDER, borderwidth=1,
            font=dict(size=11),
        ),
        xaxis=dict(
            title="Time",
            type="date",
            showgrid=show_grid,
            gridcolor="#2C3E50",
            gridwidth=1,
            zeroline=False,
            rangeslider=dict(visible=False),
            fixedrange=False, 
            rangeselector=dict(
                bgcolor=BG_CARD,
                activecolor=ACCENT,
                font=dict(color=TEXT, size=10),
                buttons=[
                    dict(count=6,    label="6h",  step="hour", stepmode="backward"),
                    dict(count=1,    label="1d",  step="day",  stepmode="backward"),
                    dict(count=7,    label="1w",  step="day",  stepmode="backward"),
                    dict(count=1,    label="1mo", step="month",stepmode="backward"),
                    dict(step="all", label="All"),
                ],
            ),
        ),
        yaxis=dict(
            title="Value",
            showgrid=show_grid,
            gridcolor="#2C3E50",
            gridwidth=1,
            zeroline=False,fixedrange=False,
        ),
        dragmode="pan",
    )

    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Helper: Compute statistics
# ─────────────────────────────────────────────────────────────────────────────
def _compute_stats(df, selected_params):
    rows = []
    for param_key, col, label, power_type in selected_params:
        if col not in df.columns:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        if power_type == "active":
            s = s[s >= 0]
        elif power_type == "reactive":
            s = s[s < 0]
        s = s.dropna()
        if s.empty:
            continue
        rows.append({
            "param": label,
            "mean":  f"{s.mean():.3f}",
            "std":   f"{s.std():.3f}",
            "min":   f"{s.min():.3f}",
            "max":   f"{s.max():.3f}",
            "count": f"{len(s):,}",
        })
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Helper: Get turbine entry from URL search param
# ─────────────────────────────────────────────────────────────────────────────
def _get_entry(search):
    if not search or "turbine=" not in search:
        return None, None
    key   = search.split("turbine=")[-1].split("&")[0]
    entry = stores.get(key)
    return key, entry


# ─────────────────────────────────────────────────────────────────────────────
# Main callback
# ─────────────────────────────────────────────────────────────────────────────

@app.callback(
    Output("ts-graph",    "figure"),
    Output("stats-table", "data"),
    Output("status-bar",  "children"),
    Output("title-text",  "children"),
    Output("start-date",  "value"),
    Output("end-date",    "value"),
    Output("start-time",  "value"),
    Output("end-time",    "value"),

    Input("btn-plot",  "n_clicks"),
    Input("btn-clear", "n_clicks"),
    Input("btn-reset", "n_clicks"),

    State("url",               "search"),
    State("cb-600s",           "value"),
    State("cb-date",           "value"),
    State("start-date",        "value"),
    State("end-date",          "value"),
    State("cb-time",           "value"),
    State("start-time",        "value"),
    State("end-time",          "value"),
    State("cb-power-full",     "value"),
    State("cb-power-active",   "value"),
    State("cb-power-reactive", "value"),
    State("cb-wind",           "value"),
    State("cb-rotor",          "value"),
    State("cb-yaw",            "value"),
    State("cb-nacelle",        "value"),
    State("cb-va",             "value"),
    State("cb-vb",             "value"),
    State("cb-vc",             "value"),
    State("cb-freq",           "value"),
    State("cb-grid",           "value"),
    State("cb-legend",         "value"),
    State("cb-markers",        "value"),
    prevent_initial_call=False,
)
def main_callback(
    n_plot, n_clear, n_reset,
    search,
    cb600, cb_date, start_date, end_date,
    cb_time, start_time, end_time,
    cb_pf, cb_pa, cb_pr,
    cb_wind, cb_rotor, cb_yaw, cb_nacelle,
    cb_va, cb_vb, cb_vc, cb_freq,
    cb_grid, cb_legend, cb_markers,
):
    _no = (dash.no_update,) * 4   # shorthand for 4 input no_updates

    def empty_fig(msg=""):
        f = go.Figure()
        f.update_layout(
            paper_bgcolor=BG_PANEL, plot_bgcolor=BG_CHART,
            font=dict(color=TEXT),
            annotations=[dict(
                text=msg, x=0.5, y=0.5, xref="paper", yref="paper",
                showarrow=False, font=dict(size=14, color=TEXT_DIM),
            )] if msg else [],
        )
        return f

    triggered = (
        callback_context.triggered[0]["prop_id"]
        if callback_context.triggered else ""
    )

    DEFAULT_TITLE = "Time Series Analysis — Wind Data Insight Pro"

    if "btn-clear" in triggered:
        return (empty_fig("Chart cleared. Select parameters and click Plot."),
                [], "Cleared.", DEFAULT_TITLE, *_no)

    _, entry = _get_entry(search)
    if not entry:
        return (empty_fig("Waiting for data...  Open from Control Panel."),
                [], "No turbine loaded.", DEFAULT_TITLE, *_no)

    raw_df        = entry.get("raw_data")
    timestamp_col = entry.get("timestamp_col", "")
    turbine_name  = entry.get("turbine_name", "Unknown")
    column_map    = entry.get("column_map", {})
    title         = f"Time Series Analysis — {turbine_name}"

    if raw_df is None or raw_df.empty or not timestamp_col:
        return (empty_fig("No data available."), [], "No data.", title, *_no)

    if "btn-reset" in triggered:
        return (empty_fig("Filters reset. Select parameters and click Plot."),
                [], "Reset.", title, "", "", "", "")

    if "btn-plot" not in triggered and triggered:
        return (dash.no_update, dash.no_update, dash.no_update, title, *_no)

    df = _apply_filters(
        raw_df, timestamp_col,
        cb600, cb_date, start_date, end_date,
        cb_time, start_time, end_time,
    )
    if df.empty:
        return (empty_fig("No data after filtering."), [], "No data after filters.", title, *_no)

    df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors="coerce")
    df = df.sort_values(timestamp_col).reset_index(drop=True)

    param_checks = [
        ("power",             column_map.get("power"),             cb_pf,      "Power (kW)",          "full"),
        ("power",             column_map.get("power"),             cb_pa,      "Active Power (kW)",   "active"),
        ("power",             column_map.get("power"),             cb_pr,      "Reactive Power (kW)", "reactive"),
        ("wind_speed",        column_map.get("wind_speed"),        cb_wind,    LABEL_MAP["wind_speed"],        None),
        ("rotor_speed",       column_map.get("rotor_speed"),       cb_rotor,   LABEL_MAP["rotor_speed"],       None),
        ("yaw_speed",         column_map.get("yaw_speed"),         cb_yaw,     LABEL_MAP["yaw_speed"],         None),
        ("nacelle_direction", column_map.get("nacelle_direction"), cb_nacelle, LABEL_MAP["nacelle_direction"], None),
        ("voltage_phase_a",   column_map.get("voltage_phase_a"),  cb_va,      LABEL_MAP["voltage_phase_a"],   None),
        ("voltage_phase_b",   column_map.get("voltage_phase_b"),  cb_vb,      LABEL_MAP["voltage_phase_b"],   None),
        ("voltage_phase_c",   column_map.get("voltage_phase_c"),  cb_vc,      LABEL_MAP["voltage_phase_c"],   None),
        ("frequency",         column_map.get("frequency"),         cb_freq,    LABEL_MAP["frequency"],         None),
    ]

    selected = [
        (pk, col, label, pt)
        for pk, col, cb, label, pt in param_checks
        if cb and "1" in cb and col
    ]

    if not selected:
        return (empty_fig("Select at least one parameter from the sidebar."),
                [], "No parameters selected.", title, *_no)

    show_grid    = bool(cb_grid    and "1" in cb_grid)
    show_legend  = bool(cb_legend  and "1" in cb_legend)
    show_markers = bool(cb_markers and "1" in cb_markers)

    fig   = _build_figure(df, timestamp_col, selected, show_grid, show_legend, show_markers)
    stats = _compute_stats(df, selected)
    status = f"{len(df):,} rows  |  {len(selected)} parameter(s)  |  {turbine_name}"

    return (fig, stats, status, title, *_no)


# ─────────────────────────────────────────────────────────────────────────────
# Export callback
# ─────────────────────────────────────────────────────────────────────────────
@app.callback(
    Output("download-csv", "data"),
    Input("btn-export", "n_clicks"),
    State("url", "search"),
    prevent_initial_call=True,
)
def export_csv(n, search):
    _, entry = _get_entry(search)
    if not entry or entry.get("raw_data") is None:
        return dash.no_update
    df   = entry["raw_data"]
    name = entry.get("turbine_name", "turbine").replace(" ", "_")
    return dcc.send_data_frame(df.to_csv, f"TimeSeries_{name}.csv", index=False)

# ─────────────────────────────────────────────────────────────────────────────
# Update Call Fiter
# ─────────────────────────────────────────────────────────────────────────────

@app.callback(
    Output("date-inputs", "style"),
    Input("cb-date", "value"),
)
def toggle_date_inputs(cb_date):
    if cb_date and "1" in cb_date:
        return {"display": "block", "marginTop": "4px"}
    return {"display": "none"}


@app.callback(
    Output("time-inputs", "style"),
    Input("cb-time", "value"),
)
def toggle_time_inputs(cb_time):
    if cb_time and "1" in cb_time:
        return {"display": "block", "marginTop": "4px"}
    return {"display": "none"}


@app.callback(
    Output("start-date", "placeholder"),
    Output("end-date",   "placeholder"),
    Output("start-time", "placeholder"),
    Output("end-time",   "placeholder"),
    Input("url", "search"),
)

def update_filter_placeholders(search):
    _, entry = _get_entry(search)
    if not entry:
        return "DD-MM-YYYY", "DD-MM-YYYY", "HH:MM", "HH:MM"

    raw_df        = entry.get("raw_data")
    timestamp_col = entry.get("timestamp_col", "")
    if raw_df is None or raw_df.empty or not timestamp_col:
        return "DD-MM-YYYY", "DD-MM-YYYY", "HH:MM", "HH:MM"

    ts = pd.to_datetime(raw_df[timestamp_col], errors="coerce").dropna()
    if ts.empty:
        return "DD-MM-YYYY", "DD-MM-YYYY", "HH:MM", "HH:MM"

    return (
        ts.min().strftime("%d-%m-%Y"),
        ts.max().strftime("%d-%m-%Y"),
        "00:00",
        "23:59",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Server start  (call once from launcher — safe to call N times)
# ─────────────────────────────────────────────────────────────────────────────
def start_server(port: int = 8050):
    global _server_started
    if _server_started:
        return
    _server_started = True

    def _run():
        app.run(port=port, debug=False, use_reloader=False, dev_tools_silence_routes_logging=True)

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    import time
    import urllib.request
    for _ in range(20):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}", timeout=0.5)
            break
        except Exception:
            time.sleep(0.5)