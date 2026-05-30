# controllers/help.py
from PyQt5.QtWidgets import *

def open_tutorials():
    QMessageBox.information(None, 'Tutorials', 'Opening learning resources')

def report_issue():
    QMessageBox.information(None, 'Support', 'Opening issue reporting interface')

def open_documentation():
    QMessageBox.information(None, 'Documentation', 'Opening user guide')

def check_updates():
    QMessageBox.information(None, 'Check Updates', 'Checking for updates')

def show_about():
    QMessageBox.about(None, "About Application", "This is Wind Data Insight Pro - Advanced Analytics Platform.")
