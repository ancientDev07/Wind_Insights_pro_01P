from PyQt5.QtGui import *
# def apply_styles(self):
#         """Apply Wind Data Insight Pro compatible theme styles"""
#         palette = QPalette()
#         palette.setColor(QPalette.Window, QColor(44, 62, 80))  # Match main app background
#         self.setPalette(palette)
        
#         self.setStyleSheet("""
#             QMainWindow { 
#                 background-color: #2C3E50; 
#                 color: #ECF0F1;
#             }
#             QGroupBox { 
#                 font-weight: bold; 
#                 border: 1px solid #B0B0B0; 
#                 border-radius: 3px; 
#                 margin-top: 10px; 
#                 padding-top: 15px;
#                 background-color: #34495E;
#                 color: #ECF0F1;
#             }
#             QGroupBox::title { 
#                 subcontrol-origin: margin; 
#                 subcontrol-position: top left; 
#                 padding: 0 5px;
#                 color: #ECF0F1;
#                 font-weight: bold;
#                 font-size: 10pt;
#             }
#             QPushButton { 
#                 background-color: #0078d7; 
#                 color: white; 
#                 border: none; 
#                 padding: 6px 12px; 
#                 border-radius: 4px; 
#                 font-weight: 500;
#             }
#             QPushButton:hover { 
#                 background-color: #005a9e; 
#             }
#             QPushButton:pressed { 
#                 background-color: #004578; 
#             }
#             QComboBox, QLineEdit { 
#                 padding: 4px; 
#                 border: 1px solid #ccc; 
#                 border-radius: 4px; 
#                 background-color: #ffffff; 
#                 color: black;
#                 selection-background-color: #e6f3ff; 
#                 selection-color: black;
#             }
#             QCheckBox { 
#                 spacing: 5px; 
#                 color: #ECF0F1;
#                 font-size: 14px;
#             }
#             QRadioButton {
#                 spacing: 5px;
#                 color: #ECF0F1;
#                 font-size: 14px;
#             }
#             QLabel {
#                 color: #ECF0F1;
#                 font-size: 14px;
#             }
#             QListWidget {
#                 gridline-color: lightgray; 
#                 selection-background-color: lightblue; 
#                 selection-color: black;
#                 background-color: white;
#                 alternate-background-color: #f9f9f9;
#                 border: 1px solid #ccc;
#                 border-radius: 4px;
#             }
#             QListWidget::item {
#                 padding: 5px;
#                 border-bottom: 1px solid #f0f0f0;
#             }
#             QListWidget::item:selected {
#                 background-color: lightblue;
#                 color: black;
#             }
#             QTextEdit {
#                 background-color: white;
#                 color: black;
#                 border: 1px solid #ccc;
#                 border-radius: 4px;
#                 padding: 4px;
#             }
#             QScrollArea {
#                 border: 1px solid #ccc;
#                 border-radius: 4px;
#                 background-color: #34495E;
#             }
#             QFrame {
#                 background-color: #34495E;
#                 border: 1px solid #B0B0B0;
#             }
#             QMenuBar {
#                 background-color: #34495E;
#                 color: #ECF0F1;
#                 font-size: 12px;
#             }
#             QMenuBar::item {
#                 background-color: transparent;
#                 padding: 4px 8px;
#             }
#             QMenuBar::item:selected {
#                 background-color: #005a9e;
#             }
#             QMenu {
#                 background-color: #34495E;
#                 color: #ECF0F1;
#                 border: 1px solid #B0B0B0;
#             }
#             QMenu::item:selected {
#                 background-color: #005a9e;
#             }
#         """)


def apply_styles(self):
    """Apply light industry-standard theme styles"""
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(255, 255, 255))  # White background
    self.setPalette(palette)
    
    self.setStyleSheet("""
        QMainWindow { 
            background-color: #FFFFFF; 
            color: #323130;
            font-family: 'Segoe UI', 'Times New Roman', sans-serif;
        }
        QGroupBox { 
            font-weight: 600; 
            border: 1px solid #EDEBE9; 
            border-radius: 4px; 
            margin-top: 10px; 
            padding-top: 15px;
            background-color: #F3F2F1;
            color: #323130;
        }
        QGroupBox::title { 
            subcontrol-origin: margin; 
            subcontrol-position: top left; 
            padding: 0 5px;
            color: #323130;
            font-weight: 600;
            font-size: 10pt;
        }
        QPushButton { 
            background-color: #0078D4; 
            color: #FFFFFF; 
            border: none; 
            padding: 8px 16px; 
            border-radius: 4px; 
            font-weight: 500;
            font-family: 'Segoe UI', 'Times New Roman', sans-serif;
        }
        QPushButton:hover { 
            background-color: #106EBE; 
        }
        QPushButton:pressed { 
            background-color: #005A9E; 
        }
        QComboBox, QLineEdit { 
            padding: 8px; 
            border: 1px solid #EDEBE9; 
            border-radius: 4px; 
            background-color: #FFFFFF; 
            color: #323130;
            selection-background-color: #0078D4; 
            selection-color: #FFFFFF;
            font-family: 'Segoe UI', 'Times New Roman', sans-serif;
        }
        QComboBox:focus, QLineEdit:focus {
            border: 2px solid #0078D4;
        }
        QCheckBox, QRadioButton { 
            spacing: 5px; 
            color: #323130;
            font-size: 14px;
            font-family: 'Segoe UI', 'Times New Roman', sans-serif;
        }
        QLabel {
            color: #323130;
            font-size: 14px;
            font-family: 'Segoe UI', 'Times New Roman', sans-serif;
        }
        QListWidget {
            gridline-color: #EDEBE9; 
            selection-background-color: #0078D4; 
            selection-color: #FFFFFF;
            background-color: #FFFFFF;
            alternate-background-color: #F3F2F1;
            border: 1px solid #EDEBE9;
            border-radius: 4px;
            font-family: 'Segoe UI', 'Times New Roman', sans-serif;
        }
        QListWidget::item {
            padding: 8px;
            border-bottom: 1px solid #F3F2F1;
        }
        QListWidget::item:selected {
            background-color: #0078D4;
            color: #FFFFFF;
        }
        QTextEdit {
            background-color: #FFFFFF;
            color: #323130;
            border: 1px solid #EDEBE9;
            border-radius: 4px;
            padding: 8px;
            font-family: 'Segoe UI', 'Times New Roman', sans-serif;
        }
        QScrollArea {
            border: 1px solid #EDEBE9;
            border-radius: 4px;
            background-color: #F3F2F1;
        }
        QFrame {
            background-color: #F3F2F1;
            border: 1px solid #EDEBE9;
        }
        QMenuBar {
            background-color: #F3F2F1;
            color: #323130;
            font-size: 12px;
            font-family: 'Segoe UI', 'Times New Roman', sans-serif;
        }
        QMenuBar::item {
            background-color: transparent;
            padding: 8px 12px;
        }
        QMenuBar::item:selected {
            background-color: #0078D4;
            color: #FFFFFF;
        }
        QMenu {
            background-color: #FFFFFF;
            color: #323130;
            border: 1px solid #EDEBE9;
            font-family: 'Segoe UI', 'Times New Roman', sans-serif;
        }
        QMenu::item:selected {
            background-color: #0078D4;
            color: #FFFFFF;
        }
    """)
