import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from controllers.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

@dataclass
class ChartConfig:
    """Configuration for a single chart."""
    chart_type: str
    title: str
    parameters: List[str]
    metrics: List[str]
    enabled: bool = True

@dataclass
class ReportConfig:
    """Configuration for report generation."""
    project_id: int
    turbine_ids: List[str]
    charts: List[ChartConfig]
    include_metadata: bool = True
    include_summary: bool = True

class ReportController:
    """Centralized report generation controller."""
    
    CHART_TEMPLATES = {
        'wind_rose': {
            'name': 'Wind Rose',
            'available_params': ['wind_speed', 'nacelle_direction'],
            'default_params': ['wind_speed', 'nacelle_direction']
        },
        'wind_speed_distribution': {
            'name': 'Wind Speed Distribution',
            'available_params': ['wind_speed'],
            'default_params': ['wind_speed']
        },
        'turbulence_intensity': {
            'name': 'Turbulence Intensity',
            'available_params': ['wind_speed'],
            'default_params': ['wind_speed']
        },
        'power_curve': {
            'name': 'Power Curve',
            'available_params': ['wind_speed', 'power'],
            'default_params': ['wind_speed', 'power']
        },
        'actual_power_curve': {
            'name': 'Actual Power Curve',
            'available_params': ['wind_speed', 'power'],
            'default_params': ['wind_speed', 'power']
        },
        'binned_power_curve': {
            'name': 'Binned Power Curve',
            'available_params': ['wind_speed', 'power'],
            'default_params': ['wind_speed', 'power']
        },
        'rotor_speed_graph': {
            'name': 'Rotor Speed Over Time',
            'available_params': ['rotor_speed', 'timestamp'],
            'default_params': ['rotor_speed', 'timestamp']
        },
        'joint_distribution': {
            'name': 'Joint Distribution',
            'available_params': ['wind_speed', 'nacelle_direction'],
            'default_params': ['wind_speed', 'nacelle_direction']
        }
    }
    
    def __init__(self, project_id: int):
        self.project_id = project_id
        self.db = DatabaseManager()
        
    def get_available_turbines(self) -> List[str]:
        """Get list of turbines for project."""
        try:
            return self.db.get_turbines(self.project_id)
        except Exception as e:
            logger.error(f"Error getting turbines: {e}")
            return []
    
    def get_project_metadata(self) -> Dict:
        """Get project metadata."""
        try:
            cursor = self.db.connection.execute(
                "SELECT project_name, location, company, capacity, model_name FROM Projects WHERE project_id = ?",
                [self.project_id]
            )
            row = cursor.fetchone()
            if row:
                return {
                    'name': row[0],
                    'location': row[1],
                    'company': row[2],
                    'capacity': row[3],
                    'model_name': row[4]
                }
        except Exception as e:
            logger.error(f"Error getting metadata: {e}")
        return {}
    
    def get_available_charts(self) -> Dict:
        """Get available chart templates."""
        return self.CHART_TEMPLATES.copy()
    
    def get_turbine_data(self, turbine_id: str):
        """Get data for specific turbine."""
        return self.db.get_turbine_data(self.project_id, turbine_id)
    
    # def generate_report(self, config: ReportConfig, output_path: str) -> bool:
    #     """Generate PDF report based on configuration."""
    #     from views.visualization_components.report_gen import PDFReportBuilder
        
    #     try:
    #         builder = PDFReportBuilder(output_path)
            
    #         # Add project metadata
    #         if config.include_metadata:
    #             metadata = self.get_project_metadata()
    #             builder.add_title_page(metadata)
            
    #         # Add summary
    #         if config.include_summary:
    #             builder.add_summary_page(self.project_id, config.turbine_ids)
            
    #         # Generate charts for each turbine
    #         for turbine_id in config.turbine_ids:
    #             data = self.get_turbine_data(turbine_id)
    #             builder.add_turbine_section(turbine_id, data, config.charts)
            
    #         builder.build()
    #         return True
            
    #     except Exception as e:
    #         logger.error(f"Report generation failed: {e}")
    #         return False
    def generate_report(self, config: ReportConfig, output_path: str) -> bool:
        """Generate PDF report based on configuration."""
        from views.visualization_components.report_gen import EnhancedReportGenerator, ReportParentAdapter
        from PyQt5.QtWidgets import QWidget
        
        try:
            # Create adapter for each turbine
            for turbine_id in config.turbine_ids:
                data = self.get_turbine_data(turbine_id)
                
                # Create mock parent
                class MockParent:
                    def __init__(self, project_id, data):
                        self.project_id = project_id
                        self.data = data
                        self.current_data = data
                
                mock = MockParent(self.project_id, data)
                adapter = ReportParentAdapter(mock)
                
                # Generate report
                generator = EnhancedReportGenerator(adapter)
                generator.generate_report()
            
            return True
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return False

    
    def close(self):
        """Clean up resources."""
        if self.db:
            self.db.close()
