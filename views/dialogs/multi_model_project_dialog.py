import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class MultiModelProjectDialog(QDialog):
    """Dialog for creating multi-model projects"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.models = []
        self.file_paths = {}
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; color: #D3D3D3; font-family: 'Segoe UI', Arial; }
            
            QGroupBox { 
                font-weight: bold; border: 1px solid #333333; border-radius: 6px; 
                margin-top: 20px; padding-top: 15px; background: #252526; 
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #5DADE2; }
            
            QLineEdit { 
                padding: 8px; border: 1px solid #333333; border-radius: 4px; 
                background: #1E1E1E; color: #FFFFFF; selection-background-color: #094771;
            }
            QLineEdit:focus { border: 1px solid #5DADE2; }
            
            QLabel { color: #CCCCCC; font-size: 13px; }
            QLabel#titleLabel { font-size: 18px; font-weight: 600; color: #FFFFFF; margin-bottom: 10px; }
            QLabel#fileLabel { color: #888888; font-style: italic; font-size: 12px; }
            QLabel#infoLabel { color: #5DADE2; font-size: 12px; font-weight: bold; }
            
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
            
            QListWidget {
                background: #252526; border: 1px solid #333333; border-radius: 4px;
                color: #FFFFFF; padding: 5px;
            }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #333333; }
            QListWidget::item:selected { background: #094771; }
            QListWidget::item:hover { background: #2A2D2E; }
        """)
        
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Create Multi-Model Project")
        self.setFixedSize(700, 800)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        title = QLabel("Multi-Model Project Setup")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        
        info = QLabel("💡 Create projects with multiple turbine models and their specific configurations")
        info.setObjectName("infoLabel")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # 1. Project Info Group
        info_group = QGroupBox("General Information")
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(15)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Alpha Wind Farm")
        
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("e.g. Gujarat, India")
        
        self.company_edit = QLineEdit()
        self.company_edit.setPlaceholderText("e.g. Tata Power")
        
        self.capacity_edit = QLineEdit()
        self.capacity_edit.setPlaceholderText("e.g. 100")
        
        info_layout.addRow("Project Name *", self.name_edit)
        info_layout.addRow("Location", self.location_edit)
        info_layout.addRow("Company", self.company_edit)
        info_layout.addRow("Total Capacity (MW)", self.capacity_edit)
        
        layout.addWidget(info_group)
        
        # 2. Turbine Models Group
        models_group = QGroupBox("Turbine Models Configuration")
        models_layout = QVBoxLayout(models_group)
        models_layout.setSpacing(10)
        
        # Model list with count
        list_header = QHBoxLayout()
        models_label = QLabel("Configured Models:")
        models_label.setStyleSheet("font-weight: bold; color: #5DADE2;")
        
        self.models_count_label = QLabel("0 models")
        self.models_count_label.setObjectName("fileLabel")
        
        list_header.addWidget(models_label)
        list_header.addWidget(self.models_count_label)
        list_header.addStretch()
        models_layout.addLayout(list_header)
        
        # Models list
        self.models_list = QListWidget()
        self.models_list.setMaximumHeight(150)
        self.models_list.itemDoubleClicked.connect(self.edit_model)
        models_layout.addWidget(self.models_list)
        
        # Model action buttons
        model_buttons = QHBoxLayout()
        model_buttons.setSpacing(10)
        
        self.add_model_btn = QPushButton("➕ Add Model")
        self.add_model_btn.setObjectName("primaryButton")
        self.add_model_btn.clicked.connect(self.add_model)
        
        self.edit_model_btn = QPushButton("✏️ Edit")
        self.edit_model_btn.setObjectName("secondaryButton")
        self.edit_model_btn.clicked.connect(self.edit_model)
        self.edit_model_btn.setEnabled(False)
        
        self.remove_model_btn = QPushButton("🗑️ Remove")
        self.remove_model_btn.setObjectName("secondaryButton")
        self.remove_model_btn.clicked.connect(self.remove_model)
        self.remove_model_btn.setEnabled(False)
        
        self.duplicate_btn = QPushButton("📋 Duplicate")
        self.duplicate_btn.setObjectName("secondaryButton")
        self.duplicate_btn.clicked.connect(self.duplicate_model)
        self.duplicate_btn.setEnabled(False)
        
        model_buttons.addWidget(self.add_model_btn)
        model_buttons.addWidget(self.edit_model_btn)
        model_buttons.addWidget(self.duplicate_btn)
        model_buttons.addWidget(self.remove_model_btn)
        model_buttons.addStretch()
        
        models_layout.addLayout(model_buttons)
        layout.addWidget(models_group)
        
        # 3. Common Data Files Group
        files_group = QGroupBox("Common Project Data")
        files_layout = QVBoxLayout(files_group)
        files_layout.setSpacing(12)
        
        files_info = QLabel("📌 Model-specific power curves are configured per model above")
        files_info.setObjectName("fileLabel")
        files_info.setWordWrap(True)
        files_layout.addWidget(files_info)
        
        self.coord_label = self.create_file_row(files_layout, "Coordinates *", "coordinate")
        self.data_label = self.create_file_row(files_layout, "SCADA Data *", "data")
        
        layout.addWidget(files_group)
        layout.addStretch()
        
        # 4. Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.clear_btn = QPushButton("Clear All")
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
        
        # Connect list selection
        self.models_list.itemSelectionChanged.connect(self.on_model_selection_changed)
    
    def create_file_row(self, parent_layout, label_text, file_key):
        """Helper to create file upload rows"""
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
        row.addWidget(path_lbl, 1)
        row.addWidget(btn)
        
        parent_layout.addLayout(row)
        return path_lbl
    
    def browse_file(self, file_type, label_widget):
        """Browse and attach file"""
        file_filters = "Supported Files (*.csv *.xlsx *.xls);;All Files (*)"
        file_path, _ = QFileDialog.getOpenFileName(self, f"Select {file_type} File", "", file_filters)
        
        if file_path:
            self.file_paths[file_type] = file_path
            label_widget.setText(os.path.basename(file_path))
            label_widget.setStyleSheet("color: #5DADE2; font-style: normal; font-weight: bold;")
    
    def add_model(self):
        """Add new turbine model"""
        from views.dialogs.model_details_dialog import ModelDetailsDialog
        
        dialog = ModelDetailsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            model_data = dialog.get_model_data()
            self.models.append(model_data)
            self.update_models_list()
    
    def edit_model(self):
        """Edit selected model"""
        current_row = self.models_list.currentRow()
        if current_row < 0:
            return
        
        from views.dialogs.model_details_dialog import ModelDetailsDialog
        
        dialog = ModelDetailsDialog(self, self.models[current_row])
        if dialog.exec_() == QDialog.Accepted:
            self.models[current_row] = dialog.get_model_data()
            self.update_models_list()
            self.models_list.setCurrentRow(current_row)
    
    def remove_model(self):
        """Remove selected model"""
        current_row = self.models_list.currentRow()
        if current_row < 0:
            return
        
        model_name = self.models[current_row].get('model_name', 'this model')
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove '{model_name}' from project?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.models[current_row]
            self.update_models_list()
    
    def duplicate_model(self):
        """Duplicate selected model"""
        current_row = self.models_list.currentRow()
        if current_row < 0:
            return
        
        import copy
        duplicated = copy.deepcopy(self.models[current_row])
        duplicated['model_name'] = duplicated.get('model_name', 'Model') + " (Copy)"
        
        # Clear file paths for duplicated model
        duplicated['files'] = {}
        
        self.models.append(duplicated)
        self.update_models_list()
        self.models_list.setCurrentRow(len(self.models) - 1)
    
    def update_models_list(self):
        """Update models list display"""
        self.models_list.clear()
        
        for model in self.models:
            item_text = f"🔧 {model.get('model_name', 'Unnamed')}"
            
            manufacturer = model.get('manufacturer', '')
            if manufacturer:
                item_text += f" - {manufacturer}"
            
            capacity = model.get('rated_capacity')
            if capacity:
                item_text += f" ({capacity} kW)"
            
            # Add power curve indicator
            if model.get('files', {}).get('power_curve'):
                item_text += " ✓"
            
            self.models_list.addItem(item_text)
        
        # Update count
        count = len(self.models)
        self.models_count_label.setText(f"{count} model{'s' if count != 1 else ''}")
        if count > 0:
            self.models_count_label.setStyleSheet("color: #5DADE2; font-weight: bold; font-style: normal;")
        else:
            self.models_count_label.setStyleSheet("color: #888888; font-style: italic;")
    
    def on_model_selection_changed(self):
        """Enable/disable edit/remove buttons"""
        has_selection = len(self.models_list.selectedItems()) > 0
        self.edit_model_btn.setEnabled(has_selection)
        self.remove_model_btn.setEnabled(has_selection)
        self.duplicate_btn.setEnabled(has_selection)
    
    def validate_and_accept(self):
        """Validate form before accepting"""
        # 1. Project name
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Project Name is required.")
            self.name_edit.setFocus()
            return
        
        # 2. At least one model
        if not self.models:
            QMessageBox.warning(
                self, 
                "No Models Configured", 
                "Please add at least one turbine model using the '➕ Add Model' button."
            )
            return
        
        # 3. Validate all models have power curves
        models_without_curves = [
            m.get('model_name', 'Unnamed') 
            for m in self.models 
            if not m.get('files', {}).get('power_curve')
        ]
        
        if models_without_curves:
            QMessageBox.warning(
                self,
                "Missing Power Curves",
                f"The following models are missing power curves:\n\n" + 
                "\n".join([f"• {name}" for name in models_without_curves]) +
                "\n\nPlease edit each model and attach a power curve file."
            )
            return
        
        # 4. Required common files
        required = ["coordinate", "data"]
        missing = [key for key in required if key not in self.file_paths]
        
        if missing:
            pretty_missing = "\n".join([f"• {m.replace('_', ' ').title()}" for m in missing])
            QMessageBox.warning(
                self, 
                "Missing Files", 
                f"Please upload the following required files:\n{pretty_missing}"
            )
            return
        
        self.accept()
    
    def clear_form(self):
        """Clear all form data"""
        reply = QMessageBox.question(
            self,
            "Clear Form",
            "Clear all entered data including configured models?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.name_edit.clear()
            self.location_edit.clear()
            self.company_edit.clear()
            self.capacity_edit.clear()
            self.models.clear()
            self.file_paths.clear()
            self.update_models_list()
            
            # Reset file labels
            self.coord_label.setText("No file selected")
            self.coord_label.setStyleSheet("color: #888888; font-style: italic;")
            self.data_label.setText("No file selected")
            self.data_label.setStyleSheet("color: #888888; font-style: italic;")
    
    def get_metadata(self):
        """Return project metadata"""
        return {
            "name": self.name_edit.text().strip(),
            "location": self.location_edit.text().strip(),
            "company": self.company_edit.text().strip(),
            "capacity": self.capacity_edit.text().strip(),
            "multi_model": True,  # Flag for multi-model project
            "models": self.models,
            "files": self.file_paths.copy()
        }
