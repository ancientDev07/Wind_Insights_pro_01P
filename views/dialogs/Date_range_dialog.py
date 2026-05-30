from PyQt5.QtWidgets import QDialog, QDateTimeEdit, QVBoxLayout, QPushButton, QLabel, QMessageBox, QHBoxLayout
from PyQt5.QtCore import QDateTime
from datetime import datetime

class DateRangeDialog(QDialog):
    def __init__(self, parent=None, min_date=None, max_date=None):
        super().__init__(parent)
        self.setWindowTitle("Select Date Range")
        layout = QVBoxLayout(self)
        
        # Start date picker
        self.start_date = QDateTimeEdit(self)
        self.start_date.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.start_date.setDateTime(min_date or QDateTime.currentDateTime())
        layout.addWidget(QLabel("Start Date:"))
        layout.addWidget(self.start_date)
        
        # End date picker
        self.end_date = QDateTimeEdit(self)
        self.end_date.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.end_date.setDateTime(max_date or QDateTime.currentDateTime())
        layout.addWidget(QLabel("End Date:"))
        layout.addWidget(self.end_date)
        
        # Set min/max dates if provided
        if min_date:
            self.start_date.setMinimumDateTime(min_date)
            self.end_date.setMinimumDateTime(min_date)
        if max_date:
            self.start_date.setMaximumDateTime(max_date)
            self.end_date.setMaximumDateTime(max_date)
        
        # Buttons
        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.validate_and_accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)

    def validate_and_accept(self):
        if self.start_date.dateTime() > self.end_date.dateTime():
            QMessageBox.warning(self, "Invalid Range", "Start date must be before end date")
            return
        self.accept()