from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class LicenseAgreementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("License Agreement - Wind Data Insight Pro")
        self.setFixedSize(600, 500)
        self.setModal(True)

        layout = QVBoxLayout()

        # Title
        title = QLabel("End User License Agreement")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 15px 0;")
        layout.addWidget(title)

        # License text
        license_text = QTextEdit()
        license_text.setReadOnly(True)
        license_text.setHtml("""
        <h3>Wind Data Insight Pro</h3>
        <p><b>Developed by:</b> Onkar Nigam<br>
        <b>Department:</b> PBU-Digital<br>
        <b>Copyright:</b> © 2025 Tata Consulting Engineers Limited</p>

        <p><b>IMPORTANT - READ CAREFULLY:</b> This End User License Agreement ("EULA") is a legal agreement between you and Tata Consulting Engineers Limited.</p>

        <h4>1. GRANT OF LICENSE</h4>
        <p>Tata Consulting Engineers Limited grants you a license to use Wind Data Insight Pro for wind data analysis and engineering purposes.</p>

        <h4>2. PERMITTED USES</h4>
        <ul>
            <li>Use the software for wind data analysis and engineering purposes</li>
            <li>Install on authorized computers within your organization</li>
            <li>Create backups for archival purposes</li>
        </ul>

        <h4>3. RESTRICTIONS</h4>
        <ul>
            <li>You may not distribute, rent, lease, or sublicense the software</li>
            <li>You may not reverse engineer, decompile, or disassemble the software</li>
            <li>Software is for internal use only</li>
        </ul>

        <h4>4. INTELLECTUAL PROPERTY</h4>
        <p>This software is the intellectual property of Tata Consulting Engineers Limited, developed by the PBU-Digital department.</p>

        <p><b>For support, contact:</b> PBU-Digital, Tata Consulting Engineers<br>
        <b>Developer:</b> Onkar Nigam</p>
        """)
        license_text.setStyleSheet("font-size: 13px;")
        layout.addWidget(license_text)

        # Accept checkbox
        self.accept_cb = QCheckBox("I have read and accept the license agreement")
        self.accept_cb.setStyleSheet("margin: 10px 0;")
        layout.addWidget(self.accept_cb)

        # Buttons
        btn_layout = QHBoxLayout()
        self.accept_btn = QPushButton("Accept")
        self.decline_btn = QPushButton("Decline")
        self.accept_btn.setEnabled(False)

        self.accept_btn.setStyleSheet("padding: 6px 12px;")
        self.decline_btn.setStyleSheet("padding: 6px 12px;")

        btn_layout.addStretch()
        btn_layout.addWidget(self.decline_btn)
        btn_layout.addWidget(self.accept_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # Connections
        self.accept_cb.toggled.connect(self.accept_btn.setEnabled)
        self.decline_btn.clicked.connect(self.reject)
        self.accept_btn.clicked.connect(self.accept)


# if __name__ == "__main__":
#     import sys
#     app = QApplication(sys.argv)
#     dialog = LicenseAgreementDialog()
#     if dialog.exec_() == QDialog.Accepted:
#         print("License accepted. Proceeding with application...")
#         # Launch main application window here
#     else:
#         print("License declined. Exiting application.")
#         sys.exit()