from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class CollapsibleSection(QWidget):
    def __init__(self, title, content_widget, expanded=False, parent=None):
        super().__init__(parent)
        self.title = title
        self.toggle_button = QPushButton(f"{title}")
        self.toggle_button.setCheckable(True) 
        self.toggle_button.setChecked(expanded)
        self.toggle_button.setStyleSheet("""
            color: white;             /* White text */
            font-weight: bold;  text-align: left; padding: 5px; 
            border: 1px solid #B0B0B0;  /* Rectangular border */
            border-radius: 3px;""")
        self.content_area = content_widget
        self.content_area.setVisible(expanded)
        layout = QVBoxLayout()
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_area)
        self.setLayout(layout)
        self.toggle_button.toggled.connect(self.on_toggled)
        self.update_icon()

    def on_toggled(self, checked):
        self.content_area.setVisible(checked)
        self.update_icon()

    def update_icon(self):
        if self.toggle_button.isChecked():
            self.toggle_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
            self.toggle_button.setText(f"{self.title}")
        else:
            self.toggle_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
            self.toggle_button.setText(f"{self.title}")
