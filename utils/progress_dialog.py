# from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
# from PyQt5.QtCore import Qt
# from PyQt5.QtGui import QFont

# class AnimatedProgressDialog(QDialog):
#     def __init__(self, parent=None, title="Processing", message="Please wait..."):
#         super().__init__(parent)
#         self.setWindowTitle(title)
#         self.setFixedSize(400, 120)
#         self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
#         self.setModal(True)
        
#         layout = QVBoxLayout(self)
        
#         self.label = QLabel(message)
#         self.label.setAlignment(Qt.AlignCenter)
#         font = QFont()
#         font.setPointSize(10)
#         self.label.setFont(font)
#         layout.addWidget(self.label)
        
#         self.progress = QProgressBar()
#         self.progress.setRange(0, 100)
#         self.progress.setValue(0)
#         layout.addWidget(self.progress)
        
#         self.setStyleSheet("""
#             QDialog {
#                 background-color: #2C3E50;
#             }
#             QLabel {
#                 color: #ECF0F1;
#                 font-size: 14px;
#                 padding: 10px;
#             }
#             QProgressBar {
#                 border: 2px solid #3498DB;
#                 border-radius: 5px;
#                 text-align: center;
#                 background-color: #34495E;
#                 color: #ECF0F1;
#             }
#             QProgressBar::chunk {
#                 background-color: #3498DB;
#             }
#         """)
    
#     def set_progress(self, value, message):
#         self.progress.setValue(value)
#         self.label.setText(message)

# utils/progress_dialog.py (UPDATE EXISTING)
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont

class AnimatedProgressDialog(QDialog):
    def __init__(self, parent=None, title="Processing", message="Please wait..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 150)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        layout.addWidget(self.label)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate by default
        layout.addWidget(self.progress)
        
        self.error_btn = QPushButton("Retry")
        self.error_btn.hide()
        self.error_btn.clicked.connect(self.retry_requested)
        layout.addWidget(self.error_btn)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2C3E50;
            }
            QLabel {
                color: #ECF0F1;
                font-size: 14px;
                padding: 10px;
            }
            QProgressBar {
                border: 2px solid #3498DB;
                border-radius: 5px;
                text-align: center;
                background-color: #34495E;
                color: #ECF0F1;
            }
            QProgressBar::chunk {
                background-color: #3498DB;
            }
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        
        self._retry_callback = None
    
    def set_progress(self, value, message):
        """Update progress with smooth transition"""
        if self.progress.maximum() == 0:
            self.progress.setRange(0, 100)
        
        # Smooth animation
        self.anim = QPropertyAnimation(self.progress, b"value")
        self.anim.setDuration(300)
        self.anim.setStartValue(self.progress.value())
        self.anim.setEndValue(value)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.start()
        
        self.label.setText(message)
    
    def set_success(self, message="Success!"):
        """Transition to success state"""
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.label.setText(f"✓ {message}")
        self.label.setStyleSheet("color: #2ECC71; font-weight: bold;")
        
        # Auto-close after 1 second
        QTimer.singleShot(1000, self.accept)
    
    def set_error(self, message, retry_callback=None):
        """Transition to error state"""
        self.progress.hide()
        self.label.setText(f"✗ {message}")
        self.label.setStyleSheet("color: #E74C3C; font-weight: bold;")
        
        if retry_callback:
            self._retry_callback = retry_callback
            self.error_btn.show()
    
    def retry_requested(self):
        if self._retry_callback:
            self.error_btn.hide()
            self.progress.show()
            self.label.setStyleSheet("color: #ECF0F1;")
            self._retry_callback()
