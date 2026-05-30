from typing import Optional, Any, Dict
import pandas as pd
from PyQt5.QtWidgets import QWidget

class CentralizedDataManager:
    """Centralized data passing manager for all sub-applications"""
    
    @staticmethod
    def create_app(app_class, data: pd.DataFrame, **kwargs) -> Any:
        """
        Centralized method to create any sub-application with data
        
        Args:
            app_class: The application class to instantiate
            data: DataFrame to pass to the application
            **kwargs: Additional parameters (turbine_name, parent, etc.)
        
        Returns:
            Instance of the application
        """
        try:
            # Validate data
            if data is None or data.empty:
                raise ValueError("Data cannot be None or empty")
            
            # Create app instance with standardized parameters
            app_instance = app_class(
                data=data,
                turbine_name=kwargs.get('turbine_name'),
                parent=kwargs.get('parent'),
                project_id = kwargs.get('project_id') # call the project id
            )
            
            return app_instance
            
        except Exception as e:
            print(f"Error creating {app_class.__name__}: {e}")
            raise

    @staticmethod
    def get_standard_params(turbine_combo, parent) -> Dict[str, Any]:
        """Get standardized parameters for app creation"""
        return {
            'turbine_name': turbine_combo.currentText() if turbine_combo.currentText() else None,
            'parent': parent
        }
