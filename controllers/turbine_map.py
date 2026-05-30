import folium
import os
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

class TurbineMapController:
    def __init__(self, db_manager, project_id):
        self.db_manager = db_manager
        self.project_id = project_id
        self.web_view = None
        
    def get_map_widget(self):
        """Return QWebEngineView widget with map"""
        coords_df = self.db_manager.get_coordinate_data(self.project_id)
        
        if coords_df.empty or coords_df['latitude'].isna().all():
            raise ValueError("No coordinate data available")
        
        center_lat = coords_df['latitude'].mean()
        center_lon = coords_df['longitude'].mean()
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        
        for _, row in coords_df.iterrows():
            folium.Marker(
                [row['latitude'], row['longitude']],
                popup=f"{row['wtg_id']}<br>Elev: {row['elevation']}m",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
        
        # Use absolute path
        html_path = os.path.abspath('temp_turbine_map.html')
        m.save(html_path)
        
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl.fromLocalFile(html_path))
        return self.web_view
