from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from utils.license_manager import LicenseManager

class LicenseActivationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.license_manager = LicenseManager()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Activate Wind Data Insight Pro")
        self.setFixedSize(450, 250)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Wind Data Insight Pro Activation")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Info
        info = QLabel("Please activate your software to continue:")
        layout.addWidget(info)
        
        # License key input
        key_layout = QFormLayout()
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("WWIP-XXXX-YYYY-ZZZZ")
        key_layout.addRow("License Key:", self.key_input)
        layout.addLayout(key_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.trial_btn = QPushButton("Start 30-Day Trial")
        self.activate_btn = QPushButton("Activate License")
        self.exit_btn = QPushButton("Exit")
        
        btn_layout.addWidget(self.trial_btn)
        btn_layout.addWidget(self.activate_btn)
        btn_layout.addWidget(self.exit_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        # Connections
        self.trial_btn.clicked.connect(self.start_trial)
        self.activate_btn.clicked.connect(self.activate_license)
        self.exit_btn.clicked.connect(self.reject)
        
    def start_trial(self):
        success, message = self.license_manager._create_trial_license()
        if success:
            QMessageBox.information(self, "Trial Started", "30-day trial activated successfully!")
            self.accept()
        else:
            QMessageBox.warning(self, "Trial Error", message)
            
    def activate_license(self):
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Missing Key", "Please enter a license key")
            return
            
        success, message = self.license_manager.activate_license(key)
        if success:
            QMessageBox.information(self, "Activated", "License activated successfully!")
            self.accept()
        else:
            QMessageBox.warning(self, "Activation Failed", message)
