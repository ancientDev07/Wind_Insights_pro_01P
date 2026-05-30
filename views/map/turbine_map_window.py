from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

class TurbineMapWindow(QMainWindow):
    def __init__(self, map_controller):
        super().__init__()
        self.map_controller = map_controller
        self.setWindowTitle("Turbine Location Map")
        self.setGeometry(100, 100, 1000, 700)
        
        self.web_view = QWebEngineView()
        self.setCentralWidget(self.web_view)
        
        map_path = self.map_controller.create_map()
        self.web_view.setUrl(QUrl.fromLocalFile(map_path))
