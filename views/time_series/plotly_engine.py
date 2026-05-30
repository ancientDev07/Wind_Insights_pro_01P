# import json
# import pandas as pd
# import numpy as np
# from datetime import datetime

# class PlotlyTimeSeriesEngine:
#     """Render time-series data using Plotly.js"""
    
#     def __init__(self):
#         self.traces = []
#         self.layout = {}
    
#     def create_html(self, data, timestamp_col, selected_params, engine, show_grid=True, show_legend=True):
#        """Generate Plotly HTML using TSAnalysisEngine for data extraction"""
#        self.traces = []
       
#        # Color mapping
#        color_map = {
#            'power': '#3498DB',
#            'wind_speed': '#2ECC71',
#            'rotor_speed': '#E67E22',
#            'yaw_speed': '#9B59B6',
#            'nacelle_direction': "#1A9CBC",
#            'voltage_phase_a': '#00CED1',
#            'voltage_phase_b': '#FF6B6B',
#            'voltage_phase_c': '#4ECDC4',
#            'frequency': '#FFD93D'
#        }
       
#        label_map = {
#            'power': 'Power (kW)',
#            'wind_speed': 'Wind Speed (m/s)',
#            'rotor_speed': 'Rotor Speed (rpm)',
#            'yaw_speed': 'Nacelle Angle (deg/s)',
#            'nacelle_direction': 'Wind Direction (deg)',
#            'voltage_phase_a': 'Voltage Phase A (V)',
#            'voltage_phase_b': 'Voltage Phase B (V)',
#            'voltage_phase_c': 'Voltage Phase C (V)',
#            'frequency': 'Frequency (Hz)'
#        }
       
#        # Extract data using TSAnalysisEngine
#        # Extract data using TSAnalysisEngine
#        for param in selected_params:
#            col = param['column']
#            param_key = param['param_key']
#            power_type = param.get('power_type')
           
#            if col not in data.columns:
#                continue
           
#            # Use engine to extract data
#            if param_key == 'power':
#                plot_data = engine.get_power_data(data, col, power_type)
#            else:
#                plot_data = engine.get_plot_data(data, col, param_key, power_type)
           
#            if plot_data is None:
#                continue
           
#            x_vals = plot_data['timestamps']
#            y_vals = plot_data['values']
           
#            if not x_vals or not y_vals:
#                continue
           
#            # Convert Timestamp objects to ISO strings for JSON serialization
#            x_vals = [pd.Timestamp(t).isoformat() if pd.notna(t) else None for t in x_vals]
           
#            label = param.get('display', label_map.get(param_key, col))
           
#            trace = {
#                'x': x_vals,
#                'y': y_vals,
#                'name': label,
#                'type': 'scatter',
#                'mode': 'lines',
#                'line': {'color': color_map.get(param_key, '#3498DB'), 'width': 2},
#                'hovertemplate': '<b>' + label + '</b><br>%{x}<br>%{y:.2f}<extra></extra>'
#            }
           
#            self.traces.append(trace)

       
#        # Layout configuration (same as before)
#        self.layout = {
#            'title': 'Time Series Analysis',
#            'xaxis': {
#                'title': 'Time',
#                'type': 'date',
#                'rangeslider': {'visible': True, 'thickness': 0.05},
#                'rangeselector': {
#                    'buttons': [
#                        {'count': 6, 'label': '6h', 'step': 'hour'},
#                        {'count': 1, 'label': '1d', 'step': 'day'},
#                        {'count': 7, 'label': '1w', 'step': 'day'},
#                        {'step': 'all', 'label': 'All'}
#                    ]
#                }
#            },
#            'yaxis': {'title': 'Value'},
#            'hovermode': 'x unified',
#            'plot_bgcolor': '#1a1a1a',
#            'paper_bgcolor': '#2C3E50',
#            'font': {'color': '#ECF0F1', 'size': 11},
#            'margin': {'l': 60, 'r': 40, 't': 40, 'b': 60},
#            'showlegend': show_legend,
#            'legend': {'x': 0.01, 'y': 0.99, 'bgcolor': 'rgba(0,0,0,0.5)'}
#        }
       
#        if not show_grid:
#            self.layout['xaxis']['showgrid'] = False
#            self.layout['yaxis']['showgrid'] = False
       
#        # Generate HTML (same as before)
#        html = f"""
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <meta charset="utf-8">
#         <script src="https://cdn.plot.ly/plotly-2.26.0.min.js" charset="utf-8"></script>
#         <style>
#             body {{ margin: 0; padding: 0; background: #2C3E50; font-family: Arial, sans-serif; }}
#             #plot {{ width: 100%; height: 100vh; }}
#         </style>
#     </head>
#     <body>
#         <div id="plot"></div>
#         <script>
#             function initPlot() {{
#                 if (typeof Plotly === 'undefined') {{
#                     setTimeout(initPlot, 100);
#                     return;
#                 }}
#                 var data = {json.dumps(self.traces)};
#                 var layout = {json.dumps(self.layout)};
#                 var config = {{
#                     responsive: true,
#                     displayModeBar: true,
#                     displaylogo: false,
#                     modeBarButtonsToRemove: ['lasso2d', 'select2d']
#                 }};
#                 Plotly.newPlot('plot', data, layout, config);
#             }}
#             initPlot();
#         </script>
#     </body>
#     </html>
#     """

#        return html

# # plotly_engine.py
# import pandas as pd
# import numpy as np
# import plotly.graph_objects as go
# import plotly.io as pio

# class PlotlyTimeSeriesEngine:
#     """Render time-series using Python Plotly (offline-safe, JS embedded)."""

#     COLOR_MAP = {
#         'power':             '#3498DB',
#         'wind_speed':        '#2ECC71',
#         'rotor_speed':       '#E67E22',
#         'yaw_speed':         '#9B59B6',
#         'nacelle_direction': '#1ABC9C',
#         'voltage_phase_a':   '#00CED1',
#         'voltage_phase_b':   '#FF6B6B',
#         'voltage_phase_c':   '#4ECDC4',
#         'frequency':         '#FFD93D',
#     }
#     LABEL_MAP = {
#         'power':             'Power (kW)',
#         'wind_speed':        'Wind Speed (m/s)',
#         'rotor_speed':       'Rotor Speed (rpm)',
#         'yaw_speed':         'Nacelle Angle (deg/s)',
#         'nacelle_direction': 'Wind Direction (deg)',
#         'voltage_phase_a':   'Voltage Phase A (V)',
#         'voltage_phase_b':   'Voltage Phase B (V)',
#         'voltage_phase_c':   'Voltage Phase C (V)',
#         'frequency':         'Frequency (Hz)',
#     }

#     def create_html(self, data, timestamp_col, selected_params,
#                     engine, show_grid=True, show_legend=True):
#         """Build offline Plotly HTML. No CDN — JS is embedded."""
#         traces = []

#         for param in selected_params:
#             col       = param['column']
#             param_key = param['param_key']
#             power_type = param.get('power_type')

#             if col not in data.columns:
#                 continue

#             plot_data = (engine.get_power_data(data, col, power_type)
#                          if param_key == 'power'
#                          else engine.get_plot_data(data, col, param_key, power_type))

#             if not plot_data:
#                 continue

#             x_vals = [pd.Timestamp(t).isoformat() if pd.notna(t) else None
#                       for t in plot_data['timestamps']]
#             y_vals = plot_data['values']

#             if not x_vals or not y_vals:
#                 continue

#             label = param.get('display', self.LABEL_MAP.get(param_key, col))
#             color = self.COLOR_MAP.get(param_key, '#3498DB')

#             traces.append(go.Scatter(
#                 x=x_vals, y=y_vals,
#                 name=label,
#                 mode='lines',
#                 line=dict(color=color, width=2),
#                 hovertemplate=f'<b>{label}</b><br>%{{x}}<br>%{{y:.2f}}<extra></extra>',
#                 connectgaps=False,   # honours NaN gaps inserted by logic layer
#             ))

#         fig = go.Figure(data=traces)

#         fig.update_layout(
#             title='Time Series Analysis',
#             xaxis=dict(
#                 title='Time',
#                 type='date',
#                 showgrid=show_grid,
#                 rangeslider=dict(visible=True, thickness=0.05),
#                 rangeselector=dict(buttons=[
#                     dict(count=6,  label='6h',  step='hour', stepmode='backward'),
#                     dict(count=1,  label='1d',  step='day',  stepmode='backward'),
#                     dict(count=7,  label='1w',  step='day',  stepmode='backward'),
#                     dict(step='all', label='All'),
#                 ]),
#             ),
#             yaxis=dict(title='Value', showgrid=show_grid),
#             hovermode='x unified',
#             plot_bgcolor='#1a1a1a',
#             paper_bgcolor='#2C3E50',
#             font=dict(color='#ECF0F1', size=11),
#             margin=dict(l=60, r=40, t=40, b=60),
#             showlegend=show_legend,
#             legend=dict(x=0.01, y=0.99, bgcolor='rgba(0,0,0,0.5)'),
#         )

#         config = dict(
#             responsive=True,
#             displayModeBar=True,
#             displaylogo=False,
#             modeBarButtonsToRemove=['lasso2d', 'select2d'],
#         )

#         # include_plotlyjs='cdn' → False, True embeds ~3 MB JS once per HTML
#         return pio.to_html(
#             fig,
#             include_plotlyjs=True,   # ← embeds JS, no network required
#             full_html=True,
#             config=config,
#         )

import json
import os
import pandas as pd
import numpy as np
from datetime import datetime


class PlotlyTimeSeriesEngine:
    """Render time-series data using Plotly.js (offline)"""

    def __init__(self):
        self.traces = []
        self.layout = {}
        js_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'js', 'plotly-3.4.0.min.js')
        )
        try:
            with open(js_path, 'r', encoding='utf-8') as f:
                self._plotly_js_inline = f.read()
        except Exception as e:
            self._plotly_js_inline = None
            print(f"[PlotlyEngine] WARNING: Could not load plotly JS: {e}")

    def create_html(self, data, timestamp_col, selected_params, engine, show_grid=True, show_legend=True):
        """Generate Plotly HTML using TSAnalysisEngine for data extraction"""
        self.traces = []

        color_map = {
            'power':             '#3498DB',
            'wind_speed':        '#2ECC71',
            'rotor_speed':       '#E67E22',
            'yaw_speed':         '#9B59B6',
            'nacelle_direction': '#1ABC9C',
            'voltage_phase_a':   '#00CED1',
            'voltage_phase_b':   '#FF6B6B',
            'voltage_phase_c':   '#4ECDC4',
            'frequency':         '#FFD93D',
        }

        label_map = {
            'power':             'Power (kW)',
            'wind_speed':        'Wind Speed (m/s)',
            'rotor_speed':       'Rotor Speed (rpm)',
            'yaw_speed':         'Nacelle Angle (deg/s)',
            'nacelle_direction': 'Wind Direction (deg)',
            'voltage_phase_a':   'Voltage Phase A (V)',
            'voltage_phase_b':   'Voltage Phase B (V)',
            'voltage_phase_c':   'Voltage Phase C (V)',
            'frequency':         'Frequency (Hz)',
        }

        for param in selected_params:
            col       = param['column']
            param_key = param['param_key']
            power_type = param.get('power_type')

            if col not in data.columns:
                continue

            if param_key == 'power':
                plot_data = engine.get_power_data(data, col, power_type)
            else:
                plot_data = engine.get_plot_data(data, col, param_key, power_type)

            if plot_data is None:
                continue

            x_vals = plot_data['timestamps']
            y_vals = plot_data['values']

            if not x_vals or not y_vals:
                continue

            x_vals = [
                pd.Timestamp(t).isoformat() if pd.notna(t) else None
                for t in x_vals
            ]

            label = param.get('display', label_map.get(param_key, col))

            self.traces.append({
                'x':             x_vals,
                'y':             y_vals,
                'name':          label,
                'type':          'scatter',
                'mode':          'lines',
                'line':          {'color': color_map.get(param_key, '#3498DB'), 'width': 2},
                'hovertemplate': f'<b>{label}</b><br>%{{x}}<br>%{{y:.2f}}<extra></extra>',
            })

        self.layout = {
            'title': 'Time Series Analysis',
            'xaxis': {
                'title': 'Time',
                'type':  'date',
                'rangeslider': {'visible': True, 'thickness': 0.05},
                'rangeselector': {
                    'buttons': [
                        {'count': 6,  'label': '6h', 'step': 'hour'},
                        {'count': 1,  'label': '1d', 'step': 'day'},
                        {'count': 7,  'label': '1w', 'step': 'day'},
                        {'step': 'all', 'label': 'All'},
                    ]
                },
                'showgrid': show_grid,
            },
            'yaxis': {
                'title':    'Value',
                'showgrid': show_grid,
            },
            'hovermode':    'x unified',
            'plot_bgcolor': '#1a1a1a',
            'paper_bgcolor':'#2C3E50',
            'font':   {'color': '#ECF0F1', 'size': 11},
            'margin': {'l': 60, 'r': 40, 't': 40, 'b': 60},
            'showlegend': show_legend,
            'legend': {'x': 0.01, 'y': 0.99, 'bgcolor': 'rgba(0,0,0,0.5)'},
        }

        if self._plotly_js_inline:
            script_tag = f"<script>{self._plotly_js_inline}</script>"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    {script_tag}
    <style>
        body {{ margin: 0; padding: 0; background: #2C3E50; font-family: Arial, sans-serif; }}
        #plot {{ width: 100%; height: 100vh; }}
    </style>
</head>
<body>
    <div id="plot"></div>
    <script>
        function initPlot() {{
            if (typeof Plotly === 'undefined') {{
                setTimeout(initPlot, 100);
                return;
            }}
            var data   = {json.dumps(self.traces)};
            var layout = {json.dumps(self.layout)};
            var config = {{
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['lasso2d', 'select2d']
            }};
            Plotly.newPlot('plot', data, layout, config);
        }}
        initPlot();
    </script>
</body>
</html>"""
        return html