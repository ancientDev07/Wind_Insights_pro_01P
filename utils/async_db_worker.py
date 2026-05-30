# utils/async_db_worker.py
from PyQt5.QtCore import QThread, pyqtSignal

class AsyncDBWorker(QThread):
    progress = pyqtSignal(str)
    success = pyqtSignal(int, list)
    error = pyqtSignal(str)
    
    def __init__(self, metadata, data_file):
        super().__init__()
        self.metadata = metadata
        self.data_file = data_file
    
    def run(self):
        try:
            from controllers.database.database_manager import DatabaseManager
            
            self.progress.emit("Initializing database...")
            db = DatabaseManager()
            
            self.progress.emit("Creating project...")
            project_id, turbines = db.create_project_from_metadata(
                self.metadata,
                self.data_file,
                progress_callback=lambda msg: self.progress.emit(msg)
            )
            
            db.close()
            self.success.emit(project_id, turbines)
            
        except Exception as e:
            self.error.emit(str(e))
