import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class ModelDetailsDialog(QDialog):
    """Dialog for single turbine model details"""
    
    def __init__(self, parent=None, model_data=None):
        super().__init__(parent)
        self.model_data = model_data or {}
        self.file_paths = self.model_data.get('files', {}).copy()
        self.setup_ui()
        self.load_existing_data()
    
    def setup_ui(self):
        self.setWindowTitle("Turbine Model Details")
        self.setFixedSize(650, 700)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog { 
                background-color: #1E1E1E; 
                color: #D3D3D3; 
                font-family: 'Segoe UI', Arial; 
            }
            QGroupBox { 
                font-weight: bold; 
                border: 1px solid #333333; 
                border-radius: 6px; 
                margin-top: 20px; 
                padding-top: 15px; 
                background: #252526; 
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 10px; 
                padding: 0 5px; 
                color: #5DADE2; 
            }
            QLineEdit, QTextEdit { 
                padding: 8px; 
                border: 1px solid #333333; 
                border-radius: 4px; 
                background: #1E1E1E; 
                color: #FFFFFF; 
                selection-background-color: #094771;
            }
            QLineEdit:focus, QTextEdit:focus { 
                border: 1px solid #5DADE2; 
            }
            QLabel { 
                color: #CCCCCC; 
                font-size: 13px; 
            }
            QLabel#titleLabel { 
                font-size: 18px; 
                font-weight: 600; 
                color: #FFFFFF; 
                margin-bottom: 10px; 
            }
            QLabel#fileLabel { 
                color: #888888; 
                font-style: italic; 
                font-size: 12px; 
            }
            QPushButton { 
                padding: 8px 16px; 
                border-radius: 4px; 
                font-weight: bold; 
                font-size: 13px;
            }
            QPushButton#primaryButton { 
                background-color: #094771; 
                color: white; 
                border: none; 
            }
            QPushButton#primaryButton:hover { 
                background-color: #0d5c91; 
            }
            QPushButton#secondaryButton { 
                background-color: #3A3D41; 
                color: white; 
                border: 1px solid #454545; 
            }
            QPushButton#secondaryButton:hover { 
                background-color: #45494d; 
            }
            QPushButton#fileButton { 
                background-color: #333333; 
                color: #D3D3D3; 
                border: 1px solid #444; 
                padding: 5px 10px;
            }
            QPushButton#fileButton:hover { 
                background-color: #444; 
                border-color: #666; 
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Turbine Model Configuration")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        
        # We'll add the form in the next step
        self.create_form_sections(layout)
        
        # Dialog buttons
        self.create_dialog_buttons(layout)
    
    def create_form_sections(self, parent_layout):
        """Create all form sections"""
        
        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        # Basic Info Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(12)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Vestas V90-2.0")
        
        self.manufacturer_edit = QLineEdit()
        self.manufacturer_edit.setPlaceholderText("e.g. Vestas")
        
        self.version_edit = QLineEdit()
        self.version_edit.setPlaceholderText("e.g. Mk7")
        
        basic_layout.addRow("Model Name *", self.name_edit)
        basic_layout.addRow("Manufacturer", self.manufacturer_edit)
        basic_layout.addRow("Version", self.version_edit)
        
        scroll_layout.addWidget(basic_group)
        
        # Technical Specs Group
        specs_group = QGroupBox("Technical Specifications")
        specs_layout = QFormLayout(specs_group)
        specs_layout.setSpacing(12)
        
        self.capacity_edit = QLineEdit()
        self.capacity_edit.setPlaceholderText("e.g. 2000")
        
        self.hub_height_edit = QLineEdit()
        self.hub_height_edit.setPlaceholderText("e.g. 80")
        
        self.rotor_diameter_edit = QLineEdit()
        self.rotor_diameter_edit.setPlaceholderText("e.g. 90")
        
        self.cut_in_edit = QLineEdit()
        self.cut_in_edit.setPlaceholderText("e.g. 3.0")
        
        self.cut_out_edit = QLineEdit()
        self.cut_out_edit.setPlaceholderText("e.g. 25.0")
        
        self.rated_speed_edit = QLineEdit()
        self.rated_speed_edit.setPlaceholderText("e.g. 12.0")
        
        specs_layout.addRow("Rated Capacity (kW) *", self.capacity_edit)
        specs_layout.addRow("Hub Height (m)", self.hub_height_edit)
        specs_layout.addRow("Rotor Diameter (m)", self.rotor_diameter_edit)
        specs_layout.addRow("Cut-in Speed (m/s)", self.cut_in_edit)
        specs_layout.addRow("Cut-out Speed (m/s)", self.cut_out_edit)
        specs_layout.addRow("Rated Speed (m/s)", self.rated_speed_edit)
        
        scroll_layout.addWidget(specs_group)
        
        # Files Group
        files_group = QGroupBox("Model-Specific Files")
        files_layout = QVBoxLayout(files_group)
        files_layout.setSpacing(10)
        
        self.power_curve_label = self.create_file_row(files_layout, "Power Curve *", "power_curve")
        self.spec_label = self.create_file_row(files_layout, "Specifications", "specifications")
        self.oem_label = self.create_file_row(files_layout, "OEM Data", "oem_data")
        
        scroll_layout.addWidget(files_group)
        
        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Additional notes or comments...")
        self.notes_edit.setMaximumHeight(80)
        notes_layout.addWidget(self.notes_edit)
        
        scroll_layout.addWidget(notes_group)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        parent_layout.addWidget(scroll)

    def create_dialog_buttons(self, parent_layout):
        """Create dialog action buttons"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("Save Model")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.validate_and_accept)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        parent_layout.addLayout(button_layout)

    def create_file_row(self, parent_layout, label_text, file_key):
        """Create file upload row"""
        row = QHBoxLayout()
        
        lbl = QLabel(label_text)
        lbl.setFixedWidth(120)
        
        path_lbl = QLabel("No file selected")
        path_lbl.setObjectName("fileLabel")
        path_lbl.setWordWrap(True)
        
        btn = QPushButton("Browse")
        btn.setObjectName("fileButton")
        btn.setFixedWidth(80)
        btn.clicked.connect(lambda: self.browse_file(file_key, path_lbl))
        
        row.addWidget(lbl)
        row.addWidget(path_lbl, 1)
        row.addWidget(btn)
        
        parent_layout.addLayout(row)
        return path_lbl
    
    def browse_file(self, file_type, label_widget):
        """Browse and attach file"""
        if file_type == "power_curve":
            file_filter = "Data Files (*.csv *.xlsx *.xls);;All Files (*)"
        elif file_type == "specifications" or file_type == "oem_data":
            file_filter = "Documents (*.pdf *.xlsx *.xls *.csv);;All Files (*)"
        else:
            file_filter = "All Files (*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            f"Select {file_type.replace('_', ' ').title()}", 
            "", 
            file_filter
        )
        
        if file_path:
            # Validate power curve
            if file_type == "power_curve":
                if not self.validate_power_curve(file_path):
                    return
            
            self.file_paths[file_type] = file_path
            label_widget.setText(os.path.basename(file_path))
            label_widget.setStyleSheet("color: #5DADE2; font-style: normal; font-weight: bold;")

    def validate_power_curve(self, file_path):
        """Validate power curve file"""
        try:
            import pandas as pd
            import models.scada_utils as su
            
            df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)
            df.columns = df.columns.str.strip().str.lower()
            
            ws_cols = su.find_matching_columns(df, 'wind_speed')
            power_cols = su.find_matching_columns(df, 'power')
            
            if not ws_cols or not power_cols:
                QMessageBox.warning(
                    self,
                    "Invalid Power Curve",
                    f"Power curve file must contain 'wind_speed' and 'power' columns.\n\nFound columns: {', '.join(df.columns)}"
                )
                return False
            
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "File Error", f"Failed to read power curve file:\n{str(e)}")
            return False

    def load_existing_data(self):
        """Load existing model data into form"""
        if not self.model_data:
            return
        
        self.name_edit.setText(self.model_data.get('model_name', ''))
        self.manufacturer_edit.setText(self.model_data.get('manufacturer', ''))
        self.version_edit.setText(self.model_data.get('version', ''))
        
        if self.model_data.get('rated_capacity'):
            self.capacity_edit.setText(str(self.model_data['rated_capacity']))
        if self.model_data.get('hub_height'):
            self.hub_height_edit.setText(str(self.model_data['hub_height']))
        if self.model_data.get('rotor_diameter'):
            self.rotor_diameter_edit.setText(str(self.model_data['rotor_diameter']))
        if self.model_data.get('cut_in_speed'):
            self.cut_in_edit.setText(str(self.model_data['cut_in_speed']))
        if self.model_data.get('cut_out_speed'):
            self.cut_out_edit.setText(str(self.model_data['cut_out_speed']))
        if self.model_data.get('rated_speed'):
            self.rated_speed_edit.setText(str(self.model_data['rated_speed']))
        
        self.notes_edit.setPlainText(self.model_data.get('notes', ''))
        
        # Update file labels
        files = self.model_data.get('files', {})
        if files.get('power_curve'):
            self.power_curve_label.setText(os.path.basename(files['power_curve']))
            self.power_curve_label.setStyleSheet("color: #5DADE2; font-style: normal; font-weight: bold;")
        if files.get('specifications'):
            self.spec_label.setText(os.path.basename(files['specifications']))
            self.spec_label.setStyleSheet("color: #5DADE2; font-style: normal; font-weight: bold;")
        if files.get('oem_data'):
            self.oem_label.setText(os.path.basename(files['oem_data']))
            self.oem_label.setStyleSheet("color: #5DADE2; font-style: normal; font-weight: bold;")

    def validate_and_accept(self):
        """Validate form before accepting"""
        # 1. Model name required
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Model Name is required.")
            self.name_edit.setFocus()
            return
        
        # 2. Rated capacity required
        if not self.capacity_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Rated Capacity is required.")
            self.capacity_edit.setFocus()
            return
        
        # 3. Validate capacity is numeric
        try:
            float(self.capacity_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Rated Capacity must be a number.")
            self.capacity_edit.setFocus()
            return
        
        # 4. Power curve required
        if 'power_curve' not in self.file_paths:
            QMessageBox.warning(self, "Validation Error", "Power Curve file is required.")
            return
        
        self.accept()

    def browse_file(self, file_type, label_widget):
        """Browse and attach file"""
        if file_type == "power_curve":
            file_filter = "Data Files (*.csv *.xlsx *.xls);;All Files (*)"
        elif file_type == "specifications" or file_type == "oem_data":
            file_filter = "Documents (*.pdf *.xlsx *.xls *.csv);;All Files (*)"
        else:
            file_filter = "All Files (*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            f"Select {file_type.replace('_', ' ').title()}", 
            "", 
            file_filter
        )
        
        if file_path:
            # Validate power curve
            if file_type == "power_curve":
                if not self.validate_power_curve(file_path):
                    return
            
            self.file_paths[file_type] = file_path
            label_widget.setText(os.path.basename(file_path))
            label_widget.setStyleSheet("color: #5DADE2; font-style: normal; font-weight: bold;")

    def validate_power_curve(self, file_path):
        """Validate power curve file"""
        try:
            import pandas as pd
            import models.scada_utils as su
            
            df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)
            df.columns = df.columns.str.strip().str.lower()
            
            ws_cols = su.find_matching_columns(df, 'wind_speed')
            power_cols = su.find_matching_columns(df, 'power')
            
            if not ws_cols or not power_cols:
                QMessageBox.warning(
                    self,
                    "Invalid Power Curve",
                    f"Power curve file must contain 'wind_speed' and 'power' columns.\n\nFound columns: {', '.join(df.columns)}"
                )
                return False
            
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "File Error", f"Failed to read power curve file:\n{str(e)}")
            return False

    def load_existing_data(self):
        """Load existing model data into form"""
        if not self.model_data:
            return
        
        self.name_edit.setText(self.model_data.get('model_name', ''))
        self.manufacturer_edit.setText(self.model_data.get('manufacturer', ''))
        self.version_edit.setText(self.model_data.get('version', ''))
        
        if self.model_data.get('rated_capacity'):
            self.capacity_edit.setText(str(self.model_data['rated_capacity']))
        if self.model_data.get('hub_height'):
            self.hub_height_edit.setText(str(self.model_data['hub_height']))
        if self.model_data.get('rotor_diameter'):
            self.rotor_diameter_edit.setText(str(self.model_data['rotor_diameter']))
        if self.model_data.get('cut_in_speed'):
            self.cut_in_edit.setText(str(self.model_data['cut_in_speed']))
        if self.model_data.get('cut_out_speed'):
            self.cut_out_edit.setText(str(self.model_data['cut_out_speed']))
        if self.model_data.get('rated_speed'):
            self.rated_speed_edit.setText(str(self.model_data['rated_speed']))
        
        self.notes_edit.setPlainText(self.model_data.get('notes', ''))
        
        # Update file labels
        files = self.model_data.get('files', {})
        if files.get('power_curve'):
            self.power_curve_label.setText(os.path.basename(files['power_curve']))
            self.power_curve_label.setStyleSheet("color: #5DADE2; font-style: normal; font-weight: bold;")
        if files.get('specifications'):
            self.spec_label.setText(os.path.basename(files['specifications']))
            self.spec_label.setStyleSheet("color: #5DADE2; font-style: normal; font-weight: bold;")
        if files.get('oem_data'):
            self.oem_label.setText(os.path.basename(files['oem_data']))
            self.oem_label.setStyleSheet("color: #5DADE2; font-style: normal; font-weight: bold;")

    def get_model_data(self):
        """Return model data dictionary"""
        data = {
            "model_name": self.name_edit.text().strip(),
            "manufacturer": self.manufacturer_edit.text().strip(),
            "version": self.version_edit.text().strip(),
            "notes": self.notes_edit.toPlainText().strip(),
            "files": self.file_paths.copy()
        }
        
        # Add numeric fields if provided
        if self.capacity_edit.text().strip():
            try:
                data["rated_capacity"] = float(self.capacity_edit.text())
            except:
                pass
        
        if self.hub_height_edit.text().strip():
            try:
                data["hub_height"] = float(self.hub_height_edit.text())
            except:
                pass
        
        if self.rotor_diameter_edit.text().strip():
            try:
                data["rotor_diameter"] = float(self.rotor_diameter_edit.text())
            except:
                pass
        
        if self.cut_in_edit.text().strip():
            try:
                data["cut_in_speed"] = float(self.cut_in_edit.text())
            except:
                pass
        
        if self.cut_out_edit.text().strip():
            try:
                data["cut_out_speed"] = float(self.cut_out_edit.text())
            except:
                pass
        
        if self.rated_speed_edit.text().strip():
            try:
                data["rated_speed"] = float(self.rated_speed_edit.text())
            except:
                pass
        
        return data
