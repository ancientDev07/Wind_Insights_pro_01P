# controllers/file_handler.py
import os
import pandas as pd
from PyQt5.QtCore import *
from utils.logger import log_info, log_error
from controllers.database.database_manager import DatabaseManager
from utils.error_handler import handle_error_simple


class FileHandlerSignals(QObject):
    turbine_data_loaded = pyqtSignal(pd.DataFrame)
    turbine_ids_available = pyqtSignal(list)
    clustering_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    status_update = pyqtSignal(str)

class FileHandler(QObject):
    def __init__(self):
        super().__init__()
        self.signals = FileHandlerSignals()
        self.db_manager = DatabaseManager()
        self.project_id = None
        self.turbine_files = {}
    
    def set_project_id(self, project_id):
        """Set project ID and load turbine list from database"""
        self.project_id = project_id
        self.load_project_from_database(project_id)
    
    def load_project_from_database(self, project_id):
        """Load project data from database and emit signals"""
        try:
            self.signals.status_update.emit("Loading turbines from database...")
            
            # Get turbine list
            turbines = self.db_manager.get_turbines(project_id)
            
            if not turbines:
                raise ValueError("No turbines found in database")
            
            # Create turbine_files dict (for compatibility)
            self.turbine_files = {turbine: None for turbine in turbines}
            
            # Emit signals
            self.signals.turbine_ids_available.emit(turbines)
            self.signals.clustering_completed.emit(self.turbine_files)
            
            # Load first turbine
            self.load_turbine_data(turbines[0])
         # CRITICAL: Load first turbine data AFTER dropdown is populated
            # Use QTimer to ensure dropdown is ready
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.load_turbine_data(turbines[0]))
            
        except Exception as e:
            # log_error(f"Failed to load from database: {e}")
            # self.signals.error_occurred.emit(str(e))
            # NEW:
            handle_error_simple(e, f"Failed to load from database: {str(e)}", show_dialog=False)
            self.signals.error_occurred.emit(str(e))
    
    def load_turbine_data(self, turbine):
        """Load turbine data from database"""
        try:
            if not self.project_id:
                raise ValueError("No project loaded")
            
            self.signals.status_update.emit(f"Loading {turbine}...")
            
            turbine_data = self.db_manager.get_turbine_data(self.project_id, turbine)
            
            self.signals.turbine_data_loaded.emit(turbine_data)
            self.signals.status_update.emit(f"✅ Loaded {turbine}")
            
        except Exception as e:
            # log_error(f"Failed to load turbine data: {e}")
            # self.signals.error_occurred.emit(f"Failed to load turbine: {str(e)}")
            # NEW:
            handle_error_simple(e, f"Failed to load turbine: {str(e)}", show_dialog=False)
            self.signals.error_occurred.emit(f"Failed to load turbine: {str(e)}")
    
    def cleanup(self):
        if self.db_manager:
            self.db_manager.close()
