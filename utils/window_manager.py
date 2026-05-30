from PyQt5.QtCore import QSettings

class WindowManager:
    """Manages SDI windows - one window per turbine per analysis type"""
    
    def __init__(self):
        self.windows = {}  # {(turbine_id, window_type): window_instance}
    
    def get_or_create(self, turbine_id, window_type, window_class, *args, **kwargs):
        """Get existing window or create new one"""
        key = (turbine_id, window_type)
        
        if key in self.windows and self.windows[key].isVisible():
            # Bring existing window to front
            self.windows[key].raise_()
            self.windows[key].activateWindow()
            return self.windows[key]
        
        # Create new window
        window = window_class(*args, **kwargs)
        self.windows[key] = window
        window.destroyed.connect(lambda: self.windows.pop(key, None))
        return window
    
    def close_all(self):
        """Close all managed windows"""
        for window in list(self.windows.values()):
            window.close()
