from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtCore import Qt
import json
import pandas as pd
from utils import datetime_utils as dtu

class UnifiedDashboard(QWidget):
    def __init__(self, db_manager, project_id):
        super().__init__()
        self.db_manager = db_manager
        self.project_id = project_id
        self.initUI()       
 
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
                
        # Web view for dashboard
        self.web_view = QWebEngineView()
        self.web_view.settings().setAttribute(QWebEngineSettings.WebGLEnabled, True)
        self.web_view.settings().setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        layout.addWidget(self.web_view)
        
        # Load turbines and initialize
        # self.load_turbines()
        self.refresh_dashboard()

    def load_turbines(self):
        """Load available turbines from database"""
        try:
            if self.project_id is None:
                print("WARNING: project_id is None, cannot load turbines")
                return
            
            turbines = self.db_manager.get_turbines(self.project_id)
            self.turbine_list = turbines
            
            self.turbine_combo.blockSignals(True)
            self.turbine_combo.clear()
            self.turbine_combo.addItem("All")
            if turbines:
                self.turbine_combo.addItems(turbines)
            self.turbine_combo.blockSignals(False)
        except Exception as e:
            print(f"Error loading turbines: {e}")
            self.turbine_combo.clear()
            self.turbine_combo.addItem("No Data")

    def on_turbine_changed(self):
        """Handle turbine selection change"""
        self.refresh_dashboard()

    def refresh_dashboard(self):
        """Refresh dashboard with current selection"""
        self.dashboard_data = self.prepare_dashboard_data_all()
        html_content = self.get_html_with_folium_map()
        self.web_view.setHtml(html_content)

    def get_html_with_folium_map(self):
        import folium
        
        # Create Folium map
        coords_df = self.db_manager.get_coordinate_data(self.project_id)
        
        if not coords_df.empty and not coords_df['latitude'].isna().all():
            center_lat = coords_df['latitude'].mean()
            center_lon = coords_df['longitude'].mean()
            m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
            
            for _, row in coords_df.iterrows():
                if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                    folium.Marker(
                        [row['latitude'], row['longitude']],
                        popup=f"{row['wtg_id']}<br>Elev: {row['elevation']}m",
                        icon=folium.Icon(color='red', icon='info-sign')
                    ).add_to(m)
            
            map_html = m._repr_html_()
        else:
            map_html = '<div style="padding:20px;color:#999;">No coordinate data available</div>'
        
        data_json = json.dumps(self.dashboard_data)
        
        return f'''<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            html, body {{ height: 100vh; font-family: 'Segoe UI', Tahoma, sans-serif; background: #2C3E50; color: #ECF0F1; overflow: hidden; }}
            #container {{ height: 100vh; display: flex; flex-direction: column; padding: 10px; }}
            .header {{ background: linear-gradient(135deg, #16A085, #1ABC9C); padding: 12px 20px; border-radius: 8px; margin-bottom: 10px; }}
            .header h1 {{ font-size: 18px; margin-bottom: 3px; }}
            .header .meta {{ font-size: 10px; opacity: 0.9; }}
            .kpi-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 10px; }}
            .kpi-card {{ background: #34495E; border: 1px solid #1ABC9C; border-radius: 6px; padding: 8px; text-align: center; }}
            .kpi-value {{ font-size: 14px; font-weight: 700; }}
            .kpi-label {{ font-size: 9px; opacity: 0.8; }}
            .main-grid {{ display: grid; grid-template-columns: 40% 60%; gap: 10px; margin-bottom: 10px; }}
            .panel {{ background: #34495E; border: 1px solid #5D6D7E; border-radius: 8px; padding: 12px; }}
            .panel-title {{ font-size: 14px; font-weight: 700; color: #1ABC9C; margin-bottom: 10px; }}
            #map {{ height: 400px; }}
            .chart-container {{ width: 100%; height: 380px; min-width: 200px; min-height: 200px; }}
            .table-panel {{ flex: 1; overflow: hidden; }}
            .table-wrapper {{ max-height: 300px; overflow-y: auto; background: #2C3E50; border-radius: 4px; }}
            .table-wrapper::-webkit-scrollbar {{ width: 8px; }}
            .table-wrapper::-webkit-scrollbar-track {{ background: #34495E; border-radius: 4px; }}
            .table-wrapper::-webkit-scrollbar-thumb {{ background: #1ABC9C; border-radius: 4px; }}
            .table-wrapper::-webkit-scrollbar-thumb:hover {{ background: #16A085; }}
            
            table {{ 
                width: 100%; 
                border-collapse: separate;
                border-spacing: 0;
                font-size: 12px;
                table-layout: fixed;
            }}
            
            thead {{ 
                position: sticky; 
                top: 0; 
                z-index: 10;
            }}
            
            th {{ 
                background: #1E2A38;
                color: #1ABC9C;
                padding: 12px 10px;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 10px;
                letter-spacing: 0.5px;
                border-bottom: 2px solid #1ABC9C;
            }}
            
            /* Column widths */
            th:nth-child(1), td:nth-child(1) {{ width: 10%; text-align: center; }}
            th:nth-child(2), td:nth-child(2) {{ width: 10%; text-align: center; }}
            th:nth-child(3), td:nth-child(3) {{ width: 20%; text-align: left; padding-left: 15px; }}
            th:nth-child(4), td:nth-child(4) {{ width: 20%; text-align: right; padding-right: 15px; }}
            th:nth-child(5), td:nth-child(5) {{ width: 20%; text-align: right; padding-right: 15px; }}
            th:nth-child(6), td:nth-child(6) {{ width: 20%; text-align: right; padding-right: 15px; }}
            
            td {{ 
                padding: 10px;
                border-bottom: 1px solid #34495E;
                color: #ECF0F1;
                transition: background 0.2s ease;
            }}
            
            tr:hover td {{ 
                background: #34495E;
            }}
            
            tr:last-child td {{
                border-bottom: none;
            }}
            
            .color-indicator {{ 
                display: inline-block; 
                width: 20px; 
                height: 12px; 
                border-radius: 3px;
                vertical-align: middle;
                box-shadow: 0 1px 3px rgba(0,0,0,0.3);
            }}
        </style>
    </head>
    <body>
        <div id="container">
            <div class="header">
                <h1>📊 {self.dashboard_data['project_name']} - InfoSights</h1>
                <div class="meta">Analysis Period: {self.dashboard_data['date_range']['start']} → {self.dashboard_data['date_range']['end']}</div>
            </div>
            <div class="kpi-grid" id="kpiGrid"></div>
            <div class="main-grid">
                <div class="panel">
                    <div class="panel-title">🗺️ TURBINE LOCATIONS</div>
                    <div id="map">{map_html}</div>
                </div>
                <div class="panel">
                    <div class="panel-title">📈 DAILY MEAN POWER</div>
                    <div class="chart-container"><canvas id="trendChart"></canvas></div>
                </div>
            </div>
            <div class="panel table-panel">
                <div class="panel-title">📋 RANKING</div>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Color</th>
                                <th>Pos</th>
                                <th>ID</th>
                                <th>Energy (MWh)</th>
                                <th>PLF (%)</th>
                                <th>Coverage (%)</th>
                            </tr>
                        </thead>
                        <tbody id="rankingBody"></tbody>
                    </table>
                </div>
            </div>
        </div>
        <script>
            const data = {data_json};
            const COLORS = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6'];
            
            document.getElementById('kpiGrid').innerHTML = data.kpis.map(k => 
                `<div class="kpi-card"><div class="kpi-value">${{k.value}} ${{k.unit}}</div><div class="kpi-label">${{k.label}}</div></div>`
            ).join('');
            
            new Chart(document.getElementById('trendChart'), {{ 
                type: 'line', 
                data: {{ 
                    labels: data.trend_data.dates, 
                    datasets: data.trend_data.turbines.map((t, i) => ({{ 
                        label: t.id, 
                        data: t.values, 
                        borderColor: COLORS[i % COLORS.length], 
                        backgroundColor: COLORS[i % COLORS.length] + '20',
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 0
                    }})) 
                }}, 
                options: {{ 
                    responsive: true, 
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: true,
                            position: 'top',
                            labels: {{ boxWidth: 12, padding: 8, font: {{ size: 10 }} }}
                        }}
                    }},
                    scales: {{
                        y: {{ beginAtZero: true }}
                    }}
                }} 
            }});
            
            document.getElementById('rankingBody').innerHTML = data.rankings.map((r, i) => 
                `<tr>
                    <td><span class="color-indicator" style="background:${{COLORS[i % COLORS.length]}}"></span></td>
                    <td>${{r.position}}</td>
                    <td>${{r.turbine_id}}</td>
                    <td>${{r.energy.toFixed(1)}}</td>
                    <td>${{r.plf.toFixed(1)}}</td>
                    <td>${{r.coverage.toFixed(1)}}</td>
                </tr>`
            ).join('');
        </script>
    </body>
    </html>'''
    
    def prepare_dashboard_data_all(self):
        """Prepare dashboard data for all turbines"""
        import models.scada_utils as su
        from views.ranking.ranking import TurbineRanker
        
        all_data = self.db_manager.get_all_turbines_data(self.project_id)
        
        id_col = su.find_matching_columns(all_data, 'turbine_id')[0]
        date_col = su.find_matching_columns(all_data, 'timestamp')[0]
        power_col = su.find_matching_columns(all_data, 'power')[0]
        ws_col = su.find_matching_columns(all_data, 'wind_speed')[0]
        
        ranker = TurbineRanker(all_data, id_col=id_col, date_col=date_col)
        ranked_df = ranker.rank_by_power_generation(power_col, iec_standard=True)
        
        coords = self.db_manager.get_coordinate_data(self.project_id)
        
        settings = QWebEngineSettings.globalSettings()
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        return {
            'project_name': self._get_project_name(),
            'date_range': {
                'start': all_data[date_col].min().strftime('%Y-%m-%d'),
                'end': all_data[date_col].max().strftime('%Y-%m-%d')
            },
            'kpis': [
                {'label': 'Turbines Analyzed', 'value': str(len(ranked_df)), 'unit': 'units'},
                {'label': 'Mean Power', 'value': f"{all_data[power_col].mean():.1f}", 'unit': 'kW'},
                {'label': 'Mean PLF', 'value': f"{ranked_df['capacity_factor'].mean():.1f}", 'unit': '%'},
                {'label': 'Mean Wind Speed', 'value': f"{all_data[ws_col].mean():.1f}", 'unit': 'm/s'},
                {'label': 'Total Energy', 'value': f"{ranked_df['total_generation'].sum()/1000:.1f}", 'unit': 'MWh'}
            ],
            'trend_data': self._get_turbine_trends(all_data, id_col, date_col, power_col, ranked_df),
            'rankings': [
                {
                    'position': int(row['rank']),
                    'turbine_id': str(row[id_col]),
                    'energy': float(row['total_generation'] / 1000),
                    'plf': float(row['capacity_factor']),
                    'coverage': float(row['availability_factor'])
                }
                for _, row in ranked_df.iterrows()
            ]
        }

    def prepare_dashboard_data_single(self, turbine_id):
        """Prepare dashboard data for a single turbine"""
        import models.scada_utils as su
        
        turbine_data = self.db_manager.get_turbine_data(self.project_id, turbine_id)
        
        date_col = su.find_matching_columns(turbine_data, 'timestamp')[0]
        power_col = su.find_matching_columns(turbine_data, 'power')[0]
        ws_col = su.find_matching_columns(turbine_data, 'wind_speed')[0]
        
        turbine_data[date_col] = dtu.parse_and_normalize_timestamps(turbine_data[date_col])
        turbine_data['date'] = turbine_data[date_col].dt.date
        daily_avg = turbine_data.groupby('date')[power_col].mean()
        
        total_energy = turbine_data[power_col].sum() / 1000
        mean_power = turbine_data[power_col].mean()
        mean_ws = turbine_data[ws_col].mean()
        
        return {
            'project_name': self._get_project_name(),
            'date_range': {
                'start': turbine_data[date_col].min().strftime('%Y-%m-%d'),
                'end': turbine_data[date_col].max().strftime('%Y-%m-%d')
            },
            'kpis': [
                {'label': 'Turbine ID', 'value': turbine_id, 'unit': ''},
                {'label': 'Mean Power', 'value': f"{mean_power:.1f}", 'unit': 'kW'},
                {'label': 'Total Energy', 'value': f"{total_energy:.1f}", 'unit': 'MWh'},
                {'label': 'Mean Wind Speed', 'value': f"{mean_ws:.1f}", 'unit': 'm/s'},
                {'label': 'Max Power', 'value': f"{turbine_data[power_col].max():.1f}", 'unit': 'kW'}
            ],
            'trend_data': {
                'dates': [str(d) for d in daily_avg.index],
                'turbines': [{
                    'id': turbine_id,
                    'values': [float(v) for v in daily_avg.values]
                }]
            },
            'rankings': [{
                'position': 1,
                'turbine_id': turbine_id,
                'energy': total_energy,
                'plf': 0.0,
                'coverage': 100.0
            }]
        }
    
    def _get_project_name(self):
        cursor = self.db_manager.connection.execute(
            "SELECT project_name FROM Projects WHERE project_id = ?", 
            [self.project_id]
        )
        result = cursor.fetchone()
        return result[0] if result else "Unknown Project"

    def _get_turbine_trends(self, data, id_col, date_col, power_col, ranked_df):
        daily = data.copy()
        daily[date_col] = dtu.parse_and_normalize_timestamps(daily[date_col])
        daily = daily[daily[date_col].notna()]
        daily['date'] = daily[date_col].dt.date
        
        all_dates = sorted(daily['date'].unique())
        
        if len(all_dates) == 0:
            return {'dates': [], 'turbines': []}
        
        turbine_trends = []
        for _, row in ranked_df.iterrows():
            turbine_id = row[id_col]
            turbine_data = daily[daily[id_col] == turbine_id]
            daily_avg = turbine_data.groupby('date')[power_col].mean().reindex(all_dates, fill_value=0)
            
            turbine_trends.append({
                'id': str(turbine_id),
                'values': [float(v) for v in daily_avg.values]
            })
        
        return {
            'dates': [str(d) for d in all_dates],
            'turbines': turbine_trends
        }