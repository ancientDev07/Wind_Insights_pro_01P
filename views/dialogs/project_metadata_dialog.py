import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class ProjectMetadataDialog(QDialog):
    def __init__(self, parent=None, existing_metadata=None):
        super().__init__(parent)
        self.existing_metadata = existing_metadata or {}
        self.file_paths = {}
        
        # Adobe-style Dark Theme
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; color: #D3D3D3; font-family: 'Segoe UI', Arial; }
            
            /* GROUPS */
            QGroupBox { 
                font-weight: bold; border: 1px solid #333333; border-radius: 6px; 
                margin-top: 20px; padding-top: 15px; background: #252526; 
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #5DADE2; }
            
            /* INPUTS */
            QLineEdit { 
                padding: 8px; border: 1px solid #333333; border-radius: 4px; 
                background: #1E1E1E; color: #FFFFFF; selection-background-color: #094771;
            }
            QLineEdit:focus { border: 1px solid #5DADE2; }
            
            /* LABELS */
            QLabel { color: #CCCCCC; font-size: 13px; }
            QLabel#titleLabel { font-size: 18px; font-weight: 600; color: #FFFFFF; margin-bottom: 10px; }
            QLabel#fileLabel { color: #888888; font-style: italic; font-size: 12px; }
            
            /* BUTTONS */
            QPushButton { 
                padding: 8px 16px; border-radius: 4px; font-weight: bold; font-size: 13px;
            }
            QPushButton#primaryButton { 
                background-color: #094771; color: white; border: none; 
            }
            QPushButton#primaryButton:hover { background-color: #0d5c91; }
            
            QPushButton#secondaryButton { 
                background-color: #3A3D41; color: white; border: 1px solid #454545; 
            }
            QPushButton#secondaryButton:hover { background-color: #45494d; }
            
            QPushButton#fileButton { 
                background-color: #333333; color: #D3D3D3; border: 1px solid #444; padding: 5px 10px;
            }
            QPushButton#fileButton:hover { background-color: #444; border-color: #666; }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Create New Project")
        self.setFixedSize(600, 720)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        title = QLabel("New Project Details")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        
        # 1. Project Info Group
        info_group = QGroupBox("General Information")
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(15)
        
        self.name_edit = QLineEdit(self.existing_metadata.get("name", ""))
        self.name_edit.setPlaceholderText("e.g. Alpha Wind Farm")
        
        self.location_edit = QLineEdit(self.existing_metadata.get("location", ""))
        self.company_edit = QLineEdit(self.existing_metadata.get("company", ""))
        self.capacity_edit = QLineEdit(self.existing_metadata.get("capacity", ""))
        self.model_edit = QLineEdit(self.existing_metadata.get("model_name", ""))
        
        info_layout.addRow("Project Name *", self.name_edit)
        info_layout.addRow("Location", self.location_edit)
        info_layout.addRow("Company", self.company_edit)
        info_layout.addRow("Capacity (MW)", self.capacity_edit)
        info_layout.addRow("Turbine Model", self.model_edit)
        
        layout.addWidget(info_group)
        
        # 2. Data Files Group
        files_group = QGroupBox("Data Source Configuration")
        files_layout = QVBoxLayout(files_group)
        files_layout.setSpacing(12)
        
        self.coord_label = self.create_file_row(files_layout, "Coordinates *", "coordinate")
        self.data_label = self.create_file_row(files_layout, "SCADA Data *", "data")
        self.air_label = self.create_file_row(files_layout, "Air Density *", "air_density")
        # self.oem_label = self.create_file_row(files_layout, "OEM Data (Opt)", "oem")
        
        layout.addWidget(files_group)
        layout.addStretch()
        
        # 3. Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("secondaryButton")
        self.clear_btn.clicked.connect(self.clear_form)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("Create Project")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.validate_and_accept)
        
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)

    def create_file_row(self, layout, label_text, file_key):
        """Helper to create consistent file upload rows"""
        row = QHBoxLayout()
        
        lbl = QLabel(label_text)
        lbl.setFixedWidth(100)
        
        path_lbl = QLabel("No file selected")
        path_lbl.setObjectName("fileLabel")
        path_lbl.setWordWrap(True)
        
        btn = QPushButton("Browse")
        btn.setObjectName("fileButton")
        btn.setFixedWidth(80)
        btn.clicked.connect(lambda: self.browse_file(file_key, path_lbl))
        
        row.addWidget(lbl)
        row.addWidget(path_lbl, 1) # Stretch factor 1 to take available space
        row.addWidget(btn)
        
        layout.addLayout(row)
        return path_lbl

    def browse_file(self, file_type, label_widget):
        file_filters = "Supported Files (*.csv *.xlsx *.xls);;All Files (*)"
        file_path, _ = QFileDialog.getOpenFileName(self, f"Select {file_type} File", "", file_filters)
        
        if file_path:
            self.file_paths[file_type] = file_path
            label_widget.setText(os.path.basename(file_path))
            label_widget.setStyleSheet("color: #ECF0F1; font-style: normal;") # Highlight logic

    def validate_and_accept(self):
        # 1. Name Validation
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Project Name is required.")
            self.name_edit.setFocus()
            return
        
        # 2. Files Validation
        required = ["coordinate", "data", "air_density"]
        missing = [key for key in required if key not in self.file_paths]
        
        if missing:
            pretty_missing = "\n".join([f"• {m.replace('_', ' ').title()}" for m in missing])
            QMessageBox.warning(self, "Missing Files", f"Please upload the following required files:\n{pretty_missing}")
            return
            
        self.accept()

    def get_metadata(self):
        return {
            "name": self.name_edit.text().strip(),
            "location": self.location_edit.text().strip(),
            "company": self.company_edit.text().strip(),
            "capacity": self.capacity_edit.text().strip(),
            "model_name": self.model_edit.text().strip(),
            "files": self.file_paths.copy()
        }

    def clear_form(self):
        self.name_edit.clear()
        self.location_edit.clear()
        self.company_edit.clear()
        self.capacity_edit.clear()
        self.model_edit.clear()
        self.file_paths.clear()
        
        # Reset labels
        for lbl in [self.coord_label, self.data_label, self.air_label, self.oem_label]:
            lbl.setText("No file selected")
            lbl.setStyleSheet("color: #888888; font-style: italic;")