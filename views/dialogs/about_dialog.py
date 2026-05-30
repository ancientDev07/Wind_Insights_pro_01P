from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("About Wind Data Insight Pro")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Logo
        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        
        # App info
        info = QLabel("""
        <h2>Wind Data Insight Pro</h2>
        <p><b>Version:</b> 1.0.0</p>
        <p><b>Developer:</b> Onkar Nigam</p>
        <p><b>Department:</b> PBU-Digital</p>
        <p><b>Company:</b> Tata Consulting Engineers</p>
        <p><b>Copyright:</b> © 2025 Tata Consulting Engineers Limited</p>
        """)
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
